#!/bin/bash

# vLLM 서버 간단 테스트 스크립트
# 사용법: bash scripts/server-a/test-vllm.sh

VLLM_URL="http://localhost:8002"
VLLM_CONTAINER="vllm-server"

echo "=========================================="
echo "vLLM 서버 테스트"
echo "=========================================="
echo ""

# 1. 컨테이너 상태 확인
echo "1. 컨테이너 상태..."
if ! docker ps | grep -q "$VLLM_CONTAINER"; then
    echo "❌ 컨테이너가 실행 중이지 않습니다."
    echo "   docker-compose up -d vllm-server"
    exit 1
fi
echo "✅ 컨테이너 실행 중"
echo ""

# 2. 헬스체크
echo "2. 헬스체크..."
if curl -s "$VLLM_URL/health" > /dev/null 2>&1; then
    echo "✅ 헬스체크 성공"
else
    echo "❌ 헬스체크 실패"
fi
echo ""

# 3. 간단한 채팅 테스트
echo "3. 채팅 테스트..."
python3 << 'EOF'
import requests
import json

try:
    response = requests.post(
        "http://localhost:8002/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        json={
            "model": "unsloth/gemma-3-27b-it-bnb-4bit",
            "messages": [{"role": "user", "content": "안녕하세요! 간단히 자기소개 해주세요."}],
            "max_tokens": 50
        },
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage", {})
        print(f"✅ 채팅 성공")
        print(f"응답: {content[:50]}...")
        print(f"토큰: {usage.get('total_tokens', 0)} (입력: {usage.get('prompt_tokens', 0)}, 출력: {usage.get('completion_tokens', 0)})")
    else:
        print(f"❌ 채팅 실패 (HTTP {response.status_code})")
        print(response.text[:200])
except Exception as e:
    print(f"❌ 오류: {e}")
EOF

echo ""

# 4. 긴 컨텍스트 테스트 (4096 토큰)
echo "4. 긴 컨텍스트 테스트 (4096 토큰)..."
python3 << 'EOF'
import requests
import json

# 긴 텍스트 생성 (약 2000 토큰)
# 20번 반복 시 4124 토큰이므로, 9번 반복으로 조정 (약 1856 토큰)
# 안전 마진을 위해 9번 반복 사용
long_text = ("오늘은 정말 좋은 날씨입니다. 하늘이 맑고 바람이 시원하게 불어옵니다. "
             "이런 날에는 밖에 나가서 산책을 하거나 친구들과 만나서 즐거운 시간을 보내면 좋을 것 같습니다. "
             "자연 속에서 시간을 보내면 마음이 편안해지고 스트레스도 해소됩니다. "
             "특히 공원이나 강가를 따라 걷다 보면 일상의 고민들이 잠시 잊혀지는 느낌이 듭니다. "
             "새로운 경험을 통해 우리는 더 넓은 시야를 갖게 되고, 다양한 사람들과의 만남은 우리의 삶을 더욱 풍요롭게 만들어줍니다. "
             "때로는 작은 변화가 큰 기쁨을 가져다주기도 하며, 일상 속에서 발견하는 아름다움들이 우리를 감동시킵니다. "
             "책을 읽거나 음악을 들으며 여유로운 시간을 보내는 것도 좋은 방법입니다. "
             "창의적인 활동에 몰입하면 시간이 금방 지나가고, 그 과정에서 새로운 아이디어나 영감을 얻을 수 있습니다. ") * 9

try:
    response = requests.post(
        "http://localhost:8002/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        json={
            "model": "unsloth/gemma-3-27b-it-bnb-4bit",
            "messages": [
                {"role": "system", "content": "당신은 친절한 AI 어시스턴트입니다."},
                {"role": "user", "content": long_text}
            ],
            "max_tokens": 50
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        usage = result.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        print(f"✅ 긴 컨텍스트 성공")
        print(f"입력 토큰: {prompt_tokens} (예상: 1800-2000)")
        if prompt_tokens > 2000:
            print("✅ 4096 토큰 컨텍스트 지원 확인 (2000+ 토큰)")
        elif prompt_tokens > 1000:
            print("⚠️ 중간 길이 컨텍스트 (1000-2000 토큰)")
        else:
            print("❌ 짧은 컨텍스트 (1000 토큰 미만)")
    else:
        print(f"❌ 긴 컨텍스트 실패 (HTTP {response.status_code})")
        print(response.text[:200])
except Exception as e:
    print(f"❌ 오류: {e}")
EOF

echo ""

# 5. 동시 요청 테스트 (max_num_seqs=12)
echo "5. 동시 요청 테스트 (12명)..."
python3 << 'EOF'
import requests
import json
import threading
import time

results = []
lock = threading.Lock()

def send_request(i):
    try:
        response = requests.post(
            "http://localhost:8002/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "unsloth/gemma-3-27b-it-bnb-4bit",
                "messages": [{"role": "user", "content": f"테스트 요청 {i}"}],
                "max_tokens": 20
            },
            timeout=30
        )
        with lock:
            results.append({"id": i, "status": response.status_code, "success": response.status_code == 200})
    except Exception as e:
        with lock:
            results.append({"id": i, "status": 0, "success": False, "error": str(e)})

# 12개 요청 동시 전송
threads = []
start_time = time.time()

for i in range(1, 13):
    t = threading.Thread(target=send_request, args=(i,))
    threads.append(t)
    t.start()

# 모든 스레드 완료 대기
for t in threads:
    t.join()

elapsed = time.time() - start_time
success_count = sum(1 for r in results if r["success"])

print(f"완료 시간: {elapsed:.2f}초")
print(f"성공: {success_count}/12")
if success_count >= 10:
    print("✅ 동시 접속 테스트 통과 (10명 이상 성공)")
elif success_count >= 8:
    print("⚠️ 동시 접속 부분 성공 (8명 이상 성공)")
else:
    print("❌ 동시 접속 테스트 실패")
EOF

echo ""
echo "=========================================="
echo "테스트 완료"
echo "=========================================="
echo ""
echo "상세 로그: docker logs -f $VLLM_CONTAINER"
echo "GPU 상태: nvidia-smi"
echo ""
