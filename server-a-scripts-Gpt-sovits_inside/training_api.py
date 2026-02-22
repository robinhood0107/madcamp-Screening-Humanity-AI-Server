
import os
import sys
import shutil
import json
import yaml
import asyncio
import subprocess
import traceback
import logging
from typing import Optional, List, Dict
from fastapi import FastAPI, BackgroundTasks, HTTPException, Body
from pydantic import BaseModel
from datetime import datetime

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="GPT-SoVITS Training API")

# --- Configuration ---
GPT_SOVITS_ROOT = "/opt/GPT-SoVITS"  # Server A Path
PYTHON_EXE = sys.executable  # Use current python (Conda env)

# Paths
TOOLS_DIR = os.path.join(GPT_SOVITS_ROOT, "tools")
GPT_SOVITS_DIR = os.path.join(GPT_SOVITS_ROOT, "GPT_SoVITS")
PRETRAINED_MODELS_DIR = os.path.join(GPT_SOVITS_DIR, "pretrained_models") # Correct path: GPT-SoVITS/GPT_SoVITS/pretrained_models
CONFIGS_DIR = os.path.join(GPT_SOVITS_DIR, "configs")
TEMP_ROOT = os.path.join(GPT_SOVITS_ROOT, "TEMP")
LOGS_ROOT = os.path.join(GPT_SOVITS_ROOT, "logs")

# Ensure required directories
os.makedirs(TEMP_ROOT, exist_ok=True)
os.makedirs(LOGS_ROOT, exist_ok=True)

# Training Status Storage (In-memory for now)
training_status: Dict[str, Dict] = {}

# --- Version Mapping ---
# Define available versions and their corresponding config/model paths
MODEL_VERSIONS = {
    "v1": {
        "s1_config": "s1longer.yaml",
        "s2_config": "s2.json",
        "s1_pretrained": "s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt",
        "s2_pretrained": "s2G488k.pth",
        "s2_pretrained_D": "s2D488k.pth" # Optional
    },
    "v2": {
        "s1_config": "s1longer-v2.yaml",
        "s2_config": "s2.json", # Assuming base v2 uses standard s2.json or similar
        "s1_pretrained": "gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt",
        "s2_pretrained": "gsv-v2final-pretrained/s2G2333k.pth",
        "s2_pretrained_D": "gsv-v2final-pretrained/s2D2333k.pth"
    },
    "v4": {
        "s1_config": "s1longer-v2.yaml", # Assuming V2 config compatible or V4 shares standard
        "s2_config": "s2.json", # Needs verification if v4 uses s2.json
        "s1_pretrained": "s1v3.ckpt",
        "s2_pretrained": "gsv-v4-pretrained/s2Gv4.pth",
        "s2_pretrained_D": "gsv-v4-pretrained/s2Dv4.pth" # Note: User specified, ensure file exists
    },
    "v2Pro": {
        "s1_config": "s1longer-v2.yaml", # Uses V2 config (Compatible with s1v3?)
        "s2_config": "s2v2Pro.json",
        "s1_pretrained": "s1v3.ckpt", # User specified
        "s2_pretrained": "v2Pro/s2Gv2Pro.pth",
        "s2_pretrained_D": "v2Pro/s2Dv2Pro.pth"
    },
    "v2ProPlus": {
        "s1_config": "s1longer-v2.yaml", 
        "s2_config": "s2v2ProPlus.json",
        "s1_pretrained": "s1v3.ckpt", # User specified
        "s2_pretrained": "v2Pro/s2Gv2ProPlus.pth",
        "s2_pretrained_D": "v2Pro/s2Dv2ProPlus.pth"
    }
}

# --- Verification & Safety Checks ---
def check_paths():
    """Verify that all required scripts exist."""
    required_scripts = [
        "tools/slice_audio.py",
        "tools/asr/fasterwhisper_asr.py",
        "GPT_SoVITS/prepare_datasets/1-get-text.py",
        "GPT_SoVITS/prepare_datasets/2-get-hubert-wav32k.py",
        "GPT_SoVITS/prepare_datasets/3-get-semantic.py",
        "GPT_SoVITS/s2_train.py",
        "GPT_SoVITS/s1_train.py",
    ]
    missing = []
    for script in required_scripts:
        full_path = os.path.join(GPT_SOVITS_ROOT, script)
        if not os.path.exists(full_path):
            missing.append(script)
    
    if missing:
        logger.error(f"Missing required scripts: {missing}")
        return False, missing
    return True, []

