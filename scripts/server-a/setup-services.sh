#!/bin/bash
# Server A - 서비스 설정 통합 스크립트 (NPM, 모델 스토리지)

echo "=========================================="
echo "서비스 설정"
echo "=========================================="
echo ""
echo "1. NPM 설정 (Nginx Proxy Manager)"
echo "2. 모델 스토리지 디렉터리 생성"
echo "3. 모두 설정"
echo "4. 취소"
echo ""
read -p "선택 (1-4): " -n 1 -r
echo
echo ""

case $REPLY in
    1)
        # NPM 설정
        echo "=========================================="
        echo "Nginx Proxy Manager 설정"
        echo "=========================================="
        echo ""
        
        NPM_DIR="./server-a"
        COMPOSE_FILE="$NPM_DIR/docker-compose.yaml"
        
        mkdir -p "$NPM_DIR/data/npm"
        mkdir -p "$NPM_DIR/data/letsencrypt"
        
        echo "docker-compose.yaml 생성 중..."
        cat > "$COMPOSE_FILE" <<EOF
version: '3.8'

services:
  npm:
    image: jc21/nginx-proxy-manager:latest
    container_name: npm
    restart: unless-stopped
    ports:
      - "80:80"
      - "81:81"
      - "443:443"
    volumes:
      - ./data/npm:/data
      - ./data/letsencrypt:/etc/letsencrypt
    networks:
      - avatar-forge-network
    extra_hosts:
      - "host.docker.internal:host-gateway"

networks:
  avatar-forge-network:
    driver: bridge
EOF
        
        echo "✅ docker-compose.yaml 생성 완료"
        echo ""
        
        echo "NPM 컨테이너 실행 중..."
        cd "$NPM_DIR"
        if docker ps -a | grep -q " npm$"; then
            echo "⚠️  기존 NPM 컨테이너 발견"
            read -p "   재생성하시겠습니까? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker-compose down
                docker-compose up -d npm
            else
                docker-compose up -d npm
            fi
        else
            docker-compose up -d npm
        fi
        cd - > /dev/null
        
        echo ""
        echo "✅ NPM 설정 완료"
        echo ""
        echo "📋 다음 단계:"
        echo "   1. NPM 웹 콘솔: http://<Server-A-IP>:81"
        echo "   2. Proxy Host 설정:"
        echo "      - Forward: http://host.docker.internal:9872 (⚠️ 중요: TTS API 포트)"
        echo "      - Scheme: http (중요!)"
        echo ""
        ;;
    2)
        # 모델 스토리지 설정
        echo "=========================================="
        echo "모델 파일 저장 디렉터리 생성"
        echo "=========================================="
        
        if [ -d "/mnt/shared_models" ]; then
            echo "⚠️  기존 디렉터리 발견: /mnt/shared_models"
            read -p "   덮어쓰시겠습니까? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                sudo rm -rf /mnt/shared_models
            else
                echo "건너뜀"
                exit 0
            fi
        fi
        
        sudo mkdir -p /mnt/shared_models/llm/gemma-3-27b-it
        
        CURRENT_USER=$(whoami)
        sudo chown -R $CURRENT_USER:$CURRENT_USER /mnt/shared_models
        sudo chmod -R 755 /mnt/shared_models
        
        echo "✅ 디렉터리 생성 완료"
        echo "   소유자: $CURRENT_USER"
        echo ""
        echo "디렉터리 구조:"
        find /mnt/shared_models -type d -maxdepth 2 | sort
        echo ""
        ;;
    3)
        echo "모델 스토리지 설정 중..."
        bash "$0" <<< "2"
        echo ""
        echo "NPM 설정 중..."
        bash "$0" <<< "1"
        ;;
    *)
        echo "취소됨"
        exit 0
        ;;
esac
