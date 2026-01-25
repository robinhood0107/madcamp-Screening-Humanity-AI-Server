# vLLM 서버 테스트 가이드

**작성일**: 2026-01-26  
**대상**: Server A (GPU 서버)

---

## 빠른 테스트 (자동 스크립트)

```bash
# 줄바꿈 문제 해결 (Windows에서 생성된 경우)
# Linux 서버에서 실행:
sed -i 's/\r$//' scripts/server-a/test-vllm.sh

# 또는 dos2unix 사용:
dos2unix scripts/server-a/test-vllm.sh

# 테스트 스크립트 실행
bash scripts/server-a/test-vllm.sh
```

이 스크립트는 다음을 자동으로 테스트합니다:
1. Docker 컨테이너 상태 확인
2. 헬스체크
3. 간단한 채팅 테스트

**⚠️ 줄바꿈 오류 발생 시**:
```bash
# Linux 서버에서 실행
sed -i 's/\r$//' scripts/server-a/test-vllm.sh
chmod +x scripts/server-a/test-vllm.sh
bash scripts/server-a/test-vllm.sh
```

---

## 수동 테스트 방법

### 1. 컨테이너 상태 확인

```bash
# 컨테이너 실행 확인
docker ps | grep vllm-server

# 컨테이너 로그 확인 (실시간)
docker logs -f vllm-server

# 최근 로그만 확인
docker logs --tail 50 vllm-server
```

### 2. GPU 메모리 확인

```bash
# 현재 GPU 메모리 사용량
nvidia-smi

# 실시간 모니터링 (1초마다 업데이트)
watch -n 1 nvidia-smi
```

**예상 메모리 사용량**:
- GPT-SoVITS: ~2GB
- vLLM 모델 가중치: ~14GB (4-bit 양자화)
- KV Cache: ~8GB (gpu_memory_utilization 0.82)
- 총 사용: ~24GB

### 3. 헬스체크

```bash
# 기본 헬스체크
curl http://localhost:8002/health

# 상세 정보 포함
curl -v http://localhost:8002/health
```

**예상 응답**:
```json
{
  "status": "ok"
}
```

### 4. 모델 목록 조회

```bash
# OpenAI 호환 API
curl http://localhost:8002/v1/models

# JSON 포맷팅
curl http://localhost:8002/v1/models | python3 -m json.tool
```

**예상 응답**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "unsloth/gemma-3-27b-it-bnb-4bit",
      "object": "model",
      "created": 1234567890,
      "owned_by": "unsloth"
    }
  ]
}
```

---

## vLLM API 엔드포인트 목록

**작성일**: 2026-01-26  
**참고**: vLLM은 OpenAI 호환 API를 제공합니다. 기본 URL은 `http://localhost:8002` (또는 설정한 포트)입니다.

### OpenAI 호환 API

#### 1. **Chat Completions API** (`POST /v1/chat/completions`) ⭐ **현재 프로젝트에서 사용 중**
- **용도**: 채팅 템플릿이 있는 텍스트 생성 모델용
- **현재 사용**: `unsloth/gemma-3-27b-it-bnb-4bit` 모델로 채팅 응답 생성
- **예시**:
  ```bash
  curl -X POST http://localhost:8002/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
      "model": "unsloth/gemma-3-27b-it-bnb-4bit",
      "messages": [{"role": "user", "content": "안녕하세요"}],
      "max_tokens": 100
    }'
  ```

#### 2. **Completions API** (`POST /v1/completions`)
- **용도**: 텍스트 생성 모델용 (채팅 템플릿 없음)
- **참고**: `suffix` 파라미터는 지원하지 않음

#### 3. **Responses API** (`POST /v1/responses`)
- **용도**: 텍스트 생성 모델용 (OpenAI Responses API 호환)

#### 4. **Embeddings API** (`POST /v1/embeddings`)
- **용도**: 임베딩 모델용
- **참고**: Pooling 모델이 필요함

#### 5. **Transcriptions API** (`POST /v1/audio/transcriptions`)
- **용도**: 자동 음성 인식 (ASR) 모델용
- **참고**: `pip install vllm[audio]` 필요
- **지원 형식**: FLAC, MP3, MP4, MPEG, MPGA, M4A, OGG, WAV, WEBM

#### 6. **Translations API** (`POST /v1/audio/translations`)
- **용도**: 음성 번역 (ASR 모델용, 비영어 → 영어)
- **참고**: `pip install vllm[audio]` 필요

### 커스텀 API

#### 7. **Tokenizer API** (`POST /tokenize`, `POST /detokenize`)
- **용도**: 토크나이저 인코딩/디코딩
- **예시**:
  ```bash
  # 토크나이즈
  curl -X POST http://localhost:8002/tokenize \
    -H "Content-Type: application/json" \
    -d '{"text": "안녕하세요"}'
  
  # 디토크나이즈
  curl -X POST http://localhost:8002/detokenize \
    -H "Content-Type: application/json" \
    -d '{"token_ids": [1, 2, 3]}'
  ```

