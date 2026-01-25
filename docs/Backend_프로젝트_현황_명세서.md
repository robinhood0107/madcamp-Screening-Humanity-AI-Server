# 프로젝트 현황 명세서

**프로젝트명**: Avatar Forge Backend (Server B)  
**작성일**: 2026-01-26  
**프레임워크**: FastAPI (Python)  
**데이터베이스**: SQLite (개발용) / PostgreSQL (운영용)

---

## 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [디렉토리 구조](#디렉토리-구조)
3. [파일별 상세 분석](#파일별-상세-분석)
4. [API 엔드포인트 목록](#api-엔드포인트-목록)
5. [데이터베이스 모델](#데이터베이스-모델)
6. [의존성 및 설정](#의존성-및-설정)
7. [실행 방법](#실행-방법)

---

## ⚠️ 미구현 기능 목록 (2026-01-26)

### Phase 5 관련 미구현 기능

1. **`app/services/context_manager.py`** (신규 생성, Phase 5.2, 미구현)
   - **용도**: 대화 히스토리 관리 및 자동 요약
   - **구현 시기**: Phase 5.1 완료 후 즉시 (우선순위: 높음, 필수)
   - **상세 내용**: [파일별 상세 분석 - app/api/chat.py](#appapichatpy) 섹션 참조

2. **`app/core/rate_limiter.py`** (신규 생성, Phase 5.3, 미구현)
   - **용도**: 동시 접속 제한 관리
   - **구현 시기**: Phase 5.1 완료 후 즉시 (우선순위: 높음, 필수)
   - **상세 내용**: [파일별 상세 분석 - app/api/chat.py](#appapichatpy) 섹션 참조

3. **`POST /api/chat` - 컨텍스트 절약 요약 기능** (Phase 5.2, 미구현)
   - **영향**: `app/api/chat.py`의 `POST /api/chat` 엔드포인트
   - **구현 시기**: Phase 5.1 완료 후 즉시
   - **상세 내용**: [API 엔드포인트 목록 - 채팅 API](#채팅-api-api) 섹션 참조

4. **`POST /api/chat` - 동시 접속 제한** (Phase 5.3, 미구현)
   - **영향**: `app/api/chat.py`의 `POST /api/chat` 엔드포인트
   - **구현 시기**: Phase 5.1 완료 후 즉시
   - **상세 내용**: [API 엔드포인트 목록 - 채팅 API](#채팅-api-api) 섹션 참조

### 기타 미구현 기능

5. **`GET /api/tts/voices`** (미구현)
   - **용도**: 사용 가능한 음성 목록 조회
   - **구현 시기**: Phase 5.1 이후 (우선순위: 중간)

**상세 구현 가이드**: `docs/PHASE5_SETUP.md`의 "Phase 5.2-5.4 구현 가이드" 섹션 참조

---

## 프로젝트 개요

Avatar Forge Backend는 FastAPI 기반의 비동기 백엔드 서버로, 다음과 같은 주요 기능을 제공합니다:

- **Google OAuth2 인증**: fastapi-sso를 통한 소셜 로그인
- **비동기 작업 처리**: 3D 생성 작업을 백그라운드에서 처리
- **LLM 채팅 프록시**: Server A (GPU 서버)와의 통신을 통한 채팅 기능
- **파일 업로드 및 생성**: 이미지 업로드를 통한 3D 모델 생성

---

## 디렉토리 구조

```
madcamp-Screening-Humanity-BACK/
├── .gitignore                          # Git 무시 파일 목록
├── implementation_plan.md              # 구현 계획서
├── run_server_b.bat                    # Windows 실행 스크립트
└── server-b/
    └── backend/
        ├── .env.example                # 환경 변수 예제 파일
        ├── avatar_forge.db             # SQLite 데이터베이스 파일
        ├── requirements.txt            # Python 패키지 의존성
        ├── run.py                      # 서버 실행 진입점
        └── app/
            ├── main.py                 # FastAPI 애플리케이션 메인
            ├── api/                    # API 라우터 모듈
            │   ├── auth.py             # 인증 관련 API
            │   ├── chat.py             # 채팅 관련 API
            │   ├── deps.py             # 의존성 주입 유틸리티
            │   └── generate.py         # 생성 작업 관련 API
            ├── core/                   # 핵심 설정 모듈
            │   ├── config.py           # 환경 설정 관리
            │   ├── database.py         # 데이터베이스 연결 설정
            │   └── security.py         # 보안 관련 유틸리티
            └── models/                 # SQLAlchemy 데이터 모델
                ├── user.py             # User 모델
                └── generation.py       # GenerationJob, Character 모델
```

---

## 파일별 상세 분석

### 1. 루트 디렉토리 파일

#### `.gitignore`
- **위치**: 프로젝트 루트
- **용도**: Git 버전 관리에서 제외할 파일/디렉토리 지정
- **주요 내용**:
  - Python 관련: `__pycache__/`, `*.pyc`, `.venv/`, `venv/`
  - 환경 파일: `.env`, `.envrc`
  - 데이터베이스: `*.db`, `*.sqlite3`
  - IDE 설정: `.vscode/`, `.idea/`
  - 빌드 산출물: `build/`, `dist/`, `*.egg-info/`
  - 테스트/커버리지: `.pytest_cache/`, `.coverage`
  - Cursor 관련: `.cursorignore`, `.cursorindexingignore`

#### `implementation_plan.md`
- **위치**: 프로젝트 루트
- **용도**: 프로젝트 구현 계획 및 로드맵 문서
- **주요 내용**:
  - **목표**: FastAPI 기반 백엔드, Google OAuth2, 비동기 작업 처리, PostgreSQL 연동, Server A 통신
  - **구현 단계** (6단계):
    1. 프로젝트 초기화 및 환경 설정
    2. 데이터베이스 모델링
    3. 인증 시스템 (Google Login)
    4. 비동기 작업 시스템
    5. API 엔드포인트 구현
    6. 테스트 및 검증
  - **기술 스택**: Python 3.10+, FastAPI, PostgreSQL/SQLite, SQLAlchemy (Async), Google OAuth2, JWT

#### `run_server_b.bat`
- **위치**: 프로젝트 루트
- **용도**: Windows 환경에서 서버를 실행하는 배치 스크립트
- **내용**:
  ```batch
  @echo off
  cd server-b\backend
  python run.py
  pause
  ```
- **동작**: `server-b/backend` 디렉토리로 이동 후 `run.py` 실행

---

### 2. Backend 디렉토리 파일

#### `.env.example`
- **위치**: `server-b/backend/.env.example`
- **용도**: 환경 변수 설정 예제 파일 (실제 `.env` 파일 생성 시 참고)
- **주요 환경 변수**:
  - `PROJECT_NAME`: "Avatar Forge Backend"
  - `DATABASE_URL`: SQLite 데이터베이스 경로 (`sqlite+aiosqlite:///./avatar_forge.db`)
  - `SECRET_KEY`: JWT 토큰 서명용 시크릿 키
  - `GOOGLE_CLIENT_ID`: Google OAuth 클라이언트 ID
  - `GOOGLE_CLIENT_SECRET`: Google OAuth 클라이언트 시크릿
  - `GOOGLE_REDIRECT_URI`: OAuth 콜백 URL (`http://localhost:8000/api/auth/google/callback`)
  - `GPU_SERVER_URL`: Server A (GPU 서버) URL (`http://localhost:8001`)
  - `SHARED_MODELS_DIR`: 공유 모델 디렉토리 경로 (`./shared_models_mock`)
  - `USER_ASSETS_DIR`: 사용자 에셋 디렉토리 경로 (`./user_assets_mock`)
  - `BACKEND_CORS_ORIGINS`: CORS 허용 오리진 목록 (JSON 배열 형식)

#### `requirements.txt`
- **위치**: `server-b/backend/requirements.txt`
- **용도**: Python 패키지 의존성 목록
- **주요 패키지**:
  - `fastapi==0.109.0`: 웹 프레임워크
  - `uvicorn[standard]==0.27.0`: ASGI 서버
  - `sqlalchemy==2.0.25`: ORM
  - `alembic==1.13.1`: 데이터베이스 마이그레이션 도구
  - `asyncpg==0.29.0`: PostgreSQL 비동기 드라이버
  - `pydantic==2.6.0`: 데이터 검증 라이브러리
  - `pydantic-settings==2.1.0`: 설정 관리
  - `python-multipart==0.0.9`: 파일 업로드 지원
  - `python-jose[cryptography]==3.3.0`: JWT 토큰 처리
  - `passlib[bcrypt]==1.7.4`: 비밀번호 해싱
  - `httpx==0.26.0`: 비동기 HTTP 클라이언트
  - `fastapi-sso==0.10.0`: SSO (Google OAuth) 지원
  - `python-dotenv==1.0.1`: 환경 변수 로드
  - `aiofiles==23.2.1`: 비동기 파일 I/O
  - `aiosqlite==0.20.0`: SQLite 비동기 드라이버

#### `run.py`
- **위치**: `server-b/backend/run.py`
- **용도**: 서버 실행 진입점
- **주요 기능**:
  1. `.env` 파일이 없으면 `.env.example`에서 복사
  2. 필요한 디렉토리 생성:
     - `./shared_models_mock`: 공유 모델 디렉토리
     - `./user_assets_mock`: 사용자 에셋 디렉토리
     - `./uploads`: 업로드 파일 임시 저장 디렉토리
  3. Uvicorn 서버 실행:
     - 호스트: `0.0.0.0`
     - 포트: `8000`
     - 리로드 모드: 활성화 (`reload=True`)
     - 애플리케이션: `app.main:app`

#### `avatar_forge.db`
- **위치**: `server-b/backend/avatar_forge.db`
- **용도**: SQLite 데이터베이스 파일 (개발용)
- **참고**: 실제 데이터베이스 파일이므로 바이너리 형식이며, Git에 포함되어 있음

---

### 3. App 디렉토리 - 메인 애플리케이션

#### `app/main.py`
- **위치**: `server-b/backend/app/main.py`
- **용도**: FastAPI 애플리케이션 메인 진입점
- **주요 구성**:

  **1. Lifespan 이벤트 핸들러**:
  - `@asynccontextmanager` 데코레이터로 애플리케이션 생명주기 관리
  - **Startup**: 데이터베이스 테이블 자동 생성 (`Base.metadata.create_all`)
  - **Shutdown**: 데이터베이스 엔진 종료

  **2. FastAPI 앱 인스턴스**:
  - 제목: `settings.PROJECT_NAME`
  - OpenAPI URL: `/api/openapi.json`
  - Lifespan 이벤트 연결

  **3. CORS 미들웨어**:
  - `BACKEND_CORS_ORIGINS` 설정에 따라 동적 구성
  - 모든 메서드 및 헤더 허용
  - Credentials 허용

  **4. 라우터 등록**:
  - `/api/auth/*`: 인증 관련 (`auth.router`)
  - `/api/*`: 생성 및 채팅 관련 (`generate.router`, `chat.router`)

  **5. 기본 엔드포인트**:
  - `GET /`: 루트 엔드포인트 ("Avatar Forge Backend Running" 반환)
  - `GET /api/health`: 헬스 체크 엔드포인트

---

### 4. App/Core 디렉토리 - 핵심 설정

#### `app/core/config.py`
- **위치**: `server-b/backend/app/core/config.py`
- **용도**: 애플리케이션 전역 설정 관리 (Pydantic Settings 사용)
- **주요 설정 항목**:

  **기본 설정**:
  - `PROJECT_NAME`: "Avatar Forge Backend"
  - `API_V1_STR`: "/api"

  **CORS 설정**:
  - `BACKEND_CORS_ORIGINS`: 허용할 오리진 목록 (문자열 또는 리스트 형식 지원)
  - Validator로 문자열을 리스트로 변환

  **데이터베이스 설정**:
  - `DATABASE_URL`: 기본값 `sqlite+aiosqlite:///./avatar_forge.db`

  **JWT 설정**:
  - `SECRET_KEY`: 기본값 "YOUR_SECRET_KEY_HERE_CHANGE_IN_PROD"
  - `ALGORITHM`: "HS256"
  - `ACCESS_TOKEN_EXPIRE_MINUTES`: 7일 (60 * 24 * 7)

  **Google OAuth 설정**:
  - `GOOGLE_CLIENT_ID`: 빈 문자열 (환경 변수에서 로드)
  - `GOOGLE_CLIENT_SECRET`: 빈 문자열
  - `GOOGLE_REDIRECT_URI`: `http://localhost:8000/api/auth/google/callback`

  **외부 서비스 설정**:
  - `GPU_SERVER_URL`: `http://localhost:8001` (Server A)

  **경로 설정**:
  - `SHARED_MODELS_DIR`: `/mnt/shared_models` (운영용) / `./shared_models_mock` (개발용)
  - `USER_ASSETS_DIR`: `/mnt/user_assets` (운영용) / `./user_assets_mock` (개발용)

  **설정 로드**:
  - `.env` 파일에서 자동 로드
  - 대소문자 구분
  - 추가 필드 무시

#### `app/core/database.py`
- **위치**: `server-b/backend/app/core/database.py`
- **용도**: 데이터베이스 연결 및 세션 관리
- **주요 구성**:

  **1. 비동기 엔진 생성**:
  - `create_async_engine`로 SQLAlchemy 비동기 엔진 생성
  - `DATABASE_URL` 사용
  - SQLite의 경우 `check_same_thread=False` 설정

  **2. 세션 팩토리**:
  - `AsyncSessionLocal`: 비동기 세션 생성 팩토리
  - `expire_on_commit=False`: 커밋 후 객체 만료 방지
  - `autocommit=False`, `autoflush=False`: 수동 제어

  **3. Base 클래스**:
  - `DeclarativeBase`: SQLAlchemy 모델의 기본 클래스

  **4. 의존성 함수**:
  - `get_db()`: FastAPI 의존성으로 사용되는 제너레이터 함수
  - 요청마다 새로운 세션 생성 및 자동 종료

#### `app/core/security.py`
- **위치**: `server-b/backend/app/core/security.py`
- **용도**: 보안 관련 유틸리티 함수
- **주요 기능**:

  **1. 비밀번호 컨텍스트**:
  - `pwd_context`: bcrypt를 사용한 비밀번호 해싱 컨텍스트
  - 현재는 사용되지 않음 (Google OAuth만 사용)

  **2. JWT 토큰 생성**:
  - `create_access_token(subject, expires_delta=None)`:
    - `subject`: 사용자 ID (문자열)
    - `expires_delta`: 만료 시간 델타 (기본값: 설정에서 로드)
    - 페이로드: `{"sub": subject, "exp": expire}`
    - HS256 알고리즘으로 서명

---

### 5. App/API 디렉토리 - API 라우터

#### `app/api/auth.py`
- **위치**: `server-b/backend/app/api/auth.py`
- **용도**: Google OAuth2 인증 API
- **주요 구성**:

  **1. GoogleSSO 인스턴스**:
  - `fastapi-sso` 라이브러리 사용
  - 설정에서 클라이언트 ID, 시크릿, 리다이렉트 URI 로드
  - `allow_insecure_http=True`: 개발 환경용

  **2. 엔드포인트**:

  **`GET /api/auth/google/login`**:
  - Google 로그인 페이지로 리다이렉트
  - `sso.get_login_redirect()` 반환

  **`GET /api/auth/google/callback`**:
  - Google OAuth 콜백 처리
  - **동작 흐름**:
    1. `sso.verify_and_process(request)`로 사용자 정보 획득
    2. 이메일로 기존 사용자 조회
    3. 사용자가 없으면 새 사용자 생성:
       - UUID 생성
       - 이메일, 사용자명, 프로필 사진, provider 저장
    4. JWT 토큰 생성 (`create_access_token`)
    5. 프론트엔드로 리다이렉트 (`http://localhost:3000/auth/callback?token={token}`)
  - **에러 처리**: 400 상태 코드 반환

#### `app/api/chat.py`
- **위치**: `server-b/backend/app/api/chat.py`
- **용도**: LLM 채팅 프록시 API (Server A와 통신)
- **주요 구성**:

  **1. Pydantic 모델**:
  - `Message`: 역할(role)과 내용(content)을 가진 메시지 모델
  - `ChatRequest`: 채팅 요청 모델
    - `messages`: 메시지 리스트
    - `persona`: 페르소나 (선택)
    - `temperature`: 0.7 (기본값)
    - `max_tokens`: 512 (기본값)
    - `model`: "gpt-oss-20b" (기본값)
    - `session_id`: 세션 ID (선택, 자동 생성)

  **2. 엔드포인트**:

  **`POST /api/chat`**:
  - 인증 필요 (`get_current_user` 의존성)
  - **동시 접속 제한**: 최대 20명 (Phase 5.3 구현)
  - **동작 흐름**:
    1. 동시 접속 제한 확인 (`ConcurrentUserLimiter`)
    2. 세션 ID 생성/조회 (없으면 자동 생성)
    3. 컨텍스트 관리자로 대화 히스토리 관리 및 자동 요약 (`ContextManager`)
    4. Server A의 LLM 서비스 URL 구성 (`GPU_SERVER_URL`의 포트를 8002로 변경)
    5. `httpx.AsyncClient`로 비동기 HTTP 요청
    6. 성공 시 Server A 응답 반환 (세션 ID 포함)
    7. 실패 시 Mock 응답 반환 (개발용)
  - **타임아웃**: 60초
  - **에러 처리**: 예외 발생 시 Mock 응답으로 폴백

  **`GET /api/chat/models`**:
  - 사용 가능한 LLM 모델 목록 반환
  - 인증 필요
  - 반환 형식:
    ```json
    {
      "success": true,
      "data": {
        "models": [
          {"id": "gpt-oss-20b", "name": "GPT-OSS-20B (Default)"},
          {"id": "dolphin-2.9-8b", "name": "Dolphin 2.9 8B (Uncensored)"}
        ]
      }
    }
    ```

  **⚠️ 중요 변경사항 (2026-01-26, 미구현)**:
  - **턴 제한 제거**: Frontend의 30턴 제한 제거, 무제한 대화 지원 (Phase 5.4, 미구현)
  - **컨텍스트 절약 요약 기능**: Phase 5.2에서 구현 예정 (필수, 미구현)
  - **동시 접속 제한**: Phase 5.3에서 구현 예정 (최대 20명, 필수, 미구현)

#### `app/services/context_manager.py` (신규 생성, Phase 5.2, 미구현)
- **위치**: `server-b/backend/app/services/context_manager.py`
- **용도**: 대화 히스토리 관리 및 자동 요약
- **구현 시기**: Phase 5.1 완료 후 즉시 구현 (우선순위: 높음, 필수)
- **상태**: 미구현
- **주요 기능**:
  - 세션별 대화 히스토리 저장/조회 (Redis 또는 메모리 캐시)
  - 토큰 수 계산 및 모니터링
  - 자동 요약 트리거 (컨텍스트 80% 사용 시)
  - 슬라이딩 윈도우 전략 (최근 18턴 유지, 이전 턴 요약)
  - 요약 캐싱 (성능 최적화)

#### `app/core/rate_limiter.py` (신규 생성, Phase 5.3, 미구현)
- **위치**: `server-b/backend/app/core/rate_limiter.py`
- **용도**: 동시 접속 제한 관리
- **구현 시기**: Phase 5.1 완료 후 즉시 구현 (우선순위: 높음, 필수)
- **상태**: 미구현
- **주요 기능**:
  - 활성 세션 수 추적 (Redis 기반)
  - 최대 동시 접속자 수 제한 (기본: 20명, 환경 변수로 설정 가능)
  - 세션 등록/해제
  - 503 에러 반환 (제한 초과 시)

#### `app/api/deps.py`
- **위치**: `server-b/backend/app/api/deps.py`
- **용도**: FastAPI 의존성 주입 유틸리티
- **주요 기능**:

  **1. OAuth2 스키마**:
  - `OAuth2PasswordBearer`: Bearer 토큰 추출 스키마
  - 토큰 URL: `/api/auth/login/access-token` (실제로는 사용되지 않음)

  **2. 현재 사용자 조회 의존성**:
  - `get_current_user(db, token)`: JWT 토큰에서 사용자 정보 추출
  - **동작 흐름**:
    1. `oauth2_scheme`으로 요청 헤더에서 토큰 추출
    2. JWT 디코딩 (`jwt.decode`)
    3. 페이로드에서 `sub` (사용자 ID) 추출
    4. 데이터베이스에서 사용자 조회
    5. 사용자가 없으면 401 에러 반환
  - **에러 처리**: 
    - JWT 디코딩 실패 시 401
    - 사용자 없음 시 401
    - `WWW-Authenticate: Bearer` 헤더 포함

#### `app/api/generate.py`
- **위치**: `server-b/backend/app/api/generate.py`
- **용도**: 3D 생성 작업 비동기 처리 API
- **주요 구성**:

  **1. 백그라운드 작업 함수**:
  - `process_generation_task(job_id, input_path, db_session)`:
    - **동작 흐름**:
      1. 새로운 데이터베이스 세션 생성 (의존성 주입 세션은 사용 불가)
      2. 작업 ID로 `GenerationJob` 조회
      3. 상태를 "processing", 진행률을 10%로 업데이트
      4. 5초 대기 (Server A 호출 시뮬레이션)
      5. 진행률을 50%로 업데이트
      6. 5초 대기
      7. 상태를 "completed", 진행률을 100%로 업데이트
      8. Mock 출력 파일 생성 (`{job_id}.glb`)
      9. `result_url` 및 `completed_at` 설정
    - **에러 처리**: 예외 발생 시 상태를 "failed", `error_message` 저장

  **2. 엔드포인트**:

  **`POST /api/generate`**:
  - 인증 필요
  - **요청**: `image` (UploadFile)
  - **동작 흐름**:
    1. UUID로 작업 ID 생성
    2. 업로드된 이미지를 `./uploads/{job_id}_input.png`로 저장
    3. `GenerationJob` 레코드 생성:
       - `user_id`: 현재 사용자 ID
       - `job_type`: "3d"
       - `status`: "pending"
       - `input_payload`: JSON 문자열 (이미지 경로 포함)
    4. 백그라운드 작업 등록 (`BackgroundTasks`)
    5. 즉시 응답 반환:
       ```json
       {
         "success": true,
         "data": {
           "job_id": "...",
           "status_url": "/api/generate/status/{job_id}"
         }
       }
       ```

  **`GET /api/status/{job_id}`**:
  - 작업 상태 조회 (인증 선택적)
  - **응답**:
    ```json
    {
      "success": true,
      "data": {
        "job_id": "...",
        "status": "pending|processing|completed|failed",
        "progress": 0-100,
        "result_url": "...",
        "error": "..."
      }
    }
    ```
  - **에러 처리**: 작업이 없으면 404 반환

---

### 6. App/Models 디렉토리 - 데이터 모델

#### `app/models/user.py`
- **위치**: `server-b/backend/app/models/user.py`
- **용도**: User 데이터 모델 정의
- **테이블명**: `users`
- **필드**:
  - `id` (String(36), PK): UUID 문자열
  - `email` (String(100), Unique, Index): 이메일 주소
  - `username` (String(50), Nullable): 사용자명 (Google 이름)
  - `picture` (String(255), Nullable): 프로필 사진 URL
  - `is_active` (Boolean, Default=True): 활성 상태
  - `is_superuser` (Boolean, Default=False): 슈퍼유저 여부
  - `provider` (String(20), Default="google"): 인증 제공자
  - `created_at` (DateTime, Timezone): 생성 시간 (서버 기본값)
  - `updated_at` (DateTime, Timezone, OnUpdate): 수정 시간 (업데이트 시 자동 갱신)

#### `app/models/generation.py`
- **위치**: `server-b/backend/app/models/generation.py`
- **용도**: 생성 작업 및 캐릭터 데이터 모델 정의
- **모델 1: GenerationJob**
  - **테이블명**: `generation_jobs`
  - **필드**:
    - `id` (String(36), PK): UUID 문자열
    - `user_id` (String(36), FK→users.id, Nullable): 사용자 ID (익명 허용)
    - `job_type` (String(20)): 작업 유형 ("3d", "style", "tts")
    - `status` (String(20), Default="pending"): 상태 ("pending", "processing", "completed", "failed")
    - `input_payload` (Text, Nullable): 입력 데이터 (JSON 문자열 또는 파일 경로)
    - `result_url` (String(255), Nullable): 결과 파일 URL
    - `error_message` (Text, Nullable): 에러 메시지
    - `progress` (Integer, Default=0): 진행률 (0-100)
    - `created_at` (DateTime, Timezone): 생성 시간
    - `completed_at` (DateTime, Timezone, Nullable): 완료 시간

- **모델 2: Character**
  - **테이블명**: `characters`
  - **필드**:
    - `id` (String(36), PK): UUID 문자열
    - `user_id` (String(36), FK→users.id): 사용자 ID
    - `name` (String(100)): 캐릭터 이름
    - `description` (Text, Nullable): 캐릭터 설명
    - `model_url` (String(255), Nullable): GLB 모델 파일 경로
    - `thumbnail_url` (String(255), Nullable): 썸네일 이미지 경로
    - `created_at` (DateTime, Timezone): 생성 시간

---

## API 엔드포인트 목록

### 인증 API (`/api/auth/*`)
| 메서드 | 경로 | 설명 | 인증 필요 |
|--------|------|------|----------|
| GET | `/api/auth/google/login` | Google 로그인 페이지로 리다이렉트 | ❌ |
| GET | `/api/auth/google/callback` | Google OAuth 콜백 처리 및 JWT 발급 | ❌ |

### 생성 API (`/api/*`)
| 메서드 | 경로 | 설명 | 인증 필요 |
|--------|------|------|----------|
| POST | `/api/generate` | 3D 생성 작업 시작 (이미지 업로드) | ✅ |
| GET | `/api/status/{job_id}` | 생성 작업 상태 조회 | ⚠️ (선택적) |

### 채팅 API (`/api/*`)
| 메서드 | 경로 | 설명 | 인증 필요 |
|--------|------|------|----------|
| POST | `/api/chat` | LLM 채팅 요청 (Server A 프록시) | ✅ |
| GET | `/api/chat/models` | 사용 가능한 LLM 모델 목록 | ✅ |

### 시스템 API
| 메서드 | 경로 | 설명 | 인증 필요 |
|--------|------|------|----------|
| GET | `/` | 루트 엔드포인트 | ❌ |
| GET | `/api/health` | 헬스 체크 | ❌ |
| GET | `/api/openapi.json` | OpenAPI 스키마 | ❌ |
| GET | `/docs` | Swagger UI 문서 | ❌ |
| GET | `/redoc` | ReDoc 문서 | ❌ |

---

## 데이터베이스 모델

### ERD 관계도

```
users (1) ──< (N) generation_jobs
users (1) ──< (N) characters
```

### 테이블 상세

#### `users`
- **용도**: 사용자 정보 저장 (Google OAuth)
- **주요 관계**: 
  - `generation_jobs.user_id` → `users.id` (FK, Nullable)
  - `characters.user_id` → `users.id` (FK)

#### `generation_jobs`
- **용도**: 비동기 생성 작업 추적
- **주요 관계**: 
  - `user_id` → `users.id` (FK, Nullable)

#### `characters`
- **용도**: 생성된 캐릭터 메타데이터 저장
- **주요 관계**: 
  - `user_id` → `users.id` (FK)

---

## 의존성 및 설정

### Python 패키지 의존성
- **웹 프레임워크**: FastAPI 0.109.0
- **서버**: Uvicorn 0.27.0
- **ORM**: SQLAlchemy 2.0.25
- **마이그레이션**: Alembic 1.13.1
- **데이터베이스 드라이버**: 
  - PostgreSQL: asyncpg 0.29.0
  - SQLite: aiosqlite 0.20.0
- **데이터 검증**: Pydantic 2.6.0, pydantic-settings 2.1.0
- **인증**: 
  - python-jose[cryptography] 3.3.0 (JWT)
  - passlib[bcrypt] 1.7.4 (비밀번호 해싱)
  - fastapi-sso 0.10.0 (Google OAuth)
- **HTTP 클라이언트**: httpx 0.26.0
- **파일 처리**: 
  - python-multipart 0.0.9 (업로드)
  - aiofiles 23.2.1 (비동기 파일 I/O)
- **환경 변수**: python-dotenv 1.0.1

### 환경 변수 설정
`.env` 파일에 다음 변수들이 필요합니다:
- `PROJECT_NAME`
- `DATABASE_URL`
- `SECRET_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `GPU_SERVER_URL`
- `SHARED_MODELS_DIR`
- `USER_ASSETS_DIR`
- `BACKEND_CORS_ORIGINS`

---

## 실행 방법

### 1. Windows 환경
```batch
# 방법 1: 배치 스크립트 사용
run_server_b.bat

# 방법 2: 직접 실행
cd server-b\backend
python run.py
```

### 2. Linux/Mac 환경
```bash
cd server-b/backend
python run.py
```

### 3. 수동 실행
```bash
cd server-b/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 서버 접속
- **API 서버**: http://localhost:8000
- **API 문서 (Swagger)**: http://localhost:8000/docs
- **API 문서 (ReDoc)**: http://localhost:8000/redoc
- **헬스 체크**: http://localhost:8000/api/health

---

## 주요 특징 및 아키텍처

### 1. 비동기 처리
- FastAPI의 비동기 특성 활용
- SQLAlchemy 비동기 세션 사용
- 백그라운드 작업으로 긴 작업 처리 (3D 생성)

### 2. 인증 및 보안
- Google OAuth2를 통한 소셜 로그인
- JWT 토큰 기반 인증
- Bearer 토큰 방식

### 3. 데이터베이스
- 개발 환경: SQLite (로컬 파일)
- 운영 환경: PostgreSQL (설정 가능)
- SQLAlchemy ORM으로 모델 관리
- 애플리케이션 시작 시 자동 테이블 생성

### 4. 파일 처리
- 이미지 업로드 지원 (`UploadFile`)
- Mock 디렉토리 구조 (개발용)
- NFS 경로 지원 (운영용, 설정 가능)

### 5. 외부 서비스 통신
- Server A (GPU 서버)와 HTTP 통신
- 채팅 API 프록시 역할
- 에러 시 Mock 응답으로 폴백 (개발용)

---

## 알려진 제한사항 및 개선 필요 사항

1. **인증**:
   - `deps.py`의 `OAuth2PasswordBearer` 토큰 URL이 실제로 사용되지 않음
   - Bearer 토큰만 사용하므로 스키마 이름이 부적절할 수 있음

2. **에러 처리**:
   - `chat.py`에서 Server A 연결 실패 시 Mock 응답 반환 (운영 환경에서는 에러 반환 필요)

3. **백그라운드 작업**:
   - `generate.py`의 `process_generation_task`가 실제 Server A 호출을 하지 않음 (Mock)
   - 실제 Server A 통신 로직 추가 필요

4. **데이터베이스**:
   - `avatar_forge.db`가 Git에 포함되어 있음 (`.gitignore`에 추가 고려)

5. **보안**:
   - `SECRET_KEY` 기본값이 프로덕션에 부적절
   - `allow_insecure_http=True`는 개발 환경 전용

6. **경로 설정**:
   - Windows/Unix 경로 차이 고려 필요
   - Mock 디렉토리와 실제 NFS 경로 전환 로직 필요

---

## 참고 사항

- 이 명세서는 현재 코드베이스 상태를 기반으로 작성되었습니다.
- `implementation_plan.md`에 따르면 일부 기능은 아직 구현 중일 수 있습니다.
- 실제 운영 환경에서는 `.env` 파일을 안전하게 관리하고, 데이터베이스 마이그레이션을 Alembic으로 관리하는 것을 권장합니다.

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026-01-26
