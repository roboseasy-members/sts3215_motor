"""Robot Studio 시작 화면 + 구글 로그인 게이트.

흐름:
    1. 웰컴 화면에서 "시작하기" 클릭
    2. QThread 에서 `google_oauth.sign_in_with_google()` 실행 → 기본 브라우저 오픈
    3. 사용자가 구글 로그인 완료 → 로컬 루프백 서버가 토큰 수신
    4. `fetch_user_info` 로 프로필 조회 후 `self.user_info` 에 저장하고 accept()

반환(accept 후 접근 가능):
    - `self.credentials`: google.oauth2.credentials.Credentials
    - `self.user_info`: dict (sub/email/name/picture 포함)
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from auth.google_oauth import fetch_user_info, sign_in_with_google
from resources import resource_path

STYLESHEET = """
QDialog {
    background-color: #F5F3F8;
}
QFrame#headerBar {
    background-color: #3B1D6B;
    border: none;
}
QLabel#headerTitle {
    color: rgba(255,255,255,0.95);
    font-size: 16px;
    font-weight: bold;
}
QLabel#headerSubtitle {
    color: rgba(255,255,255,0.55);
    font-size: 11px;
}
QLabel#brandTitle {
    color: #2D2640;
    font-size: 38px;
    font-weight: 700;
    letter-spacing: 1px;
}
QLabel#brandSubtitle {
    color: #6B5B8A;
    font-size: 14px;
}
QLabel#statusLabel {
    color: #6B5B8A;
    font-size: 12px;
}
QPushButton#startBtn {
    background-color: #2D2640;
    color: rgba(255,255,255,0.95);
    border: none;
    border-radius: 10px;
    font-size: 16px;
    font-weight: 700;
    padding: 16px 32px;
    min-width: 360px;
    min-height: 52px;
}
QPushButton#startBtn:hover {
    background-color: #3B1D6B;
}
QPushButton#startBtn:pressed {
    background-color: #1C1628;
}
QPushButton#startBtn:disabled {
    background-color: #9E94B0;
    color: rgba(255,255,255,0.8);
}
QPushButton#quitBtn {
    background-color: transparent;
    color: #6B5B8A;
    border: 1px solid #C9BFD9;
    border-radius: 6px;
    font-size: 12px;
    padding: 6px 16px;
}
QPushButton#quitBtn:hover {
    background-color: #EDE7F3;
}
"""


class _GoogleSignInWorker(QThread):
    """백그라운드 스레드에서 OAuth 플로우 실행.

    `run_local_server` 는 블로킹이라 UI 스레드에서 돌리면 안 됨.
    """

    succeeded = pyqtSignal(object, dict)  # Credentials, user_info
    failed = pyqtSignal(str)  # error message (사용자에게 노출)

    def run(self) -> None:  # noqa: D401 - QThread 규약
        try:
            creds = sign_in_with_google()
            user_info = fetch_user_info(creds)
        except FileNotFoundError as e:
            self.failed.emit(str(e))
            return
        except Exception as e:
            self.failed.emit(f"로그인에 실패했습니다.\n({type(e).__name__}: {e})")
            return
        self.succeeded.emit(creds, user_info)


class WelcomeDialog(QDialog):
    """Robot Studio 웰컴 + 구글 로그인 화면."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Robot Studio — 로보시지")
        self.setFixedSize(760, 560)
        self.setStyleSheet(STYLESHEET)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint
        )

        self.credentials: Optional[Any] = None
        self.user_info: Optional[Dict[str, Any]] = None
        self._worker: Optional[_GoogleSignInWorker] = None

        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        root.addWidget(self._build_header())
        root.addLayout(self._build_body())

    # ── Header (모드 선택 화면과 동일한 보라색 바) ──

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("headerBar")
        header.setFixedHeight(52)
        h = QHBoxLayout(header)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(10)

        logo_path = resource_path("logo.png")
        if os.path.isfile(logo_path):
            logo_label = QLabel()
            pix = QPixmap(logo_path).scaledToHeight(
                28, Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(pix)
        else:
            logo_label = QLabel("LOGO")
            logo_label.setFixedSize(60, 28)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_label.setStyleSheet(
                "background-color: rgba(255,255,255,0.12); border-radius: 6px;"
                "color: rgba(255,255,255,0.7); font-size: 11px; font-weight: bold;"
            )
        h.addWidget(logo_label)

        sep = QFrame()
        sep.setFixedSize(1, 20)
        sep.setStyleSheet("background-color: rgba(255,255,255,0.2);")
        h.addWidget(sep)

        title = QLabel("Robot Studio")
        title.setObjectName("headerTitle")
        h.addWidget(title)

        h.addStretch()

        subtitle = QLabel("by 로보시지")
        subtitle.setObjectName("headerSubtitle")
        h.addWidget(subtitle)

        return header

    # ── Body (브랜드 로고 + 시작하기 버튼) ──

    def _build_body(self) -> QVBoxLayout:
        body = QVBoxLayout()
        body.setSpacing(18)
        body.setContentsMargins(40, 40, 40, 24)

        body.addStretch(1)

        # 큰 로고 — resource/logo.png 를 220px 로 확대 표시
        logo_path = resource_path("logo.png")
        logo_row = QHBoxLayout()
        logo_row.addStretch()
        if os.path.isfile(logo_path):
            big_logo = QLabel()
            big_logo.setPixmap(
                QPixmap(logo_path).scaledToHeight(
                    180, Qt.TransformationMode.SmoothTransformation
                )
            )
            logo_row.addWidget(big_logo)
        logo_row.addStretch()
        body.addLayout(logo_row)

        # 브랜드 타이틀
        title = QLabel("Robot Studio")
        title.setObjectName("brandTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.addWidget(title)

        subtitle = QLabel("로봇 세팅의 가장 쉬운 방법")
        subtitle.setObjectName("brandSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.addWidget(subtitle)

        body.addSpacing(8)

        # 시작하기 버튼
        self._start_btn = QPushButton("시작하기")
        self._start_btn.setObjectName("startBtn")
        self._start_btn.clicked.connect(self._on_start_clicked)
        start_row = QHBoxLayout()
        start_row.addStretch()
        start_row.addWidget(self._start_btn)
        start_row.addStretch()
        body.addLayout(start_row)

        # 상태 메시지(로그인 진행 중 안내 / 에러 복구 안내)
        self._status_label = QLabel(
            "구글 계정으로 로그인하면 Robot Studio를 시작할 수 있습니다."
        )
        self._status_label.setObjectName("statusLabel")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setWordWrap(True)
        body.addWidget(self._status_label)

        body.addStretch(1)

        # 종료 버튼(우하단)
        quit_row = QHBoxLayout()
        quit_row.addStretch()
        quit_btn = QPushButton("종료")
        quit_btn.setObjectName("quitBtn")
        quit_btn.clicked.connect(self.reject)
        quit_row.addWidget(quit_btn)
        body.addLayout(quit_row)

        return body

    # ── Slots ──

    def _on_start_clicked(self) -> None:
        # 이미 진행 중이면 무시
        if self._worker is not None and self._worker.isRunning():
            return

        self._start_btn.setEnabled(False)
        self._start_btn.setText("로그인 중...")
        self._status_label.setText(
            "브라우저가 열렸습니다. 구글 계정으로 로그인을 완료해주세요."
        )

        self._worker = _GoogleSignInWorker(self)
        self._worker.succeeded.connect(self._on_signin_succeeded)
        self._worker.failed.connect(self._on_signin_failed)
        self._worker.start()

    def _on_signin_succeeded(self, creds: Any, user_info: Dict[str, Any]) -> None:
        self.credentials = creds
        self.user_info = user_info
        self.accept()

    def _on_signin_failed(self, message: str) -> None:
        self._start_btn.setEnabled(True)
        self._start_btn.setText("시작하기")
        self._status_label.setText("다시 시도해주세요.")
        QMessageBox.warning(self, "로그인 실패", message)

    # 창을 닫을 때 스레드가 남아있지 않도록 정리
    def reject(self) -> None:  # type: ignore[override]
        self._stop_worker()
        super().reject()

    def accept(self) -> None:  # type: ignore[override]
        self._stop_worker()
        super().accept()

    def _stop_worker(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            # run_local_server 는 중간 취소가 어려워 타임아웃(5분) 으로만 종료됨.
            # 창을 먼저 닫고 스레드는 백그라운드에서 자연 종료되도록 둔다.
            self._worker.quit()