#### 8. **Pooling API** (`POST /pooling`)
- **용도**: Pooling 모델로 입력 프롬프트 인코딩
- **참고**: Pooling 모델이 필요함

#### 9. **Classification API** (`POST /classify`)
- **용도**: 시퀀스 분류 모델용
- **예시**:
  ```bash
  curl -X POST http://localhost:8002/classify \
    -H "Content-Type: application/json" \
    -d '{
      "model": "jason9693/Qwen2.5-1.5B-apeach",
      "input": "Loved the new café—coffee was great."
    }'
  ```

#### 10. **Score API** (`POST /score`)
- **용도**: Cross-encoder 또는 Embedding 모델로 문장/멀티모달 쌍의 점수 예측
- **예시**:
  ```bash
  curl -X POST http://localhost:8002/score \
    -H "Content-Type: application/json" \
    -d '{
      "model": "BAAI/bge-reranker-v2-m3",
      "text_1": "What is the capital of France?",
      "text_2": "The capital of France is Paris."
    }'
  ```

#### 11. **Re-rank API** (`POST /rerank`, `POST /v1/rerank`, `POST /v2/rerank`)
- **용도**: 쿼리와 문서 리스트 간 관련성 점수 예측
- **참고**: Jina AI 및 Cohere API 호환
- **예시**:
  ```bash
  curl -X POST http://localhost:8002/v1/rerank \
    -H "Content-Type: application/json" \
    -d '{
      "model": "BAAI/bge-reranker-base",
      "query": "What is the capital of France?",
      "documents": [
        "The capital of Brazil is Brasilia.",
        "The capital of France is Paris."
      ]
    }'
  ```

### 시스템 API

#### 12. **Health Check** (`GET /health`)
- **용도**: 서버 상태 확인
- **예시**:
  ```bash
  curl http://localhost:8002/health
  ```
- **응답**:
  ```json
  {"status": "ok"}
  ```

#### 13. **Models List** (`GET /v1/models`)
- **용도**: 사용 가능한 모델 목록 조회
- **예시**:
  ```bash
  curl http://localhost:8002/v1/models
  ```

---

### 현재 프로젝트에서 사용 중인 API

현재 프로젝트에서는 다음 API만 사용 중입니다:

1. **`POST /v1/chat/completions`** - Server B Backend에서 Server A vLLM으로 채팅 요청 전송
2. **`GET /health`** - 헬스체크 (선택적)
3. **`GET /v1/models`** - 모델 목록 조회 (선택적)

다른 API는 향후 필요 시 추가로 활용할 수 있습니다.

---

### 참고 자료

- **vLLM 공식 문서**: https://docs.vllm.ai/en/stable/serving/openai_compatible_server.html
- **OpenAI API 문서**: https://platform.openai.com/docs/api-reference

### 5. 간단한 채팅 테스트

```bash
curl -X POST http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "unsloth/gemma-3-27b-it-bnb-4bit",
    "messages": [
      {"role": "user", "content": "안녕하세요! 간단히 자기소개 해주세요."}
    ],
    "max_tokens": 100,
    "temperature": 0.7
  }' | python3 -m json.tool
```

**예상 응답**:
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "unsloth/gemma-3-27b-it-bnb-4bit",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "안녕하세요! 저는 AI 어시스턴트입니다..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 45,
    "total_tokens": 70
  }
}
```

### 6. 긴 컨텍스트 테스트 (4096 토큰)

**방법 1: Python 스크립트 사용 (권장)**

```bash
# Python으로 전체 요청 생성 및 전송
python3 << 'EOF'
import requests
import json

# 긴 텍스트 생성 (약 2000 토큰)
long_text = "안녕하세요! " * 200

# 요청 데이터
data = {
    "model": "unsloth/gemma-3-27b-it-bnb-4bit",
    "messages": [
        {"role": "system", "content": "당신은 친절한 AI 어시스턴트입니다."},
        {"role": "user", "content": long_text}
    ],
    "max_tokens": 50,
    "temperature": 0.7
}

# 요청 전송
response = requests.post(
    "http://localhost:8002/v1/chat/completions",
    headers={"Content-Type": "application/json"},
    json=data
)

# 응답 출력
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
EOF
```

**방법 2: 변수 사용 (주의 필요)**

```bash
# 긴 텍스트 생성 (변수에 저장)
LONG_TEXT=$(python3 -c "print('안녕하세요! ' * 200)")

# JSON 파일 생성 (더 안전)
cat > /tmp/test_request.json << EOF
{
  "model": "unsloth/gemma-3-27b-it-bnb-4bit",
  "messages": [
    {"role": "system", "content": "당신은 친절한 AI 어시스턴트입니다."},
    {"role": "user", "content": "$LONG_TEXT"}
  ],
  "max_tokens": 50,
  "temperature": 0.7
}
EOF

# 파일에서 요청 전송
curl -X POST http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d @/tmp/test_request.json | python3 -m json.tool

