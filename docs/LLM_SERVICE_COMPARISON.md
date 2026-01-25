# LLM 서비스 비교: vLLM vs Ollama

**작성일**: 2026-01-26  
**버전**: 1.0

---

## 📋 목차

1. [개요](#1-개요)
2. [케이스 A: vLLM](#2-케이스-a-vllm)
3. [케이스 B: Ollama](#3-케이스-b-ollama)
4. [API 차이점 비교](#4-api-차이점-비교)
5. [Backend 구현 차이점](#5-backend-구현-차이점)
6. [환경 변수 설정](#6-환경-변수-설정)

---

## 1. 개요

**⚠️ 중요**: vLLM과 Ollama는 동시에 실행할 수 없습니다 (VRAM 제약). 하나만 선택하여 사용하세요.

### 선택 기준

| 항목 | vLLM | Ollama |
|------|------|--------|
| **모델 형식** | BitsAndBytes 4-bit | GGUF (Q4_K_XL) |
| **용량** | ~14GB | ~16.8GB |
| **성능** | 높은 처리량 (동시 접속 10-12명) | 중간 처리량 |
| **API 표준** | OpenAI 호환 | Ollama 자체 API |
| **설정 복잡도** | 중간 | 낮음 |
| **추천 용도** | 프로덕션, 높은 동시 접속 | 개발/테스트, 간단한 설정 |

---

## 2. 케이스 A: vLLM

### 2.1 서버 설정

**포트**: 8002 (외부) → 8000 (내부 컨테이너)  
**기본 URL**: `http://server-a:8002` 또는 `http://localhost:8002`  
**API 표준**: OpenAI 호환 API

### 2.2 Docker Compose 설정

```yaml
# docker-compose.yml (vLLM 사용 시)
services:
  vllm-server:
    image: vllm/vllm-openai:latest
    container_name: vllm-server
    ports:
      - "8002:8000"
    command:
      - unsloth/gemma-3-27b-it-bnb-4bit
      - --tensor-parallel-size 1
      - --dtype auto
      - --quantization bitsandbytes
      - --max-model-len 4096
```

### 2.3 API 엔드포인트

#### `POST /v1/chat/completions`

**요청 형식**:
```json
{
  "model": "unsloth/gemma-3-27b-it-bnb-4bit",
  "messages": [
    {"role": "system", "content": "당신은 친절한 AI 어시스턴트입니다."},
    {"role": "user", "content": "안녕하세요"}
  ],
  "max_tokens": 512,
  "temperature": 0.7
}
```

**응답 형식**:
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "unsloth/gemma-3-27b-it-bnb-4bit",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "안녕하세요! 무엇을 도와드릴까요?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

#### `GET /v1/models`

**응답 형식**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "unsloth/gemma-3-27b-it-bnb-4bit",
      "object": "model",
      "created": 1769364590,
      "owned_by": "vllm"
    }
  ]
}
```

---

## 3. 케이스 B: Ollama

### 3.1 서버 설정

**포트**: 11434  
**기본 URL**: `http://server-a:11434` 또는 `http://localhost:11434`  
**API 표준**: Ollama 자체 API

### 3.2 Docker Compose 설정

```yaml
# docker-compose.yml (Ollama 사용 시)
services:
  ollama-server:
    image: ollama/ollama:latest
    container_name: ollama-server
    ports:
      - "11434:11434"
    volumes:
      - /mnt/shared_models/llm/gemma-3-27b-it-GGUF:/models:ro
      - ollama-data:/root/.ollama
```

### 3.3 모델 등록

```bash
# Ollama 실행 후 모델 등록
docker exec -it ollama-server ollama create gemma-3-27b-it -f /models/gemma-3-27b-it-UD-Q4_K_XL.gguf
```

### 3.4 API 엔드포인트

**⚠️ 중요**: 채팅 기능에는 `/api/chat`를 사용합니다. `/api/generate`는 단순 프롬프트만 지원하므로 채팅에 부적합합니다.

#### `POST /api/chat` ✅ **채팅용 (권장)**

**요청 형식**:
```json
{
  "model": "gemma-3-27b-it",
  "messages": [
    {"role": "system", "content": "당신은 친절한 AI 어시스턴트입니다."},
    {"role": "user", "content": "안녕하세요"}
  ],
  "stream": false,
  "options": {
    "temperature": 0.7,
    "num_predict": 512
  }
}
```

**응답 형식**:
```json
{
  "model": "gemma-3-27b-it",
  "created_at": "2026-01-26T12:00:00Z",
  "message": {
    "role": "assistant",
    "content": "안녕하세요! 무엇을 도와드릴까요?"
  },
  "done": true,
  "total_duration": 1234567890,
  "load_duration": 1234567,
  "prompt_eval_count": 10,
  "prompt_eval_duration": 1234567,
  "eval_count": 20,
  "eval_duration": 1234567890
}
```

#### `GET /api/tags`

**응답 형식** (공식 문서 기준):
```json
{
  "models": [
    {
      "name": "gemma-3-27b-it",
      "modified_at": "2026-01-26T12:00:00Z",
      "size": 16800000000,
      "digest": "sha256:abc123...",
      "details": {
        "format": "gguf",
        "family": "gemma",
        "families": ["gemma"],
        "parameter_size": "27B",
        "quantization_level": "Q4_K_XL"
      }
    }
  ]
}
```

#### `POST /api/generate` ⚠️ **참고용 (채팅에는 사용하지 않음)**

**용도**: 단순 프롬프트 기반 텍스트 생성 (메시지 히스토리 미지원)

**요청 형식**:
```json
{
  "model": "gemma-3-27b-it",
  "prompt": "안녕하세요",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "num_predict": 512
  }
}
```

**응답 형식**:
```json
{
  "model": "gemma-3-27b-it",
  "created_at": "2026-01-26T12:00:00Z",
  "response": "안녕하세요! 무엇을 도와드릴까요?",
  "done": true,
  "prompt_eval_count": 10,
  "eval_count": 20
}
```

**⚠️ 주의**: `/api/generate`는 `prompt`만 사용하고 `messages`를 지원하지 않으므로, 채팅 기능에는 `/api/chat`를 사용해야 합니다.

---

## 4. API 차이점 비교

### 4.1 엔드포인트 비교

| 기능 | vLLM | Ollama |
|------|------|--------|
| **채팅 완료** | `POST /v1/chat/completions` | `POST /api/chat` (권장) |
| **텍스트 생성** | `POST /v1/completions` | `POST /api/generate` (단순 프롬프트만) |
| **모델 목록** | `GET /v1/models` | `GET /api/tags` |
| **헬스체크** | `GET /health` | `GET /api/version` |

### 4.2 요청 형식 비교

#### vLLM 요청
```json
{
  "model": "unsloth/gemma-3-27b-it-bnb-4bit",
  "messages": [...],
  "temperature": 0.7,
  "max_tokens": 512
}
```

#### Ollama 요청
```json
{
  "model": "gemma-3-27b-it",
  "messages": [...],
  "stream": false,
  "options": {
    "temperature": 0.7,
    "num_predict": 512
  }
}
```

**주요 차이점**:
- vLLM: `max_tokens` 직접 사용
- Ollama: `options.num_predict` 사용
- Ollama: `stream` 필드 필수

### 4.3 응답 형식 비교

#### vLLM 응답
```json
{
  "choices": [{
    "message": {"role": "assistant", "content": "..."}
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20
  }
}
```

#### Ollama 응답
```json
{
  "message": {"role": "assistant", "content": "..."},
  "prompt_eval_count": 10,
  "eval_count": 20
}
```

**주요 차이점**:
- vLLM: `choices[0].message.content`
- Ollama: `message.content`
- vLLM: `usage.prompt_tokens`, `usage.completion_tokens`
- Ollama: `prompt_eval_count`, `eval_count`

---

## 5. Backend 구현 차이점

### 5.1 Server B Backend 코드 수정 필요

**위치**: `server-b/backend/app/api/chat.py`

#### 케이스 A: vLLM 사용

```python
# 환경 변수
LLM_SERVICE = os.getenv("LLM_SERVICE", "vllm")
LLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://server-a:8002")

# API 호출
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{LLM_BASE_URL}/v1/chat/completions",
        json={
            "model": request.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        },
        timeout=60.0
    )
    result = response.json()
    
    # 응답 파싱
    content = result["choices"][0]["message"]["content"]
    usage = {
        "prompt_tokens": result["usage"]["prompt_tokens"],
        "completion_tokens": result["usage"]["completion_tokens"]
    }
```

#### 케이스 B: Ollama 사용

```python
# 환경 변수
LLM_SERVICE = os.getenv("LLM_SERVICE", "ollama")
LLM_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://server-a:11434")

# API 호출
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{LLM_BASE_URL}/api/chat",
        json={
            "model": request.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens
            }
        },
        timeout=60.0
    )
    result = response.json()
    
    # 응답 파싱 (변환 필요)
    content = result["message"]["content"]
    usage = {
        "prompt_tokens": result.get("prompt_eval_count", 0),
        "completion_tokens": result.get("eval_count", 0)
    }
```

### 5.2 통합 구현 예시

```python
# server-b/backend/app/api/chat.py
import os
import httpx
from typing import List, Dict, Any

LLM_SERVICE = os.getenv("LLM_SERVICE", "vllm")  # "vllm" 또는 "ollama"

if LLM_SERVICE == "vllm":
    LLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://server-a:8002")
    LLM_API_PATH = "/v1/chat/completions"
elif LLM_SERVICE == "ollama":
    LLM_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://server-a:11434")
    LLM_API_PATH = "/api/chat"
else:
    raise ValueError(f"Unknown LLM_SERVICE: {LLM_SERVICE}")

async def call_llm_service(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 512
) -> Dict[str, Any]:
    """LLM 서비스 호출 (케이스별 분기)"""
    
    async with httpx.AsyncClient() as client:
        if LLM_SERVICE == "vllm":
            # 케이스 A: vLLM OpenAI API 호환
            response = await client.post(
                f"{LLM_BASE_URL}{LLM_API_PATH}",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=60.0
            )
            result = response.json()
            return {
                "content": result["choices"][0]["message"]["content"],
                "usage": {
                    "prompt_tokens": result["usage"]["prompt_tokens"],
                    "completion_tokens": result["usage"]["completion_tokens"]
                }
            }
        
        elif LLM_SERVICE == "ollama":
            # 케이스 B: Ollama API
            response = await client.post(
                f"{LLM_BASE_URL}{LLM_API_PATH}",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=60.0
            )
            result = response.json()
            return {
                "content": result["message"]["content"],
                "usage": {
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0)
                }
            }
```

---

## 6. 환경 변수 설정

### 6.1 Server B Backend 환경 변수

**파일**: `server-b/backend/.env`

#### 케이스 A: vLLM 사용

```bash
# LLM 서비스 선택
LLM_SERVICE=vllm

# vLLM 서버 URL
VLLM_BASE_URL=http://server-a:8002
```

#### 케이스 B: Ollama 사용

```bash
# LLM 서비스 선택
LLM_SERVICE=ollama

# Ollama 서버 URL
OLLAMA_BASE_URL=http://server-a:11434
```

### 6.2 Server A Docker Compose

#### 케이스 A: vLLM 실행

```bash
docker-compose --profile vllm up -d vllm-server
```

#### 케이스 B: Ollama 실행

```bash
docker-compose --profile ollama up -d ollama-server
```

---

## 7. 요약

### 주요 차이점

1. **API 엔드포인트**:
   - vLLM: `/v1/chat/completions` (OpenAI 호환)
   - Ollama: `/api/chat` (Ollama 자체)

2. **요청 형식**:
   - vLLM: `max_tokens` 직접 사용
   - Ollama: `options.num_predict` 사용

3. **응답 형식**:
   - vLLM: `choices[0].message.content`
   - Ollama: `message.content`

4. **토큰 사용량**:
   - vLLM: `usage.prompt_tokens`, `usage.completion_tokens`
   - Ollama: `prompt_eval_count`, `eval_count`

5. **포트**:
   - vLLM: 8002
   - Ollama: 11434

### 구현 시 주의사항

1. **환경 변수로 선택**: `LLM_SERVICE=vllm` 또는 `LLM_SERVICE=ollama`
2. **응답 파싱 분기**: 케이스별로 다른 응답 형식 처리
3. **토큰 사용량 변환**: Ollama의 경우 필드명 변환 필요
4. **모델 이름**: vLLM은 Hugging Face 모델 ID, Ollama는 등록된 모델 이름 사용

---

**참고 문서**:
- **Ollama 공식 문서**: https://docs.ollama.com/api/introduction
- `docs/PROJECT_API_SUMMARY.md` - API 명세서
- `docs/FINALFINAL.md` - 통합 명세서
- `docs/Backend_프로젝트_현황_명세서.md` - Backend 구현 명세서
