# vLLM API 응답 해석 가이드

**작성일**: 2026-01-26

---

## 기본 응답 구조

vLLM은 OpenAI 호환 API를 제공하므로, 응답 형식이 OpenAI와 동일합니다.

### 전체 응답 예시

```json
{
    "id": "chatcmpl-b5bfd4fe028ed508",
    "object": "chat.completion",
    "created": 1769362372,
    "model": "unsloth/gemma-3-27b-it-bnb-4bit",
    "choices": [...],
    "usage": {...}
}
```

---

## 주요 필드 설명

### 1. `id`
- **타입**: 문자열
- **의미**: 이 채팅 완료 요청의 고유 ID
- **용도**: 로깅, 디버깅, 요청 추적
- **예시**: `"chatcmpl-b5bfd4fe028ed508"`

### 2. `object`
- **타입**: 문자열
- **의미**: 응답 객체 타입
- **값**: 항상 `"chat.completion"`

### 3. `created`
- **타입**: 정수 (Unix 타임스탬프)
- **의미**: 응답 생성 시간 (초 단위)
- **예시**: `1769362372` = 2026년 1월 26일

### 4. `model`
- **타입**: 문자열
- **의미**: 사용된 모델 ID
- **예시**: `"unsloth/gemma-3-27b-it-bnb-4bit"`

---

## `choices` 배열

각 요청은 하나 이상의 응답을 포함할 수 있습니다 (n > 1인 경우).

### `choices[0]` 구조

```json
{
    "index": 0,
    "message": {
        "role": "assistant",
        "content": "...",
        "refusal": null,
        "annotations": null,
        "audio": null,
        "function_call": null,
        "tool_calls": [],
        "reasoning": null,
        "reasoning_content": null
    },
    "logprobs": null,
    "finish_reason": "length",
    "stop_reason": null,
    "token_ids": null
}
```

### 주요 필드

#### `index`
- **타입**: 정수
- **의미**: 선택지 인덱스 (보통 0)

#### `message.role`
- **타입**: 문자열
- **의미**: 메시지 역할
- **값**: `"assistant"` (AI 응답)

#### `message.content` ⭐ 중요
- **타입**: 문자열
- **의미**: AI가 생성한 실제 응답 텍스트
- **주의**: Unicode 이스케이프 시퀀스가 포함될 수 있음

**Unicode 이스케이프 해석 방법**:

```bash
# Python으로 해석
python3 -c "import json; print(json.loads('\"\\uc548\\ub155\\ud558\\uc138\\uc694\"'))"
# 출력: 안녕하세요

# 또는 Python 스크립트
python3 << 'EOF'
import json
content = "\uc548\ub155\ud558\uc138\uc694! \uc800\ub294 \uad6c\uae00 \ub525\ub9c8\uc778\ub4dc\uc5d0\uc11c..."
print(content)
EOF
```

**실제 응답 내용**:
```
안녕하세요! 저는 구글 마인드에서 개발한 대화모델 언어 모델 Gemma입니다. 텍스트와 이미지를 입력으로 받아 텍스트만 출력할 수 있습니다. 오픈 웨이트 모델이면서, 누구나 자유롭게 사용할 수 있습니다. 

저는 다양한 작업을 수행할 수 있습니다. 예를 들어, 질문에 답변하고, 텍스트를 요약하고, 창의적인 글을 작성하는 등의 작업을 할 수 있습니다. 

만나서 반갑습니다! 😊
```

#### `finish_reason` ⭐ 중요
- **타입**: 문자열
- **의미**: 응답이 종료된 이유
- **가능한 값**:
  - `"stop"`: 정상 종료 (stop sequence 도달 또는 자연스러운 종료)
  - `"length"`: `max_tokens` 제한에 도달하여 종료
  - `"content_filter"`: 콘텐츠 필터에 의해 차단됨
  - `"function_call"`: 함수 호출 필요
  - `"tool_calls"`: 도구 호출 필요

