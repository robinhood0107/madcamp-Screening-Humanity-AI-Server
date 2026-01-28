"""
GPT-SoVITS 파일 스캔 및 관리 API
Server A에서 실행하여 모델/음성 파일 목록 조회, 업로드, 삭제 기능을 제공합니다.

실행 방법:
    cd /opt/GPT-SoVITS
    pip install fastapi uvicorn python-multipart aiofiles
    uvicorn file_scanner_api:app --host 0.0.0.0 --port 10001

또는 systemd 서비스로 등록하여 자동 시작
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import List, Dict, Any, Optional
import os
import shutil
import aiofiles
from datetime import datetime

app = FastAPI(
    title="GPT-SoVITS File Scanner API",
    description="Server A의 GPT-SoVITS 모델/음성 파일 목록 조회 및 관리 API",
    version="1.1.0"
)

# CORS 설정 (Server B에서 호출 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기본 경로 설정
BASE_DIR = Path("/opt/GPT-SoVITS")

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
                    audio_files.append({
                        "name": f.name,
                        "size_bytes": f.stat().st_size,
                        "size_mb": round(f.stat().st_size / (1024 * 1024), 2)
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


@app.get("/api/health")
async def health_check():
    """서비스 상태 확인"""
    return {
        "status": "healthy",
        "base_dir_exists": BASE_DIR.exists(),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10001)
