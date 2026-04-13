"""
시리얼 포트 스캔 유틸리티
"""
import serial.tools.list_ports


def get_available_ports():
    """
    사용 가능한 시리얼 포트 목록을 반환
    
    Returns:
        list: 포트 이름 리스트 (예: ['COM3', 'COM7'])
    """
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]


def get_port_info(port_name):
    """
    특정 포트의 상세 정보를 반환
    
    Args:
        port_name (str): 포트 이름 (예: 'COM7')
    
    Returns:
        dict: 포트 정보 (description, hwid 등)
    """
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.device == port_name:
            return {
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid
            }
    return None
