#!/bin/bash
# Server A - Hugging Face 캐시 삭제 및 GGUF 모델 다운로드

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

HF_CACHE_DIR="${HOME}/.cache/huggingface"
HF_HUB_DIR="$HF_CACHE_DIR/hub"
NEW_MODEL_REPO="unsloth/gemma-3-27b-it-GGUF"
NEW_MODEL_DIR="/mnt/shared_models/llm/gemma-3-27b-it-GGUF"

echo ""
echo -e "${BLUE}=========================================="
echo "Hugging Face 캐시 삭제 및 GGUF 모델 다운로드"
echo -e "==========================================${NC}"
echo ""
echo "이 스크립트는 다음 작업을 수행합니다:"
echo "1. Hugging Face 캐시 전체 삭제 (~/.cache/huggingface/hub/...)"
echo "2. GGUF 모델 다운로드 (unsloth/gemma-3-27b-it-GGUF)"
echo ""

# 1단계: Hugging Face 캐시 삭제
echo -e "${YELLOW}=========================================="
echo "1단계: Hugging Face 캐시 삭제"
echo -e "==========================================${NC}"

if [ -d "$HF_HUB_DIR" ]; then
    HF_CACHE_SIZE=$(du -sh "$HF_HUB_DIR" 2>/dev/null | awk '{print $1}')
    echo "Hugging Face 캐시 위치: $HF_HUB_DIR"
    echo "캐시 크기: $HF_CACHE_SIZE"
    echo ""
    read -p "Hugging Face 캐시를 전체 삭제하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$HF_HUB_DIR"/*
        echo -e "${GREEN}✅ Hugging Face 캐시 삭제 완료${NC}"
    else
        echo -e "${BLUE}ℹ️  Hugging Face 캐시 유지${NC}"
    fi
else
    echo -e "${BLUE}ℹ️  Hugging Face 캐시 디렉터리가 없습니다${NC}"
fi

# 2단계: GGUF 모델 다운로드
echo ""
echo -e "${YELLOW}=========================================="
echo "2단계: GGUF 모델 다운로드"
echo -e "==========================================${NC}"

echo "다운로드할 모델: $NEW_MODEL_REPO"
echo "저장 위치: $NEW_MODEL_DIR"
echo ""
echo "⚠️  참고: Gemma 모델은 Hugging Face 로그인이 필요할 수 있습니다."
echo "   hf auth login 또는 HF_TOKEN 환경 변수 설정이 필요합니다."
echo ""

# 디렉터리 생성
sudo mkdir -p "$NEW_MODEL_DIR"
sudo chown -R $(whoami):$(whoami) "$NEW_MODEL_DIR" 2>/dev/null || true

# 방법 1: Hugging Face 공식 CLI 사용 (권장, 가장 간단)
if command -v hf &> /dev/null; then
    echo "Hugging Face CLI(hf) 사용"
    echo "모델 다운로드 시작 중..."
    echo "⚠️  이 작업은 시간이 걸릴 수 있습니다 (~13-16GB)"
    echo ""
    # Q4_K_XL 파일만 다운로드 (Python API 사용, hf CLI는 특정 파일 다운로드 미지원)
    echo "⚠️  hf CLI는 특정 파일 다운로드를 지원하지 않습니다."
    echo "   Python API를 사용하여 Q4_K_XL 파일만 다운로드합니다."
    echo ""
    python3 -c "from huggingface_hub import hf_hub_download; import os; os.makedirs('/mnt/shared_models/llm/gemma-3-27b-it-GGUF', exist_ok=True); hf_hub_download(repo_id='unsloth/gemma-3-27b-it-GGUF', filename='gemma-3-27b-it-UD-Q4_K_XL.gguf', local_dir='/mnt/shared_models/llm/gemma-3-27b-it-GGUF', local_dir_use_symlinks=False); print('✅ 다운로드 완료')"
# 방법 2: Python API 사용
else
    echo "Python API 사용"
    echo "⚠️  참고: hf CLI가 없어 Python API를 사용합니다."
    echo "   hf CLI 설치: pip install --user huggingface-hub[cli]"
    echo ""
    
    # Python 환경 확인
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}❌ Python이 설치되어 있지 않습니다${NC}"
        exit 1
    fi
    
    # huggingface_hub 설치 확인
    if ! $PYTHON_CMD -c "import huggingface_hub" 2>/dev/null; then
        echo -e "${RED}❌ huggingface_hub가 설치되어 있지 않습니다${NC}"
        echo "   설치 방법:"
        echo "   1. Conda 환경 사용: conda activate <env> && pip install huggingface_hub"
        echo "   2. 가상환경 사용: python3 -m venv venv && source venv/bin/activate && pip install huggingface_hub"
        echo "   3. 또는 hf CLI 설치: pip install --user huggingface-hub[cli]"
        exit 1
    fi
    
    echo "모델 다운로드 시작 중..."
    echo "⚠️  이 작업은 시간이 걸릴 수 있습니다 (~13-16GB)"
    echo ""
    
    $PYTHON_CMD << PYTHON_SCRIPT
import sys
from huggingface_hub import hf_hub_download

model_repo = "unsloth/gemma-3-27b-it-GGUF"
filename = "gemma-3-27b-it-UD-Q4_K_XL.gguf"
local_dir = "/mnt/shared_models/llm/gemma-3-27b-it-GGUF"

print(f"다운로드 중: {model_repo}/{filename}")
print(f"저장 위치: {local_dir}")

try:
    from huggingface_hub import hf_hub_download
    hf_hub_download(
        repo_id=model_repo,
        filename=filename,
        local_dir=local_dir,
        local_dir_use_symlinks=False
    )
    print(f"✅ 다운로드 완료: {local_dir}")
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    print("   Hugging Face 로그인이 필요할 수 있습니다: hf auth login")
    sys.exit(1)
PYTHON_SCRIPT
fi

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✅ 모든 작업 완료!"
    echo -e "==========================================${NC}"
    echo ""
    echo "다운로드된 모델:"
    du -sh "$NEW_MODEL_DIR"
    echo ""
    echo "다음 단계:"
    echo "1. Ollama Docker 컨테이너 설정 (docker-compose.yml)"
    echo "2. Ollama에서 모델 사용: ollama run hf.co/$NEW_MODEL_REPO"
    echo ""
else
    echo -e "${RED}❌ 모델 다운로드 실패${NC}"
    exit 1
fi
