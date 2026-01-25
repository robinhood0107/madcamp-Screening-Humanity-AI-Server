# 프로젝트 현황 명세서

## 프로젝트 개요

**프로젝트명**: 인생 극장 (Life Theater)  
**프로젝트 타입**: Next.js 기반 웹 애플리케이션  
**프로젝트 버전**: 0.1.0  
**설명**: AI와 함께하는 몰입형 롤플레이 학습 플랫폼

---

## ⚠️ 미구현 기능 목록 (2026-01-26)

### Phase 5 관련 미구현 기능

1. **`components/chat-room.tsx` - 턴 제한 제거** (Phase 5.4, 미구현)
   - **변경 사항**: 30턴 제한 제거, 무제한 대화 지원
   - **구현 시기**: Phase 5.1 완료 후
   - **상세 내용**: [파일별 상세 설명 - chat-room.tsx](#chat-roomtsx) 섹션 참조

2. **`components/chat-room.tsx` - 세션 관리 로직 추가** (Phase 5.4, 미구현)
   - **변경 사항**: 세션 ID 생성/유지, API 호출 시 `session_id` 포함
   - **구현 시기**: Phase 5.1 완료 후
   - **상세 내용**: [파일별 상세 설명 - chat-room.tsx](#chat-roomtsx) 섹션 참조

3. **컨텍스트 절약 기능 연동** (Phase 5.2, 미구현)
   - **영향**: Backend에서 자동으로 대화 히스토리 요약 처리
   - **Frontend 변경**: 특별한 변경 불필요 (Backend에서 처리)
   - **구현 시기**: Phase 5.1 완료 후 즉시 (Backend 구현)

### 기타 미구현 기능

4. **TTS 음성 목록 조회 UI** (미구현)
   - **API**: `GET /api/tts/voices`
   - **구현 시기**: Phase 5.1 이후 (우선순위: 중간)

**상세 구현 가이드**: `docs/PHASE5_SETUP.md`의 "Phase 5.4: Frontend 턴 제한 제거" 섹션 참조

---

## 기술 스택

### 프레임워크 및 라이브러리
- **Next.js**: 16.0.10 (React 19.2.0 기반)
- **React**: 19.2.0
- **TypeScript**: ^5
- **Tailwind CSS**: ^4.1.9 (PostCSS 기반)
- **Zustand**: 5.0.10 (상태 관리)
- **NextAuth.js**: ^5.0.0-beta.30 (인증)

### 주요 의존성
- **UI 라이브러리**: Radix UI 컴포넌트 세트 (40+ 컴포넌트)
- **3D 렌더링**: @react-three/fiber, @react-three/drei, three.js
- **폼 관리**: react-hook-form, @hookform/resolvers, zod
- **스타일링**: tailwind-merge, clsx, class-variance-authority
- **아이콘**: lucide-react
- **차트**: recharts
- **애니메이션**: tailwindcss-animate, tw-animate-css
- **기타**: date-fns, sonner (토스트), next-themes (다크모드)

---

## 프로젝트 구조

```
madcamp-Screening-Humanity-FRONT/
├── app/                          # Next.js App Router
│   ├── api/                      # API 라우트
│   │   └── auth/
│   │       └── [...nextauth]/   # NextAuth 동적 라우트
│   │           └── route.ts      # 인증 핸들러 (GET, POST)
│   ├── globals.css               # 전역 스타일 (Tailwind 설정)
│   ├── layout.tsx                # 루트 레이아웃
│   └── page.tsx                  # 메인 페이지 (홈)
├── components/                   # React 컴포넌트
│   ├── ui/                       # shadcn/ui 기반 UI 컴포넌트 (50+)
│   ├── auth-components.tsx       # 인증 컴포넌트 (SignIn, SignOut)
│   ├── landing-page.tsx          # 랜딩 페이지
│   ├── mode-select-modal.tsx     # 모드 선택 모달
│   ├── avatar-upload.tsx         # 아바타 업로드
│   ├── avatar-preview.tsx        # 3D 아바타 미리보기
│   ├── scenario-setup.tsx        # 시나리오 설정
│   ├── script-preview.tsx        # 스크립트 미리보기
│   ├── loading-screen.tsx        # 로딩 화면
│   ├── chat-room.tsx             # 채팅방 (메인 게임 화면)
│   └── theme-provider.tsx        # 테마 프로바이더
├── hooks/                        # 커스텀 훅
│   ├── use-chat.ts               # 채팅 훅
│   ├── use-generation.ts         # 3D 생성 훅
│   ├── use-tts.ts                # TTS 훅
│   ├── use-mobile.ts             # 모바일 감지 훅
│   └── use-toast.ts              # 토스트 훅
├── lib/                          # 유틸리티 및 라이브러리
│   ├── api/                      # API 클라이언트
│   │   ├── client.ts             # API 클라이언트 구현
│   │   ├── types.ts              # API 타입 정의
│   │   └── index.ts              # API 모듈 export
│   ├── store.ts                  # Zustand 상태 관리 스토어
│   └── utils.ts                  # 유틸리티 함수 (cn)
├── public/                       # 정적 파일
│   ├── icon-*.png                # 파비콘 (라이트/다크)
│   ├── icon.svg                  # SVG 아이콘
│   ├── apple-icon.png            # Apple 터치 아이콘
│   └── placeholder-*.{jpg,svg}  # 플레이스홀더 이미지
├── styles/                       # 추가 스타일
│   └── globals.css               # 전역 스타일 (중복?)
├── auth.ts                       # NextAuth 설정
├── components.json               # shadcn/ui 설정
├── next.config.mjs               # Next.js 설정
├── postcss.config.mjs            # PostCSS 설정
├── tsconfig.json                 # TypeScript 설정
├── package.json                  # 프로젝트 의존성
├── task.md                       # 작업 목록 (프론트엔드 실행)
└── task_auth.md                  # 작업 목록 (인증 구현)
```

---

## 파일별 상세 설명

### 설정 파일

#### `package.json`
- **역할**: 프로젝트 의존성 및 스크립트 관리
- **주요 스크립트**:
  - `dev`: 개발 서버 실행
  - `build`: 프로덕션 빌드
  - `start`: 프로덕션 서버 실행
  - `lint`: ESLint 실행
- **의존성**: 70+ 패키지 (프로덕션 + 개발)

#### `tsconfig.json`
- **역할**: TypeScript 컴파일러 설정
- **주요 설정**:
  - 타겟: ES6
  - 모듈 해석: bundler
  - JSX: react-jsx
  - 경로 별칭: `@/*` → `./*`
  - 엄격 모드: 활성화

#### `next.config.mjs`
- **역할**: Next.js 설정
- **주요 설정**:
  - TypeScript 빌드 에러 무시: `true`
  - 이미지 최적화: 비활성화 (`unoptimized: true`)

#### `postcss.config.mjs`
- **역할**: PostCSS 설정
- **플러그인**: `@tailwindcss/postcss`

#### `components.json`
- **역할**: shadcn/ui 컴포넌트 설정
- **스타일**: new-york
- **경로 별칭**:
  - `@/components` → 컴포넌트
  - `@/lib/utils` → 유틸리티
  - `@/components/ui` → UI 컴포넌트

#### `.gitignore`
- **무시 항목**:
  - `node_modules/`
  - `.next/`, `out/`, `build/`
  - `.env*` (환경 변수)
  - 로그 파일
  - TypeScript 빌드 정보

---

### 인증 관련

#### `auth.ts`
- **역할**: NextAuth.js 설정
- **프로바이더**: Google OAuth
- **내보내기**:
  - `handlers`: API 라우트 핸들러
  - `signIn`: 로그인 함수
  - `signOut`: 로그아웃 함수
  - `auth`: 세션 확인 함수
- **콜백**: 세션 콜백 (추가 정보 포함 가능)

#### `app/api/auth/[...nextauth]/route.ts`
- **역할**: NextAuth API 라우트 핸들러
- **메서드**: GET, POST
- **기능**: 인증 요청 처리

#### `components/auth-components.tsx`
- **컴포넌트**:
  - `SignIn`: Google 로그인 버튼 (서버 액션)
  - `SignOut`: 로그아웃 버튼 (서버 액션)

---

### 상태 관리

#### `lib/store.ts`
- **역할**: Zustand 기반 전역 상태 관리
- **저장소 이름**: `life-theater-storage` (localStorage)
- **주요 상태**:
  - `step`: 현재 앱 단계 (`landing`, `mode-select`, `avatar-upload`, `avatar-preview`, `scenario-setup`, `script-preview`, `loading`, `chat`)
  - `isLoggedIn`: 로그인 상태
  - `userName`: 사용자 이름
  - `displayName`: 표시 이름
  - `gameMode`: 게임 모드 (`actor` | `director`)
  - `avatarUrl`: 아바타 URL
  - `uploadedImage`: 업로드된 이미지 (base64)
  - `scenario`: 시나리오 정보 (background, opponent, situation)
  - `generatedScript`: 생성된 스크립트
  - `messages`: 채팅 메시지 배열
  - `turnCount`: 턴 수
  - `chatHistories`: 채팅 기록 배열
  - `currentChatId`: 현재 채팅 ID
  - `generationJobId`: 3D 생성 작업 ID
- **주요 액션**:
  - `setStep`: 단계 변경
  - `saveChatHistory`: 채팅 기록 저장
  - `loadChatHistory`: 채팅 기록 불러오기
  - `deleteChatHistory`: 채팅 기록 삭제
  - `resetGame`: 게임 초기화
  - `goToHome`: 홈으로 이동
- **지속성**: `chatHistories`, `userName`, `displayName`, `isLoggedIn`만 localStorage에 저장

---

### API 클라이언트

#### `lib/api/types.ts`
- **역할**: API 타입 정의
- **주요 타입**:
  - `ApiResponse<T>`: 공통 응답 타입
  - `ChatRequest`, `ChatResponse`: 채팅 API
  - `TTSRequest`, `TTSResponse`: TTS API
  - `GenerationRequest`, `GenerationResponse`, `GenerationStatus`: 3D 생성 API
  - `StyleTransferRequest`, `StyleTransferResponse`, `StyleTransferStatus`: 스타일 변환 API
  - `AnimationsResponse`: 애니메이션 API
  - `StoryRequest`, `StoryResponse`: 스토리 생성 API
  - `SystemStatus`: 시스템 상태 API

#### `lib/api/client.ts`
- **역할**: API 클라이언트 구현
- **기본 URL**: `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`
- **API 버전**: `/api/v1`
- **주요 API 모듈**:
  - `chatApi`: 채팅 API (chat, listModels)
  - `ttsApi`: TTS API (generateSpeech, listVoices, getAudioUrl)
  - `generationApi`: 3D 생성 API (generateCharacter, getStatus, pollUntilComplete, getResultUrl)
  - `styleApi`: 스타일 변환 API (transformStyle, getStatus, pollUntilComplete)
  - `animationApi`: 애니메이션 API (listAnimations, getAnimationUrl)
  - `storyApi`: 스토리 생성 API (generateStory)
  - `systemApi`: 시스템 API (getStatus, healthCheck)
- **통합 객체**: `api` (모든 API 모듈 포함)

#### `lib/api/index.ts`
- **역할**: API 모듈 재export
- **내보내기**: types, client, api 객체

---

### 유틸리티

#### `lib/utils.ts`
- **역할**: 유틸리티 함수
- **함수**:
  - `cn(...inputs)`: 클래스명 병합 (clsx + tailwind-merge)

---

### 페이지 컴포넌트

#### `app/layout.tsx`
- **역할**: 루트 레이아웃
- **기능**:
  - 메타데이터 설정 (제목, 설명, 아이콘)
  - Geist 폰트 로드
  - Vercel Analytics 통합
  - 전역 스타일 적용

#### `app/page.tsx`
- **역할**: 메인 페이지
- **기능**:
  - 단계별 컴포넌트 렌더링
  - Zustand 스토어 기반 조건부 렌더링
- **렌더링 컴포넌트**:
  - `LandingPage` (step === "landing")
  - `ModeSelectModal`
  - `AvatarUpload`
  - `AvatarPreview`
  - `ScenarioSetup`
  - `ScriptPreview`
  - `LoadingScreen`
  - `ChatRoom`

#### `app/globals.css`
- **역할**: 전역 스타일 및 Tailwind 설정
- **기능**:
  - Tailwind CSS import
  - CSS 변수 정의 (다크모드 지원)
  - 테마 색상 정의 (oklch 색공간)
  - 기본 스타일 적용

---

### 주요 컴포넌트

#### `components/landing-page.tsx`
- **역할**: 랜딩 페이지
- **기능**:
  - 로그인 상태 확인
  - Google 로그인 버튼
  - 채팅 기록 표시 (사이드 패널)
  - 채팅 기록 불러오기/삭제
  - 새 연극 시작 버튼
- **상태**: `step === "landing"`일 때만 표시

#### `components/mode-select-modal.tsx`
- **역할**: 게임 모드 선택 모달
- **모드**:
  - `actor`: 주연 배우 모드 (1:1 롤플레이)
  - `director`: 감독 모드 (AI vs AI 관전)
- **기능**: 모드 선택 시 다음 단계로 이동

#### `components/avatar-upload.tsx`
- **역할**: 아바타 이미지 업로드
- **기능**:
  - 드래그 앤 드롭 지원
  - 파일 선택
  - 이미지 미리보기
  - 3D 생성 API 호출
  - 기본 캐릭터 사용 옵션
- **API 연동**: `generationApi.generateCharacter()`

#### `components/avatar-preview.tsx`
- **역할**: 3D 아바타 미리보기 및 생성 상태 확인
- **기능**:
  - 생성 작업 상태 폴링
  - 진행률 표시
  - 3D 모델 렌더링 (React Three Fiber)
  - 오류 처리
  - 확인 후 다음 단계로 이동
- **3D 라이브러리**: @react-three/fiber, @react-three/drei
- **API 연동**: `generationApi.pollUntilComplete()`

#### `components/scenario-setup.tsx`
- **역할**: 시나리오 설정
- **기능**:
  - 배경 선택 (학교, 회사, 몰입캠프, 병원, 카페)
  - 상대역 설정 (텍스트 입력)
  - 상황 설정 (텍스트 영역)
  - 유효성 검사
- **다음 단계**: `script-preview`

#### `components/script-preview.tsx`
- **역할**: AI 생성 스크립트 미리보기 및 편집
- **기능**:
  - 사용자 이름 설정/변경
  - AI 스크립트 생성 (시뮬레이션)
  - 스크립트 편집
  - 스크립트 확인 후 다음 단계로 이동
- **다음 단계**: `loading`

#### `components/loading-screen.tsx`
- **역할**: 로딩 화면
- **기능**:
  - 단계별 로딩 애니메이션
  - 진행률 표시
  - 시나리오 요약 표시
  - 자동으로 채팅방으로 전환
- **다음 단계**: `chat`

#### `components/chat-room.tsx`
- **역할**: 메인 채팅방 (게임 화면)
- **기능**:
  - 3D 아바타 표시 (AI, 사용자)
  - 채팅 메시지 표시
  - 메시지 입력 및 전송
  - ~~턴 수 관리 (최대 30턴)~~ **제거됨 (2026-01-26)**: 무제한 대화 지원
  - 세션 관리 (세션 ID 자동 생성/유지)
  - 힌트 표시
  - 종료 모달
  - 채팅 기록 자동 저장
- **3D 렌더링**: React Three Fiber (간단한 아바타)
- **AI 응답**: 현재 하드코딩된 응답 (실제 API 연동 필요)

**⚠️ 중요 변경사항 (2026-01-26, 미구현)**:
- **턴 제한 제거**: 30턴 제한을 제거하여 무제한 대화 지원 (Phase 5.4, 미구현)
- **세션 관리 추가**: 세션 ID를 통해 대화 히스토리 유지 (Phase 5.4, 미구현)
- **컨텍스트 절약**: Backend에서 자동으로 대화 히스토리 요약 처리 (Phase 5.2, 미구현)

#### `components/theme-provider.tsx`
- **역할**: 테마 프로바이더 (다크모드)
- **기능**: next-themes 래퍼

---

### 커스텀 훅

#### `hooks/use-chat.ts`
- **역할**: 채팅 기능 훅
- **기능**:
  - 메시지 상태 관리
  - 메시지 전송 (`sendMessage`)
  - 메시지 초기화 (`clearMessages`)
  - 로딩 상태
  - 에러 처리
- **API 연동**: `chatApi.chat()`

#### `hooks/use-generation.ts`
- **역할**: 3D 생성 기능 훅
- **기능**:
  - 생성 작업 시작
  - 상태 폴링
  - 진행률 콜백
  - 에러 처리
  - 리셋
- **API 연동**: `generationApi.generateCharacter()`, `generationApi.pollUntilComplete()`

#### `hooks/use-tts.ts`
- **역할**: TTS (Text-to-Speech) 기능 훅
- **기능**:
  - 음성 생성 (`generateSpeech`)
  - 오디오 재생 (`play`, `pause`, `stop`)
  - 재생 상태 관리
  - 에러 처리
- **API 연동**: `ttsApi.generateSpeech()`

#### `hooks/use-mobile.ts`
- **역할**: 모바일 감지 훅
- **기능**: 화면 너비 기반 모바일 감지 (768px 기준)

#### `hooks/use-toast.ts`
- **역할**: 토스트 알림 훅
- **기능**: 토스트 메시지 관리 (추가, 업데이트, 제거)

---

### UI 컴포넌트 (`components/ui/`)

shadcn/ui 기반 컴포넌트 라이브러리 (50+ 컴포넌트)

**주요 컴포넌트**:
- `button.tsx`: 버튼
- `input.tsx`: 입력 필드
- `textarea.tsx`: 텍스트 영역
- `dialog.tsx`: 다이얼로그/모달
- `card.tsx`: 카드
- `toast.tsx`, `toaster.tsx`: 토스트 알림
- `avatar.tsx`: 아바타
- `badge.tsx`: 배지
- `form.tsx`: 폼 (react-hook-form 통합)
- `select.tsx`: 선택 드롭다운
- `tabs.tsx`: 탭
- `accordion.tsx`: 아코디언
- `alert.tsx`, `alert-dialog.tsx`: 알림
- `calendar.tsx`: 캘린더
- `chart.tsx`: 차트
- `sidebar.tsx`: 사이드바
- 기타 30+ 컴포넌트

---

### 정적 파일 (`public/`)

- `icon-light-32x32.png`: 라이트 모드 파비콘
- `icon-dark-32x32.png`: 다크 모드 파비콘
- `icon.svg`: SVG 파비콘
- `apple-icon.png`: Apple 터치 아이콘
- `placeholder-*.{jpg,svg,png}`: 플레이스홀더 이미지

---

### 스타일 파일

#### `app/globals.css`
- Tailwind CSS 설정
- CSS 변수 정의 (다크모드)
- 기본 스타일

#### `styles/globals.css`
- 중복 파일 (사용 여부 확인 필요)

---

### 작업 문서

#### `task.md`
- **내용**: 프론트엔드 실행 및 백엔드 연동 작업 목록
- **상태**: 모든 항목 완료

#### `task_auth.md`
- **내용**: NextAuth.js 구글 로그인 구현 작업 목록
- **상태**: 대부분 완료, LandingPage 연동 미완료

---

## 애플리케이션 플로우

### 사용자 여정

1. **랜딩 페이지** (`landing`)
   - 로그인하지 않은 경우: Google 로그인
   - 로그인한 경우: 새 연극 시작 버튼
   - 채팅 기록 확인/불러오기

2. **모드 선택** (`mode-select`)
   - 주연 배우 모드 선택 → 아바타 업로드
   - 감독 모드 선택 → 시나리오 설정

3. **아바타 업로드** (`avatar-upload`) - 주연 배우 모드만
   - 이미지 업로드 또는 기본 캐릭터 선택
   - 3D 생성 API 호출

4. **아바타 미리보기** (`avatar-preview`) - 주연 배우 모드만
   - 생성 상태 확인 (폴링)
   - 3D 모델 미리보기
   - 확인 후 다음 단계

5. **시나리오 설정** (`scenario-setup`)
   - 배경 선택
   - 상대역 설정
   - 상황 설정

6. **스크립트 미리보기** (`script-preview`)
   - 사용자 이름 설정
   - AI 스크립트 생성/편집
   - 확인 후 다음 단계

7. **로딩 화면** (`loading`)
   - 단계별 로딩 애니메이션
   - 자동으로 채팅방으로 전환

8. **채팅방** (`chat`)
   - 3D 아바타 표시
   - 채팅 메시지 교환
   - 턴 수 관리 (최대 30턴)
   - 종료 모달

---

## API 통신

### 백엔드 API 엔드포인트

**기본 URL**: `process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'`  
**API 버전**: `/api/v1`

#### 주요 엔드포인트

1. **채팅 API** (`/api/v1/chat`)
   - POST: 채팅 요청
   - GET: 모델 목록 조회

2. **TTS API** (`/api/v1/tts`)
   - POST: 음성 생성
   - GET: 음성 목록 조회

3. **3D 생성 API** (`/api/v1/generate`)
   - POST: 캐릭터 생성 시작
   - GET: 생성 상태 조회 (`/api/v1/generate/status/{job_id}`)

4. **스타일 변환 API** (`/api/v1/style/transform`)
   - POST: 스타일 변환 시작
   - GET: 변환 상태 조회 (`/api/v1/style/status/{job_id}`)

5. **애니메이션 API** (`/api/v1/animations`)
   - GET: 애니메이션 목록 조회

6. **스토리 API** (`/api/v1/story/generate`)
   - POST: 스토리 생성

7. **시스템 API** (`/api/v1/system`)
   - GET: 상태 조회 (`/status`)
   - GET: 헬스 체크 (`/health`)

---

## 상태 관리 구조

### Zustand 스토어 (`lib/store.ts`)

**저장소 이름**: `life-theater-storage`  
**지속성**: localStorage (일부 상태만)

**주요 상태 그룹**:

1. **앱 상태**
   - `step`: 현재 단계
   - `isLoggedIn`: 로그인 상태
   - `userName`: 사용자 이름
   - `displayName`: 표시 이름

2. **게임 상태**
   - `gameMode`: 게임 모드
   - `avatarUrl`: 아바타 URL
   - `uploadedImage`: 업로드된 이미지
   - `scenario`: 시나리오 정보
   - `generatedScript`: 생성된 스크립트
   - `generationJobId`: 생성 작업 ID

3. **채팅 상태**
   - `messages`: 메시지 배열
   - `turnCount`: 턴 수
   - `chatHistories`: 채팅 기록 배열
   - `currentChatId`: 현재 채팅 ID

**지속되는 상태** (localStorage):
- `chatHistories`
- `userName`
- `displayName`
- `isLoggedIn`

---

## 스타일링

### Tailwind CSS 설정

- **버전**: 4.1.9
- **PostCSS 플러그인**: `@tailwindcss/postcss`
- **애니메이션**: `tailwindcss-animate`, `tw-animate-css`

### 테마 시스템

- **색상 시스템**: OKLCH 색공간
- **다크모드**: CSS 변수 기반
- **폰트**: Geist, Geist Mono

### CSS 변수

- `--background`, `--foreground`
- `--primary`, `--secondary`
- `--muted`, `--accent`
- `--destructive`
- `--border`, `--input`, `--ring`
- `--chart-1` ~ `--chart-5`
- `--sidebar-*` (사이드바 관련)

---

## 환경 변수

### 필요한 환경 변수

- `NEXT_PUBLIC_API_URL`: 백엔드 API URL (기본값: `http://localhost:8000`)
- `AUTH_SECRET`: NextAuth 시크릿 키
- `GOOGLE_CLIENT_ID`: Google OAuth 클라이언트 ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth 클라이언트 시크릿

---

## 개발 스크립트

```bash
npm run dev      # 개발 서버 실행
npm run build    # 프로덕션 빌드
npm run start    # 프로덕션 서버 실행
npm run lint     # ESLint 실행
```

---

## 알려진 이슈 및 TODO

### 완료된 작업
- ✅ 의존성 설치
- ✅ 개발 서버 실행
- ✅ 백엔드 연동 확인
- ✅ NextAuth 설정
- ✅ 인증 컴포넌트 구현

### 미완료 작업
- ⏳ LandingPage에 NextAuth 로그인 연동 (부분 완료, 확인 필요)
- ⏳ 실제 AI 채팅 API 연동 (현재 하드코딩)
- ⏳ TTS 기능 통합
- ⏳ 3D 모델 로딩 및 애니메이션

---

## 프로젝트 특징

1. **모듈화된 구조**: 컴포넌트, 훅, API 클라이언트 분리
2. **타입 안정성**: TypeScript 전면 사용
3. **상태 관리**: Zustand 기반 전역 상태 + localStorage 지속성
4. **3D 렌더링**: React Three Fiber 통합
5. **반응형 디자인**: Tailwind CSS 기반
6. **다크모드 지원**: CSS 변수 기반 테마 시스템
7. **인증 시스템**: NextAuth.js 기반 OAuth

---

## 의존성 요약

### 프로덕션 의존성 (주요)
- Next.js, React, TypeScript
- Zustand (상태 관리)
- NextAuth.js (인증)
- Radix UI (40+ 컴포넌트)
- React Three Fiber (3D)
- Tailwind CSS (스타일링)
- React Hook Form, Zod (폼 관리)
- 기타 60+ 패키지

### 개발 의존성
- TypeScript 타입 정의
- Tailwind CSS PostCSS 플러그인
- ESLint

---

## 빌드 및 배포

### 빌드 설정
- TypeScript 빌드 에러 무시: 활성화 (개발 중)
- 이미지 최적화: 비활성화
- 정적 파일: `public/` 디렉터리

### 배포 고려사항
- 환경 변수 설정 필요
- 백엔드 API URL 설정
- NextAuth 시크릿 키 설정
- Google OAuth 인증 정보 설정

---

**문서 생성일**: 2026-01-26  
**프로젝트 버전**: 0.1.0  
**문서 버전**: 1.0.0
