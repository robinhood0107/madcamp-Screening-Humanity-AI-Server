# Avatar Forge - Screening Humanity AI Server

Avatar Forge 프로젝트의 AI 서버 구현

## 3090 24GB의 경우 gemma 3 27b 4bit 양자화를 최대토큰 4096으로 해야지 그나마 사용할만하게 돌아갔음
### (근데 너무 상담사같은 모델이라서 롤플레잉에는 부적합한듯, 프롬프팅도 너무 안되서 컨텍스트 윈도우 조절이나 주기적인 summary(요약)등등 망각에 대비한 여러 조치를 취해야 했음)

- vllm의 경우 2026년 1월 기준으로는 gguf에 대한 지원은 그리 많지 않다(쓰기 어렵고 옵션 넣을 것도 많고 도커컴포즈도 잘 안됬다),하지만 기능이 매우 강력하다(도커 이미지 30~38기가 한듯하다)
- ollama의 경우 도커 이미지도 가볍고 세팅도 외부 모델을 modelfile로 copy해서 컨테이너에 넣는 방식이라 일단 구축하기도 편했음, 근데 vllm보단 동시접속 및 대규모 서비스에는 어울리지는 않는 것 같음. 하지만 gguf 및 세팅이 쉽단 장점!(도커 이미지 10기가 정도 한듯하다)
- lamma.cpp는 api기능이 없기 때문에 논외, 하지만 순수c/c++이라 속도 빠르고 순수 채팅 목적의 web ui로는 좋다고 한다

- 26년 1월 28일이랑 29일에 얼마전 새로 나온 GLM-4.7-flash의 양자화 버전인 gguf도 사용해보았는데 31B라서 그런지 이정도 로컬 모델을 3090으로 돌리려니 컨텍스트랑 VRAM이 감당이 안되었다. 대화 한번 /api/chat이랑 /api/generate로 주고 받았는데 진짜 느리게 2분정도 뒤에 답변을 주더라...

- Gemini api에는 꽤 다양한 옵션이 있다. 스트리밍도 지원해서 이 기능 사용하면 실제로 글써주듯이 한글자씩 완성되는 글자를(마치 gemini 홈페이지에서 쓰듯) 구현해서 사용자의 기다림과 UX, 사용성에 대한 한계를 늘려줄 수 있다는 점을 알았다

## 📚 문서

- [최종 통합 명세서 (FINALFINAL.md)](docs/FINALFINAL.md) - 전체 프로젝트 명세
- [Phase 5 설정 가이드](docs/PHASE5_SETUP.md) - NVIDIA Container Toolkit 설치 및 모델 파일 준비
- [GPT-SoVITS 자동화 구성 가이드](server-a-scripts-Gpt-sovits_inside/자동화.md) - Server A 자동화 API 구성/포트/운영 모드 정리
- [GPT-SoVITS 자동화 실행법](server-a-scripts-Gpt-sovits_inside/실행법.md) - Host/Conda + Docker Sidecar 실행 절차

## 🔧 GPT-SoVITS 운영 방식 (업데이트)

현재 GPT-SoVITS 관련 구성은 두 가지 운영 방식을 함께 지원합니다.

- Docker 기반 운영 (권장)
  - 최상위 `docker-compose.yaml` 사용
  - GPT-SoVITS 본체(`gpt-sovits-cu128`) + 자동화 API sidecar 2개(`10001`, `10002`)
  - 자동화 API:
    - `gpt-sovits-files-api` (포트 `10001`)
    - `gpt-sovits-training-api` (포트 `10002`)
- Host/Conda 기반 운영 (레거시 유지)
  - `docker-compose.conda.yaml` 보존
  - `/opt/GPT-SoVITS` + `systemd` (`service_manager.sh`) 기반 운영

### GPT-SoVITS Docker 이미지 버전 메모

- `cu128-20260209-e4ae04` (주석으로 최상위 `docker-compose.yaml`에 명시)

### 포트 요약

- GPT-SoVITS 본체: `9871`, `9872`, `9873`, `9874`, `9880`
- 자동화 API: `10001`(파일 스캐너), `10002`(학습 API)

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
├── server-a-scripts-Gpt-sovits_inside/   # GPT-SoVITS 자동화 API/운영 스크립트/문서
│   ├── 자동화.md
│   ├── 실행법.md
│   ├── training_api.py
│   ├── file_scanner_api.py
│   ├── service_manager.sh      # Host/systemd용
│   ├── compose_manager.sh      # Docker Compose용
│   └── docker/
│       ├── Dockerfile.automation
│       ├── run-file-scanner.sh
│       └── run-training-api.sh
├── scripts/                 # 설치/설정 스크립트
│   ├── server-a/           # GPU 서버 스크립트
│   └── server-b/           # CPU 서버 스크립트
├── ../docker-compose.yaml   # (repo root) Docker 기반 GPT-SoVITS 포함 메인 compose
├── ../docker-compose.conda.yaml # (repo root) 기존 conda/비도커 GPT-SoVITS 전제 compose 보존본
└── README.md
```

## 📝 상세 가이드

자세한 설정 방법은 [Phase 5 설정 가이드](docs/PHASE5_SETUP.md)를 참조하세요.

GPT-SoVITS 자동화/학습/파일 관리 관련 내용은 아래 문서를 우선 참고하세요.

- [server-a-scripts-Gpt-sovits_inside/자동화.md](server-a-scripts-Gpt-sovits_inside/자동화.md)
- [server-a-scripts-Gpt-sovits_inside/실행법.md](server-a-scripts-Gpt-sovits_inside/실행법.md)
