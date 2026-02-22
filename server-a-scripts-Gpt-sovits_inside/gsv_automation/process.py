from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

PathLike = Union[str, Path]


async def run_subprocess(
    cmd: List[str],
    *,
    env: Optional[Dict[str, str]] = None,
    log_file: Optional[PathLike] = None,
    dry_run: bool = False,
    cwd: Optional[PathLike] = None,
    pythonpath_root: Optional[PathLike] = None,
    logger: Optional[logging.Logger] = None,
    raise_on_error: bool = True,
) -> str:
    """서브프로세스를 실행하고 stdout/stderr를 실시간으로 로그 파일에 기록한다.

    [역할]
    - training 파이프라인과 스트리밍 검증 유틸에서 공통으로 쓰는 프로세스 실행기.

    [왜 공통화했냐]
    - 예전에는 `training_api.py`와 `temp_runner.py`에 거의 같은 코드가 중복돼 있었음.
    - 이런 코드는 한 군데만 고쳐야 버그/로그 정책이 일관되게 유지된다.

    [부작용]
    - 프로세스 실행
    - log_file 지정 시 파일 append

    [주의]
    - training 경로에서는 실패 시 예외를 던져야 상위 상태를 failed로 바꿀 수 있음.
    - 테스트 유틸에서는 `raise_on_error=False`로 써서 관찰만 할 수도 있음.
    """
    log = logger or logging.getLogger(__name__)
    cmd_str = " ".join(cmd)
    log.info("Running command: %s", cmd_str)

    if dry_run:
        log.info("[DRY RUN] Skipping actual execution.")
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[DRY RUN] Would execute: {cmd_str}\n")
        return f"[DRY RUN] Executed: {cmd_str}"

    current_env = os.environ.copy()
    if pythonpath_root:
        current_env["PYTHONPATH"] = str(pythonpath_root)
    if env:
        current_env.update(env)
    current_env["PYTHONUNBUFFERED"] = "1"

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=current_env,
        cwd=str(cwd) if cwd else None,
    )

    full_output: List[str] = []
    log_path = Path(log_file) if log_file else None
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)

    async def _drain_stdout_with_file() -> None:
        with open(log_path, "a", encoding="utf-8", buffering=1) as f:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                decoded_line = line.decode(errors="ignore")
                f.write(decoded_line)
                f.flush()
                full_output.append(decoded_line)

    async def _drain_stdout_only() -> None:
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            full_output.append(line.decode(errors="ignore"))

    try:
        if log_path:
            await _drain_stdout_with_file()
        else:
            await _drain_stdout_only()
    except Exception as e:
        log.error("Failed while streaming subprocess output: %s", e)
        # 로그 파일 쓰기 실패해도 프로세스 stdout은 끝까지 비워줘야 hang 안 난다.
        await _drain_stdout_only()

    await process.wait()
    output_str = "".join(full_output)

    if process.returncode != 0:
        log.error("Command failed: %s\nOutput: %s", cmd_str, output_str)
        if raise_on_error:
            raise RuntimeError(f"Command failed with return code {process.returncode}")

    return output_str
