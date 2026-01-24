#!/bin/bash
# Server A - 시스템 모니터링 통합 스크립트 (디스크, 로그, 포트, 모델, NPM 연결)

echo "=========================================="
echo "시스템 모니터링"
echo "=========================================="
echo ""
echo "1. 전체 설치 항목 용량 확인"
echo "2. GPT-SoVITS 디스크 사용량 확인"
echo "3. GPT-SoVITS 로그 확인"
echo "4. 포트 확인 (9872/9873/9874)"
echo "5. 모델 검증"
echo "6. NPM 연결 테스트"
echo "7. 취소"
echo ""
read -p "선택 (1-7): " -n 1 -r
echo
echo ""

case $REPLY in
    1)
        # 전체 설치 항목 용량 확인
        echo "=========================================="
        echo "PHASE5_SETUP.md 설치 항목 전체 용량 확인"
        echo "=========================================="
        echo ""
        
        TOTAL_SIZE_BYTES=0
        
        echo "1️⃣  전체 디스크 사용량"
        echo "----------------------------------------"
        df -h / | tail -1
        echo ""
        
        echo "2️⃣  LLM 모델"
        echo "----------------------------------------"
        
        GEMMA_DIR="/mnt/shared_models/llm/gemma-3-27b-it"
        if [ -d "$GEMMA_DIR" ]; then
            SIZE=$(du -sh "$GEMMA_DIR" 2>/dev/null | awk '{print $1}')
            SIZE_BYTES=$(du -sb "$GEMMA_DIR" 2>/dev/null | awk '{print $1}')
            TOTAL_SIZE_BYTES=$((TOTAL_SIZE_BYTES + SIZE_BYTES))
            echo "✅ Gemma 3 27B IT (4-bit 양자화)"
            echo "   위치: $GEMMA_DIR"
            echo "   크기: $SIZE"
        else
            echo "❌ Gemma 3 27B IT: 설치되지 않음"
        fi
        echo ""
        
        
        echo "3️⃣  TTS 모델 (GPT-SoVITS)"
        echo "----------------------------------------"
        
        REPO_DIR="/opt/GPT-SoVITS"
        CONDA_ENV="GPTSoVits"
        CONDA_BASE=$(conda info --base 2>/dev/null || echo "$HOME/miniconda3")
        CONDA_ENV_DIR="$CONDA_BASE/envs/$CONDA_ENV"
        
        if [ -d "$REPO_DIR" ]; then
            SIZE=$(du -sh "$REPO_DIR" 2>/dev/null | awk '{print $1}')
            SIZE_BYTES=$(du -sb "$REPO_DIR" 2>/dev/null | awk '{print $1}')
            TOTAL_SIZE_BYTES=$((TOTAL_SIZE_BYTES + SIZE_BYTES))
            echo "✅ 소스 코드"
            echo "   위치: $REPO_DIR"
            echo "   크기: $SIZE"
        else
            echo "❌ 소스 코드: 설치되지 않음"
        fi
        
        if [ -d "$CONDA_ENV_DIR" ]; then
            SIZE=$(du -sh "$CONDA_ENV_DIR" 2>/dev/null | awk '{print $1}')
            SIZE_BYTES=$(du -sb "$CONDA_ENV_DIR" 2>/dev/null | awk '{print $1}')
            TOTAL_SIZE_BYTES=$((TOTAL_SIZE_BYTES + SIZE_BYTES))
            echo "✅ Conda 환경"
            echo "   위치: $CONDA_ENV_DIR"
            echo "   크기: $SIZE"
        else
            echo "❌ Conda 환경: 설치되지 않음"
        fi
        echo ""
        
        echo "4️⃣  Docker 이미지"
        echo "----------------------------------------"
        docker system df 2>/dev/null | head -5 || echo "   Docker가 실행되지 않았습니다"
        echo ""
        
        echo "5️⃣  캐시 파일"
        echo "----------------------------------------"
        PIP_CACHE_DIR="$HOME/.cache/pip"
        if [ -d "$PIP_CACHE_DIR" ]; then
            PIP_SIZE=$(du -sh "$PIP_CACHE_DIR" 2>/dev/null | awk '{print $1}')
            echo "📦 pip 캐시: $PIP_SIZE"
        fi
        
        HF_CACHE_DIR="$HOME/.cache/huggingface"
        if [ -d "$HF_CACHE_DIR" ]; then
            HF_SIZE=$(du -sh "$HF_CACHE_DIR" 2>/dev/null | awk '{print $1}')
            echo "📦 Hugging Face 캐시: $HF_SIZE"
        fi
        
        if [ -d "$CONDA_BASE/pkgs" ]; then
            CONDA_CACHE_SIZE=$(du -sh "$CONDA_BASE/pkgs" 2>/dev/null | awk '{print $1}')
            echo "📦 Conda 패키지 캐시: $CONDA_CACHE_SIZE"
        fi
        echo ""
        
        echo "=========================================="
        echo "📊 총 사용량 요약"
        echo "=========================================="
        if [ "$TOTAL_SIZE_BYTES" -gt 0 ]; then
            TOTAL_GB=$(python3 -c "print(f'{$TOTAL_SIZE_BYTES/1024/1024/1024:.2f}')" 2>/dev/null || awk "BEGIN {printf \"%.2f\", $TOTAL_SIZE_BYTES/1024/1024/1024}")
            echo "✅ 실제 설치된 크기: ~${TOTAL_GB}GB"
        fi
        echo ""
        echo "💾 디스크 여유 공간:"
        df -h / | tail -1
        echo ""
        ;;
    2)
        # GPT-SoVITS 디스크 사용량
        echo "=========================================="
        echo "GPT-SoVITS 디스크 사용량 확인"
        echo "=========================================="
        echo ""
        
        REPO_DIR="/opt/GPT-SoVITS"
        CONDA_ENV="GPTSoVits"
        CONDA_BASE=$(conda info --base 2>/dev/null || echo "$HOME/miniconda3")
        CONDA_ENV_DIR="$CONDA_BASE/envs/$CONDA_ENV"
        
        echo "1️⃣  전체 디스크 사용량"
        echo "----------------------------------------"
        df -h / | tail -1
        echo ""
        
        echo "2️⃣  GPT-SoVITS 관련 디렉터리"
        echo "----------------------------------------"
        
        if [ -d "$REPO_DIR" ]; then
            SIZE=$(du -sh "$REPO_DIR" 2>/dev/null | awk '{print $1}')
            echo "📁 소스 코드: $REPO_DIR"
            echo "   크기: $SIZE"
        else
            echo "⚠️  소스 코드 디렉터리가 없습니다"
        fi
        echo ""
        
        if [ -d "$CONDA_ENV_DIR" ]; then
            SIZE=$(du -sh "$CONDA_ENV_DIR" 2>/dev/null | awk '{print $1}')
            echo "🐍 Conda 환경: $CONDA_ENV_DIR"
            echo "   크기: $SIZE"
        else
            echo "⚠️  Conda 환경 디렉터리가 없습니다"
        fi
        echo ""
        
        echo "3️⃣  캐시 파일"
        echo "----------------------------------------"
        
        if [ -d "$REPO_DIR" ]; then
            PYCACHE_COUNT=$(find "$REPO_DIR" -type d -name "__pycache__" 2>/dev/null | wc -l)
            if [ "$PYCACHE_COUNT" -gt 0 ]; then
                echo "📦 Python 캐시 (__pycache__): $PYCACHE_COUNT개"
            fi
        fi
        
        PIP_CACHE_DIR="$HOME/.cache/pip"
        if [ -d "$PIP_CACHE_DIR" ]; then
            PIP_SIZE=$(du -sh "$PIP_CACHE_DIR" 2>/dev/null | awk '{print $1}')
            echo "📦 pip 캐시: $PIP_SIZE"
        fi
        
        HF_CACHE_DIR="$HOME/.cache/huggingface"
        if [ -d "$HF_CACHE_DIR" ]; then
            HF_SIZE=$(du -sh "$HF_CACHE_DIR" 2>/dev/null | awk '{print $1}')
            echo "📦 Hugging Face 캐시: $HF_SIZE"
        fi
        
        if [ -d "$CONDA_BASE/pkgs" ]; then
            CONDA_CACHE_SIZE=$(du -sh "$CONDA_BASE/pkgs" 2>/dev/null | awk '{print $1}')
            echo "📦 Conda 패키지 캐시: $CONDA_CACHE_SIZE"
        fi
        echo ""
        ;;
    3)
        # 로그 확인
        echo "=========================================="
        echo "GPT-SoVITS 서비스 로그 확인"
        echo "=========================================="
        echo ""
        
        echo "서비스 상태:"
        sudo systemctl status gpt-sovits --no-pager -l | head -15
        echo ""
        
        echo "로그 확인 방법:"
        echo "1️⃣  실시간 로그: sudo journalctl -u gpt-sovits -f"
        echo "2️⃣  최근 50줄: sudo journalctl -u gpt-sovits -n 50"
        echo "3️⃣  오늘 로그: sudo journalctl -u gpt-sovits --since today"
        echo "4️⃣  에러만: sudo journalctl -u gpt-sovits -p err"
        echo ""
        
        read -p "실시간 로그를 보시겠습니까? (Y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            echo ""
            echo "실시간 로그 시작 (Ctrl+C로 종료)..."
            echo "=========================================="
            sudo journalctl -u gpt-sovits -f
        else
            echo ""
            echo "최근 50줄 로그:"
            echo "=========================================="
            sudo journalctl -u gpt-sovits -n 50 --no-pager
        fi
        ;;
    4)
        # 포트 확인
        echo "=========================================="
        echo "GPT-SoVITS 포트 확인"
        echo "=========================================="
        echo ""
        echo "⚠️  GPT-SoVITS 포트 구분:"
        echo "   - 포트 9872: TTS API (텍스트-음성 변환)"
        echo "   - 포트 9873: 반주 분리 (UVR5)"
        echo "   - 포트 9874: WebUI (관리 인터페이스)"
        echo ""
        echo "포트 상태:"
        sudo ss -tlnp | grep -E "987[234]" || echo "   포트가 리스닝하지 않습니다"
        echo ""
        echo "서비스 상태:"
        sudo systemctl status gpt-sovits --no-pager -l | head -10
        ;;
    5)
        # 모델 검증
        echo "=========================================="
        echo "모델 파일 검증"
        echo "=========================================="
        echo ""
        
        echo "Gemma 3 27B IT:"
        if [ -d "/mnt/shared_models/llm/gemma-3-27b-it" ]; then
            du -sh /mnt/shared_models/llm/gemma-3-27b-it/
            ls -lh /mnt/shared_models/llm/gemma-3-27b-it/ | head -5
        else
            echo "❌ 디렉터리가 존재하지 않습니다"
        fi
        echo ""
        
        
        echo "GPT-SoVITS:"
        if [ -d "/opt/GPT-SoVITS" ]; then
            echo "✅ 소스 코드 디렉터리: /opt/GPT-SoVITS"
            du -sh /opt/GPT-SoVITS
            echo "   Conda 환경:"
            conda env list | grep GPTSoVits || echo "   ⚠️  Conda 환경이 아직 생성되지 않았습니다"
            echo "   systemd 서비스:"
            systemctl is-active gpt-sovits 2>/dev/null && echo "   ✅ 서비스 실행 중" || echo "   ⚠️  서비스가 실행되지 않았습니다"
        else
            echo "❌ 디렉터리가 존재하지 않습니다"
        fi
        echo ""
        ;;
    6)
        # NPM 연결 테스트
        echo "=========================================="
        echo "NPM ↔ 호스트 Conda 서비스 연결 테스트"
        echo "=========================================="
        echo ""
        
        echo "1️⃣  NPM 컨테이너 상태 확인"
        echo "----------------------------------------"
        if docker ps | grep -q " npm$"; then
            echo "✅ NPM 컨테이너가 실행 중입니다"
            docker ps | grep npm
        else
            echo "❌ NPM 컨테이너가 실행되지 않았습니다"
            exit 1
        fi
        echo ""
        
        echo "2️⃣  호스트 서비스 포트 확인 (9872/9873/9874)"
        echo "----------------------------------------"
        echo "⚠️  GPT-SoVITS 포트 구분:"
        echo "   - 포트 9872: TTS API (텍스트-음성 변환)"
        echo "   - 포트 9873: 반주 분리 (UVR5)"
        echo "   - 포트 9874: WebUI (관리 인터페이스)"
        echo ""
        
        PORTS_OK=true
        for PORT in 9872 9873 9874; do
            if sudo ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
                echo "✅ 포트 $PORT가 열려있습니다"
                sudo ss -tlnp | grep ":$PORT "
            else
                echo "❌ 포트 $PORT가 열려있지 않습니다"
                PORTS_OK=false
            fi
            echo ""
        done
        
        if [ "$PORTS_OK" = false ]; then
            echo "⚠️  일부 포트가 열려있지 않습니다"
            echo "   서비스 시작: sudo systemctl start gpt-sovits"
        fi
        echo ""
        
        echo "3️⃣  호스트에서 직접 접근 테스트"
        echo "----------------------------------------"
        for PORT in 9872 9873 9874; do
            if curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT | grep -q "200\|301\|302"; then
                RESPONSE_SIZE=$(curl -s http://localhost:$PORT | wc -c)
                echo "   ✅ localhost:$PORT 접근 가능 (응답: ${RESPONSE_SIZE} bytes)"
            else
                echo "   ❌ localhost:$PORT 접근 불가"
            fi
        done
        echo ""
        
        echo "4️⃣  host.docker.internal 확인"
        echo "----------------------------------------"
        if docker exec npm getent hosts host.docker.internal > /dev/null 2>&1; then
            HOST_IP=$(docker exec npm getent hosts host.docker.internal | awk '{print $1}')
            echo "✅ host.docker.internal 확인됨: $HOST_IP"
        else
            echo "❌ host.docker.internal을 찾을 수 없습니다"
            echo "   NPM 컨테이너에 extra_hosts 설정이 필요합니다"
            exit 1
        fi
        echo ""
        
        echo "5️⃣  NPM 컨테이너에서 호스트 접근 테스트"
        echo "----------------------------------------"
        echo "⚠️  중요: NPM 프록시는 포트 9872 (TTS API)를 사용해야 합니다"
        echo ""
        
        TEST1_SUCCESS=false
        TEST2_SUCCESS=false
        
        if docker exec npm curl -s -o /dev/null -w "%{http_code}" http://host.docker.internal:9872 2>/dev/null | grep -q "200\|301\|302"; then
            RESPONSE_SIZE=$(docker exec npm curl -s http://host.docker.internal:9872 2>/dev/null | wc -c)
            echo "   ✅ host.docker.internal:9872 접근 가능 (응답: ${RESPONSE_SIZE} bytes)"
            TEST1_SUCCESS=true
        else
            echo "   ❌ host.docker.internal:9872 접근 불가"
        fi
        
        if docker exec npm curl -s -o /dev/null -w "%{http_code}" http://172.17.0.1:9872 2>/dev/null | grep -q "200\|301\|302"; then
            RESPONSE_SIZE=$(docker exec npm curl -s http://172.17.0.1:9872 2>/dev/null | wc -c)
            echo "   ✅ 172.17.0.1:9872 접근 가능 (응답: ${RESPONSE_SIZE} bytes)"
            TEST2_SUCCESS=true
        else
            echo "   ❌ 172.17.0.1:9872 접근 불가"
        fi
        echo ""
        
        echo "=========================================="
        echo "📊 테스트 결과 요약"
        echo "=========================================="
        echo ""
        
        if [ "$TEST1_SUCCESS" = true ]; then
            echo "✅ 권장: NPM 설정에서 'host.docker.internal:9872' 사용 (TTS API)"
            echo "   - Forward Hostname/IP: host.docker.internal"
            echo "   - Forward Port: 9872 (⚠️ 중요: TTS API 포트)"
            echo "   - Scheme: http"
        elif [ "$TEST2_SUCCESS" = true ]; then
            echo "✅ 대안: NPM 설정에서 '172.17.0.1:9872' 사용 (TTS API)"
            echo "   - Forward Hostname/IP: 172.17.0.1"
            echo "   - Forward Port: 9872 (⚠️ 중요: TTS API 포트)"
            echo "   - Scheme: http"
        else
            echo "❌ 두 방법 모두 실패했습니다"
            echo "   해결: bash scripts/server-a/setup-services.sh (옵션 1)"
        fi
        echo ""
        ;;
    *)
        echo "취소됨"
        exit 0
        ;;
esac
