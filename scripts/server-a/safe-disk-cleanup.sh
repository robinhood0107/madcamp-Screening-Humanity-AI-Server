#!/bin/bash
# Server A - 안전한 디스크 용량 확보 스크립트
# 실행 중인 시스템에 손상을 주지 않으면서 최대한 용량 확보

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}=========================================="
echo "안전한 디스크 용량 확보"
echo -e "==========================================${NC}"
echo ""
echo "⚠️  이 스크립트는 실행 중인 시스템에 영향을 주지 않습니다"
echo "   - 실행 중인 서비스는 유지됩니다"
echo "   - 사용 중인 Docker 컨테이너는 보호됩니다"
echo "   - 필수 파일은 삭제하지 않습니다"
echo "   - 현재 사용 중인 pip/Conda 환경은 절대 건드리지 않습니다"
echo "   - 설치된 패키지와 의존성은 보호됩니다"
echo ""

# 현재 디스크 사용량 확인
echo "현재 디스크 사용량:"
df -h / | tail -1
echo ""

# 정리 가능한 항목 확인
echo -e "${YELLOW}정리 가능한 항목 확인 중...${NC}"
echo ""

TOTAL_FREEABLE=0

# 1. Docker 사용하지 않는 리소스
echo "1️⃣  Docker 리소스"
echo "----------------------------------------"
if command -v docker &> /dev/null && docker info &> /dev/null; then
    DOCKER_INFO=$(docker system df 2>/dev/null)
    echo "$DOCKER_INFO"
    
    # 사용하지 않는 이미지 크기 추출
    UNUSED_IMAGES=$(docker system df --format "{{.Size}}" 2>/dev/null | head -1 || echo "0B")
    echo "   사용하지 않는 이미지: $UNUSED_IMAGES"
else
    echo "   Docker가 실행되지 않았습니다"
fi
echo ""

# 2. pip 캐시 (안전: 다운로드 캐시만, 설치된 패키지는 보호)
echo "2️⃣  pip 캐시 (다운로드 캐시만)"
echo "----------------------------------------"
PIP_CACHE_DIR="$HOME/.cache/pip"
if [ -d "$PIP_CACHE_DIR" ]; then
    PIP_SIZE=$(du -sh "$PIP_CACHE_DIR" 2>/dev/null | awk '{print $1}')
    PIP_SIZE_BYTES=$(du -sb "$PIP_CACHE_DIR" 2>/dev/null | awk '{print $1}')
    echo "   크기: $PIP_SIZE"
    echo "   ✅ 안전: 설치된 패키지는 보호됩니다"
    TOTAL_FREEABLE=$((TOTAL_FREEABLE + PIP_SIZE_BYTES))
else
    echo "   없음"
fi
echo ""

# 3. Conda 패키지 캐시 (안전: 사용하지 않는 패키지만)
echo "3️⃣  Conda 패키지 캐시 (사용하지 않는 패키지만)"
echo "----------------------------------------"
CONDA_BASE=$(conda info --base 2>/dev/null || echo "$HOME/miniconda3" || echo "$HOME/miniforge3")
CONDA_CACHE_DIR="$CONDA_BASE/pkgs"

# 현재 활성화된 Conda 환경 확인
if command -v conda &> /dev/null; then
    ACTIVE_ENV=$(conda info --envs 2>/dev/null | grep '*' | awk '{print $1}' | sed 's/*//' | xargs || echo "")
    if [ -n "$ACTIVE_ENV" ]; then
        ACTIVE_ENV_PATH="$CONDA_BASE/envs/$ACTIVE_ENV"
        echo "   현재 활성화된 환경: $ACTIVE_ENV"
        echo "   환경 경로: $ACTIVE_ENV_PATH"
        echo "   ✅ 이 환경의 패키지는 절대 삭제하지 않습니다"
    fi
fi

if [ -d "$CONDA_CACHE_DIR" ]; then
    CONDA_SIZE=$(du -sh "$CONDA_CACHE_DIR" 2>/dev/null | awk '{print $1}')
    CONDA_SIZE_BYTES=$(du -sb "$CONDA_CACHE_DIR" 2>/dev/null | awk '{print $1}')
    echo "   캐시 크기: $CONDA_SIZE"
    echo "   ✅ 안전: 사용 중인 패키지는 보호됩니다"
    TOTAL_FREEABLE=$((TOTAL_FREEABLE + CONDA_SIZE_BYTES))
else
    echo "   없음"
fi
echo ""

