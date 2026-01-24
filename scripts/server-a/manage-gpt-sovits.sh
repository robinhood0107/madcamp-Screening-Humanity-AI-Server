#!/bin/bash
# Server A - GPT-SoVITS 통합 관리 스크립트 (설치, 재설치, 삭제, 서비스 관리, 의존성 재설치)

set -e

INSTALL_DIR="/opt"
REPO_DIR="$INSTALL_DIR/GPT-SoVITS"
CONDA_ENV="GPTSoVits"
SERVICE_FILE="/etc/systemd/system/gpt-sovits.service"
CONDA_BASE=$(conda info --base 2>/dev/null || echo "$HOME/miniconda3")
CONDA_ENV_DIR="$CONDA_BASE/envs/$CONDA_ENV"

echo "=========================================="
echo "GPT-SoVITS 통합 관리"
echo "=========================================="
echo ""
echo "1. 설치 (처음 설치)"
echo "2. 재설치 (완전 삭제 후 재설치)"
echo "3. 삭제 (완전 제거)"
echo "4. 서비스 관리 (시작/중지/재시작/상태)"
echo "5. systemd 서비스 생성 (서비스만 생성)"
echo "6. 의존성 재설치"
echo "7. 취소"
echo ""
read -p "선택 (1-7): " -n 1 -r
echo
echo ""

case $REPLY in
    1)
        # 설치
        echo "=========================================="
        echo "GPT-SoVITS 설치"
        echo "=========================================="
        
        # Conda 설치 확인
        if ! command -v conda &> /dev/null; then
            echo "❌ Conda가 설치되어 있지 않습니다"
            exit 1
        fi
        
        # 기존 디렉터리 확인
        if [ -d "$REPO_DIR" ]; then
            echo "⚠️  기존 디렉터리 발견: $REPO_DIR"
            read -p "   덮어쓰시겠습니까? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                sudo rm -rf "$REPO_DIR"
            fi
        fi
        
        # Conda 환경 생성
        source "$(conda info --base)/etc/profile.d/conda.sh" 2>/dev/null || true
        
        if conda env list | grep -q "^$CONDA_ENV "; then
            echo "⚠️  Conda 환경 '$CONDA_ENV'이 이미 존재합니다"
            read -p "   재생성하시겠습니까? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                conda activate base 2>/dev/null || true
                conda env remove -n "$CONDA_ENV" -y
            fi
        fi
        
        if ! conda env list | grep -q "^$CONDA_ENV "; then
            echo "Conda 환경 생성 중..."
            conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main 2>/dev/null || true
            conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r 2>/dev/null || true
            conda config --add channels conda-forge 2>/dev/null || true
            conda config --set channel_priority strict 2>/dev/null || true
            conda create -n "$CONDA_ENV" python=3.9 -y
        fi
        
        # 저장소 클론
        echo "저장소 클론 중..."
        cd "$INSTALL_DIR"
        git clone https://github.com/RVC-Boss/GPT-SoVITS.git GPT-SoVITS
        cd "$REPO_DIR"
        
        # 의존성 설치
        echo "의존성 설치 중..."
        conda activate "$CONDA_ENV"
        
        # ⚠️ 매우 중요: Python, PyTorch, torchcodec 버전 호환성
        echo ""
        echo "=========================================="
        echo "⚠️  매우 중요: PyTorch 버전 선택"
        echo "=========================================="
        echo ""
        echo "GPT-SoVITS는 Python, PyTorch, torchcodec 버전이 반드시 호환되어야 합니다!"
        echo "잘못된 버전 조합은 ImportError, 런타임 오류 등을 발생시킬 수 있습니다."
        echo ""
        echo "공식 문서를 반드시 참고하세요:"
        echo "  - https://github.com/RVC-Boss/GPT-SoVITS"
        echo "  - https://github.com/RVC-Boss/GPT-SoVITS/blob/main/docs/ko/README.md"
        echo ""
        
        # CUDA 버전 확인
        CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}' | cut -d. -f1,2 || echo "12.8")
        echo "감지된 CUDA 버전: $CUDA_VERSION"
        echo ""
        echo "PyTorch 버전 선택:"
        echo "  1. CUDA 12.6/12.7 (--device CU126)"
        echo "  2. CUDA 12.8/13.0/13.1 (--device CU128, 권장)"
        echo "  3. CPU (--device CPU, 권장하지 않음)"
        echo ""
        read -p "선택 (1-3, 기본값: 2): " -n 1 -r
        echo
        CHOICE=${REPLY:-2}
        
        case $CHOICE in
            1) DEVICE="CU126" ;;
            2) DEVICE="CU128" ;;
            3) DEVICE="CPU" ;;
            *) DEVICE="CU128" ;;
        esac
        
        echo ""
        echo "선택된 디바이스: $DEVICE"
        echo "⚠️  이 선택에 따라 PyTorch 버전이 자동으로 결정됩니다"
        echo "   Python 3.9와 호환되는 PyTorch 버전이 설치됩니다"
        echo ""
        read -p "계속하시겠습니까? (Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            echo "취소됨"
            exit 0
        fi
        
        echo ""
        echo "의존성 설치 중 (시간이 걸릴 수 있습니다)..."
        bash install.sh --device "$DEVICE" --source HF
        
        # 설치 후 버전 확인
        echo ""
        echo "=========================================="
        echo "설치된 버전 확인"
        echo "=========================================="
        python -c "import sys; print(f'Python: {sys.version}')" 2>/dev/null || echo "Python: 확인 불가"
        python -c "import torch; print(f'PyTorch: {torch.__version__}')" 2>/dev/null || echo "PyTorch: 확인 불가"
        python -c "import torchcodec; print(f'torchcodec: 설치됨')" 2>/dev/null || echo "torchcodec: 확인 불가 (설치 후 확인 필요)"
        echo ""
        
        # systemd 서비스 생성
        echo "systemd 서비스 생성 중..."
        CONDA_PYTHON="$CONDA_BASE/envs/$CONDA_ENV/bin/python"
        sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=GPT-SoVITS TTS Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$REPO_DIR
