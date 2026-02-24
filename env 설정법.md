# AI-Server `env 설정법`

이 문서는 `madcamp-Screening-Humanity-AI-Server` 관련 환경변수 설정 방법을 정리합니다.

이 폴더는 성격이 조금 다릅니다.
- 루트 `docker-compose.yaml`에서 사용하는 env (repo 루트 기준)
- AI-Server 내부 스크립트에서 사용하는 env
- GPT-SoVITS 자동화(sidecar) 컨테이너에서 사용하는 env

즉, "어디서 실행하느냐"에 따라 env를 넣는 위치가 달라집니다.

보안 정책(중요):
- Gemini 비밀키는 **AI-Server가 아니라** `madcamp-Screening-Humanity-BACK/.env`의 `GEMINI_API_KEY`에서 관리합니다.
- `NEXT_PUBLIC_GEMINI_API_KEY`는 FRONT에서 사용 금지(폐기됨)입니다.

## 1. 먼저 개념 정리 (중요)

## A. 루트 compose용 env (repo 루트에서 사용)
대상:
- `/mnt/d/repo/madcamp03/docker-compose.yaml`
- `/mnt/d/repo/madcamp03/docker-compose.conda.yaml`

용도:
- Front build arg, Backend의 Server A 연결 주소 override

넣는 위치:
- repo 루트 `.env` (권장) 또는 쉘 `export`

## B. AI-Server 스크립트용 env (이 폴더에서 사용)
대상:
- `scripts/server-a/test-vllm.sh`
- `scripts/ollama_pull_progress.py`
- `server-a-scripts-Gpt-sovits_inside/test_training.py`

용도:
- 테스트 대상 URL/호스트 바꾸기

넣는 위치:
- 실행 전에 쉘 `export` 또는 명령 앞에 `VAR=...`

## C. GPT-SoVITS 컨테이너 런타임 env (compose가 주입)
대상:
- `gpt-sovits-files-api`
- `gpt-sovits-training-api`

대표값:
- `GPT_SOVITS_ROOT`
- `is_half`

보통은 compose에서 이미 넣어주므로 직접 건드릴 일은 적음

## 2. 자주 쓰는 env 목록 (실제 사용 기준)

## 루트 compose override용 (repo 루트에서 설정)

### `SERVER_A_FILES_API_URL_OVERRIDE` (선택)
- 기본값: `http://gpt-sovits-files-api:10001`
- 용도: Backend가 붙을 File API 주소를 외부 주소로 바꾸고 싶을 때

### `SERVER_A_TRAINING_API_URL_OVERRIDE` (선택)
- 기본값: `http://gpt-sovits-training-api:10002`
- 용도: Backend가 붙을 Training API 주소 override

### `TTS_BASE_URL_OVERRIDE` (선택)
- 기본값: `http://gpt-sovits-cu128:9880`
- 용도: Backend가 붙을 GPT-SoVITS TTS API 주소 override

### `NEXT_PUBLIC_API_URL` (선택, frontend build arg)
- 프론트가 브라우저에서 접근할 백엔드 주소
- 예시(로컬): `http://localhost:8000`
- 예시(배포): `https://api.example.com`

### `NEXT_PUBLIC_MEDIA_BASE_URL` (선택, frontend build arg)
- 프론트의 오디오/정적 파일 base URL
- 비우면 FRONT 내부에서 `NEXT_PUBLIC_API_URL` fallback 사용

### `NEXT_PUBLIC_BACKEND_DISPLAY_URL` (선택, frontend build arg)
- 프론트 에러 메시지/안내 문구용 표시 URL

## AI-Server 스크립트용 env (이 폴더에서 자주 씀)

### `VLLM_URL`
대상 파일:
- `scripts/server-a/test-vllm.sh`

기본값:
- `http://localhost:8002`

예시:
```bash
export VLLM_URL=http://localhost:8002
bash scripts/server-a/test-vllm.sh
```

### `OLLAMA_HOST`
대상 파일:
- `scripts/ollama_pull_progress.py`

기본값:
- `localhost:11434`

예시:
```bash
export OLLAMA_HOST=localhost:11434
python scripts/ollama_pull_progress.py glm-4.7-flash
```

### `TRAINING_API_URL`
대상 파일:
- `server-a-scripts-Gpt-sovits_inside/test_training.py`

기본값:
- `http://localhost:10002`

