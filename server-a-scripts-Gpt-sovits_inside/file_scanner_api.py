"""
GPT-SoVITS 파일 스캔 및 관리 API (Server A)

[이 파일의 역할]
- FastAPI 엔드포인트 정의 (transport layer)
- 요청 파라미터를 받아서 `gsv_automation.file_core` 서비스 함수 호출

[왜 이렇게 분리했냐]
- 예전에는 엔드포인트 함수 안에 파일시스템/오디오 처리/에러응답 로직이 다 섞여서
  수정할 때 실수 범위가 너무 컸다.
- 지금은 엔드포인트는 얇게 두고, 실제 로직은 재사용 가능한 core 모듈로 모았다.

실행 방법(Host 예시):
    cd /opt/GPT-SoVITS
    pip install fastapi uvicorn python-multipart aiofiles pydub
    # pydub는 ffmpeg가 필요합니다: apt-get install ffmpeg
    uvicorn file_scanner_api:app --host 0.0.0.0 --port 10001
"""

import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from gsv_automation.file_core import (
    GPT_DIRS,
    SOVITS_DIRS,
    PYDUB_AVAILABLE,
    build_all_file_summary,
    create_train_voice_dir,
    delete_path_under_base,
    get_audio_duration,
    get_file_info,
    list_audio_metadata,
    prepare_ref_audio,
    resolve_upload_target,
    save_upload_file,
    scan_logs_outputs,
    scan_models,
    scan_train_voices,
    trim_audio_file,
    validate_ref_audio_duration,
)
from gsv_automation.http_utils import ApiError, json_error, validate_path_under_base
from gsv_automation.runtime import DEFAULT_ROOT_CANDIDATES, resolve_gpt_sovits_root_info

app = FastAPI(
    title="GPT-SoVITS File Scanner API",
    description="Server A의 GPT-SoVITS 모델/음성 파일 목록 조회 및 관리 API",
    version="1.1.0",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS 설정 (Server B에서 호출 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Runtime path resolution (Host/Docker 겸용) ---
ROOT_INFO = resolve_gpt_sovits_root_info(logger=logger)
DEFAULT_ROOT_CANDIDATES = list(DEFAULT_ROOT_CANDIDATES)
BASE_DIR = ROOT_INFO.path
BASE_DIR_SOURCE = ROOT_INFO.source
BASE_DIR_STRUCTURE_OK = ROOT_INFO.structure_ok
BASE_DIR_CHECKED = ROOT_INFO.checked
LOGS_ROOT = BASE_DIR / "logs"


def _looks_like_gpt_sovits_root(path: Path) -> bool:
    from gsv_automation.runtime import looks_like_gpt_sovits_root

    return looks_like_gpt_sovits_root(path)


def resolve_base_dir() -> Tuple[Path, str, bool, List[str]]:
    info = resolve_gpt_sovits_root_info(logger=logger)
    return info.path, info.source, info.structure_ok, info.checked


def validate_path(path_str: str) -> Path:
    """기존 함수명 유지용 래퍼. 실제 검증은 공통 유틸에서 처리."""
    try:
        return validate_path_under_base(BASE_DIR, path_str)
    except ApiError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "status": "running",
        "service": "GPT-SoVITS File Scanner",
        "base_dir": str(BASE_DIR),
        "version": "1.1.0",
    }


@app.get("/api/files/models")
async def list_models():
    """GPT 및 SoVITS 모델 파일 목록 조회"""
    return scan_models(BASE_DIR)


@app.get("/api/files/train-voices")
async def list_train_voices():
    """훈련용 음성 파일 목록 조회 (sample_train_voice)"""
    return scan_train_voices(BASE_DIR)


@app.get("/api/files/logs")
async def list_logs():
    """logs/ 하위 학습 산출물(.ckpt/.pth) 조회"""
    return scan_logs_outputs(LOGS_ROOT)


@app.get("/api/files/all")
async def list_all_files():
    """모든 파일 목록 한번에 조회 (models, train_voices, logs)"""
    return build_all_file_summary(BASE_DIR)


# ============ 파일 관리 (업로드/삭제/폴더생성) ============

@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form(..., description="train_voice, gpt_weights, sovits_weights"),
    sub_path: str = Form(None, description="하위 경로 (예: 캐릭터명 폴더)"),
    model_version: str = Form("v2", description="모델 버전 (gpt/sovits 인 경우)"),
):
    """파일 업로드"""
    try:
        target_dir = resolve_upload_target(BASE_DIR, category, sub_path, model_version)
        return await save_upload_file(file, target_dir)
    except ApiError as e:
        return e.to_json_response()
    except Exception as e:
        traceback.print_exc()
        return json_error(500, f"업로드 실패: {str(e)}")