# 임시 파일 정리
rm -f /tmp/test_request.json
```

**방법 3: jq 사용 (JSON 안전하게 생성)**

```bash
# jq가 설치되어 있는 경우
LONG_TEXT=$(python3 -c "print('안녕하세요! ' * 200)")

jq -n \
  --arg model "unsloth/gemma-3-27b-it-bnb-4bit" \
  --arg long_text "$LONG_TEXT" \
  '{
    model: $model,
    messages: [
      {role: "system", content: "당신은 친절한 AI 어시스턴트입니다."},
      {role: "user", content: $long_text}
    ],
    max_tokens: 50,
    temperature: 0.7
  }' | curl -X POST http://localhost:8002/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d @- | python3 -m json.tool
```

**확인 사항**:
- `prompt_tokens`가 2000 이상인지 확인
- 응답이 정상적으로 생성되는지 확인
- OOM 에러가 발생하지 않는지 확인

### 7. 동시 요청 테스트 (max_num_seqs=12)

```bash
# 동시에 10개의 요청 전송
for i in {1..10}; do
  curl -X POST http://localhost:8002/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"unsloth/gemma-3-27b-it-bnb-4bit\",
      \"messages\": [{\"role\": \"user\", \"content\": \"테스트 요청 $i\"}],
      \"max_tokens\": 20
    }" > /tmp/vllm_response_$i.json 2>&1 &
done

# 모든 요청 완료 대기
wait

# 결과 확인
for i in {1..10}; do
  echo "요청 $i:"
  cat /tmp/vllm_response_$i.json | python3 -m json.tool 2>/dev/null || cat /tmp/vllm_response_$i.json
  echo ""
done

# 임시 파일 정리
rm -f /tmp/vllm_response_*.json
```

**확인 사항**:
- 최소 10개 이상의 요청이 성공해야 함
- 일부 요청이 대기 상태일 수 있음 (정상)
- 모든 요청이 200 응답을 받아야 함

### 8. 설정 확인 (로그에서)

```bash
# 컨테이너 로그에서 설정 확인
docker logs vllm-server 2>&1 | grep -E "max_model_len|gpu_memory_utilization|max_num_seqs"
```

**예상 출력**:
```
INFO ... Using max model len 4096
INFO ... gpu_memory_utilization: 0.82
INFO ... max_num_seqs: 12
```

---

## 문제 해결

### 컨테이너가 시작되지 않음

```bash
# 컨테이너 로그 확인
docker logs vllm-server

# 컨테이너 재시작
docker-compose restart vllm-server

# 컨테이너 재생성
docker-compose up -d --force-recreate vllm-server
```

### CUDA out of memory 에러

```bash
# GPU 메모리 확인
nvidia-smi

# 다른 프로세스가 메모리를 사용 중인지 확인
nvidia-smi | grep -E "Process|PID"

# 필요시 GPT-SoVITS 중지 후 vLLM만 실행
# 또는 docker-compose.yml에서 설정 조정:
# - max_num_seqs를 10으로 낮춤
# - gpu_memory_utilization을 0.80으로 낮춤
```

### 연결 거부 (Connection refused)

```bash
# 포트 확인
netstat -tuln | grep 8002

# 컨테이너 내부에서 포트 확인
docker exec vllm-server netstat -tuln | grep 8000

# 컨테이너 재시작
docker-compose restart vllm-server
```

### 모델을 찾을 수 없음

```bash
# Hugging Face 캐시 확인
ls -lh /root/.cache/huggingface/

# 모델 다운로드 확인
docker exec vllm-server ls -lh /root/.cache/huggingface/hub/

# HF_TOKEN 확인
echo $HF_TOKEN
```

---

## 성능 벤치마크

### 응답 시간 측정

```bash
# 단일 요청 응답 시간 측정
time curl -X POST http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "unsloth/gemma-3-27b-it-bnb-4bit",
    "messages": [{"role": "user", "content": "안녕하세요"}],
    "max_tokens": 100
  }' > /dev/null
```

**예상 응답 시간**:
- 첫 요청 (콜드 스타트): 2-5초
- 이후 요청 (웜 스타트): 0.5-2초

### 처리량 측정

```bash
# 1분간 요청 수 측정
for i in {1..60}; do
  curl -X POST http://localhost:8002/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"unsloth/gemma-3-27b-it-bnb-4bit\",
      \"messages\": [{\"role\": \"user\", \"content\": \"테스트 $i\"}],
      \"max_tokens\": 20
    }" > /dev/null 2>&1 &
  sleep 1
done
```

---

## 다음 단계

테스트가 성공하면:
1. ✅ Server A NPM 설정 (vLLM 프록시)
2. ✅ Server B Backend 연결 수정
3. ✅ Frontend 연동 테스트
4. ✅ Phase 5.2-5.4 구현 (컨텍스트 절약, 동시 접속 제한)

---

**참고**: 모든 테스트는 Server A에서 실행해야 합니다.