**`"length"`인 경우**:
- `max_tokens` 설정값에 도달했음을 의미
- 응답이 잘렸을 수 있음
- 더 긴 응답이 필요하면 `max_tokens`를 늘려야 함

#### `message.refusal`
- **타입**: null 또는 객체
- **의미**: 모델이 요청을 거부한 경우 (안전 필터)

#### `message.tool_calls`
- **타입**: 배열
- **의미**: 함수/도구 호출이 필요한 경우

---

## `usage` 객체

토큰 사용량 정보를 제공합니다.

```json
{
    "prompt_tokens": 19,
    "total_tokens": 119,
    "completion_tokens": 100,
    "prompt_tokens_details": null
}
```

### 필드 설명

#### `prompt_tokens`
- **타입**: 정수
- **의미**: 입력 프롬프트에 사용된 토큰 수
- **예시**: `19` = 입력 메시지가 19 토큰

#### `completion_tokens`
- **타입**: 정수
- **의미**: 생성된 응답에 사용된 토큰 수
- **예시**: `100` = 응답이 100 토큰 (max_tokens 제한에 도달)

#### `total_tokens`
- **타입**: 정수
- **의미**: 총 사용된 토큰 수
- **계산**: `prompt_tokens + completion_tokens`
- **예시**: `119 = 19 + 100`

---

## 실제 응답 해석 예시

### 제공된 응답 분석

```json
{
    "id": "chatcmpl-b5bfd4fe028ed508",
    "model": "unsloth/gemma-3-27b-it-bnb-4bit",
    "choices": [{
        "message": {
            "content": "\uc548\ub155\ud558\uc138\uc694! \uc800\ub294..."
        },
        "finish_reason": "length"
    }],
    "usage": {
        "prompt_tokens": 19,
        "completion_tokens": 100,
        "total_tokens": 119
    }
}
```

### 해석 결과

1. **요청 ID**: `chatcmpl-b5bfd4fe028ed508`
2. **모델**: `unsloth/gemma-3-27b-it-bnb-4bit`
3. **AI 응답**: "안녕하세요! 저는 구글 마인드에서 개발한 대화모델 언어 모델 Gemma입니다..."
4. **종료 이유**: `"length"` - max_tokens(100)에 도달하여 종료됨
5. **토큰 사용량**:
   - 입력: 19 토큰
   - 출력: 100 토큰
   - 총: 119 토큰

### 문제점

- `finish_reason: "length"`는 응답이 잘렸을 수 있음을 의미
- 더 긴 응답이 필요하면 `max_tokens`를 늘려야 함

---

## 응답 처리 방법

### Python 예시

```python
import json

# API 응답 받기
response = requests.post(...)
data = response.json()

# 응답 추출
if data.get("choices"):
    choice = data["choices"][0]
    content = choice["message"]["content"]
    finish_reason = choice["finish_reason"]
    
    # Unicode 이스케이프 자동 해석됨 (Python은 자동 처리)
    print(f"AI 응답: {content}")
    print(f"종료 이유: {finish_reason}")
    
    # 토큰 사용량
    usage = data.get("usage", {})
    print(f"입력 토큰: {usage.get('prompt_tokens', 0)}")
    print(f"출력 토큰: {usage.get('completion_tokens', 0)}")
    print(f"총 토큰: {usage.get('total_tokens', 0)}")
    
    # 응답이 잘렸는지 확인
    if finish_reason == "length":
        print("⚠️ 응답이 max_tokens 제한에 도달했습니다.")
        print("더 긴 응답이 필요하면 max_tokens를 늘리세요.")
```

### JavaScript/TypeScript 예시

