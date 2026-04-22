"""Supabase user DB upsert (경량 PostgREST 클라이언트).

Google OAuth 로 로그인한 사용자를 `public.users` 테이블에 upsert 하기 위해서만 존재.
supabase-py 는 gotrue/storage/realtime 등 여러 하위 모듈을 끌고 와서 PyInstaller
번들이 커지므로, 여기서는 PostgREST 엔드포인트를 `requests` 로 직접 호출한다.

보안 주의(A안):
    현재 RLS 정책은 anon 키로 모든 row 를 INSERT/UPDATE 할 수 있게 열려 있다. 즉
    앱에 동봉된 anon 키가 유출되면 임의의 더미 row 로 테이블이 오염될 수 있다.
    정식 릴리즈 / 운영 전에는 반드시 B안(Edge Function 에서 Google ID token 검증
    후 insert) 으로 이관해야 한다. 관련 체크리스트는 CLAUDE.md 참고.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import requests

from resources import resource_path

_CONFIG_FILENAME = "supabase_config.json"
_TABLE = "users"
_TIMEOUT = 10  # 초 — 네트워크 지연이 있어도 로그인이 과도하게 블로킹되지 않도록 짧게.


def _load_config() -> Optional[Dict[str, str]]:
    """`resource/supabase_config.json` 을 로드.

    파일이 없거나 손상되면 None — 호출자는 Supabase 연동을 건너뛰어야 한다
    (오프라인/미설정 환경에서도 모터 기능은 정상 동작해야 하므로).
    """
    path = resource_path(_CONFIG_FILENAME)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not cfg.get("url") or not cfg.get("anon_key"):
        return None
    return {"url": cfg["url"].rstrip("/"), "anon_key": cfg["anon_key"]}


def upsert_user(sub: str, email: str, name: Optional[str]) -> bool:
    """Google 프로필로 `users` 테이블 upsert.

    - `sub` 를 PK 로 사용, 충돌 시 `email`/`name` 갱신.
    - 네트워크/설정 문제로 실패해도 예외를 던지지 않고 False 반환 —
      로그인 게이트가 이미 통과된 상태에서 DB 저장 실패로 앱 사용을 막으면 안 됨.

    Returns:
        True  — upsert 성공
        False — 설정 없음 / 네트워크 오류 / 서버 오류
    """
    cfg = _load_config()
    if cfg is None:
        return False

    endpoint = f"{cfg['url']}/rest/v1/{_TABLE}?on_conflict=sub"
    headers = {
        "apikey": cfg["anon_key"],
        "Authorization": f"Bearer {cfg['anon_key']}",
        "Content-Type": "application/json",
        # merge-duplicates: 충돌 시 row 덮어쓰기, return=minimal: 응답 body 없이 빠르게.
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    payload = [{"sub": sub, "email": email, "name": name}]

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=_TIMEOUT)
    except requests.RequestException:
        return False

    return 200 <= resp.status_code < 300
