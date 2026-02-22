import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional

from gsv_automation.process import run_subprocess as _run_subprocess

# [역할]
# 이 파일은 스트리밍 로그 동작을 눈으로 확인하는 테스트 유틸이다.
# training_api의 실제 실행기와 같은 로직을 재사용해서, 로그 스트리밍 회귀를 빨리 확인할 수 있게 만든다.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GPT_SOVITS_ROOT = os.getcwd()


async def run_subprocess(cmd: List[str], env: Dict = None, log_file=None, dry_run=False):
    """호환성 래퍼: 기존 verify_streaming.py import 경로를 유지한다."""
    return await _run_subprocess(
        cmd,
        env=env,
        log_file=log_file,
        dry_run=dry_run,
        cwd=GPT_SOVITS_ROOT,
        pythonpath_root=GPT_SOVITS_ROOT,
        logger=logger,
        raise_on_error=False,
    )


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def main():
        print("Running self-test...", flush=True)
        log_file = "test_stream.log"
        if os.path.exists(log_file):
            os.remove(log_file)

        cmd = [sys.executable, "test_streaming.py"]

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
