"""Google OAuth 2.0 Desktop 플로우 래퍼.

Robot Studio 로그인 게이트에서 사용. 기본 브라우저로 구글 로그인 페이지를 열고
loopback(`http://localhost:<랜덤포트>/`) 으로 토큰을 수신한다.

토큰은 OS 표준 설정 디렉토리에 저장되어 다음 실행 시 자동 로그인에 사용된다.
- Linux:   ~/.config/Roboseasy/auth.json
- Windows: %APPDATA%\\Roboseasy\\auth.json
- macOS:   ~/Library/Application Support/Roboseasy/auth.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import requests

from resources import resource_path

# 요청 스코프 — 민감 스코프가 아니어서 구글 앱 심사 불필요.
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

# 브라우저 리다이렉트 성공 화면에 표시되는 문구(HTML 내 삽입됨).
_SUCCESS_MESSAGE = (
    "Robot Studio 로그인에 성공했습니다. 이 창을 닫고 앱으로 돌아가주세요."
)

_APP_DIR_NAME = "Roboseasy"
_TOKEN_FILENAME = "auth.json"


def _app_config_dir() -> Path:
    """플랫폼별 사용자 설정 디렉토리(Roboseasy 전용)."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif os.uname().sysname == "Darwin":  # type: ignore[attr-defined]
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    d = base / _APP_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def _token_path() -> Path:
    return _app_config_dir() / _TOKEN_FILENAME


def _client_secret_path() -> str:
    """GCP Desktop OAuth 클라이언트 JSON 경로.

    PyInstaller 번들에선 `sys._MEIPASS/oauth_client.json`, 개발 모드에선
    `resource/oauth_client.json` 를 가리킨다.
    """
    return resource_path("oauth_client.json")


def load_saved_credentials() -> Optional[Credentials]:
    """저장된 refresh token 으로 유효한 Credentials 를 복원.

    - 토큰 파일이 없거나 손상됐으면 None.
    - access token 만 만료된 경우 자동으로 refresh 후 저장하고 반환.
    - refresh 자체가 실패(사용자가 구글에서 revoke 등) 하면 토큰 파일을 지우고 None.
    """
    path = _token_path()
    if not path.exists():
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(path), SCOPES)
    except Exception:
        # 손상된 토큰 파일 → 삭제하고 재로그인 유도
        try:
            path.unlink()
        except OSError:
            pass
        return None

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            # 서버에서 revoke 되었거나 네트워크 문제 → 로그인 다시 받기
            try:
                path.unlink()
            except OSError:
                pass
            return None
        _save_credentials(creds)
        return creds

    return None


def sign_in_with_google() -> Credentials:
    """브라우저 기반 OAuth 플로우 실행 (블로킹).

    GUI 코드에서 직접 호출하면 UI 스레드가 멈추므로 반드시 QThread 등
    백그라운드 스레드에서 호출해야 한다.
    """
    client_secret = _client_secret_path()
    if not os.path.isfile(client_secret):
        raise FileNotFoundError(
            f"OAuth 클라이언트 설정 파일을 찾을 수 없습니다: {client_secret}\n"
            "resource/oauth_client.json 이 배포에 포함되어 있는지 확인하세요."
        )

    flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
    # port=0: OS 가 비어있는 로컬 포트 자동 할당 → 여러 인스턴스 동시 실행 대응
    creds = flow.run_local_server(
        port=0,
        open_browser=True,
        success_message=_SUCCESS_MESSAGE,
        timeout_seconds=300,
    )
    _save_credentials(creds)
    return creds


def fetch_user_info(creds: Credentials) -> Dict[str, Any]:
    """구글 OpenID userinfo 엔드포인트에서 프로필 조회.

    반환 딕셔너리 주요 키: `sub`(구글 user ID, 구독 DB 키로 사용 예정),
    `email`, `email_verified`, `name`, `given_name`, `picture`.
    """
    resp = requests.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {creds.token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def sign_out() -> None:
    """저장된 토큰 파일 삭제(로컬 로그아웃). 서버측 revoke 는 하지 않음."""
    path = _token_path()
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass


def _save_credentials(creds: Credentials) -> None:
    path = _token_path()
    path.write_text(creds.to_json(), encoding="utf-8")
    # 토큰 파일은 사용자 외엔 읽을 수 없게 제한 (POSIX 에서만 의미)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
