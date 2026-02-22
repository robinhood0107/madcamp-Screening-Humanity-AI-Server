from __future__ import annotations

import contextlib
import traceback
import wave
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import aiofiles

from .http_utils import ApiError, ensure_safe_train_subdir_name, validate_path_under_base

# [구조 규칙]
# 파일 분할을 과하게 하지 않으려고, file API 관련 로직(스캔/파일조작/오디오조작)은 이 파일 하나로 묶는다.
# 대신 내부를 섹션/함수로 나눠서 읽기 쉽게 유지한다.

GPT_DIRS: List[str] = [
    "GPT_weights",
    "GPT_weights_v2",
    "GPT_weights_v2Pro",
    "GPT_weights_v2ProPlus",
    "GPT_weights_v3",
    "GPT_weights_v4",
]

SOVITS_DIRS: List[str] = [
    "SoVITS_weights",
    "SoVITS_weights_v2",
    "SoVITS_weights_v2Pro",
    "SoVITS_weights_v2ProPlus",
    "SoVITS_weights_v3",
    "SoVITS_weights_v4",
]

AUDIO_GLOB_PATTERNS: Tuple[str, ...] = ("*.wav", "*.mp3", "*.flac", "*.ogg")
AUDIO_SUFFIXES: Tuple[str, ...] = (".wav", ".mp3", ".flac", ".ogg")

try:
    from pydub import AudioSegment  # type: ignore

    PYDUB_AVAILABLE = True
except ImportError:
    AudioSegment = None
    PYDUB_AVAILABLE = False