Environment="PATH=$CONDA_BASE/envs/$CONDA_ENV/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$CONDA_PYTHON webui.py ko-KR
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        sudo systemctl enable gpt-sovits
        
        read -p "   지금 서비스를 시작하시겠습니까? (Y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            sudo systemctl start gpt-sovits
        fi
        
        echo "✅ 설치 완료"
        ;;
    2)
        # 재설치
        echo "=========================================="
        echo "GPT-SoVITS 재설치 (삭제 후 재설치)"
        echo "=========================================="
        read -p "정말로 재설치하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
        
        # 삭제
        if systemctl is-active --quiet gpt-sovits 2>/dev/null; then
            sudo systemctl stop gpt-sovits
        fi
        if systemctl is-enabled --quiet gpt-sovits 2>/dev/null; then
            sudo systemctl disable gpt-sovits
        fi
        if [ -f "$SERVICE_FILE" ]; then
            sudo rm -f "$SERVICE_FILE"
            sudo systemctl daemon-reload
        fi
        
        source "$CONDA_BASE/etc/profile.d/conda.sh" 2>/dev/null || true
        CURRENT_ENV=$(conda info --envs 2>/dev/null | grep '*' | awk '{print $1}' | sed 's/*//' | xargs || echo "")
        if [ "$CURRENT_ENV" = "$CONDA_ENV" ]; then
            conda deactivate 2>/dev/null || true
            conda activate base 2>/dev/null || true
        fi
        if conda env list | grep -q "^$CONDA_ENV "; then
            conda env remove -n "$CONDA_ENV" -y
        fi
        
        if [ -d "$REPO_DIR" ]; then
            sudo rm -rf "$REPO_DIR"
        fi
        
        # 재설치 (옵션 1 실행)
        echo "재설치 중..."
        bash "$0" <<< "1"
        ;;
    3)
        # 삭제
        echo "=========================================="
        echo "GPT-SoVITS 삭제"
        echo "=========================================="
        read -p "정말로 삭제하시겠습니까? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
        
        if systemctl is-active --quiet gpt-sovits 2>/dev/null; then
            sudo systemctl stop gpt-sovits
        fi
        if systemctl is-enabled --quiet gpt-sovits 2>/dev/null; then
            sudo systemctl disable gpt-sovits
        fi
        if [ -f "$SERVICE_FILE" ]; then
            sudo rm -f "$SERVICE_FILE"
            sudo systemctl daemon-reload
        fi
        
        source "$CONDA_BASE/etc/profile.d/conda.sh" 2>/dev/null || true
        CURRENT_ENV=$(conda info --envs 2>/dev/null | grep '*' | awk '{print $1}' | sed 's/*//' | xargs || echo "")
        if [ "$CURRENT_ENV" = "$CONDA_ENV" ]; then
            conda deactivate 2>/dev/null || true
            conda activate base 2>/dev/null || true
        fi
        if conda env list | grep -q "^$CONDA_ENV "; then
            conda env remove -n "$CONDA_ENV" -y
        fi
        
        if [ -d "$REPO_DIR" ]; then
            sudo rm -rf "$REPO_DIR"
        fi
        
        echo "✅ 삭제 완료"
        ;;
    4)
        # 서비스 관리
        echo "=========================================="
        echo "GPT-SoVITS 서비스 관리"
        echo "=========================================="
        echo "1. 시작"
        echo "2. 중지"
        echo "3. 재시작"
        echo "4. 상태 확인"
        echo "5. 취소"
        read -p "선택 (1-5): " -n 1 -r
        echo
        case $REPLY in
            1) sudo systemctl start gpt-sovits ;;
            2) sudo systemctl stop gpt-sovits ;;
            3) sudo systemctl restart gpt-sovits ;;
            4) sudo systemctl status gpt-sovits ;;
        esac
        ;;
    5)
        # systemd 서비스 생성
        echo "=========================================="
        echo "systemd 서비스 생성"
        echo "=========================================="
        CONDA_PYTHON="$CONDA_BASE/envs/$CONDA_ENV/bin/python"
        if [ ! -f "$CONDA_PYTHON" ]; then
            echo "❌ Conda 환경을 찾을 수 없습니다"
            exit 1
        fi
        sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=GPT-SoVITS TTS Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$REPO_DIR