@app.on_event("startup")
async def startup_event():
    ok, missing = check_paths()
    if not ok:
        logger.warning(f"⚠️  CRITICAL: Missing scripts: {missing}. The API may fail.")

class TrainRequest(BaseModel):
    model_name: str
    upload_path: str 
    version: str = "v2" 
    # User specified default values from 1Ba-SoVITS and 1Bb-GPT
    batch_size: int = 11  # Updated from 4
    total_epochs: int = 8 # Updated, do not increase too high
    text_low_lr_rate: float = 0.4
    if_save_latest: bool = True
    if_save_every_weights: bool = True
    save_every_epoch: int = 4 # SoVITS save freq
    gpu_numbers: str = "0-0" # Updated format
    dry_run: bool = False 

class TrainStatusResponse(BaseModel):
    model_name: str
    status: str  
    progress: float
    message: str
    error: Optional[str] = None
    created_at: str
    updated_at: str


async def run_subprocess(cmd: List[str], env: Dict = None, log_file=None, dry_run=False):
    """Running subprocess asynchronously and streaming output to log in REAL-TIME"""
    cmd_str = ' '.join(cmd)
    logger.info(f"Running command: {cmd_str}")
    
    if dry_run:
        logger.info("[DRY RUN] Skipping actual execution.")
        if log_file:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[DRY RUN] Would execute: {cmd_str}\n")
        return f"[DRY RUN] Executed: {cmd_str}"

    # Merge env
    current_env = os.environ.copy()
    current_env["PYTHONPATH"] = GPT_SOVITS_ROOT 
    if env:
        current_env.update(env)
    
    # 🌟 Unbuffered output for Python sub-processes to ensure real-time logging
    current_env["PYTHONUNBUFFERED"] = "1"

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT, 
        env=current_env,
        cwd=GPT_SOVITS_ROOT 
    )

    # Real-time streaming loop
    full_output = []
    
    if log_file:
        # Open file once for appending
        try:
             with open(log_file, "a", encoding="utf-8", buffering=1) as f: # Line buffering
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    
                    decoded_line = line.decode(errors='ignore')
                    # Write to file immediately
                    f.write(decoded_line)
                    f.flush() # Ensure it's written to disk
                    
                    # Also keep in memory if needed for return (optional, careful with huge logs)
                    full_output.append(decoded_line)
        except Exception as e:
            logger.error(f"Failed to write to log file: {e}")
            # Continue reading even if file write fails to avoid blocking process
            while True:
                line = await process.stdout.readline()
                if not line: break
                full_output.append(line.decode(errors='ignore'))
    else:
        # If no log file, just drain stdout
        while True:
            line = await process.stdout.readline()
            if not line: break
            full_output.append(line.decode(errors='ignore'))

    await process.wait()
    
    output_str = "".join(full_output)

    if process.returncode != 0:
        logger.error(f"Command failed: {cmd_str}\nOutput: {output_str}")
        raise Exception(f"Command failed with return code {process.returncode}")
    
    return output_str

