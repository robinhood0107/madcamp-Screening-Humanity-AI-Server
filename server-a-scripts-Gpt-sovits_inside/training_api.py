"""
GPT-SoVITS Training API (Server A 자동 학습 오케스트레이터)

[이 파일의 역할]
- FastAPI 엔드포인트를 제공한다. (transport layer)
- 실제 학습 파이프라인 로직은 `gsv_automation.training_core`로 위임한다.

[왜 이렇게 나눴냐]
- 예전에는 training_pipeline 하나가 너무 커서(300줄+) 수정할 때 사고가 나기 쉬웠다.
- 엔드포인트는 얇게 유지하고, 단계 로직/상태관리/설정생성은 core 모듈로 분리했다.

[운영 모드]
- Host/systemd: /opt/GPT-SoVITS
- Docker sidecar: /workspace/GPT-SoVITS
- 실제 사용 경로는 GPT_SOVITS_ROOT + 자동탐지 결과를 health 응답으로 확인 가능
"""

import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from gsv_automation.process import run_subprocess  # 호환성용 re-export (기존 내부 함수명 유지)
from gsv_automation.runtime import (
    DEFAULT_ROOT_CANDIDATES as RUNTIME_DEFAULT_ROOT_CANDIDATES,
    resolve_gpt_sovits_root_info,
)
from gsv_automation.training_core import (
    MODEL_VERSIONS,
    build_training_runtime,
    check_required_paths as core_check_required_paths,
    ensure_runtime_dirs as core_ensure_runtime_dirs,
    load_status_from_disk,
    queue_status_payload,
    read_pipeline_log,
    training_pipeline,
)

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="GPT-SoVITS Training API")

# --- Configuration / Runtime ---
# [주의]
# 아래 전역 변수들은 기존 코드/문서/운영 점검 스크립트에서 읽을 수 있어서 이름을 유지한다.
ROOT_INFO = resolve_gpt_sovits_root_info(logger=logger)
DEFAULT_ROOT_CANDIDATES = list(RUNTIME_DEFAULT_ROOT_CANDIDATES)
GPT_SOVITS_ROOT = ROOT_INFO.path_str
ROOT_SOURCE = ROOT_INFO.source
ROOT_STRUCTURE_OK = ROOT_INFO.structure_ok
ROOT_CHECKED = ROOT_INFO.checked
PYTHON_EXE = sys.executable

TRAINING_RUNTIME = build_training_runtime(ROOT_INFO, python_exe=PYTHON_EXE)
TOOLS_DIR = str(TRAINING_RUNTIME.tools_dir)
GPT_SOVITS_DIR = str(TRAINING_RUNTIME.gpt_sovits_dir)
PRETRAINED_MODELS_DIR = str(TRAINING_RUNTIME.pretrained_models_dir)
CONFIGS_DIR = str(TRAINING_RUNTIME.configs_dir)
TEMP_ROOT = str(TRAINING_RUNTIME.temp_root)
LOGS_ROOT = str(TRAINING_RUNTIME.logs_root)

# Training Status Storage (In-memory for now)
training_status: Dict[str, Dict] = {}


def _looks_like_gpt_sovits_root(path: str) -> bool:
    """호환성 래퍼: 예전 함수명 유지."""
    from gsv_automation.runtime import looks_like_gpt_sovits_root
    from pathlib import Path

    return looks_like_gpt_sovits_root(Path(path))


def resolve_gpt_sovits_root() -> Tuple[str, str, bool, List[str]]:
    """호환성 래퍼: 예전 함수 시그니처 유지."""
    info = resolve_gpt_sovits_root_info(logger=logger)
    return info.path_str, info.source, info.structure_ok, info.checked


def ensure_runtime_dirs_wrapper() -> None:
    """호환성 래퍼: 이름 충돌 피하려고 wrapper 이름 사용."""
    core_ensure_runtime_dirs(TRAINING_RUNTIME, logger)