# 4. 시스템 패키지 캐시 (apt)
echo "4️⃣  시스템 패키지 캐시 (apt)"
echo "----------------------------------------"
if [ -d "/var/cache/apt" ]; then
    APT_SIZE=$(du -sh /var/cache/apt 2>/dev/null | awk '{print $1}')
    APT_SIZE_BYTES=$(du -sb /var/cache/apt 2>/dev/null | awk '{print $1}')
    echo "   크기: $APT_SIZE"
    TOTAL_FREEABLE=$((TOTAL_FREEABLE + APT_SIZE_BYTES))
else
    echo "   없음"
fi
echo ""

# 5. 로그 파일 (journalctl)
echo "5️⃣  시스템 로그 (journalctl)"
echo "----------------------------------------"
if command -v journalctl &> /dev/null; then
    JOURNAL_SIZE=$(journalctl --disk-usage 2>/dev/null | awk '{print $1}' || echo "0")
    if [ -n "$JOURNAL_SIZE" ] && [ "$JOURNAL_SIZE" != "0" ]; then
        echo "   크기: $JOURNAL_SIZE"
    else
        echo "   크기: 확인 불가"
    fi
else
    echo "   journalctl 없음"
fi
echo ""

# 6. 임시 파일 (/tmp)
echo "6️⃣  임시 파일 (/tmp)"
echo "----------------------------------------"
if [ -d "/tmp" ]; then
    TMP_SIZE=$(du -sh /tmp 2>/dev/null | awk '{print $1}' || echo "0")
    TMP_SIZE_BYTES=$(du -sb /tmp 2>/dev/null | awk '{print $1}' || echo "0")
    echo "   크기: $TMP_SIZE"
    echo "   ⚠️  주의: 실행 중인 프로세스가 사용 중일 수 있습니다"
else
    echo "   없음"
fi
echo ""