예시:
```bash
export TRAINING_API_URL=http://localhost:10002
python server-a-scripts-Gpt-sovits_inside/test_training.py
```

### `TRAINING_TEST_MODEL_NAME` / `TRAINING_TEST_UPLOAD_PATH` / `TRAINING_TEST_VERSION` (선택)
대상 파일:
- `server-a-scripts-Gpt-sovits_inside/test_training.py`

용도:
- dry-run 테스트 대상 모델명/업로드 경로/버전 변경

예시:
```bash
export TRAINING_TEST_MODEL_NAME=dry_run_test_custom
export TRAINING_TEST_UPLOAD_PATH=/opt/GPT-SoVITS/sample_train_voice/my_voice
export TRAINING_TEST_VERSION=v2
python server-a-scripts-Gpt-sovits_inside/test_training.py
```

## GPT-SoVITS sidecar/컨테이너용 env (compose가 넣어줌)

### `GPT_SOVITS_ROOT`
- 자동화 API(`file_scanner_api.py`, `training_api.py`)가 GPT-SoVITS 루트 경로를 찾는 기준
- Docker에서는 보통 `/workspace/GPT-SoVITS`
- Host/Conda에서는 `/opt/GPT-SoVITS` (자동 폴백 지원)

### `is_half`
- GPT-SoVITS half precision 사용 여부
- 보통 GPU 환경에서 `true`

### `PYTHONUNBUFFERED`
- 로그 flush 지연 줄이기용 (`1`)

## 3. 루트 compose용 복붙 예시 (repo 루트 `.env`)

파일 위치:
- `/mnt/d/repo/madcamp03/.env` (권장, 선택)

```env
# Front build args (브라우저에서 접근하는 공개 주소)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MEDIA_BASE_URL=http://localhost:8000
NEXT_PUBLIC_BACKEND_DISPLAY_URL=http://localhost:8000

# Backend -> Server A 연결 override (특수한 외부 연결이 필요할 때만)
# 보통 로컬 Docker 개발에서는 비워둬도 됨 (compose 기본값 사용)
SERVER_A_FILES_API_URL_OVERRIDE=
SERVER_A_TRAINING_API_URL_OVERRIDE=
TTS_BASE_URL_OVERRIDE=
```

팁:
- 로컬 Docker 개발에서는 `SERVER_A_*_OVERRIDE`, `TTS_BASE_URL_OVERRIDE`를 비워두는 경우가 많음
- 기본값으로 내부 서비스명(`gpt-sovits-files-api`, `gpt-sovits-training-api`, `gpt-sovits-cu128`)을 사용하기 때문
- Gemini 비밀키는 여기(repo 루트 `.env`)가 아니라 `madcamp-Screening-Humanity-BACK/.env`에 둡니다.

## 4. AI-Server 폴더에서 바로 테스트할 때 예시

```bash
cd /mnt/d/repo/madcamp03/madcamp-Screening-Humanity-AI-Server

# vLLM 테스트
export VLLM_URL=http://localhost:8002
bash scripts/server-a/test-vllm.sh

# Ollama pull 진행률 보기
export OLLAMA_HOST=localhost:11434
python scripts/ollama_pull_progress.py glm-4.7-flash

# GPT-SoVITS training API dry-run 테스트
export TRAINING_API_URL=http://localhost:10002
python server-a-scripts-Gpt-sovits_inside/test_training.py
```

## 5. 자주 헷갈리는 포인트

- `NEXT_PUBLIC_*`는 AI-Server 폴더 env가 아니라 "루트 compose에서 frontend 빌드할 때" 쓰는 값
- `SERVER_A_*_OVERRIDE`도 AI-Server 앱 내부 env가 아니라 "루트 compose가 backend에 넣는 값"
- `GPT_SOVITS_ROOT`는 보통 compose가 자동으로 넣어주므로 수동 설정 필요가 적음

## 6. 빠른 체크리스트

- 루트 compose로 실행 중이면 env는 repo 루트 기준으로 넣었는가
- 스크립트 단독 실행이면 해당 터미널 세션에 `export` 했는가
- `TRAINING_API_URL`/`VLLM_URL`/`OLLAMA_HOST` 포트가 실제 서비스 포트와 맞는가
- Docker와 Host/Conda 경로를 혼용하지 않았는가 (`/workspace/GPT-SoVITS` vs `/opt/GPT-SoVITS`)
