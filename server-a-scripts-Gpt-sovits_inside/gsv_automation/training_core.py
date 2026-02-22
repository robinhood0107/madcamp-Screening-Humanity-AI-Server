from __future__ import annotations

import json
import logging
import os
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .process import run_subprocess
from .runtime import ResolvedRootInfo

# [호환성 계약]
# 이 모듈은 training_api 엔드포인트의 내부 구현만 담당한다.
# 포트/엔드포인트/응답 키/로그 파일명/상태 문자열은 엔트리포인트 계약이라 여기서도 그대로 유지해야 함.

MODEL_VERSIONS: Dict[str, Dict[str, str]] = {
    "v1": {
        "s1_config": "s1longer.yaml",
        "s2_config": "s2.json",
        "s1_pretrained": "s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt",
        "s2_pretrained": "s2G488k.pth",
        "s2_pretrained_D": "s2D488k.pth",
    },
    "v2": {
        "s1_config": "s1longer-v2.yaml",
        "s2_config": "s2.json",
        "s1_pretrained": "gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt",
        "s2_pretrained": "gsv-v2final-pretrained/s2G2333k.pth",
        "s2_pretrained_D": "gsv-v2final-pretrained/s2D2333k.pth",
    },
    "v4": {
        "s1_config": "s1longer-v2.yaml",
        "s2_config": "s2.json",
        "s1_pretrained": "s1v3.ckpt",
        "s2_pretrained": "gsv-v4-pretrained/s2Gv4.pth",
        "s2_pretrained_D": "gsv-v4-pretrained/s2Dv4.pth",
    },
    "v2Pro": {
        "s1_config": "s1longer-v2.yaml",
        "s2_config": "s2v2Pro.json",
        "s1_pretrained": "s1v3.ckpt",
        "s2_pretrained": "v2Pro/s2Gv2Pro.pth",
        "s2_pretrained_D": "v2Pro/s2Dv2Pro.pth",
    },
    "v2ProPlus": {
        "s1_config": "s1longer-v2.yaml",
        "s2_config": "s2v2ProPlus.json",
        "s1_pretrained": "s1v3.ckpt",
        "s2_pretrained": "v2Pro/s2Gv2ProPlus.pth",
        "s2_pretrained_D": "v2Pro/s2Dv2ProPlus.pth",
    },
}

REQUIRED_TRAINING_SCRIPTS: Tuple[str, ...] = (
    "tools/slice_audio.py",
    "tools/asr/fasterwhisper_asr.py",
    "GPT_SoVITS/prepare_datasets/1-get-text.py",
    "GPT_SoVITS/prepare_datasets/2-get-hubert-wav32k.py",
    "GPT_SoVITS/prepare_datasets/3-get-semantic.py",
    "GPT_SoVITS/s2_train.py",
    "GPT_SoVITS/s1_train.py",
)


@dataclass(frozen=True)
class TrainingRuntime:
    """학습 파이프라인이 의존하는 런타임 경로/환경 묶음.

    [왜 dataclass로 묶냐]
    - 함수 분해할 때 인자를 10개씩 넘기기 시작하면 실수 확률이 급격히 올라간다.
    - root/config/log/temp/python 경로를 한 객체로 고정해두면 단계 함수 재사용이 쉬워진다.
    """

    root_info: ResolvedRootInfo
    python_exe: str
    tools_dir: Path
    gpt_sovits_dir: Path
    pretrained_models_dir: Path
    configs_dir: Path
    temp_root: Path
    logs_root: Path

    @property
    def root(self) -> Path:
        return self.root_info.path


@dataclass(frozen=True)
class TrainingPaths:
    model_id: str
    work_dir: Path
    log_dir: Path
    sliced_dir: Path
    status_file: Path
    pipeline_log_file: Path


