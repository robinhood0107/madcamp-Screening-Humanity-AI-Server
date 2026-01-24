#!/usr/bin/env python3
"""
Hugging Face 모델 다운로드 스크립트
사용법: python download_hf_model.py <repo_id> <local_dir>
"""

import sys
import os
from huggingface_hub import snapshot_download

def main():
    if len(sys.argv) < 3:
        print("사용법: python download_hf_model.py <repo_id> <local_dir>")
        print("예시: python download_hf_model.py cognitivecomputations/dolphin-2.9-llama3-8b /mnt/shared_models/llm/dolphin-2.9-8b")
        sys.exit(1)
    
    repo_id = sys.argv[1]
    local_dir = sys.argv[2]
    
    # 디렉터리 생성
    os.makedirs(local_dir, exist_ok=True)
    
    print(f"==========================================")
    print(f"모델 다운로드 시작")
    print(f"==========================================")
    print(f"저장소: {repo_id}")
    print(f"저장 위치: {local_dir}")
    print(f"")
    
    try:
        snapshot_download(
            repo_id=repo_id,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            resume_download=True
        )
        print(f"")
        print(f"==========================================")
        print(f"✅ 다운로드 완료: {local_dir}")
        print(f"==========================================")
        
        # 디렉터리 크기 확인
        import subprocess
        result = subprocess.run(['du', '-sh', local_dir], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"디렉터리 크기: {result.stdout.strip()}")
        
    except Exception as e:
        print(f"")
        print(f"==========================================")
        print(f"❌ 오류 발생: {e}")
        print(f"==========================================")
        sys.exit(1)

if __name__ == "__main__":
    main()