def get_file_info(file_path: Path) -> Dict[str, Any]:
    """파일 메타데이터를 API 응답 포맷으로 정리한다."""
    stat = file_path.stat()
    return {
        "name": file_path.name,
        "stem": file_path.stem,
        "path": str(file_path),
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


def get_audio_duration(file_path: str) -> Optional[float]:
    """오디오 길이(초)를 반환한다. pydub 우선, 실패하면 wave(wav 전용) fallback."""
    if PYDUB_AVAILABLE:
        try:
            audio = AudioSegment.from_file(file_path)  # type: ignore[union-attr]
            return len(audio) / 1000.0
        except Exception:
            pass

    if file_path.lower().endswith(".wav"):
        try:
            with contextlib.closing(wave.open(file_path, "r")) as f:
                frames = f.getnframes()
                rate = f.getframerate()
                if rate > 0:
                    return frames / float(rate)
        except Exception:
            pass

    return None


def _iter_audio_files(dir_path: Path) -> Iterable[Path]:
    for ext in AUDIO_GLOB_PATTERNS:
        for f in dir_path.glob(ext):
            yield f


# ==================== 조회(Query) 계열 ====================

def scan_models(base_dir: Path) -> Dict[str, Any]:
    """GPT/SoVITS 가중치 파일 목록을 스캔한다.

    [주의]
    - 응답 키 구조(`gpt`, `sovits`, `summary`)는 backend/UI에서 그대로 쓰고 있을 수 있어서 유지한다.
    """
    result = {
        "gpt": {},
        "sovits": {},
        "summary": {"gpt_total": 0, "sovits_total": 0},
    }

    for dir_name in GPT_DIRS:
        dir_path = base_dir / dir_name
        if dir_path.exists() and dir_path.is_dir():
            files = [get_file_info(f) for f in dir_path.glob("*.ckpt")]
            if files:
                result["gpt"][dir_name] = files
                result["summary"]["gpt_total"] += len(files)

    for dir_name in SOVITS_DIRS:
        dir_path = base_dir / dir_name
        if dir_path.exists() and dir_path.is_dir():
            files = [get_file_info(f) for f in dir_path.glob("*.pth")]
            if files:
                result["sovits"][dir_name] = files
                result["summary"]["sovits_total"] += len(files)

    return result


def scan_train_voices(base_dir: Path) -> Dict[str, Any]:
    """`sample_train_voice` 하위 폴더를 스캔해서 학습용 오디오 목록을 만든다."""
    train_dir = base_dir / "sample_train_voice"
    voices: List[Dict[str, Any]] = []

    if not train_dir.exists():
        return {"voices": [], "total": 0, "message": "sample_train_voice 폴더가 없습니다"}

    for item in sorted(train_dir.iterdir()):
        if not item.is_dir():
            continue

        audio_files: List[Dict[str, Any]] = []
        for f in _iter_audio_files(item):
            duration = get_audio_duration(str(f))
            if duration is not None:
                duration = round(duration, 2)
                valid = 3.0 <= duration <= 10.0
            else:
                valid = False

            audio_files.append(
                {
                    "name": f.name,
                    "size_bytes": f.stat().st_size,
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                    "duration_sec": duration,
                    "valid_for_ref": valid,
                }
            )

        total_size_mb = sum(f["size_mb"] for f in audio_files)
        voices.append(
            {
                "character_name": item.name,
                "path": str(item),
                "file_count": len(audio_files),
                "files": audio_files,
                "total_size_mb": round(total_size_mb, 2),
                "status": "ready" if audio_files else "empty",
            }
        )

    return {"voices": voices, "total": len(voices), "base_path": str(train_dir)}


def scan_logs_outputs(logs_root: Path) -> Dict[str, Any]:
    """logs/{model_name}에서 학습 산출물(.ckpt/.pth)을 추론한다."""
    result = {"models": []}
    if not logs_root.exists() or not logs_root.is_dir():
        return result

    for item in sorted(logs_root.iterdir()):
        if not item.is_dir():
            continue
        model_name = item.name
        gpt_path = None
        sovits_path = None

        ckpts = list(item.glob("*.ckpt"))
        if ckpts:
            gpt_path = str(ckpts[0])

        pths = [p for p in item.glob("*.pth") if "pretrained" not in p.name.lower()]
        if pths:
            sovits_path = str(pths[0])

        result["models"].append(
            {"model_name": model_name, "gpt_path": gpt_path, "sovits_path": sovits_path}
        )

    return result


def build_all_file_summary(base_dir: Path) -> Dict[str, Any]:
    return {
        "models": scan_models(base_dir),
        "train_voices": scan_train_voices(base_dir),
        "logs": scan_logs_outputs(base_dir / "logs"),
    }


# ==================== 파일 조작(Modifier) 계열 ====================

def resolve_upload_target(base_dir: Path, category: str, sub_path: Optional[str], model_version: str) -> Path:
    """업로드 category를 실제 저장 경로로 매핑한다."""
    if category == "train_voice":
        if not sub_path:
            raise ApiError(400, "train_voice 업로드 시 sub_path(캐릭터명) 필수")
        return base_dir / "sample_train_voice" / sub_path

    if category == "gpt_weights":
        dir_name = f"GPT_weights_{model_version}" if model_version != "v1" else "GPT_weights"
        if dir_name not in GPT_DIRS:
            raise ApiError(400, f"유효하지 않은 모델 버전/경로: {dir_name}")
        return base_dir / dir_name

    if category == "sovits_weights":
        dir_name = f"SoVITS_weights_{model_version}" if model_version != "v1" else "SoVITS_weights"
        if dir_name not in SOVITS_DIRS:
            raise ApiError(400, f"유효하지 않은 모델 버전/경로: {dir_name}")
        return base_dir / dir_name

    raise ApiError(400, "유효하지 않은 category")


async def save_upload_file(file: Any, target_dir: Path) -> Dict[str, Any]:
    """업로드 파일을 저장하고 기존 응답 포맷으로 결과를 반환한다."""
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / file.filename

    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    return {
        "success": True,
        "filename": file.filename,
        "path": str(file_path),
        "size_bytes": file_path.stat().st_size,
        "message": "파일 업로드 완료",
    }


def delete_path_under_base(base_dir: Path, path_str: str) -> Dict[str, Any]:
    target_path = validate_path_under_base(base_dir, path_str)
    if not target_path.exists():
        raise ApiError(404, "파일을 찾을 수 없습니다")

    if target_path.is_dir():
        import shutil

        shutil.rmtree(target_path)
        return {"success": True, "message": f"폴더 삭제 완료: {target_path.name}"}

    target_path.unlink()
    return {"success": True, "message": f"파일 삭제 완료: {target_path.name}"}


def create_train_voice_dir(base_dir: Path, folder_name: str) -> Dict[str, Any]:
    ensure_safe_train_subdir_name(folder_name)
    target_dir = base_dir / "sample_train_voice" / folder_name
    if target_dir.exists():
        raise ApiError(400, "이미 존재하는 폴더입니다")
    target_dir.mkdir(parents=True, exist_ok=True)
    return {"success": True, "path": str(target_dir), "message": f"폴더 생성 완료: {folder_name}"}


# ==================== 오디오 조작(Modifier + Query 혼합) ====================

def _require_pydub() -> None:
    if not PYDUB_AVAILABLE:
        raise ApiError(500, "pydub 라이브러리가 설치되어 있지 않습니다. 'pip install pydub' 실행 후 다시 시도하세요.")


def trim_audio_file(base_dir: Path, source_path: str, max_duration_sec: float, output_suffix: str) -> Dict[str, Any]:
    """오디오를 최대 길이로 자르고 결과 메타데이터를 반환한다."""
    source = validate_path_under_base(base_dir, source_path)
    if not source.exists():
        raise ApiError(404, f"파일을 찾을 수 없습니다: {source_path}")
    if source.suffix.lower() not in AUDIO_SUFFIXES:
        raise ApiError(400, "지원하지 않는 오디오 형식입니다 (wav, mp3, flac, ogg만 지원)")

    _require_pydub()
    audio = AudioSegment.from_file(str(source))  # type: ignore[union-attr]
    duration_sec = len(audio) / 1000.0

    if duration_sec <= max_duration_sec:
        return {
            "success": True,
            "trimmed": False,
            "original_path": str(source),
            "output_path": str(source),
            "original_duration_sec": round(duration_sec, 2),
            "output_duration_sec": round(duration_sec, 2),
            "message": f"원본 길이가 {max_duration_sec}초 이하입니다. 자르지 않았습니다.",
        }

    trimmed_audio = audio[: int(max_duration_sec * 1000)]
    output_path = source.parent / f"{source.stem}{output_suffix}.wav"
    trimmed_audio.export(str(output_path), format="wav")

    return {
        "success": True,
        "trimmed": True,
        "original_path": str(source),
        "output_path": str(output_path),
        "original_duration_sec": round(duration_sec, 2),
        "output_duration_sec": round(max_duration_sec, 2),
        "message": f"오디오를 {max_duration_sec}초로 잘랐습니다.",
    }


def prepare_ref_audio(base_dir: Path, train_input_dir: str, max_duration_sec: float) -> Dict[str, Any]:
    """훈련 폴더에서 가장 긴 파일을 골라 ref_audio.wav로 저장한다."""
    train_dir = base_dir / "sample_train_voice" / train_input_dir
    if not train_dir.exists():
        raise ApiError(404, f"훈련 폴더를 찾을 수 없습니다: {train_input_dir}")

    _require_pydub()

    longest_file: Optional[Path] = None
    longest_duration = 0.0
    for audio_file in _iter_audio_files(train_dir):
        try:
            audio = AudioSegment.from_file(str(audio_file))  # type: ignore[union-attr]
            duration = len(audio) / 1000.0
            if duration > longest_duration:
                longest_duration = duration
                longest_file = audio_file
        except Exception:
            # 여기서 하나 실패했다고 전체를 죽이면 운영자가 폴더 정리할 때 너무 불편해진다.
            continue

    if not longest_file:
        raise ApiError(404, "훈련 폴더에 오디오 파일이 없습니다.")

    audio = AudioSegment.from_file(str(longest_file))  # type: ignore[union-attr]
    if longest_duration > max_duration_sec:
        trimmed_audio = audio[: int(max_duration_sec * 1000)]
        output_duration = max_duration_sec
    else:
        trimmed_audio = audio
        output_duration = longest_duration

    output_path = train_dir / "ref_audio.wav"
    trimmed_audio.export(str(output_path), format="wav")

    return {
        "success": True,
        "source_file": longest_file.name,
        "source_duration_sec": round(longest_duration, 2),
        "output_path": str(output_path),
        "output_duration_sec": round(output_duration, 2),
        "ref_audio_file": "ref_audio.wav",
        "message": f"가장 긴 파일({longest_file.name}, {round(longest_duration, 2)}초)을 {round(output_duration, 2)}초로 잘라 ref_audio.wav로 저장했습니다.",
    }


def list_audio_metadata(base_dir: Path, relative_path: str) -> Dict[str, Any]:
    """특정 학습 폴더의 오디오 목록 + 길이/valid_for_ref 정보를 반환한다."""
    target_dir = base_dir / "sample_train_voice" / relative_path
    if not target_dir.exists():
        raise ApiError(404, f"폴더를 찾을 수 없습니다: {relative_path}")

    audio_files: List[Dict[str, Any]] = []
    for audio_file in _iter_audio_files(target_dir):
        file_info = {
            "name": audio_file.name,
            "path": str(audio_file),
            "size_bytes": audio_file.stat().st_size,
            "size_mb": round(audio_file.stat().st_size / (1024 * 1024), 2),
            "duration_sec": None,
            "valid_for_ref": False,
        }
        duration = get_audio_duration(str(audio_file))
        if duration is not None:
            file_info["duration_sec"] = round(duration, 2)
            file_info["valid_for_ref"] = 3.0 <= duration <= 10.0
        audio_files.append(file_info)

    audio_files.sort(key=lambda x: x.get("duration_sec") or 0, reverse=True)
    return {
        "success": True,
        "path": str(target_dir),
        "files": audio_files,
        "total": len(audio_files),
        "pydub_available": PYDUB_AVAILABLE,
    }


def validate_ref_audio_duration(base_dir: Path, path_str: str) -> Dict[str, Any]:
    """ref_audio 길이 조건(3~10초) 검증 결과를 반환한다."""
    target = validate_path_under_base(base_dir, path_str)
    if not target.exists():
        raise ApiError(404, "File not found", extra={"valid": False})

    duration = get_audio_duration(str(target))
    if duration is None:
        raise ApiError(500, "Duration check failed (n/a)", extra={"valid": False})

    valid = 3.0 <= duration <= 10.0
    return {
        "valid": valid,
        "duration_sec": round(duration, 2),
        "message": "Valid" if valid else f"Duration {round(duration, 2)}s is out of range (3.0-10.0s)",
    }
