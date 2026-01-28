import asyncio
import os
import sys
import logging
import temp_runner
from temp_runner import run_subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_streaming():
    print("Testing streaming...", flush=True)
    log_file = "test_stream.log"
    
    # Remove old log if exists
    if os.path.exists(log_file):
        os.remove(log_file)
    
    # Run the mock script
    # We use python to run the test_streaming.py script we just created
    cmd = [sys.executable, "test_streaming.py"]
    
    # Run functionality
    task = asyncio.create_task(run_subprocess(cmd, log_file=log_file))
    
    # Monitor the log file while process is running
    print(f"Monitoring log file: {log_file}", flush=True)
    previous_size = 0
    for _ in range(7): # Check for 7 seconds (script takes ~5s)
        await asyncio.sleep(1)
        if os.path.exists(log_file):
            current_size = os.path.getsize(log_file)
            print(f"Log size: {current_size} bytes", flush=True)
            if current_size > previous_size:
                print(" -> Log file updated!", flush=True)
                with open(log_file, "r", encoding="utf-8") as f:
                    # Print last line
                    lines = f.readlines()
                    if lines:
                         print(f"    Last line: {lines[-1].strip()}", flush=True)
            previous_size = current_size
    
    await task
    print("Test Complete.", flush=True)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_streaming())