Environment="PATH=$CONDA_BASE/envs/$CONDA_ENV/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$CONDA_PYTHON webui.py ko-KR
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
        sudo systemctl daemon-reload
        sudo systemctl enable gpt-sovits
        read -p "   지금 서비스를 시작하시겠습니까? (Y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            sudo systemctl start gpt-sovits
        fi
        echo "✅ 서비스 생성 완료"
        ;;
    6)
        # 의존성 재설치
        echo "=========================================="
        echo "의존성 재설치"
        echo "=========================================="
        if [ ! -d "$REPO_DIR" ]; then
            echo "❌ 소스 코드 디렉터리가 없습니다"
            exit 1
        fi
        source "$CONDA_BASE/etc/profile.d/conda.sh"
        conda activate "$CONDA_ENV"
        cd "$REPO_DIR"
        
        # ⚠️ 버전 호환성 경고
        echo ""
        echo "⚠️  매우 중요: Python, PyTorch, torchcodec 버전 호환성"
        echo "   의존성 재설치 시 기존 PyTorch 버전이 유지됩니다"
        echo "   버전 호환성 문제가 있다면 완전 재설치(옵션 2)를 권장합니다"
        echo "   공식 문서 참고: https://github.com/RVC-Boss/GPT-SoVITS"
        echo ""
        
        echo "1. requirements.txt만"
        echo "2. extra-req.txt + requirements.txt (권장)"
        echo "3. pip 캐시 정리 후 재설치"
        echo "4. 전체 재설치 (pip 업그레이드 포함)"
        read -p "선택 (1-4): " -n 1 -r
        echo
        case $REPLY in
            1) pip install --upgrade --force-reinstall -r requirements.txt ;;
            2) pip install --upgrade --force-reinstall -r extra-req.txt --no-deps && pip install --upgrade --force-reinstall -r requirements.txt ;;
            3) pip cache purge && pip install --upgrade --force-reinstall -r extra-req.txt --no-deps && pip install --upgrade --force-reinstall -r requirements.txt ;;
            4) pip install --upgrade pip setuptools wheel && pip cache purge && pip install --upgrade --force-reinstall -r extra-req.txt --no-deps && pip install --upgrade --force-reinstall -r requirements.txt ;;
        esac
        
        # 재설치 후 버전 확인
        echo ""
        echo "설치된 버전 확인:"
        python -c "import sys; print(f'Python: {sys.version}')" 2>/dev/null || echo "Python: 확인 불가"
        python -c "import torch; print(f'PyTorch: {torch.__version__}')" 2>/dev/null || echo "PyTorch: 확인 불가"
        python -c "import torchcodec; print(f'torchcodec: 설치됨')" 2>/dev/null || echo "torchcodec: 확인 불가"
        echo ""
        echo "✅ 의존성 재설치 완료"
        ;;
    *)
        echo "취소됨"
        exit 0
        ;;
esac
