#!/bin/bash
# Server A - 시스템 정리 통합 스크립트 (디스크, Docker)

echo "=========================================="
echo "시스템 정리"
echo "=========================================="
echo ""
echo "1. 디스크 공간 정리 (캐시)"
echo "2. Docker 공간 정리"
echo "3. 모두 정리 (디스크 + Docker)"
echo "4. 취소"
echo ""
read -p "선택 (1-4): " -n 1 -r
echo
echo ""

case $REPLY in
    1)
        # 디스크 공간 정리
        echo "=========================================="
        echo "디스크 공간 정리"
        echo "=========================================="
        echo ""
        
        echo "현재 디스크 사용량:"
        df -h / | tail -1
        echo ""
        
        PIP_CACHE_DIR="$HOME/.cache/pip"
        HF_CACHE_DIR="$HOME/.cache/huggingface"
        CONDA_BASE=$(conda info --base 2>/dev/null || echo "$HOME/miniconda3")
        CONDA_CACHE_DIR="$CONDA_BASE/pkgs"
        REPO_DIR="/opt/GPT-SoVITS"
        
        echo "정리 가능한 항목:"
        echo "----------------------------------------"
        
        if [ -d "$PIP_CACHE_DIR" ]; then
            PIP_SIZE=$(du -sh "$PIP_CACHE_DIR" 2>/dev/null | awk '{print $1}')
            echo "1. pip 캐시: $PIP_SIZE"
        else
            echo "1. pip 캐시: 없음"
        fi
        
        if [ -d "$HF_CACHE_DIR" ]; then
            HF_SIZE=$(du -sh "$HF_CACHE_DIR" 2>/dev/null | awk '{print $1}')
            echo "2. Hugging Face 캐시: $HF_SIZE"
        else
            echo "2. Hugging Face 캐시: 없음"
        fi
        
        if [ -d "$CONDA_CACHE_DIR" ]; then
            CONDA_SIZE=$(du -sh "$CONDA_CACHE_DIR" 2>/dev/null | awk '{print $1}')
            echo "3. Conda 패키지 캐시: $CONDA_SIZE"
        else
            echo "3. Conda 패키지 캐시: 없음"
        fi
        
        if [ -d "$REPO_DIR" ]; then
            PYCACHE_COUNT=$(find "$REPO_DIR" -type d -name "__pycache__" 2>/dev/null | wc -l)
            if [ "$PYCACHE_COUNT" -gt 0 ]; then
                echo "4. Python 캐시: $PYCACHE_COUNT개"
            else
                echo "4. Python 캐시: 없음"
            fi
        fi
        echo ""
        
        echo "⚠️  경고: 다음 항목이 삭제됩니다:"
        echo "   - pip 캐시 (재다운로드 가능)"
        echo "   - Hugging Face 캐시 (재다운로드 필요)"
        echo "   - Conda 패키지 캐시 (재다운로드 가능)"
        echo "   - Python 캐시 (자동 재생성)"
        echo ""
        
        read -p "정말로 정리하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "취소됨"
            exit 0
        fi
        
        echo ""
        echo "정리 시작..."
        echo ""
        
        if [ -d "$PIP_CACHE_DIR" ]; then
            echo "1. pip 캐시 정리 중..."
            pip cache purge 2>/dev/null || rm -rf "$PIP_CACHE_DIR"/*
            echo "   ✅ 정리 완료"
        fi
        echo ""
        
        if [ -d "$HF_CACHE_DIR" ]; then
            echo "2. Hugging Face 캐시 정리 중..."
            rm -rf "$HF_CACHE_DIR"/*
            echo "   ✅ 정리 완료"
        fi
        echo ""
        
        if [ -d "$CONDA_CACHE_DIR" ]; then
            echo "3. Conda 패키지 캐시 정리 중..."
            conda clean --all -y
            echo "   ✅ 정리 완료"
        fi
        echo ""
        
        if [ -d "$REPO_DIR" ]; then
            echo "4. Python 캐시 정리 중..."
            find "$REPO_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
            find "$REPO_DIR" -name "*.pyc" -delete 2>/dev/null || true
            echo "   ✅ 정리 완료"
        fi
        echo ""
        
        echo "정리 후 디스크 사용량:"
        df -h / | tail -1
        echo ""
        ;;
    2)
        # Docker 공간 정리
        echo "=========================================="
        echo "Docker 공간 정리"
        echo "=========================================="
        echo ""
        
        echo "현재 Docker 사용량:"
        docker system df
        echo ""
        
        echo "정리 옵션:"
        echo "1. 사용하지 않는 이미지만 삭제 (안전)"
        echo "2. 사용하지 않는 모든 항목 삭제"
        echo "3. 빌드 캐시만 정리"
        echo "4. 볼륨 정리 (⚠️ 주의: 데이터 손실 가능)"
        echo "5. 전체 정리 (⚠️ 주의)"
        echo "6. 취소"
        echo ""
        read -p "선택 (1-6): " -n 1 -r
        echo
        echo ""
        
        case $REPLY in
            1)
                echo "사용하지 않는 이미지 삭제 중..."
                docker image prune -a -f
                echo "✅ 완료"
                ;;
            2)
                echo "사용하지 않는 모든 항목 삭제 중..."
                docker system prune -f
                echo "✅ 완료"
                ;;
            3)
                echo "빌드 캐시 정리 중..."
                docker builder prune -a -f
                echo "✅ 완료"
                ;;
            4)
                echo "⚠️  볼륨 정리"
                read -p "   정말로 진행하시겠습니까? (y/N): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    docker volume prune -f
                    echo "✅ 완료"
                else
                    echo "취소됨"
                fi
                ;;
            5)
                echo "⚠️  전체 정리"
                read -p "   정말로 진행하시겠습니까? (y/N): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    docker system prune -a -f --volumes
                    echo "✅ 완료"
                else
                    echo "취소됨"
                fi
                ;;
            *)
                echo "취소됨"
                exit 0
                ;;
        esac
        
        echo ""
        echo "정리 후 Docker 사용량:"
        docker system df
        echo ""
        ;;
    3)
        echo "디스크 정리 중..."
        bash "$0" <<< "1"
        echo ""
        echo "Docker 정리 중..."
        bash "$0" <<< "2"
        ;;
    *)
        echo "취소됨"
        exit 0
        ;;
esac