def ensure_runtime_dirs() -> None:
    """기존 함수명 호환성 유지용 래퍼."""
    core_ensure_runtime_dirs(TRAINING_RUNTIME, logger)


def check_paths() -> Tuple[bool, List[str]]:
    """학습 필수 스크립트 존재 여부 확인 (기존 함수명 유지)."""
    return core_check_required_paths(TRAINING_RUNTIME, logger)


@app.on_event("startup")
async def startup_event():
    # 여기서 runtime 디렉토리와 필수 스크립트 확인을 먼저 해둬야 운영자가 health/log 보고 바로 원인 파악 가능함.
    core_ensure_runtime_dirs(TRAINING_RUNTIME, logger)
    logger.info(
        "GPT-SoVITS root resolved to %s (source=%s, structure_ok=%s)",
        GPT_SOVITS_ROOT,
        ROOT_SOURCE,
        ROOT_STRUCTURE_OK,
    )
    ok, missing = core_check_required_paths(TRAINING_RUNTIME, logger)
    if not ok:
        logger.warning("⚠️  CRITICAL: Missing scripts: %s. The API may fail.", missing)


class TrainRequest(BaseModel):
    # [역할]
    # backend -> training API 요청 payload를 그대로 받는 모델.
    # 응답/요청 호환성 때문에 필드명은 1차 리팩토링에서 바꾸지 않는다.
    model_name: str
    upload_path: str
    version: str = "v2"
    batch_size: int = 11
    total_epochs: int = 8
    text_low_lr_rate: float = 0.4
    if_save_latest: bool = True
    if_save_every_weights: bool = True
    save_every_epoch: int = 4
    gpu_numbers: str = "0-0"
    dry_run: bool = False


class TrainStatusResponse(BaseModel):
    model_name: str
    status: str
    progress: float
    message: str
    error: Optional[str] = None
    created_at: str
    updated_at: str


@app.get("/api/health")
async def health():
    """Server B /health/detailed 등에서 헬스 체크용. 200 반환으로 404 로그 노이즈 제거."""
    return {
        "status": "ok",
        "resolved_root": GPT_SOVITS_ROOT,
        "root_source": ROOT_SOURCE,
        "root_exists": TRAINING_RUNTIME.root.exists(),
        "root_structure_ok": ROOT_STRUCTURE_OK,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/train/start")
async def start_training(req: TrainRequest, background_tasks: BackgroundTasks):
    """학습 파이프라인 시작 요청.

    [왜 여기서 최소한만 처리하나]
    - transport 검증(중복 실행 방지, 큐 상태 기록)까지만 하고,
      실제 파이프라인은 core 모듈로 넘겨야 재사용/테스트가 쉬워진다.
    """
    if req.model_name in training_status and training_status[req.model_name]["status"] in [
        "queued",
        "processing",
        "training_sovits",
        "training_gpt",
    ]:
        if not req.dry_run:
            raise HTTPException(status_code=400, detail="Model is already training")

    queued = queue_status_payload(req.model_name, req.dry_run)
    training_status[req.model_name] = queued

    background_tasks.add_task(training_pipeline, req, TRAINING_RUNTIME, training_status, logger)
    return queued


@app.get("/api/train/status/{model_name}")
async def get_status(model_name: str):
    if model_name in training_status:
        return training_status[model_name]

    data = load_status_from_disk(TRAINING_RUNTIME, training_status, model_name)
    if data is not None:
        return data

    raise HTTPException(status_code=404, detail="Model training status not found")


@app.get("/api/train/log/{model_name}")
async def get_log(model_name: str):
    """Retrieve the full content of pipeline.log for a specific model."""
    try:
        content = read_pipeline_log(TRAINING_RUNTIME, model_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read log file: {str(e)}")

    if content is not None:
        return {"model_name": model_name, "log": content}

    if model_name in training_status:
        return {"model_name": model_name, "log": "Log file not created yet. Training may be in queue or initializing."}

    raise HTTPException(status_code=404, detail="Log not found for this model")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=10002)  # Use 10002 for Training API