```typescript
// API 응답 받기
const response = await fetch(...);
const data = await response.json();

// 응답 추출
if (data.choices && data.choices.length > 0) {
    const choice = data.choices[0];
    const content = choice.message.content; // Unicode 자동 해석됨
    const finishReason = choice.finish_reason;
    
    console.log(`AI 응답: ${content}`);
    console.log(`종료 이유: ${finishReason}`);
    
    // 토큰 사용량
    const usage = data.usage || {};
    console.log(`입력 토큰: ${usage.prompt_tokens || 0}`);
    console.log(`출력 토큰: ${usage.completion_tokens || 0}`);
    console.log(`총 토큰: ${usage.total_tokens || 0}`);
    
    // 응답이 잘렸는지 확인
    if (finishReason === "length") {
        console.warn("⚠️ 응답이 max_tokens 제한에 도달했습니다.");
    }
}
```

### Bash/curl 예시

```bash
# JSON 응답 받기
RESPONSE=$(curl -X POST http://localhost:8002/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "unsloth/gemma-3-27b-it-bnb-4bit",
    "messages": [{"role": "user", "content": "안녕하세요"}],
    "max_tokens": 100
  }')

# Python으로 파싱 (Unicode 자동 해석)
echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'choices' in data and len(data['choices']) > 0:
    choice = data['choices'][0]
    print('AI 응답:', choice['message']['content'])
    print('종료 이유:', choice['finish_reason'])
    usage = data.get('usage', {})
    print(f\"토큰 사용량: {usage.get('prompt_tokens', 0)} 입력 + {usage.get('completion_tokens', 0)} 출력 = {usage.get('total_tokens', 0)} 총\")
"

# 또는 jq 사용 (Unicode는 수동 해석 필요)
echo "$RESPONSE" | jq -r '.choices[0].message.content'
echo "$RESPONSE" | jq -r '.choices[0].finish_reason'
echo "$RESPONSE" | jq '.usage'
```

---

## 일반적인 문제 해결

### 1. Unicode 이스케이프 시퀀스

**문제**: `\uc548\ub155\ud558\uc138\uc694` 같은 문자가 보임

**해결**:
- Python/JavaScript는 자동으로 해석함
- Bash에서는 `python3 -c "import json; print(json.loads('\"...\"'))"` 사용

### 2. `finish_reason: "length"`

**문제**: 응답이 중간에 잘림

**해결**:
```json
{
  "max_tokens": 200  // 기본값 512에서 더 늘림
}
```

### 3. 빈 응답

**문제**: `content`가 비어있음

**원인**:
- `finish_reason: "content_filter"` (콘텐츠 필터 차단)
- 모델 오류

**해결**:
- 로그 확인: `docker logs vllm-server`
- 다른 프롬프트 시도

### 4. 토큰 사용량 모니터링

**목적**: 비용/성능 최적화

```python
# 토큰 사용량 추적
total_prompt_tokens = 0
total_completion_tokens = 0

for response in responses:
    usage = response.get("usage", {})
    total_prompt_tokens += usage.get("prompt_tokens", 0)
    total_completion_tokens += usage.get("completion_tokens", 0)

print(f"총 사용: {total_prompt_tokens + total_completion_tokens} 토큰")
```

---

## 응답 검증 체크리스트

✅ **정상 응답 확인**:
- [ ] `choices` 배열이 비어있지 않음
- [ ] `message.content`가 존재함
- [ ] `finish_reason`이 `"stop"` 또는 `"length"`임
- [ ] `usage.total_tokens`가 0보다 큼

⚠️ **주의 필요**:
- [ ] `finish_reason: "length"` → `max_tokens` 늘리기 고려
- [ ] `finish_reason: "content_filter"` → 콘텐츠 필터 확인
- [ ] `usage.total_tokens`가 예상보다 큼 → 컨텍스트 길이 확인

❌ **에러 응답**:
- [ ] `error` 필드가 존재함 → 에러 메시지 확인
- [ ] HTTP 상태 코드가 200이 아님 → 로그 확인

---

## 참고

- **OpenAI API 문서**: https://platform.openai.com/docs/api-reference/chat
- **vLLM 문서**: https://docs.vllm.ai/
- **Unicode 이스케이프**: https://www.unicode.org/
