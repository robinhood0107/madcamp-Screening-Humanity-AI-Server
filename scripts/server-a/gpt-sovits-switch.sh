#!/bin/bash
# Server A - GPT-SoVITS 서비스 전환 스크립트 (api_v2.py ↔ webui.py)

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 서비스 이름
API_SERVICE="gpt-sovits-api"
WEBUI_SERVICE="gpt-sovits"

# 상태 표시 함수
show_status() {
    echo ""
    echo -e "${BLUE}=========================================="
    echo "GPT-SoVITS 서비스 상태"
    echo -e "==========================================${NC}"
    
    # API 서비스 상태
    if systemctl is-active --quiet $API_SERVICE 2>/dev/null; then
        echo -e "${GREEN}✅ api_v2.py (포트 9880): 실행 중${NC}"
        sudo systemctl status $API_SERVICE --no-pager -l | grep -E "Active|Main PID" | head -2
    else
        echo -e "${RED}❌ api_v2.py (포트 9880): 중지됨${NC}"
    fi
    
    echo ""
    
    # WebUI 서비스 상태
    if systemctl is-active --quiet $WEBUI_SERVICE 2>/dev/null; then
        echo -e "${GREEN}✅ webui.py (포트 9872/9874): 실행 중${NC}"
        sudo systemctl status $WEBUI_SERVICE --no-pager -l | grep -E "Active|Main PID" | head -2
    else
        echo -e "${RED}❌ webui.py (포트 9872/9874): 중지됨${NC}"
    fi
    
    # 포트 확인
    echo ""
    echo -e "${BLUE}=========================================="
    echo "포트 상태"
    echo -e "==========================================${NC}"
    PORTS=$(sudo ss -tlnp 2>/dev/null | grep -E "987[234]|9880" || echo "")
    if [ -z "$PORTS" ]; then
        echo -e "${RED}❌ GPT-SoVITS 포트가 열려있지 않습니다${NC}"
    else
        echo "$PORTS" | awk '{print "  포트 " $4}'
    fi
    echo ""
}

# API 모드로 전환
switch_to_api() {
    echo ""
    echo -e "${YELLOW}=========================================="
    echo "API 모드로 전환 중..."
    echo -e "==========================================${NC}"
    
    # WebUI 중지
    if systemctl is-active --quiet $WEBUI_SERVICE 2>/dev/null; then
        echo -e "${YELLOW}⏹️  webui.py 중지 중...${NC}"
        sudo systemctl stop $WEBUI_SERVICE
        sleep 2
        echo -e "${GREEN}✅ webui.py 중지 완료${NC}"
    else
        echo -e "${BLUE}ℹ️  webui.py는 이미 중지되어 있습니다${NC}"
    fi
    
    # API 시작
    echo -e "${YELLOW}▶️  api_v2.py 시작 중...${NC}"
    sudo systemctl start $API_SERVICE
    sleep 3
    
    # 상태 확인
    if systemctl is-active --quiet $API_SERVICE; then
        echo -e "${GREEN}✅ API 모드 전환 완료!${NC}"
        echo -e "${BLUE}   포트 9880에서 API 서비스가 실행 중입니다${NC}"
    else
        echo -e "${RED}❌ API 시작 실패${NC}"
        echo -e "${YELLOW}로그 확인: sudo journalctl -u $API_SERVICE -n 50${NC}"
        exit 1
    fi
    
    show_status
}

# WebUI 모드로 전환
switch_to_webui() {
    echo ""
    echo -e "${YELLOW}=========================================="
    echo "WebUI 모드로 전환 중..."
    echo -e "==========================================${NC}"
    
    # API 중지
    if systemctl is-active --quiet $API_SERVICE 2>/dev/null; then
        echo -e "${YELLOW}⏹️  api_v2.py 중지 중...${NC}"
        sudo systemctl stop $API_SERVICE
        sleep 2
        echo -e "${GREEN}✅ api_v2.py 중지 완료${NC}"
    else
        echo -e "${BLUE}ℹ️  api_v2.py는 이미 중지되어 있습니다${NC}"
    fi
    
    # WebUI 시작
    echo -e "${YELLOW}▶️  webui.py 시작 중...${NC}"
    sudo systemctl start $WEBUI_SERVICE
    sleep 3
    
    # 상태 확인
    if systemctl is-active --quiet $WEBUI_SERVICE; then
        echo -e "${GREEN}✅ WebUI 모드 전환 완료!${NC}"
        echo -e "${BLUE}   포트 9872 (TTS API), 9874 (WebUI)에서 서비스가 실행 중입니다${NC}"
    else
        echo -e "${RED}❌ WebUI 시작 실패${NC}"
        echo -e "${YELLOW}로그 확인: sudo journalctl -u $WEBUI_SERVICE -n 50${NC}"
        exit 1
    fi
    
    show_status
}

# 모든 서비스 중지
stop_all() {
    echo ""
    echo -e "${YELLOW}=========================================="
    echo "모든 GPT-SoVITS 서비스 중지 중..."
    echo -e "==========================================${NC}"
    
    if systemctl is-active --quiet $API_SERVICE 2>/dev/null; then
        echo -e "${YELLOW}⏹️  api_v2.py 중지 중...${NC}"
        sudo systemctl stop $API_SERVICE
    fi
    
    if systemctl is-active --quiet $WEBUI_SERVICE 2>/dev/null; then
        echo -e "${YELLOW}⏹️  webui.py 중지 중...${NC}"
        sudo systemctl stop $WEBUI_SERVICE
    fi
    
    sleep 2
    echo -e "${GREEN}✅ 모든 서비스 중지 완료${NC}"
    
    show_status
}

# 사용법 표시
show_usage() {
    echo ""
    echo -e "${BLUE}=========================================="
    echo "GPT-SoVITS 서비스 전환 스크립트"
    echo -e "==========================================${NC}"
    echo ""
    echo "사용법: $0 {api|webui|status|stop}"
    echo ""
    echo "명령어:"
    echo "  api     - api_v2.py (포트 9880) 실행, webui.py 중지"
    echo "  webui   - webui.py (포트 9872/9874) 실행, api_v2.py 중지"
    echo "  status  - 현재 서비스 상태 확인"
    echo "  stop    - 모든 GPT-SoVITS 서비스 중지"
    echo ""
    show_status
}

# 메인 로직
case "$1" in
    api)
        switch_to_api
        ;;
    webui)
        switch_to_webui
        ;;
    status)
        show_status
        ;;
    stop)
        stop_all
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
