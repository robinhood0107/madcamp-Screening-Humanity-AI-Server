#!/bin/bash
# Server A - NVIDIA Container Toolkit 설치 스크립트

set -e  # 오류 발생 시 스크립트 중단

echo "=========================================="
echo "NVIDIA Container Toolkit 설치 시작"
echo "=========================================="

# 1. 패키지 저장소 및 GPG 키 설정
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 2. 패키지 목록 업데이트
sudo apt-get update

# 3. NVIDIA Container Toolkit 설치
sudo apt-get install -y nvidia-container-toolkit

# 4. Docker 런타임 설정
sudo nvidia-ctk runtime configure --runtime=docker

# 5. Docker 데몬 재시작
sudo systemctl restart docker

# 6. 설치 확인
echo "=========================================="
echo "GPU 컨테이너 테스트"
echo "=========================================="
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

echo "=========================================="
echo "✅ NVIDIA Container Toolkit 설치 완료"
echo "=========================================="
