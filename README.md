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

- [루트 docs 허브 (통폐합)](../docs/README.md) - 현재 기준 문서 색인
- [운영 구축 가이드](../docs/01_운영_구축_가이드.md) - 실행 모드, GPT-SoVITS 운영, 점검 절차
- [API 연동 가이드](../docs/02_API_연동_가이드.md) - BACK/Server A API 연동 계약 정리
- [데이터 모델 스키마](../docs/03_데이터_모델_스키마.md) - BACK 실제 모델 기준 스키마
- [로드맵/이력/정합성](../docs/04_로드맵_이력_정합성.md) - 변경 이력/정합성/아카이브 안내
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
├── ../docs/                 # (repo root) 통폐합 문서 허브/기준 문서
│   ├── README.md
│   ├── 01_운영_구축_가이드.md
│   ├── 02_API_연동_가이드.md
│   ├── 03_데이터_모델_스키마.md
│   ├── 04_로드맵_이력_정합성.md
│   └── archive/legacy_20260222/   # 기존 루트 문서 원본 보존
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

자세한 설정 방법은 [루트 docs 허브](../docs/README.md)와 [운영 구축 가이드](../docs/01_운영_구축_가이드.md)를 먼저 참조하세요.

GPT-SoVITS 자동화/학습/파일 관리 관련 내용은 아래 문서를 우선 참고하세요.

- [server-a-scripts-Gpt-sovits_inside/자동화.md](server-a-scripts-Gpt-sovits_inside/자동화.md)
- [server-a-scripts-Gpt-sovits_inside/실행법.md](server-a-scripts-Gpt-sovits_inside/실행법.md)

## 🧭 GPT-SoVITS 자동화 코드 유지보수 규칙 (요약)

이번 리팩토링부터는 `server-a-scripts-Gpt-sovits_inside`를 아래 규칙으로 유지합니다.

- 외부 계약 고정:
  - 포트 `10001`, `10002`
  - 엔드포인트 path/method
  - 주요 응답 키(backend가 참조하는 값)
  - 엔트리포인트 파일명 `training_api.py`, `file_scanner_api.py`
- 리팩토링 방식:
  - `Characterization(행동 고정)` -> `Extract Function` -> `모듈 추출` -> `회귀 검증`
- 과분할 금지:
  - 신규 helper 모듈은 `gsv_automation/` 내부 **6개 내외**로 제한
  - 연관 기능끼리 묶어서 분리 (공통/runtime/process/http + training_core + file_core)
- 주석 원칙:
  - 함수 앞에 역할/이유/부작용/주의점 설명
  - 핵심 줄에만 inline 주석
  - “코드 그대로 읽는 주석” 금지

상세 규칙/절차는 아래 문서에 분리 기록합니다.

- 아키텍처/주석 규칙: `server-a-scripts-Gpt-sovits_inside/자동화.md`
- 실행 순서/검증 체크리스트: `server-a-scripts-Gpt-sovits_inside/실행법.md`

## 🌐 도메인/URL 환경변수 관리 규칙 (요약)

세 프로젝트(FRONT/BACK/AI-Server)에서 서비스 URL/도메인은 아래 원칙으로 관리합니다.

- `FRONT`: 컴포넌트에서 직접 `process.env.NEXT_PUBLIC_API_URL || ...` 쓰지 않고 `lib/config/runtime.ts` 경유
- `BACK`: route/service 레벨에서 `localhost` fallback 금지, `app/core/config.py`의 `Settings`를 단일 진실 원천으로 사용
- `docker-compose*.yaml`: 공개 접근 URL/내부 오버라이드 URL은 가능한 범위에서 `${VAR:-default}` interpolation 사용
- 테스트 스크립트: URL 기본값은 `VAR=${VAR:-default}` 또는 env fallback으로 관리
- Gemini 비밀키는 `FRONT`/`AI-Server`가 아니라 `BACK`(`madcamp-Screening-Humanity-BACK/.env`의 `GEMINI_API_KEY`)에서만 관리
