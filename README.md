# Avatar Forge - Screening Humanity AI Server

Avatar Forge 프로젝트의 AI 서버 구현

## 📚 문서

- [최종 통합 명세서 (FINALFINAL.md)](docs/FINALFINAL.md) - 전체 프로젝트 명세
- [Phase 5 설정 가이드](docs/PHASE5_SETUP.md) - NVIDIA Container Toolkit 설치 및 모델 파일 준비

## 🚀 Phase 5 빠른 시작

### Server A (GPU 서버) - NVIDIA Container Toolkit 설치

```bash
# 스크립트에 실행 권한 부여
chmod +x scripts/server-a/install-nvidia-container-toolkit.sh

# 실행
sudo ./scripts/server-a/install-nvidia-container-toolkit.sh
```

### Server B (CPU 서버) - 모델 파일 준비

```bash
# 1. 스토리지 디렉터리 설정
chmod +x scripts/server-b/setup-model-storage.sh
sudo ./scripts/server-b/setup-model-storage.sh

# 2. LLM 모델 다운로드
chmod +x scripts/server-b/download-llm-models.sh
./scripts/server-b/download-llm-models.sh

# 3. 모델 파일 검증
chmod +x scripts/server-b/verify-models.sh
./scripts/server-b/verify-models.sh
```

## 📁 프로젝트 구조

```
.
├── docs/                    # 문서
│   ├── FINALFINAL.md       # 최종 통합 명세서
│   └── PHASE5_SETUP.md     # Phase 5 설정 가이드
├── scripts/                 # 설치/설정 스크립트
│   ├── server-a/           # GPU 서버 스크립트
│   └── server-b/           # CPU 서버 스크립트
└── README.md
```

## 📝 상세 가이드

자세한 설정 방법은 [Phase 5 설정 가이드](docs/PHASE5_SETUP.md)를 참조하세요.
