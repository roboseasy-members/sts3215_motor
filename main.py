import os
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from auth.google_oauth import fetch_user_info, load_saved_credentials, sign_out
from auth.supabase_client import upsert_user
from resources import resource_path
from ui.id_setup_wizard import IdSetupWizard
from ui.main_window import MainWindow
from ui.mode_select_dialog import (
    MODE_ID_SETUP,
    MODE_LOGOUT,
    MODE_SINGLE,
    MODE_SOARM101,
    ModeSelectDialog,
)
from ui.soarm101_window import SoArm101Window
from ui.welcome_dialog import WelcomeDialog


def _set_windows_app_id():
    """Windows 작업표시줄에서 이 앱을 python.exe와 분리해 고유 아이콘으로 표시하도록 설정.
    AppUserModelID를 지정하지 않으면 Windows가 Python 호스트로 그룹화해 기본 아이콘이 표시됨."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        app_id = "RoboSEasy.STS3215MotorTest.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        # 실패해도 기능에는 영향 없음
        pass


def main():
    _set_windows_app_id()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    # GNOME Shell 등이 창을 .desktop 파일에 매칭해 올바른 아이콘을 표시하도록 지정.
    # AppImage 내부 .desktop 의 StartupWMClass 및 파일명(Roboseasy.desktop) 과 일치해야 함.
    app.setApplicationName("Roboseasy")
    app.setDesktopFileName("Roboseasy")

    # 작업표시줄/타이틀바 아이콘 설정 — 가능한 경우 .ico 우선 (Windows 표시 품질 우수), 아니면 .png
    icon_ico = resource_path("icon.ico")
    icon_png = resource_path("icon.png")
    icon_path = icon_ico if os.path.isfile(icon_ico) else icon_png
    if os.path.isfile(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 외부 루프: 로그아웃 시 웰컴 화면으로 복귀하기 위한 재진입 지점.
    while True:
        # ── 로그인 게이트 ─────────────────────────────────────────────
        # 저장된 refresh_token 이 있으면 조용히 자동 로그인, 없으면 웰컴 화면을 띄움.
        # 로그인 실패/취소 시 앱 종료(오프라인/스킵 모드는 의도적으로 미지원).
        user_info = None
        creds = load_saved_credentials()
        if creds is not None:
            try:
                user_info = fetch_user_info(creds)
            except Exception:
                # 네트워크 일시 오류 등 — 웰컴 화면으로 폴백
                creds = None

        if user_info is None:
            welcome = WelcomeDialog()
            if welcome.exec() != WelcomeDialog.DialogCode.Accepted:
                sys.exit(0)
            user_info = welcome.user_info

        # Supabase users 테이블에 프로필 upsert. 실패해도 앱은 계속 동작 —
        # 오프라인/설정 누락 환경에서 모터 기능까지 막지 않기 위함.
        if user_info and user_info.get("sub") and user_info.get("email"):
            upsert_user(
                sub=user_info["sub"],
                email=user_info["email"],
                name=user_info.get("name"),
            )

        # ── 모드 선택 + 창 실행 루프 ───────────────────────────────
        logout_requested = False
        while True:
            dialog = ModeSelectDialog()
            if dialog.exec() != ModeSelectDialog.DialogCode.Accepted:
                sys.exit(0)

            mode = dialog.selected_mode

            if mode == MODE_LOGOUT:
                sign_out()
                logout_requested = True
                break

            if mode == MODE_ID_SETUP:
                window = IdSetupWizard()
            elif mode == MODE_SINGLE:
                window = MainWindow(mode=MODE_SINGLE)
            elif mode == MODE_SOARM101:
                window = SoArm101Window()
            else:
                sys.exit(0)

            window.show()

            back_requested = False

            def on_back():
                nonlocal back_requested
                back_requested = True
                window.close()

            window.back_to_menu.connect(on_back)
            app.exec()

            if not back_requested:
                sys.exit(0)

        if not logout_requested:
            break


if __name__ == "__main__":
    main()