async def training_pipeline(req: TrainRequest):
    # Validate version
    if req.version not in MODEL_VERSIONS:
        raise Exception(f"Invalid version: {req.version}. Available: {list(MODEL_VERSIONS.keys())}")
    
    version_config = MODEL_VERSIONS[req.version]

    model_id = req.model_name
    work_dir = os.path.join(TEMP_ROOT, model_id)
    log_dir = os.path.join(LOGS_ROOT, model_id)
    sliced_dir = os.path.join(work_dir, "sliced")
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    
    status_file = os.path.join(log_dir, "status.json") # Persist status
    pipeline_log_file = os.path.join(log_dir, "pipeline.log") # Main pipeline log

    def log_pipeline(msg):
        """Append message to pipeline log file with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(pipeline_log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    
    def update_status(status, progress, message, error=None):
        now = datetime.now().isoformat()
        training_status[model_id] = {
            "model_name": model_id,
            "status": status,
            "progress": progress,
            "message": message,
            "error": error,
            "created_at": training_status.get(model_id, {}).get("created_at", now),
            "updated_at": now
        }
        
        # Log to pipeline.log
        log_msg = f"[{status.upper()}] {message} (Progress: {progress})"
        if error:
            log_msg += f" | ERROR: {error}"
        log_pipeline(log_msg)

        # Save to status file
        with open(status_file, "w") as f:
            json.dump(training_status[model_id], f)

    try:
        update_status("processing", 0.1, f"Starting Audio Slicing (Version: {req.version})...")
        
        # 1. Slice Audio
        # User Params: -34, 4000, 300, 10, 500, 0.9, 0.25, 0, 1 (all_parts)
        slice_cmd = [
            PYTHON_EXE, "tools/slice_audio.py",
            req.upload_path, sliced_dir,
            "-34", "4000", "300", "10", "500", "0.9", "0.25", "0", "1"
        ]
        await run_subprocess(slice_cmd, log_file=os.path.join(log_dir, "slice.log"), dry_run=req.dry_run)
        
        update_status("processing", 0.2, "Audio Slicing Done. Starting ASR...")

        # 2. ASR
        # User Params: large-v3-turbo, float32, auto
        asr_cmd = [
            PYTHON_EXE, "tools/asr/fasterwhisper_asr.py",
            "-i", sliced_dir,
            "-o", work_dir,
            "-s", "large-v3-turbo", 
            "-l", "auto",
            "-p", "float32"
        ]
        await run_subprocess(asr_cmd, log_file=os.path.join(log_dir, "asr.log"), dry_run=req.dry_run)
        
        # Identify .list file
        list_file = os.path.join(work_dir, "sliced.list")
        if req.dry_run:
            # Create dummy .list file for next steps
            with open(list_file, "w") as f: f.write("dummy|dummy|ZH|dummy text")
        
        if not os.path.exists(list_file):
             # Try finding any .list file
             files = [f for f in os.listdir(work_dir) if f.endswith(".list")]
             if files:
                 list_file = os.path.join(work_dir, files[0])
             else:
                 raise Exception("ASR failed to generate .list file")

        update_status("processing", 0.3, "ASR Done. Preparing Dataset...")

        # 3. Data Formatting (1-get-text)
        # Env vars required: inp_text, inp_wav_dir, exp_name, opt_dir, bert_pretrained_dir
        env_common = {
            "inp_text": list_file,
            "inp_wav_dir": sliced_dir,
            "exp_name": model_id,
            "opt_dir": log_dir,
            "i_part": "0",
            "all_parts": "1",
            "_CUDA_VISIBLE_DEVICES": req.gpu_numbers.split("-")[0], # Use first GPU if format is 0-0
            "is_half": "True"
        }
        
        # BERT path check
        bert_dir = os.path.join(PRETRAINED_MODELS_DIR, "chinese-roberta-wwm-ext-large")
        if not os.path.exists(bert_dir):
            bert_dir = "GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large"
        
        env_text = env_common.copy()
        env_text["bert_pretrained_dir"] = bert_dir
        
        # Dry Run Mocking
        if req.dry_run:
            with open(os.path.join(log_dir, "2-name2text-0.txt"), "w") as f: f.write("dummy")

        await run_subprocess([PYTHON_EXE, "GPT_SoVITS/prepare_datasets/1-get-text.py"], env=env_text, log_file=os.path.join(log_dir, "format_text.log"), dry_run=req.dry_run)
        
        update_status("processing", 0.4, "Text Formatting Done. Extracting Features...")

        # 4. Feature Extraction (2-get-hubert, 3-get-semantic)
        cnhubert_dir = os.path.join(PRETRAINED_MODELS_DIR, "chinese-hubert-base")
        if not os.path.exists(cnhubert_dir):
             cnhubert_dir = "GPT_SoVITS/pretrained_models/chinese-hubert-base"

        env_hubert = env_common.copy()
        env_hubert["cnhubert_base_dir"] = cnhubert_dir
        
        await run_subprocess([PYTHON_EXE, "GPT_SoVITS/prepare_datasets/2-get-hubert-wav32k.py"], env=env_hubert, log_file=os.path.join(log_dir, "format_hubert.log"), dry_run=req.dry_run)
        
        # 3-get-semantic (Version Dependent)
        pretrained_s2G = os.path.join(PRETRAINED_MODELS_DIR, version_config["s2_pretrained"])
        s2config_src = os.path.join(CONFIGS_DIR, version_config["s2_config"])
        
        # Verify Model Existence
        if not os.path.exists(pretrained_s2G) and not req.dry_run:
             # Try relative path check
             if os.path.exists(os.path.join("GPT_SoVITS", "pretrained_models", version_config["s2_pretrained"])):
                 pretrained_s2G = os.path.join("GPT_SoVITS", "pretrained_models", version_config["s2_pretrained"])
             else:
                 raise Exception(f"Pretrained Model Not Found: {pretrained_s2G}")

        env_semantic = env_common.copy()
        env_semantic["pretrained_s2G"] = pretrained_s2G
        env_semantic["s2config_path"] = s2config_src
        
        if req.dry_run:
             with open(os.path.join(log_dir, "6-name2semantic-0.tsv"), "w") as f: f.write("dummy")

        await run_subprocess([PYTHON_EXE, "GPT_SoVITS/prepare_datasets/3-get-semantic.py"], env=env_semantic, log_file=os.path.join(log_dir, "format_semantic.log"), dry_run=req.dry_run)

        update_status("training_sovits", 0.5, f"Preprocessing Done. Starting SoVITS Training ({req.version})...")

        # 5. SoVITS Training
        if os.path.exists(s2config_src):
            with open(s2config_src, "r") as f:
                s2_data = json.load(f)
            
            s2_data["train"]["batch_size"] = req.batch_size
            s2_data["train"]["epochs"] = req.total_epochs
            s2_data["train"]["text_low_lr_rate"] = req.text_low_lr_rate
            s2_data["train"]["if_save_latest"] = req.if_save_latest
            s2_data["train"]["if_save_every_weights"] = req.if_save_every_weights
            s2_data["train"]["save_every_epoch"] = req.save_every_epoch
            s2_data["data"]["exp_dir"] = log_dir 
            
            user_s2_config = os.path.join(work_dir, "s2.json")
            with open(user_s2_config, "w") as f:
                json.dump(s2_data, f, indent=4)
        else:
            if not req.dry_run:
                raise Exception(f"Config not found: {s2config_src}")
            user_s2_config = "dummy_s2.json"

        # SoVITS Command
        sovits_cmd = [
             PYTHON_EXE, "GPT_SoVITS/s2_train.py", 
             "--config", user_s2_config,
        ]
        await run_subprocess(sovits_cmd, env=env_common, log_file=os.path.join(log_dir, "train_s2.log"), dry_run=req.dry_run)
        
        update_status("training_gpt", 0.7, f"SoVITS Training Done. Starting GPT Training ({req.version})...")
        
        # 6. GPT Training
        # User Params: Batch 11, Epochs 15, Save Frequency 5
        gpt_epochs = 15
        gpt_save_freq = 5
        
        s1config_src = os.path.join(CONFIGS_DIR, version_config["s1_config"])
        if os.path.exists(s1config_src):
            with open(s1config_src, "r") as f:
                s1_data = yaml.safe_load(f)
                
            s1_data["train"]["exp_name"] = model_id
            s1_data["output_dir"] = log_dir
            s1_data["train"]["epochs"] = gpt_epochs
            s1_data["train"]["batch_size"] = req.batch_size
            s1_data["train"]["save_every_n_epoch"] = gpt_save_freq
            s1_data["train"]["if_save_latest"] = req.if_save_latest
            s1_data["train"]["if_save_every_weights"] = req.if_save_every_weights
            
            s1_data["train_semantic_path"] = os.path.join(log_dir, "6-name2semantic-0.tsv")
            s1_data["train_phoneme_path"] = os.path.join(log_dir, "2-name2text-0.txt")
            
            user_s1_config = os.path.join(work_dir, "s1.yaml")
            with open(user_s1_config, "w") as f:
                yaml.dump(s1_data, f)
        else:
            if not req.dry_run:
                 raise Exception(f"Config not found: {s1config_src}")
            user_s1_config = "dummy_s1.yaml"
            
        await run_subprocess([PYTHON_EXE, "GPT_SoVITS/s1_train.py", "--config_file", user_s1_config], env=env_common, log_file=os.path.join(log_dir, "train_s1.log"), dry_run=req.dry_run)
        
        update_status("completed", 1.0, "All Training Completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline Error: {traceback.format_exc()}")
        update_status("failed", 0.0, "Training Failed", error=str(e))
        
        # 1. Slice Audio
        # User Params: -34, 4000, 300, 10, 500, 0.9, 0.25, 0, 4 (threads)
        # slice_audio.py args mapping (based on previous analysis):
        # inp, opt_root, threshold, min_length, min_interval, hop_size, max_sil_kept, _max, alpha, i_part, all_part
        # Wait, slice_audio.py args are positional. 
        # User requested: threshold=-34, min_length=4000, min_interval=300, hop_size=10, max_sil_kept=500, _max=0.9, alpha=0.25
        # CPU threads? slice_audio.py usually uses multiprocess inside, maybe not configurable via args or uses n_proc?
        # Let's check slice_audio.py args again if needed, assuming mapped order.
        # Order: threshold, min_length, min_interval, hop_size, max_sil_kept, _max, alpha, i_part, all_part
        slice_cmd = [
            PYTHON_EXE, "tools/slice_audio.py",
            req.upload_path, sliced_dir,
            "-34", "4000", "300", "10", "500", "0.9", "0.25", "0", "1"
        ]
        await run_subprocess(slice_cmd, log_file=os.path.join(log_dir, "slice.log"), dry_run=req.dry_run)
        
        update_status("processing", 0.2, "Audio Slicing Done. Starting ASR...")

        # 2. ASR
        # User Params: large-v3-turbo, float32, auto
        asr_cmd = [
            PYTHON_EXE, "tools/asr/fasterwhisper_asr.py",
            "-i", sliced_dir,
            "-o", work_dir,
            "-s", "large-v3-turbo", 
            "-l", "auto",
            "-p", "float32"
        ]
        await run_subprocess(asr_cmd, log_file=os.path.join(log_dir, "asr.log"), dry_run=req.dry_run)
        
        # ... (List file check logic remains) ...
        # ... (Setup for 3. Formatting) ...

        # 3. Data Formatting
        env_common = {
            "inp_text": list_file,
            "inp_wav_dir": sliced_dir,
            "exp_name": model_id,
            "opt_dir": log_dir,
            "i_part": "0",
            "all_parts": "1",
            "_CUDA_VISIBLE_DEVICES": req.gpu_numbers.split("-")[0], # Use first GPU if format is 0-0
            "is_half": "True"
        }
        
        # ... (BERT/Hubert logic remains same) ...
        
        # ... (run 1-get-text) ...
        # ... (run 2-get-hubert) ...
        # ... (run 3-get-semantic) ...

        update_status("training_sovits", 0.5, f"Preprocessing Done. Starting SoVITS Training ({req.version})...")

        # 5. SoVITS Training
        if os.path.exists(s2config_src):
            with open(s2config_src, "r") as f:
                s2_data = json.load(f)
            
            s2_data["train"]["batch_size"] = req.batch_size
            s2_data["train"]["epochs"] = req.total_epochs
            s2_data["train"]["text_low_lr_rate"] = req.text_low_lr_rate
            s2_data["train"]["if_save_latest"] = req.if_save_latest
            s2_data["train"]["if_save_every_weights"] = req.if_save_every_weights
            s2_data["train"]["save_every_epoch"] = req.save_every_epoch
            # GPU handling? s2_train uses env var usually.
            s2_data["data"]["exp_dir"] = log_dir 
            
            user_s2_config = os.path.join(work_dir, "s2.json")
            with open(user_s2_config, "w") as f:
                json.dump(s2_data, f, indent=4)
        else:
             # ... error handling ...
             user_s2_config = "dummy.json"

        # SoVITS Command
        sovits_cmd = [
             PYTHON_EXE, "GPT_SoVITS/s2_train.py", 
             "--config", user_s2_config,
        ]
        await run_subprocess(sovits_cmd, env=env_common, log_file=os.path.join(log_dir, "train_s2.log"), dry_run=req.dry_run)
        
        update_status("training_gpt", 0.7, f"SoVITS Training Done. Starting GPT Training ({req.version})...")
        
        # 6. GPT Training
        # User Params: Batch 11, Epochs 15, Save Frequency 5
        gpt_epochs = 15
        gpt_save_freq = 5
        
        s1config_src = os.path.join(CONFIGS_DIR, version_config["s1_config"])
        if os.path.exists(s1config_src):
            with open(s1config_src, "r") as f:
                s1_data = yaml.safe_load(f)
                
            s1_data["train"]["exp_name"] = model_id
            s1_data["output_dir"] = log_dir
            s1_data["train"]["epochs"] = gpt_epochs
            s1_data["train"]["batch_size"] = req.batch_size
            s1_data["train"]["save_every_n_epoch"] = gpt_save_freq
            s1_data["train"]["if_save_latest"] = req.if_save_latest
            s1_data["train"]["if_save_every_weights"] = req.if_save_every_weights
            
            s1_data["train_semantic_path"] = os.path.join(log_dir, "6-name2semantic-0.tsv")
            s1_data["train_phoneme_path"] = os.path.join(log_dir, "2-name2text-0.txt")
            
            user_s1_config = os.path.join(work_dir, "s1.yaml")
            with open(user_s1_config, "w") as f:
                yaml.dump(s1_data, f)
        else:
            # ...
            user_s1_config = "dummy_s1.yaml"
            
        await run_subprocess([PYTHON_EXE, "GPT_SoVITS/s1_train.py", "--config_file", user_s1_config], env=env_common, log_file=os.path.join(log_dir, "train_s1.log"), dry_run=req.dry_run)
        
        update_status("completed", 1.0, "All Training Completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline Error: {traceback.format_exc()}")
        update_status("failed", 0.0, "Training Failed", error=str(e))
        

@app.get("/api/health")
async def health():
    """Server B /health/detailed 등에서 헬스 체크용. 200 반환으로 404 로그 노이즈 제거."""
    return {"status": "ok"}


@app.post("/api/train/start")
async def start_training(req: TrainRequest, background_tasks: BackgroundTasks):
    if req.model_name in training_status and training_status[req.model_name]["status"] in ["queued", "processing", "training_sovits", "training_gpt"]:
        if not req.dry_run:
            raise HTTPException(status_code=400, detail="Model is already training")
    
    update_status = {
        "model_name": req.model_name,
        "status": "queued",
        "progress": 0.0,
        "message": "Queued for training" + (" [DRY RUN]" if req.dry_run else ""),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    training_status[req.model_name] = update_status
    
    background_tasks.add_task(training_pipeline, req)
    
    return update_status

@app.get("/api/train/status/{model_name}")
async def get_status(model_name: str):
    if model_name in training_status:
        return training_status[model_name]
    
    # Try finding in logs
    status_file = os.path.join(LOGS_ROOT, model_name, "status.json")
    if os.path.exists(status_file):
        try:
            with open(status_file, "r") as f:
                data = json.load(f)
                training_status[model_name] = data
                return data
        except:
            pass
            
    raise HTTPException(status_code=404, detail="Model training status not found")

@app.get("/api/train/log/{model_name}")
async def get_log(model_name: str):
    """Retrieve the full content of pipeline.log for a specific model."""
    log_file = os.path.join(LOGS_ROOT, model_name, "pipeline.log")
    
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()
            return {"model_name": model_name, "log": content}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read log file: {str(e)}")
            
    # If log file doesn't exist yet, return empty or specific message
    if model_name in training_status:
         return {"model_name": model_name, "log": "Log file not created yet. Training may be in queue or initializing."}

    raise HTTPException(status_code=404, detail="Log not found for this model")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10002) # Use 10002 for Training API
