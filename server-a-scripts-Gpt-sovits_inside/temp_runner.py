import asyncio
import os
import sys
import logging
from typing import List, Dict

# Mock logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GPT_SOVITS_ROOT = os.getcwd()

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

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT, 
            env=current_env,
            cwd=GPT_SOVITS_ROOT 
        )
    except Exception as e:
        logger.error(f"Failed to start subprocess: {e}")
        return ""

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
        # raise Exception(f"Command failed with return code {process.returncode}")
    
    return output_str

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    async def main():
        print("Running self-test...", flush=True)
        log_file = "test_stream.log"
        if os.path.exists(log_file): os.remove(log_file)
        
        # Run test_streaming.py using current python
        cmd = [sys.executable, "test_streaming.py"]
        
        # Start monitoring task
        async def monitor():
            prev_size = 0
            for _ in range(7):
                await asyncio.sleep(1)
                if os.path.exists(log_file):
                    size = os.path.getsize(log_file)
                    print(f"Log Size: {size}", flush=True)
                    if size > prev_size:
                        print(" -> Log updated!", flush=True)
                        prev_size = size
        
        monitor_task = asyncio.create_task(monitor())
        await run_subprocess(cmd, log_file=log_file)
        await monitor_task
        print("Done.", flush=True)

    asyncio.run(main())