@app.delete("/api/files")
async def delete_file(path: str = Query(..., description="삭제할 파일/폴더의 절대 경로")):
    """파일 또는 폴더 삭제"""
    try:
        return delete_path_under_base(BASE_DIR, path)
    except ApiError as e:
        return e.to_json_response()
    except Exception as e:
        return json_error(500, f"삭제 실패: {str(e)}")


@app.post("/api/files/mkdir")
async def make_directory(path: str = Form(..., description="생성할 폴더 이름 (sample_train_voice 내부)")):
    """훈련 음성용 폴더 생성"""
    try:
        return create_train_voice_dir(BASE_DIR, path)
    except ApiError as e:
        return e.to_json_response()
    except Exception as e:
        return json_error(500, f"폴더 생성 실패: {str(e)}")


@app.post("/api/files/trim-audio")
async def trim_audio(
    source_path: str = Form(..., description="원본 오디오 파일의 절대 경로"),
    max_duration_sec: float = Form(10.0, description="최대 길이 (초, 기본값 10초)"),
    output_suffix: str = Form("_trimmed", description="출력 파일 접미사 (기본값 _trimmed)"),
):
    """오디오 파일을 지정된 최대 길이로 자릅니다."""
    try:
        return trim_audio_file(BASE_DIR, source_path, max_duration_sec, output_suffix)
    except ApiError as e:
        return e.to_json_response()
    except Exception as e:
        traceback.print_exc()
        return json_error(500, f"오디오 자르기 실패: {str(e)}")


@app.post("/api/files/prepare-ref-audio")
async def prepare_ref_audio_endpoint(
    train_input_dir: str = Form(..., description="훈련 입력 디렉토리 (sample_train_voice 기준 상대 경로)"),
    max_duration_sec: float = Form(8.0, description="ref_audio 최대 길이 (초)"),
):
    """훈련 폴더에서 가장 긴 오디오를 찾아 ref_audio.wav로 준비합니다."""
    try:
        return prepare_ref_audio(BASE_DIR, train_input_dir, max_duration_sec)
    except ApiError as e:
        return e.to_json_response()
    except Exception as e:
        traceback.print_exc()
        return json_error(500, f"ref_audio 준비 실패: {str(e)}")


@app.get("/api/files/audio-list")
async def list_audio_files(path: str = Query(..., description="조회할 폴더 경로 (sample_train_voice 기준 상대 경로)")):
    """지정한 폴더 내 오디오 파일 목록과 길이를 반환합니다."""
    try:
        return list_audio_metadata(BASE_DIR, path)
    except ApiError as e:
        return e.to_json_response()
    except Exception as e:
        traceback.print_exc()
        return json_error(500, f"오디오 파일 목록 조회 실패: {str(e)}")


@app.post("/api/files/validate-ref-audio")
async def validate_ref_audio(path: str = Form(..., description="검증할 오디오 파일 절대 경로")):
    """오디오 파일이 ref_audio 조건(3~8초 문서 기준, 실제 검증은 3~10초 유지)을 만족하는지 검증."""
    try:
        return validate_ref_audio_duration(BASE_DIR, path)
    except ApiError as e:
        # 이 엔드포인트는 기존부터 {valid, message} 형태를 자주 쓰므로 extra payload를 그대로 전달한다.
        payload = {"valid": False, "message": e.message}
        payload.update(e.extra)
        return JSONResponse(status_code=e.status_code, content=payload)
    except Exception as e:
        return JSONResponse(status_code=500, content={"valid": False, "message": str(e)})


@app.get("/api/health")
async def health_check():
    """서비스 상태 확인"""
    return {
        "status": "healthy",
        "resolved_root": str(BASE_DIR),
        "root_source": BASE_DIR_SOURCE,
        "base_dir_exists": BASE_DIR.exists(),
        "root_structure_ok": BASE_DIR_STRUCTURE_OK,
        "pydub_available": PYDUB_AVAILABLE,
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=10001)
