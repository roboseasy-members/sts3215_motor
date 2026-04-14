import threading
from dataclasses import dataclass

from st3215 import ST3215


@dataclass
class MotorStatus:
    position: int = 0
    speed: int = 0
    temperature: int = 0
    voltage: float = 0.0
    current: float = 0.0
    load: int = 0
    is_moving: bool = False


class MotorController:
    def __init__(self):
        self._servo: ST3215 | None = None
        self._lock = threading.Lock()
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self, port: str, retries: int = 2, retry_delay: float = 0.6) -> None:
        """시리얼 포트에 연결. PermissionError 등 일시적 실패 시 자동 재시도."""
        import time
        last_exc: Exception | None = None
        for attempt in range(retries + 1):
            try:
                with self._lock:
                    self._servo = ST3215(port)
                    self._connected = True
                return
            except Exception as e:
                last_exc = e
                # 이전 실패로 열린 핸들이 남아있을 가능성 — 정리 후 재시도
                self._servo = None
                self._connected = False
                import gc
                gc.collect()
                if attempt < retries:
                    time.sleep(retry_delay)
        # 모든 재시도 실패
        if last_exc is not None:
            raise last_exc

    def disconnect(self) -> None:
        """시리얼 포트를 명시적으로 닫고 모든 참조를 제거한다.
        (Windows에서 다음 연결 시 PermissionError(13) 방지)"""
        import gc
        with self._lock:
            if self._servo is not None:
                # ST3215 라이브러리는 내부적으로 portHandler(scservo_sdk PortHandler)를 가짐
                try:
                    ph = getattr(self._servo, "portHandler", None)
                    if ph is not None:
                        try:
                            ph.closePort()
                        except Exception:
                            pass
                        # pyserial 래퍼일 경우 직접 close 시도
                        ser = getattr(ph, "ser", None)
                        if ser is not None:
                            try:
                                ser.close()
                            except Exception:
                                pass
                except Exception:
                    pass
            self._servo = None
            self._connected = False
        # OS가 핸들을 확실히 반환하도록 GC 강제 실행
        gc.collect()

    def scan_motors(self, id_range: range = range(1, 30)) -> list[int]:
        found = []
        with self._lock:
            if not self._servo:
                return found
            for motor_id in id_range:
                try:
                    if self._servo.PingServo(motor_id):
                        found.append(motor_id)
                except Exception:
                    continue
        return found

    def ping(self, motor_id: int) -> bool:
        with self._lock:
            if not self._servo:
                return False
            try:
                return bool(self._servo.PingServo(motor_id))
            except Exception:
                return False

    def move_to(self, motor_id: int, position: int, speed: int = 700, acceleration: int = 50) -> None:
        with self._lock:
            if not self._servo:
                raise ConnectionError("Not connected")
            self._servo.SetSpeed(motor_id, speed)
            self._servo.SetAcceleration(motor_id, acceleration)
            self._servo.MoveTo(motor_id, position)

    def read_position(self, motor_id: int) -> int:
        """위치만 빠르게 읽기 (시리얼 1회). read_status는 7회 읽기로 느림.

        실패 시 ConnectionError/RuntimeError 예외 발생 (0 반환 안 함).
        """
        with self._lock:
            if not self._servo:
                raise ConnectionError("Not connected")
            pos = self._servo.ReadPosition(motor_id)
            if isinstance(pos, tuple):
                pos = pos[0] if pos else None
            if pos is None:
                raise RuntimeError(f"ReadPosition(ID={motor_id}) 응답 없음")
            return int(pos)

    def read_status(self, motor_id: int) -> MotorStatus:
        with self._lock:
            if not self._servo:
                raise ConnectionError("Not connected")
            s = self._servo
            return MotorStatus(
                position=s.ReadPosition(motor_id),
                speed=s.ReadSpeed(motor_id),
                temperature=s.ReadTemperature(motor_id),
                voltage=s.ReadVoltage(motor_id),
                current=s.ReadCurrent(motor_id),
                load=s.ReadLoad(motor_id),
                is_moving=s.IsMoving(motor_id),
            )

    def stop(self, motor_id: int) -> None:
        with self._lock:
            if not self._servo:
                raise ConnectionError("Not connected")
            self._servo.StopServo(motor_id)

    def set_torque(self, motor_id: int, enable: bool) -> None:
        with self._lock:
            if not self._servo:
                raise ConnectionError("Not connected")
            if enable:
                self._servo.StartServo(motor_id)
            else:
                self._servo.StopServo(motor_id)

    def change_id(self, current_id: int, new_id: int) -> None:
        with self._lock:
            if not self._servo:
                raise ConnectionError("Not connected")
            result = self._servo.ChangeId(current_id, new_id)
            if result is not None:
                raise RuntimeError(str(result))

    def change_id_broadcast(self, new_id: int) -> None:
        """브로드캐스트로 버스에 연결된 모터의 ID를 변경한다.
        모터가 1대만 연결된 상태에서 사용해야 한다."""
        BROADCAST_ID = 0xFE
        STS_ID = 5
        STS_LOCK = 55
        with self._lock:
            if not self._servo:
                raise ConnectionError("Not connected")
            s = self._servo
            s.write1ByteTxOnly(BROADCAST_ID, STS_LOCK, 0)   # EPROM 잠금 해제
            s.write1ByteTxOnly(BROADCAST_ID, STS_ID, new_id) # ID 변경
            s.write1ByteTxOnly(BROADCAST_ID, STS_LOCK, 1)   # EPROM 잠금
