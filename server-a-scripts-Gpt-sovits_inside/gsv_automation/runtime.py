from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

# Host(systemd)와 Docker(sidecar)를 둘 다 지원해야 해서 후보 경로를 명시적으로 관리한다.
DEFAULT_ROOT_CANDIDATES: Sequence[str] = (
    "/workspace/GPT-SoVITS",  # Docker sidecar 기본값
    "/opt/GPT-SoVITS",        # Host/systemd 기본값
)


@dataclass(frozen=True)
class ResolvedRootInfo:
    """GPT-SoVITS 루트 탐지 결과.

    [역할]
    - 루트 경로 + 탐지 출처 + 검증 상태를 한 객체로 묶는다.

    [왜 이렇게 묶냐]
    - health 응답, startup 로그, 파일/학습 서비스 초기화를 같은 근거로 맞추기 위해서.
    - 문자열 여러 개 따로 들고 다니면 나중에 값이 어긋나기 쉽다.
    """

    path: Path
    source: str
    structure_ok: bool
    checked: List[str]

    @property
    def path_str(self) -> str:
        return str(self.path)

    @property
    def exists(self) -> bool:
        return self.path.exists()

    def as_health_dict(self) -> dict:
        return {
            "resolved_root": self.path_str,
            "root_source": self.source,
            "root_exists": self.exists,
            "root_structure_ok": self.structure_ok,
        }


def looks_like_gpt_sovits_root(path: Path) -> bool:
    """GPT-SoVITS 루트처럼 보이는지 최소 구조만 확인한다.

    [주의]
    - 여기서는 '완전한 설치'를 검증하지 않는다.
    - 엔트리포인트 존재 여부 정도만 보고, 세부 스크립트 검증은 training 쪽에서 따로 한다.
    """
    return path.is_dir() and (path / "tools").exists() and (path / "GPT_SoVITS").exists()


def resolve_gpt_sovits_root_info(
    env_var: str = "GPT_SOVITS_ROOT",
    candidates: Optional[Iterable[str]] = None,
    logger: Optional[logging.Logger] = None,
) -> ResolvedRootInfo:
    """GPT-SoVITS 루트를 탐지하고, 못 찾으면 보수적으로 fallback 한다.

    [왜 fallback 하냐]
    - 기존 host 환경(`/opt/GPT-SoVITS`) 호환성을 깨지 않으면서 Docker 경로를 먼저 시도하려고 함.
    - 운영 중에는 health 응답으로 실제 사용 경로를 확인할 수 있게 한다.
    """
    log = logger or logging.getLogger(__name__)
    env_root = os.environ.get(env_var, "").strip()

    ordered: List[str] = []
    if env_root:
        ordered.append(env_root)

    for candidate in (list(candidates) if candidates is not None else list(DEFAULT_ROOT_CANDIDATES)):
        if candidate not in ordered:
            ordered.append(candidate)

    checked: List[str] = []
    for candidate in ordered:
        checked.append(candidate)
        candidate_path = Path(candidate)
        if looks_like_gpt_sovits_root(candidate_path):
            source = "env" if env_root and candidate == env_root else "auto"
            return ResolvedRootInfo(candidate_path, source, True, checked)

    fallback = Path(env_root) if env_root else Path(DEFAULT_ROOT_CANDIDATES[-1])
    source = "env-fallback" if env_root else "fallback"
    log.warning(
        "Could not auto-detect GPT-SoVITS root. Falling back to %s. Checked: %s",
        str(fallback),
        checked,
    )
    return ResolvedRootInfo(fallback, source, False, checked)
