from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from fastapi.responses import JSONResponse


@dataclass
class ApiError(Exception):
    """HTTP 계층으로 변환할 수 있는 도메인 에러.

    [왜 custom 에러를 쓰냐]
    - 서비스 로직(file_core/training_core)에서 FastAPI 객체를 직접 만들기 시작하면
      나중에 테스트/재사용할 때 결합도가 너무 높아진다.
    - 그래서 서비스 레이어는 `ApiError`만 던지고, 엔드포인트에서 JSONResponse로 바꾼다.
    """

    status_code: int
    message: str
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_json_response(self) -> JSONResponse:
        payload = {"message": self.message}
        payload.update(self.extra)
        return JSONResponse(status_code=self.status_code, content=payload)


def json_error(status_code: int, message: str, **extra: Any) -> JSONResponse:
    """반복되는 JSONResponse 에러 생성 패턴을 통일한다."""
    payload = {"message": message}
    payload.update(extra)
    return JSONResponse(status_code=status_code, content=payload)


def _is_under_base(base_resolved: Path, target_resolved: Path) -> bool:
    """target이 base 내부인지 안전하게 판정한다 (문자열 prefix 비교 금지)."""
    try:
        target_resolved.relative_to(base_resolved)
        return True
    except ValueError:
        return False


def validate_path_under_base(base_dir: Path, path_str: str) -> Path:
    """기준 디렉토리 내부 경로만 허용한다.

    [주의]
    - 기존 코드의 startswith 비교는 `/opt/GPT-SoVITS` vs `/opt/GPT-SoVITS-backup` 같은 케이스에 취약할 수 있음.
    - 여기서는 resolve + relative_to로 실제 경로 포함 관계만 허용한다.
    """
    target_path = Path(path_str).resolve()
    base_path = base_dir.resolve()
    if not _is_under_base(base_path, target_path):
        raise ApiError(status_code=403, message="허용되지 않은 경로입니다.")
    return target_path


def ensure_safe_train_subdir_name(path: str) -> str:
    """sample_train_voice 하위 폴더명용 간단 검증.

    [왜 엄격하게 하냐]
    - 여기서 폴더명 규칙이 느슨하면 나중에 파일 API/학습 경로가 섞여서 디버깅이 더 어려워진다.
    """
    if not path or ".." in path or path.startswith("/"):
        raise ApiError(status_code=400, message="유효하지 않은 폴더 이름")
    # Windows 경로 구분자까지 보수적으로 막는다.
    if "\\" in path:
        raise ApiError(status_code=400, message="유효하지 않은 폴더 이름")
    return path


def list_dir_exists(path: Path) -> bool:
    return path.exists() and path.is_dir()
