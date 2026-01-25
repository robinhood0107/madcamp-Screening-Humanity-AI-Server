#!/bin/bash
# Server A - LLM 모델 삭제 스크립트

set -e

MODEL_DIR="/mnt/shared_models/llm"

echo "=========================================="
echo "LLM 모델 삭제"
echo "=========================================="
echo ""

# 설치된 모델 목록 확인
if [ ! -d "$MODEL_DIR" ]; then
    echo "❌ 모델 디렉터리가 존재하지 않습니다: $MODEL_DIR"
    exit 1
fi

echo "현재 설치된 모델:"
ls -lh "$MODEL_DIR" 2>/dev/null | grep "^d" | awk '{print "  - " $9}' || echo "  (모델 없음)"
echo ""

# 삭제할 모델 선택
echo "삭제할 모델을 선택하세요:"
echo "1. gemma-3-27b-it"
echo "2. dolphin-2.9-8b"
echo "3. 모든 LLM 모델 삭제"
echo "4. 취소"
echo ""
read -p "선택 (1-4): " -n 1 -r
echo
echo ""

case $REPLY in
    1)
        MODEL_NAME="gemma-3-27b-it"
        MODEL_PATH="$MODEL_DIR/$MODEL_NAME"
        ;;
    2)
        MODEL_NAME="dolphin-2.9-8b"
        MODEL_PATH="$MODEL_DIR/$MODEL_NAME"
        ;;
    3)
        echo "⚠️  경고: 모든 LLM 모델을 삭제합니다!"
        read -p "   정말로 삭제하시겠습니까? (yes 입력): " -r
        echo
        if [ "$REPLY" != "yes" ]; then
            echo "취소됨"
            exit 0
        fi
        
        # vLLM 컨테이너가 실행 중인지 확인
        if docker ps | grep -q vllm-server; then
            echo "⚠️  vLLM 컨테이너가 실행 중입니다"
            read -p "   컨테이너를 중지하고 삭제하시겠습니까? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker stop vllm-server 2>/dev/null || true
                docker rm vllm-server 2>/dev/null || true
            fi
        fi
        
        echo "모든 LLM 모델 삭제 중..."
        sudo rm -rf "$MODEL_DIR"/*
        echo "✅ 모든 LLM 모델 삭제 완료"
        exit 0
        ;;
    *)
        echo "취소됨"
        exit 0
        ;;
esac

# 선택된 모델 삭제
if [ ! -d "$MODEL_PATH" ]; then
    echo "❌ 모델이 존재하지 않습니다: $MODEL_PATH"
    exit 1
fi

# 모델 크기 확인
MODEL_SIZE=$(du -sh "$MODEL_PATH" 2>/dev/null | awk '{print $1}')
echo "삭제할 모델: $MODEL_NAME"
echo "크기: $MODEL_SIZE"
echo "경로: $MODEL_PATH"
echo ""

# vLLM 컨테이너가 해당 모델을 사용 중인지 확인
if docker ps | grep -q vllm-server; then
    echo "⚠️  vLLM 컨테이너가 실행 중입니다"
    CONTAINER_MODEL=$(docker inspect vllm-server 2>/dev/null | grep -oP '--model \K[^\s]+' || echo "")
    if echo "$CONTAINER_MODEL" | grep -q "$MODEL_NAME"; then
        echo "⚠️  경고: 현재 실행 중인 vLLM 컨테이너가 이 모델을 사용 중입니다!"
        read -p "   컨테이너를 중지하고 삭제하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker stop vllm-server 2>/dev/null || true
            docker rm vllm-server 2>/dev/null || true
            echo "✅ vLLM 컨테이너 중지 및 삭제 완료"
        else
            echo "❌ 모델이 사용 중이므로 삭제할 수 없습니다"
            exit 1
        fi
    fi
fi

# 최종 확인
read -p "정말로 삭제하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "취소됨"
    exit 0
fi

# 모델 삭제
echo "모델 삭제 중..."
sudo rm -rf "$MODEL_PATH"

echo "✅ 모델 삭제 완료: $MODEL_NAME"
echo ""
echo "확인:"
ls -lh "$MODEL_DIR" 2>/dev/null | grep "^d" | awk '{print "  - " $9}' || echo "  (모델 없음)"