class StatusWriter:
    """인메모리 상태 + 디스크 상태(status.json/pipeline.log)를 같이 관리한다.

    [역할]
    - training_status dict와 logs/{model}/status.json/pipeline.log를 한 군데에서 업데이트.

    [왜 분리했냐]
    - 예전 코드는 이 로직이 `training_pipeline()` 안쪽 nested function에 숨어 있어서
      단계 분해할 때 재사용/테스트가 어려웠다.
    """

    def __init__(
        self,
        *,
        training_status: Dict[str, Dict[str, Any]],
        paths: TrainingPaths,
        logger: logging.Logger,
    ) -> None:
        self.training_status = training_status
        self.paths = paths
        self.logger = logger

    def log_pipeline(self, msg: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.paths.pipeline_log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")

    def update(self, status: str, progress: float, message: str, error: Optional[str] = None) -> Dict[str, Any]:
        now = datetime.now().isoformat()
        model_id = self.paths.model_id
        payload: Dict[str, Any] = {
            "model_name": model_id,
            "status": status,
            "progress": progress,
            "message": message,
            "error": error,
            "created_at": self.training_status.get(model_id, {}).get("created_at", now),
            "updated_at": now,
        }
        self.training_status[model_id] = payload

        log_msg = f"[{status.upper()}] {message} (Progress: {progress})"
        if error:
            log_msg += f" | ERROR: {error}"
        self.log_pipeline(log_msg)

        with open(self.paths.status_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        return payload


def build_training_runtime(root_info: ResolvedRootInfo, python_exe: str) -> TrainingRuntime:
    root = root_info.path
    gpt_sovits_dir = root / "GPT_SoVITS"
    return TrainingRuntime(
        root_info=root_info,
        python_exe=python_exe,
        tools_dir=root / "tools",
        gpt_sovits_dir=gpt_sovits_dir,
        pretrained_models_dir=gpt_sovits_dir / "pretrained_models",
        configs_dir=gpt_sovits_dir / "configs",
        temp_root=root / "TEMP",
        logs_root=root / "logs",
    )


def ensure_runtime_dirs(runtime: TrainingRuntime, logger: logging.Logger) -> None:
    """학습 중간 산출물 디렉토리를 미리 보장한다."""
    try:
        runtime.temp_root.mkdir(parents=True, exist_ok=True)
        runtime.logs_root.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning("Failed to ensure runtime dirs under %s: %s", runtime.root, e)


def check_required_paths(runtime: TrainingRuntime, logger: logging.Logger) -> Tuple[bool, List[str]]:
    """학습 파이프라인 필수 스크립트 존재 여부를 확인한다."""
    missing: List[str] = []
    for rel in REQUIRED_TRAINING_SCRIPTS:
        if not (runtime.root / rel).exists():
            missing.append(rel)
    if missing:
        logger.error("Missing required scripts: %s", missing)
        return False, missing
    return True, []


def build_training_paths(runtime: TrainingRuntime, model_id: str) -> TrainingPaths:
    work_dir = runtime.temp_root / model_id
    log_dir = runtime.logs_root / model_id
    sliced_dir = work_dir / "sliced"
    work_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    return TrainingPaths(
        model_id=model_id,
        work_dir=work_dir,
        log_dir=log_dir,
        sliced_dir=sliced_dir,
        status_file=log_dir / "status.json",
        pipeline_log_file=log_dir / "pipeline.log",
    )


def queue_status_payload(model_name: str, dry_run: bool) -> Dict[str, Any]:
    now = datetime.now().isoformat()
    return {
        "model_name": model_name,
        "status": "queued",
        "progress": 0.0,
        "message": "Queued for training" + (" [DRY RUN]" if dry_run else ""),
        "created_at": now,
        "updated_at": now,
    }


def load_status_from_disk(runtime: TrainingRuntime, training_status: Dict[str, Dict[str, Any]], model_name: str) -> Optional[Dict[str, Any]]:
    status_file = runtime.logs_root / model_name / "status.json"
    if not status_file.exists():
        return None
    try:
        with open(status_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        training_status[model_name] = data
        return data
    except Exception:
        return None


def read_pipeline_log(runtime: TrainingRuntime, model_name: str) -> Optional[str]:
    log_file = runtime.logs_root / model_name / "pipeline.log"
    if not log_file.exists():
        return None
    with open(log_file, "r", encoding="utf-8") as f:
        return f.read()


def _resolve_list_file(paths: TrainingPaths, dry_run: bool) -> Path:
    list_file = paths.work_dir / "sliced.list"
    if dry_run:
        # dry_run에서도 다음 단계 입력 형식을 맞춰줘야 파이프라인 전체 회귀 테스트가 가능하다.
        with open(list_file, "w", encoding="utf-8") as f:
            f.write("dummy|dummy|ZH|dummy text")

    if list_file.exists():
        return list_file

    fallback = [f for f in os.listdir(paths.work_dir) if f.endswith(".list")]
    if fallback:
        return paths.work_dir / fallback[0]
    raise RuntimeError("ASR failed to generate .list file")


def _build_common_env(req: Any, *, list_file: Path, paths: TrainingPaths) -> Dict[str, str]:
    return {
        "inp_text": str(list_file),
        "inp_wav_dir": str(paths.sliced_dir),
        "exp_name": paths.model_id,
        "opt_dir": str(paths.log_dir),
        "i_part": "0",
        "all_parts": "1",
        "_CUDA_VISIBLE_DEVICES": req.gpu_numbers.split("-")[0],
        "is_half": "True",
    }


def _resolve_bert_dir(runtime: TrainingRuntime) -> str:
    bert_dir = runtime.pretrained_models_dir / "chinese-roberta-wwm-ext-large"
    if bert_dir.exists():
        return str(bert_dir)
    return "GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large"


def _resolve_cnhubert_dir(runtime: TrainingRuntime) -> str:
    cnhubert_dir = runtime.pretrained_models_dir / "chinese-hubert-base"
    if cnhubert_dir.exists():
        return str(cnhubert_dir)
    return "GPT_SoVITS/pretrained_models/chinese-hubert-base"


def _resolve_pretrained_s2g(runtime: TrainingRuntime, version_config: Dict[str, str], dry_run: bool) -> str:
    abs_path = runtime.pretrained_models_dir / version_config["s2_pretrained"]
    if abs_path.exists() or dry_run:
        return str(abs_path)

    rel_path = Path("GPT_SoVITS") / "pretrained_models" / version_config["s2_pretrained"]
    if rel_path.exists():
        return str(rel_path)

    raise RuntimeError(f"Pretrained Model Not Found: {abs_path}")


async def _run_slice_step(req: Any, runtime: TrainingRuntime, paths: TrainingPaths, logger: logging.Logger) -> None:
    """slice_audio.py 실행 단계.

    [주의]
    - positional arg 순서를 바꾸면 바로 다른 파라미터로 해석돼서 결과가 틀어진다.
    - 이 단계는 외부 툴 계약이라 인자 순서를 절대 건드리지 않는다.
    """
    slice_cmd = [
        runtime.python_exe,
        "tools/slice_audio.py",
        req.upload_path,
        str(paths.sliced_dir),
        "-34",
        "4000",
        "300",
        "10",
        "500",
        "0.9",
        "0.25",
        "0",
        "1",
    ]
    await run_subprocess(
        slice_cmd,
        log_file=paths.log_dir / "slice.log",
        dry_run=req.dry_run,
        cwd=runtime.root,
        pythonpath_root=runtime.root,
        logger=logger,
    )


async def _run_asr_step(req: Any, runtime: TrainingRuntime, paths: TrainingPaths, logger: logging.Logger) -> None:
    asr_cmd = [
        runtime.python_exe,
        "tools/asr/fasterwhisper_asr.py",
        "-i",
        str(paths.sliced_dir),
        "-o",
        str(paths.work_dir),
        "-s",
        "large-v3-turbo",
        "-l",
        "auto",
        "-p",
        "float32",
    ]
    await run_subprocess(
        asr_cmd,
        log_file=paths.log_dir / "asr.log",
        dry_run=req.dry_run,
        cwd=runtime.root,
        pythonpath_root=runtime.root,
        logger=logger,
    )


async def _run_prepare_text_step(req: Any, runtime: TrainingRuntime, paths: TrainingPaths, env_common: Dict[str, str], logger: logging.Logger) -> None:
    env_text = env_common.copy()
    env_text["bert_pretrained_dir"] = _resolve_bert_dir(runtime)

    if req.dry_run:
        with open(paths.log_dir / "2-name2text-0.txt", "w", encoding="utf-8") as f:
            f.write("dummy")

    await run_subprocess(
        [runtime.python_exe, "GPT_SoVITS/prepare_datasets/1-get-text.py"],
        env=env_text,
        log_file=paths.log_dir / "format_text.log",
        dry_run=req.dry_run,
        cwd=runtime.root,
        pythonpath_root=runtime.root,
        logger=logger,
    )


async def _run_prepare_hubert_step(req: Any, runtime: TrainingRuntime, paths: TrainingPaths, env_common: Dict[str, str], logger: logging.Logger) -> None:
    env_hubert = env_common.copy()
    env_hubert["cnhubert_base_dir"] = _resolve_cnhubert_dir(runtime)

    await run_subprocess(
        [runtime.python_exe, "GPT_SoVITS/prepare_datasets/2-get-hubert-wav32k.py"],
        env=env_hubert,
        log_file=paths.log_dir / "format_hubert.log",
        dry_run=req.dry_run,
        cwd=runtime.root,
        pythonpath_root=runtime.root,
        logger=logger,
    )


async def _run_prepare_semantic_step(
    req: Any,
    runtime: TrainingRuntime,
    paths: TrainingPaths,
    env_common: Dict[str, str],
    version_config: Dict[str, str],
    logger: logging.Logger,
) -> Tuple[str, Path]:
    pretrained_s2g = _resolve_pretrained_s2g(runtime, version_config, req.dry_run)
    s2config_src = runtime.configs_dir / version_config["s2_config"]

    env_semantic = env_common.copy()
    env_semantic["pretrained_s2G"] = pretrained_s2g
    env_semantic["s2config_path"] = str(s2config_src)

    if req.dry_run:
        with open(paths.log_dir / "6-name2semantic-0.tsv", "w", encoding="utf-8") as f:
            f.write("dummy")

    await run_subprocess(
        [runtime.python_exe, "GPT_SoVITS/prepare_datasets/3-get-semantic.py"],
        env=env_semantic,
        log_file=paths.log_dir / "format_semantic.log",
        dry_run=req.dry_run,
        cwd=runtime.root,
        pythonpath_root=runtime.root,
        logger=logger,
    )
    return pretrained_s2g, s2config_src


def _build_s2_config(req: Any, paths: TrainingPaths, s2config_src: Path) -> str:
    if s2config_src.exists():
        with open(s2config_src, "r", encoding="utf-8") as f:
            s2_data = json.load(f)

        s2_data["train"]["batch_size"] = req.batch_size
        s2_data["train"]["epochs"] = req.total_epochs
        s2_data["train"]["text_low_lr_rate"] = req.text_low_lr_rate
        s2_data["train"]["if_save_latest"] = req.if_save_latest
        s2_data["train"]["if_save_every_weights"] = req.if_save_every_weights
        s2_data["train"]["save_every_epoch"] = req.save_every_epoch
        s2_data["data"]["exp_dir"] = str(paths.log_dir)

        user_s2_config = paths.work_dir / "s2.json"
        with open(user_s2_config, "w", encoding="utf-8") as f:
            json.dump(s2_data, f, indent=4)
        return str(user_s2_config)

    if not req.dry_run:
        raise RuntimeError(f"Config not found: {s2config_src}")
    return "dummy_s2.json"


async def _run_sovits_train_step(req: Any, runtime: TrainingRuntime, paths: TrainingPaths, env_common: Dict[str, str], user_s2_config: str, logger: logging.Logger) -> None:
    sovits_cmd = [runtime.python_exe, "GPT_SoVITS/s2_train.py", "--config", user_s2_config]
    await run_subprocess(
        sovits_cmd,
        env=env_common,
        log_file=paths.log_dir / "train_s2.log",
        dry_run=req.dry_run,
        cwd=runtime.root,
        pythonpath_root=runtime.root,
        logger=logger,
    )


def _build_s1_config(req: Any, runtime: TrainingRuntime, paths: TrainingPaths, version_config: Dict[str, str]) -> str:
    gpt_epochs = 15
    gpt_save_freq = 5
    s1config_src = runtime.configs_dir / version_config["s1_config"]

    if s1config_src.exists():
        with open(s1config_src, "r", encoding="utf-8") as f:
            s1_data = yaml.safe_load(f)

        s1_data["train"]["exp_name"] = paths.model_id
        s1_data["output_dir"] = str(paths.log_dir)
        s1_data["train"]["epochs"] = gpt_epochs
        s1_data["train"]["batch_size"] = req.batch_size
        s1_data["train"]["save_every_n_epoch"] = gpt_save_freq
        s1_data["train"]["if_save_latest"] = req.if_save_latest
        s1_data["train"]["if_save_every_weights"] = req.if_save_every_weights
        s1_data["train_semantic_path"] = str(paths.log_dir / "6-name2semantic-0.tsv")
        s1_data["train_phoneme_path"] = str(paths.log_dir / "2-name2text-0.txt")

        user_s1_config = paths.work_dir / "s1.yaml"
        with open(user_s1_config, "w", encoding="utf-8") as f:
            yaml.dump(s1_data, f)
        return str(user_s1_config)

    if not req.dry_run:
        raise RuntimeError(f"Config not found: {s1config_src}")
    return "dummy_s1.yaml"


async def _run_gpt_train_step(req: Any, runtime: TrainingRuntime, paths: TrainingPaths, env_common: Dict[str, str], user_s1_config: str, logger: logging.Logger) -> None:
    await run_subprocess(
        [runtime.python_exe, "GPT_SoVITS/s1_train.py", "--config_file", user_s1_config],
        env=env_common,
        log_file=paths.log_dir / "train_s1.log",
        dry_run=req.dry_run,
        cwd=runtime.root,
        pythonpath_root=runtime.root,
        logger=logger,
    )


async def training_pipeline(req: Any, runtime: TrainingRuntime, training_status: Dict[str, Dict[str, Any]], logger: logging.Logger) -> None:
    """학습 파이프라인 오케스트레이터.

    [역할]
    - slice -> asr -> dataset prepare -> SoVITS train -> GPT train 순서로 단계를 실행한다.

    [왜 오케스트레이터를 따로 뒀냐]
    - 엔드포인트 함수는 transport만 담당하고, 학습 흐름은 여기서 한 번에 관리해야 재사용/테스트가 쉬움.

    [주의]
    - 상태 문자열/로그 파일명/단계 순서는 backend와 운영 문서가 기대하는 계약이라 유지한다.
    """
    if req.version not in MODEL_VERSIONS:
        raise RuntimeError(f"Invalid version: {req.version}. Available: {list(MODEL_VERSIONS.keys())}")

    version_config = MODEL_VERSIONS[req.version]
    paths = build_training_paths(runtime, req.model_name)
    status_writer = StatusWriter(training_status=training_status, paths=paths, logger=logger)

    try:
        status_writer.update("processing", 0.1, f"Starting Audio Slicing (Version: {req.version})...")
        await _run_slice_step(req, runtime, paths, logger)

        status_writer.update("processing", 0.2, "Audio Slicing Done. Starting ASR...")
        await _run_asr_step(req, runtime, paths, logger)

        list_file = _resolve_list_file(paths, req.dry_run)
        status_writer.update("processing", 0.3, "ASR Done. Preparing Dataset...")

        env_common = _build_common_env(req, list_file=list_file, paths=paths)

        await _run_prepare_text_step(req, runtime, paths, env_common, logger)
        status_writer.update("processing", 0.4, "Text Formatting Done. Extracting Features...")

        await _run_prepare_hubert_step(req, runtime, paths, env_common, logger)
        _, s2config_src = await _run_prepare_semantic_step(req, runtime, paths, env_common, version_config, logger)

        status_writer.update("training_sovits", 0.5, f"Preprocessing Done. Starting SoVITS Training ({req.version})...")
        user_s2_config = _build_s2_config(req, paths, s2config_src)
        await _run_sovits_train_step(req, runtime, paths, env_common, user_s2_config, logger)

        status_writer.update("training_gpt", 0.7, f"SoVITS Training Done. Starting GPT Training ({req.version})...")
        user_s1_config = _build_s1_config(req, runtime, paths, version_config)
        await _run_gpt_train_step(req, runtime, paths, env_common, user_s1_config, logger)

        status_writer.update("completed", 1.0, "All Training Completed successfully.")
    except Exception as e:
        logger.error("Pipeline Error: %s", traceback.format_exc())
        status_writer.update("failed", 0.0, "Training Failed", error=str(e))

