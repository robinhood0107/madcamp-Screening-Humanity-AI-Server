"""
GPT-SoVITS 파일 스캔 및 관리 API
Server A에서 실행하여 모델/음성 파일 목록 조회, 업로드, 삭제 기능을 제공합니다.

실행 방법:
    cd /opt/GPT-SoVITS
    pip install fastapi uvicorn python-multipart aiofiles pydub
    # pydub는 ffmpeg가 필요합니다: apt-get install ffmpeg
    uvicorn file_scanner_api:app --host 0.0.0.0 --port 10001

또는 systemd 서비스로 등록하여 자동 시작
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import os
import shutil
import aiofiles
import wave
import contextlib
import logging
from datetime import datetime

# 오디오 처리용 pydub (pip install pydub, apt-get install ffmpeg)
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None

app = FastAPI(
    title="GPT-SoVITS File Scanner API",
    description="Server A의 GPT-SoVITS 모델/음성 파일 목록 조회 및 관리 API",
    version="1.1.0"
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

DEFAULT_ROOT_CANDIDATES = [
    "/workspace/GPT-SoVITS",  # Docker (sidecar)
    "/opt/GPT-SoVITS",        # Host / systemd
]


def _looks_like_gpt_sovits_root(path: Path) -> bool:
    return path.is_dir() and (path / "tools").exists() and (path / "GPT_SoVITS").exists()


def resolve_base_dir() -> Tuple[Path, str, bool, List[str]]:
    env_root = os.environ.get("GPT_SOVITS_ROOT", "").strip()
    candidates: List[str] = []
    if env_root:
        candidates.append(env_root)
    for candidate in DEFAULT_ROOT_CANDIDATES:
        if candidate not in candidates:
            candidates.append(candidate)

    checked: List[str] = []
    for candidate in candidates:
        checked.append(candidate)
        candidate_path = Path(candidate)
        if _looks_like_gpt_sovits_root(candidate_path):
            source = "env" if env_root and candidate == env_root else "auto"
            return candidate_path, source, True, checked

    fallback = Path(env_root) if env_root else Path(DEFAULT_ROOT_CANDIDATES[-1])
    source = "env-fallback" if env_root else "fallback"
    logger.warning(
        "Could not auto-detect GPT-SoVITS root. Falling back to %s. Checked: %s",
        str(fallback),
        checked,
    )
    return fallback, source, False, checked


# 기본 경로 설정 (Docker/Host 겸용)
BASE_DIR, BASE_DIR_SOURCE, BASE_DIR_STRUCTURE_OK, BASE_DIR_CHECKED = resolve_base_dir()

# GPT 모델 디렉토리 목록
GPT_DIRS = [
    "GPT_weights",
    "GPT_weights_v2",
    "GPT_weights_v2Pro",
    "GPT_weights_v2ProPlus",
    "GPT_weights_v3",
    "GPT_weights_v4"
]

# SoVITS 모델 디렉토리 목록
SOVITS_DIRS = [
    "SoVITS_weights",
    "SoVITS_weights_v2",
    "SoVITS_weights_v2Pro",
    "SoVITS_weights_v2ProPlus",
    "SoVITS_weights_v3",
    "SoVITS_weights_v4"
]

# 훈련 로그·산출물 (logs/{model_name} 내 .ckpt, .pth)
LOGS_ROOT = BASE_DIR / "logs"


def get_file_info(file_path: Path) -> Dict[str, Any]:
    """파일 정보 반환"""
    stat = file_path.stat()
    return {
        "name": file_path.name,
        "stem": file_path.stem,
        "path": str(file_path),
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
    }


def get_audio_duration(file_path: str) -> float:
    """
    오디오 파일의 길이를 초 단위로 반환합니다.
    pydub를 우선 사용하고, 실패 시 wave 모듈(wav 파일)을 시도합니다.
    """
    duration = None
    
    # 1. pydub 시도
    if PYDUB_AVAILABLE:
        try:
            audio = AudioSegment.from_file(file_path)
            duration = len(audio) / 1000.0
            return duration
        except Exception:
            pass
            
    # 2. wave 모듈 시도 (wav 파일인 경우)
    if file_path.lower().endswith(".wav"):
        try:
            with contextlib.closing(wave.open(file_path, 'r')) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                if rate > 0:
                    duration = frames / float(rate)
                    return duration
        except Exception:
            pass
            
    return None


def validate_path(path_str: str) -> Path:
    """경로 유효성 검사 (상위 디렉토리 접근 방지)"""
    # BASE_DIR 내부인지 확인
    target_path = Path(path_str).resolve()
    base_path_resolved = BASE_DIR.resolve()
    
    if not str(target_path).startswith(str(base_path_resolved)):
        raise HTTPException(status_code=403, detail="허용되지 않은 경로입니다.")
    
    return target_path


@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "status": "running",
        "service": "GPT-SoVITS File Scanner",
        "base_dir": str(BASE_DIR),
        "version": "1.1.0"
    }


@app.get("/api/files/models")
async def list_models():
    """GPT 및 SoVITS 모델 파일 목록 조회"""
    result = {
        "gpt": {},
        "sovits": {},
        "summary": {
            "gpt_total": 0,
            "sovits_total": 0
        }
    }
    
    # GPT 모델 스캔
    for dir_name in GPT_DIRS:
        dir_path = BASE_DIR / dir_name
        if dir_path.exists() and dir_path.is_dir():
            files = []
            for f in dir_path.glob("*.ckpt"):
                files.append(get_file_info(f))
            if files:
                result["gpt"][dir_name] = files
                result["summary"]["gpt_total"] += len(files)
    
    # SoVITS 모델 스캔
    for dir_name in SOVITS_DIRS:
        dir_path = BASE_DIR / dir_name
        if dir_path.exists() and dir_path.is_dir():
            files = []
            for f in dir_path.glob("*.pth"):
                files.append(get_file_info(f))
            if files:
                result["sovits"][dir_name] = files
                result["summary"]["sovits_total"] += len(files)
    
    return result


@app.get("/api/files/train-voices")
async def list_train_voices():
    """훈련용 음성 파일 목록 조회 (sample_train_voice)"""
    train_dir = BASE_DIR / "sample_train_voice"
    voices = []
    
    if not train_dir.exists():
        return {"voices": [], "total": 0, "message": "sample_train_voice 폴더가 없습니다"}
    
    for item in sorted(train_dir.iterdir()):
        if item.is_dir():
            # 캐릭터별 폴더
            audio_files = []
            for ext in ["*.wav", "*.mp3", "*.flac", "*.ogg"]:
                for f in item.glob(ext):
                    duration = get_audio_duration(str(f))
                    if duration is not None:
                         duration = round(duration, 2)
                         valid = 3.0 <= duration <= 10.0
                    else:
                         valid = False  # 길이 확인 불가 시 일단 False로 (Ref Audio 자동 선택 제외)

                    audio_files.append({
                        "name": f.name,
                        "size_bytes": f.stat().st_size,
                        "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                        "duration_sec": duration,
                        "valid_for_ref": valid
                    })
            
            total_size_mb = sum(f["size_mb"] for f in audio_files)
            
            voices.append({
                "character_name": item.name,
                "path": str(item),
                "file_count": len(audio_files),
                "files": audio_files,
                "total_size_mb": round(total_size_mb, 2),
                "status": "ready" if audio_files else "empty"
            })
    
    return {
        "voices": voices,
        "total": len(voices),
        "base_path": str(train_dir)
    }


@app.get("/api/files/logs")
async def list_logs():
    """
    logs/ 하위 model_name별 디렉터리에서 .ckpt 1개, .pth 1개를 수집.
    반환: { "models": [ { "model_name", "gpt_path", "sovits_path" } ] }
    """
    result = {"models": []}
    if not LOGS_ROOT.exists() or not LOGS_ROOT.is_dir():
        return result

    for item in sorted(LOGS_ROOT.iterdir()):
        if not item.is_dir():
            continue
        model_name = item.name
        gpt_path = None
        sovits_path = None

        ckpts = list(item.glob("*.ckpt"))
        if ckpts:
            gpt_path = str(ckpts[0])

        # s2 산출물만 (pretrained 등 제외: 파일명에 pretrained 미포함)
        pths = [p for p in item.glob("*.pth") if "pretrained" not in p.name.lower()]
        if pths:
            sovits_path = str(pths[0])

        result["models"].append({
            "model_name": model_name,
            "gpt_path": gpt_path,
            "sovits_path": sovits_path
        })

    return result


@app.get("/api/files/all")
async def list_all_files():
    """모든 파일 목록 한번에 조회 (models, train_voices, logs)"""
    models = await list_models()
    train_voices = await list_train_voices()
    logs = await list_logs()
    return {
        "models": models,
        "train_voices": train_voices,
        "logs": logs
    }


# ============ 파일 관리 (업로드/삭제/폴더생성) ============

@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form(..., description="train_voice, gpt_weights, sovits_weights"),
    sub_path: str = Form(None, description="하위 경로 (예: 캐릭터명 폴더)"),
    model_version: str = Form("v2", description="모델 버전 (gpt/sovits 인 경우)")
):
    """파일 업로드"""
    try:
        # 대상 디렉토리 결정
        target_dir = None
        
        if category == "train_voice":
            base_train = BASE_DIR / "sample_train_voice"
            if sub_path:
                target_dir = base_train / sub_path
            else:
                return JSONResponse(status_code=400, content={"message": "train_voice 업로드 시 sub_path(캐릭터명) 필수"})
        elif category == "gpt_weights":
            # GPT_weights_v2 등으로 매핑
            dir_name = f"GPT_weights_{model_version}" if model_version != "v1" else "GPT_weights"
            if dir_name not in GPT_DIRS:
                return JSONResponse(status_code=400, content={"message": f"유효하지 않은 모델 버전/경로: {dir_name}"})
            target_dir = BASE_DIR / dir_name
        elif category == "sovits_weights":
            dir_name = f"SoVITS_weights_{model_version}" if model_version != "v1" else "SoVITS_weights"
            if dir_name not in SOVITS_DIRS:
                return JSONResponse(status_code=400, content={"message": f"유효하지 않은 모델 버전/경로: {dir_name}"})
            target_dir = BASE_DIR / dir_name
        else:
            return JSONResponse(status_code=400, content={"message": "유효하지 않은 category"})
        
        # 디렉토리 생성
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일 저장
        file_path = target_dir / file.filename
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
            
        return {
            "success": True,
            "filename": file.filename,
            "path": str(file_path),
            "size_bytes": file_path.stat().st_size,
            "message": "파일 업로드 완료"
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"message": f"업로드 실패: {str(e)}"})


@app.delete("/api/files")
async def delete_file(
    path: str = Query(..., description="삭제할 파일/폴더의 절대 경로")
):
    """파일 또는 폴더 삭제"""
    try:
        target_path = validate_path(path)
        
        if not target_path.exists():
            return JSONResponse(status_code=404, content={"message": "파일을 찾을 수 없습니다"})
            
        if target_path.is_dir():
            shutil.rmtree(target_path)
            return {"success": True, "message": f"폴더 삭제 완료: {target_path.name}"}
        else:
            target_path.unlink()
            return {"success": True, "message": f"파일 삭제 완료: {target_path.name}"}
            
    except HTTPException as he:
        raise he
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"삭제 실패: {str(e)}"})


@app.post("/api/files/mkdir")
async def make_directory(
    path: str = Form(..., description="생성할 폴더 이름 (sample_train_voice 내부)"),
):
    """훈련 음성용 폴더 생성"""
    try:
        if not path or ".." in path or path.startswith("/"):
            return JSONResponse(status_code=400, content={"message": "유효하지 않은 폴더 이름"})
            
        target_dir = BASE_DIR / "sample_train_voice" / path
        
        if target_dir.exists():
             return JSONResponse(status_code=400, content={"message": "이미 존재하는 폴더입니다"})
             
        target_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "success": True,
            "path": str(target_dir),
            "message": f"폴더 생성 완료: {path}"
        }
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"폴더 생성 실패: {str(e)}"})


@app.post("/api/files/trim-audio")
async def trim_audio(
    source_path: str = Form(..., description="원본 오디오 파일의 절대 경로"),
    max_duration_sec: float = Form(10.0, description="최대 길이 (초, 기본값 10초)"),
    output_suffix: str = Form("_trimmed", description="출력 파일 접미사 (기본값 _trimmed)")
):
    """
    오디오 파일을 지정된 최대 길이로 자릅니다.
    
    - source_path: 원본 오디오 파일 경로 (Server A 내부 경로)
    - max_duration_sec: 최대 길이 (초, 기본값 8초)
    - output_suffix: 출력 파일 이름에 붙일 접미사
    
    원본 파일이 max_duration_sec보다 짧으면 그대로 반환합니다.
    잘린 파일은 원본과 같은 디렉토리에 {원본이름}{suffix}.wav로 저장됩니다.
    """
    try:
        source = validate_path(source_path)
        
        if not source.exists():
            return JSONResponse(status_code=404, content={"message": f"파일을 찾을 수 없습니다: {source_path}"})
        
        if not source.suffix.lower() in [".wav", ".mp3", ".flac", ".ogg"]:
            return JSONResponse(status_code=400, content={"message": "지원하지 않는 오디오 형식입니다 (wav, mp3, flac, ogg만 지원)"})
        
        # pydub 사용 가능 여부 확인
        if not PYDUB_AVAILABLE:
            return JSONResponse(status_code=500, content={
                "message": "pydub 라이브러리가 설치되어 있지 않습니다. 'pip install pydub' 실행 후 다시 시도하세요."
            })
        
        audio = AudioSegment.from_file(str(source))
        duration_sec = len(audio) / 1000.0  # 밀리초 -> 초
        
        if duration_sec <= max_duration_sec:
            # 자를 필요 없음
            return {
                "success": True,
                "trimmed": False,
                "original_path": str(source),
                "output_path": str(source),
                "original_duration_sec": round(duration_sec, 2),
                "output_duration_sec": round(duration_sec, 2),
                "message": f"원본 길이가 {max_duration_sec}초 이하입니다. 자르지 않았습니다."
            }
        
        # 최대 길이로 자르기
        trimmed_audio = audio[:int(max_duration_sec * 1000)]
        
        # 출력 파일 경로 생성
        output_path = source.parent / f"{source.stem}{output_suffix}.wav"
        
        # WAV로 저장 (최상의 품질 유지)
        trimmed_audio.export(str(output_path), format="wav")
        
        return {
            "success": True,
            "trimmed": True,
            "original_path": str(source),
            "output_path": str(output_path),
            "original_duration_sec": round(duration_sec, 2),
            "output_duration_sec": round(max_duration_sec, 2),
            "message": f"오디오를 {max_duration_sec}초로 잘랐습니다."
        }
        
    except ImportError:
        return JSONResponse(status_code=500, content={
            "message": "pydub 라이브러리가 설치되어 있지 않습니다. 'pip install pydub' 실행 후 다시 시도하세요."
        })
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"message": f"오디오 자르기 실패: {str(e)}"})


@app.post("/api/files/prepare-ref-audio")
async def prepare_ref_audio(
    train_input_dir: str = Form(..., description="훈련 입력 디렉토리 (sample_train_voice 기준 상대 경로)"),
    max_duration_sec: float = Form(8.0, description="ref_audio 최대 길이 (초)")
):
    """
    훈련 폴더에서 가장 긴 오디오를 찾아 max_duration_sec로 잘라서 ref_audio로 준비합니다.
    
    잘린 파일은 {train_input_dir}/ref_audio.wav로 저장됩니다.
    이 파일을 Voice 등록 시 ref_audio_file로 사용합니다.
    """
    try:
        train_dir = BASE_DIR / "sample_train_voice" / train_input_dir
        
        if not train_dir.exists():
            return JSONResponse(status_code=404, content={"message": f"훈련 폴더를 찾을 수 없습니다: {train_input_dir}"})
        
        # pydub 사용 가능 여부 확인
        if not PYDUB_AVAILABLE:
            return JSONResponse(status_code=500, content={
                "message": "pydub 라이브러리가 설치되어 있지 않습니다. 'pip install pydub' 실행 후 다시 시도하세요."
            })
        
        longest_file = None
        longest_duration = 0
        
        for ext in ["*.wav", "*.mp3", "*.flac", "*.ogg"]:
            for audio_file in train_dir.glob(ext):
                try:
                    audio = AudioSegment.from_file(str(audio_file))
                    duration = len(audio) / 1000.0
                    if duration > longest_duration:
                        longest_duration = duration
                        longest_file = audio_file
                except Exception:
                    continue
        
        if not longest_file:
            return JSONResponse(status_code=404, content={"message": "훈련 폴더에 오디오 파일이 없습니다."})
        
        # 로드하여 자르기
        audio = AudioSegment.from_file(str(longest_file))
        
        if longest_duration > max_duration_sec:
            # 자르기
            trimmed_audio = audio[:int(max_duration_sec * 1000)]
            output_duration = max_duration_sec
        else:
            # 자를 필요 없음
            trimmed_audio = audio
            output_duration = longest_duration
        
        # ref_audio.wav로 저장
        output_path = train_dir / "ref_audio.wav"
        trimmed_audio.export(str(output_path), format="wav")
        
        return {
            "success": True,
            "source_file": longest_file.name,
            "source_duration_sec": round(longest_duration, 2),
            "output_path": str(output_path),
            "output_duration_sec": round(output_duration, 2),
            "ref_audio_file": "ref_audio.wav",
            "message": f"가장 긴 파일({longest_file.name}, {round(longest_duration, 2)}초)을 {round(output_duration, 2)}초로 잘라 ref_audio.wav로 저장했습니다."
        }
        
    except ImportError:
        return JSONResponse(status_code=500, content={
            "message": "pydub 라이브러리가 설치되어 있지 않습니다. 'pip install pydub' 실행 후 다시 시도하세요."
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"message": f"ref_audio 준비 실패: {str(e)}"})
@app.get("/api/files/audio-list")
async def list_audio_files(
    path: str = Query(..., description="조회할 폴더 경로 (sample_train_voice 기준 상대 경로)")
):
    """
    지정한 폴더 내 오디오 파일 목록과 각 파일의 길이를 반환합니다.
    
    관리자 페이지에서 ref_audio 선택 시 사용합니다.
    """
    try:
        target_dir = BASE_DIR / "sample_train_voice" / path
        
        if not target_dir.exists():
            return JSONResponse(status_code=404, content={"message": f"폴더를 찾을 수 없습니다: {path}"})
        
        audio_files = []
        
        for ext in ["*.wav", "*.mp3", "*.flac", "*.ogg"]:
            for audio_file in target_dir.glob(ext):
                file_info = {
                    "name": audio_file.name,
                    "path": str(audio_file),
                    "size_bytes": audio_file.stat().st_size,
                    "size_mb": round(audio_file.stat().st_size / (1024 * 1024), 2),
                    "duration_sec": None,
                    "valid_for_ref": False  # 3-8초 사이면 True
                }
                
                # 오디오 길이 분석
                duration = get_audio_duration(str(audio_file))
                
                if duration is not None:
                     file_info["duration_sec"] = round(duration, 2)
                     # 3-8초 사이면 ref_audio로 사용 가능
                     file_info["valid_for_ref"] = 3.0 <= duration <= 10.0
                
                audio_files.append(file_info)
        
        # 길이 기준 내림차순 정렬 (가장 긴 파일 먼저)
        audio_files.sort(key=lambda x: x.get("duration_sec") or 0, reverse=True)
        
        return {
            "success": True,
            "path": str(target_dir),
            "files": audio_files,
            "total": len(audio_files),
            "pydub_available": PYDUB_AVAILABLE
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"message": f"오디오 파일 목록 조회 실패: {str(e)}"})


@app.post("/api/files/validate-ref-audio")
async def validate_ref_audio(
    path: str = Form(..., description="검증할 오디오 파일 절대 경로")
):
    """오디오 파일이 ref_audio 조건(3~8초)을 만족하는지 검증"""
    try:
        target = validate_path(path)
        if not target.exists():
             return JSONResponse(status_code=404, content={"valid": False, "message": "File not found"})
        
        duration = get_audio_duration(str(target))
        
        if duration is None:
             return JSONResponse(status_code=500, content={"valid": False, "message": "Duration check failed (n/a)"})
             
        valid = 3.0 <= duration <= 10.0
        
        return {
            "valid": valid,
            "duration_sec": round(duration, 2),
            "message": "Valid" if valid else f"Duration {round(duration, 2)}s is out of range (3.0-10.0s)"
        }
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
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10001)