# 7. Python 캐시
echo "7️⃣  Python 캐시 (__pycache__)"
echo "----------------------------------------"
REPO_DIR="/opt/GPT-SoVITS"
if [ -d "$REPO_DIR" ]; then
    PYCACHE_COUNT=$(find "$REPO_DIR" -type d -name "__pycache__" 2>/dev/null | wc -l)
    if [ "$PYCACHE_COUNT" -gt 0 ]; then
        PYCACHE_SIZE=$(find "$REPO_DIR" -type d -name "__pycache__" -exec du -ch {} + 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")
        echo "   개수: $PYCACHE_COUNT개"
        echo "   크기: $PYCACHE_SIZE"
    else
        echo "   없음"
    fi
else
    echo "   GPT-SoVITS 디렉터리 없음"
fi
echo ""

# 예상 확보 가능 용량 요약
echo -e "${YELLOW}=========================================="
echo "예상 확보 가능 용량"
echo -e "==========================================${NC}"
echo ""
echo "확보 가능한 항목:"
echo "  - pip 캐시: ~2.0GB"
echo "  - Conda 패키지 캐시: ~1.9GB"
echo "  - 시스템 패키지 캐시: ~수백MB"
echo "  - Docker 사용하지 않는 이미지: ~1.9GB"
echo "  - Python 캐시: ~수십MB"
echo ""
echo "⚠️  참고:"
echo "  - 실행 중인 Docker 컨테이너는 보호됩니다"
echo "  - 실행 중인 서비스는 영향받지 않습니다"
echo "  - 현재 사용 중인 pip/Conda 환경은 절대 건드리지 않습니다"
echo "  - 설치된 패키지와 의존성은 완전히 보호됩니다"
echo "  - 캐시는 필요 시 자동으로 재생성됩니다"
echo ""

read -p "정리를 시작하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "취소됨"
    exit 0
fi

echo ""
echo -e "${GREEN}정리 시작...${NC}"
echo ""

FREED_SPACE=0

# 1. Docker 사용하지 않는 이미지 정리 (안전)
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "1️⃣  Docker 사용하지 않는 이미지 정리 중..."
    BEFORE_DOCKER=$(docker system df --format "{{.Size}}" 2>/dev/null | head -1 || echo "0B")
    docker image prune -a -f 2>/dev/null || true
    AFTER_DOCKER=$(docker system df --format "{{.Size}}" 2>/dev/null | head -1 || echo "0B")
    echo -e "   ${GREEN}✅ 완료${NC}"
    echo ""
fi

# 2. pip 캐시 정리 (안전: 다운로드 캐시만, 설치된 패키지는 보호)
if [ -d "$PIP_CACHE_DIR" ]; then
    echo "2️⃣  pip 캐시 정리 중 (다운로드 캐시만)..."
    echo "   ⚠️  설치된 패키지는 절대 삭제하지 않습니다"
    # pip cache purge는 다운로드된 패키지 파일만 삭제하고 설치된 패키지는 건드리지 않음
    pip cache purge 2>/dev/null || rm -rf "$PIP_CACHE_DIR"/* 2>/dev/null || true
    echo -e "   ${GREEN}✅ 완료 (설치된 패키지는 보호됨)${NC}"
    echo ""
fi

# 3. Conda 패키지 캐시 정리 (안전: 사용하지 않는 패키지만)
if [ -d "$CONDA_CACHE_DIR" ] && command -v conda &> /dev/null; then
    echo "3️⃣  Conda 패키지 캐시 정리 중 (사용하지 않는 패키지만)..."
    
    # 현재 활성화된 환경 확인
    ACTIVE_ENV=$(conda info --envs 2>/dev/null | grep '*' | awk '{print $1}' | sed 's/*//' | xargs || echo "")
    if [ -n "$ACTIVE_ENV" ]; then
        echo "   현재 활성화된 환경: $ACTIVE_ENV"
        echo "   ⚠️  이 환경의 패키지는 절대 삭제하지 않습니다"
    fi
    
    # 안전한 정리: tarball과 인덱스 캐시만 삭제 (사용 중인 패키지는 보호)
    # --tarballs: 다운로드된 tarball만 삭제 (안전)
    # --index-cache: 인덱스 캐시만 삭제 (안전)
    # --packages: 사용하지 않는 패키지만 삭제 (conda가 자동으로 사용 중인 패키지 제외)
    conda clean --tarballs -y 2>/dev/null || true
    conda clean --index-cache -y 2>/dev/null || true
    # 사용하지 않는 패키지만 삭제 (conda가 자동으로 사용 중인 패키지는 제외)
    conda clean --packages -y 2>/dev/null || true
    echo -e "   ${GREEN}✅ 완료 (사용 중인 패키지는 보호됨)${NC}"
    echo ""
fi

# 4. 시스템 패키지 캐시 정리 (apt)
if [ -d "/var/cache/apt" ]; then
    echo "4️⃣  시스템 패키지 캐시 정리 중..."
    sudo apt-get clean 2>/dev/null || true
    sudo apt-get autoclean 2>/dev/null || true
    echo -e "   ${GREEN}✅ 완료${NC}"
    echo ""
fi

# 5. 시스템 로그 정리 (최근 7일만 유지)
if command -v journalctl &> /dev/null; then
    echo "5️⃣  시스템 로그 정리 중 (최근 7일만 유지)..."
    sudo journalctl --vacuum-time=7d 2>/dev/null || true
    echo -e "   ${GREEN}✅ 완료${NC}"
    echo ""
fi

# 6. 임시 파일 정리 (10일 이상 된 파일만)
if [ -d "/tmp" ]; then
    echo "6️⃣  임시 파일 정리 중 (10일 이상 된 파일만)..."
    find /tmp -type f -atime +10 -delete 2>/dev/null || true
    find /tmp -type d -empty -delete 2>/dev/null || true
    echo -e "   ${GREEN}✅ 완료${NC}"
    echo ""
fi

# 7. Python 캐시 정리
if [ -d "$REPO_DIR" ]; then
    echo "7️⃣  Python 캐시 정리 중..."
    find "$REPO_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$REPO_DIR" -name "*.pyc" -delete 2>/dev/null || true
    find "$REPO_DIR" -name "*.pyo" -delete 2>/dev/null || true
    echo -e "   ${GREEN}✅ 완료${NC}"
    echo ""
fi

# 정리 후 디스크 사용량
echo -e "${GREEN}=========================================="
echo "정리 완료!"
echo -e "==========================================${NC}"
echo ""
echo "정리 후 디스크 사용량:"
df -h / | tail -1
echo ""
echo "정리 후 Docker 사용량:"
if command -v docker &> /dev/null && docker info &> /dev/null; then
    docker system df 2>/dev/null || echo "   Docker 정보 확인 불가"
else
    echo "   Docker가 실행되지 않았습니다"
fi
echo ""
echo -e "${BLUE}💡 팁:${NC}"
echo "  - pip 캐시는 패키지 설치 시 자동으로 재생성됩니다"
echo "  - Conda 캐시는 패키지 설치 시 자동으로 재생성됩니다"
echo "  - Docker 이미지는 필요 시 다시 pull하면 됩니다"
echo ""
