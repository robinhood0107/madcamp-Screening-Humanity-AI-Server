# 📘 GPT-SoVITS WebAPI 통합 문서

**작성일**: 2026-01-26  
**프로젝트 사용 현황**: Server A (GPU 서버)에서 실행, Server B Backend가 내부 호출

---

## 📋 프로젝트에서 사용하는 API

### ✅ 사용 중인 API

1. **`POST /tts`** - 텍스트-음성 변환
   - **호출자**: Server B Backend (`POST /api/tts`)
   - **상태**: 사용 중

2. **`GET /tts`** - 텍스트-음성 변환 (GET 방식)
   - **호출자**: 직접 호출 또는 테스트용
   - **상태**: 사용 가능

### ⚠️ 미사용 API (관리용)

3. **`GET /set_gpt_weights`** - GPT 모델 변경
   - **상태**: 관리용, 현재 미사용

4. **`GET /set_sovits_weights`** - SoVITS 모델 변경
   - **상태**: 관리용, 현재 미사용

5. **`GET /control?command=restart`** - 서버 재시작
   - **상태**: 관리용, 현재 미사용

---

## 1. 서버 실행 (Server Startup)

터미널에서 아래 명령어로 서버를 시작합니다.

```bash
python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml

```

**실행 파라미터:**

* `-a`: 바인딩 IP 주소 (기본값: `127.0.0.1`)
* `-p`: 바인딩 포트 (기본값: `9880`)
* `-c`: TTS 설정 파일 경로 (기본값: `GPT_SoVITS/configs/tts_infer.yaml`)

---

## 2. 텍스트 음성 변환 (Text-to-Speech)

**Endpoint:** `/tts`

**Method:** `GET` / `POST`

### 📤 POST 요청 (권장)

복잡한 설정을 세밀하게 제어하려면 POST 방식을 권장합니다.

**Request Body (JSON):**

```json
{
    // --- 필수 입력 항목 ---
    "text": "안녕하세요, 반갑습니다.",      // 합성할 텍스트
    "text_lang": "ko",                   // 텍스트 언어 (zh, en, ja, ko 등)
    "ref_audio_path": "path/to/ref.wav", // 참조 오디오 파일 경로 (서버 내부 경로)
    "prompt_lang": "ko",                 // 참조 오디오의 언어
    
    // --- 참조 오디오 관련 (선택) ---
    "prompt_text": "",                   // 참조 오디오의 텍스트 (비워두면 자동 인식 시도하지만, 입력 권장)
    "aux_ref_audio_paths": [],           // 다화자 톤 융합을 위한 추가 참조 오디오 경로 리스트

    // --- 추론 및 품질 설정 ---
    "top_k": 5,                          // Top-K 샘플링 (기본값: 5)
    "top_p": 1,                          // Top-P 샘플링 (기본값: 1)
    "temperature": 1,                    // 샘플링 온도 (기본값: 1)
    "repetition_penalty": 1.35,          // 반복 패널티 (T2S 모델, 기본값: 1.35)
    "batch_size": 1,                     // 추론 배치 크기 (기본값: 1)
    "speed_factor": 1.0,                 // 발화 속도 조절 (1.0 = 정속)
    "seed": -1,                          // 랜덤 시드 (-1 = 무작위)
    "parallel_infer": true,              // 병렬 추론 사용 여부 (기본값: true)

    // --- 텍스트 처리 ---
    "text_split_method": "cut5",         // 텍스트 분할 방식 (cut0, cut1, cut2, cut3, cut4, cut5)
    "batch_threshold": 0.75,             // 배치 분할 임계값 (기본값: 0.75)
    "split_bucket": true,                // 배치를 버킷으로 나눌지 여부 (기본값: true)

    // --- 출력 형식 및 스트리밍 ---
    "media_type": "wav",                 // 응답 포맷 ("wav", "ogg", "aac", "raw")
    "streaming_mode": 0,                 // 스트리밍 모드 설정 (아래 상세 설명 참조)
    
    // --- 스트리밍 세부 설정 (streaming_mode 켜짐 시) ---
    "overlap_length": 2,                 // 스트리밍 시맨틱 토큰 중첩 길이 (기본값: 2)
    "min_chunk_length": 16,              // 스트리밍 최소 청크 길이 (기본값: 16)
    "fragment_interval": 0.3,            // 오디오 조각 간격 제어 (기본값: 0.3)

    // --- VITS 모델 고급 설정 ---
    "sample_steps": 32,                  // VITS 모델 샘플링 스텝 수 (기본값: 32)
    "super_sampling": false              // VITS 초해상도(Super Sampling) 사용 여부 (기본값: false)
}

```

#### 💡 `streaming_mode` 상세 옵션

* `0` (False): 비활성화 (전체 생성 후 반환)
* `1` (True): **고품질** 스트리밍 (응답 속도 느림, 구버전 방식)
* `2`: **중간 품질** 스트리밍 (응답 속도 보통)
* `3`: **저품질** 스트리밍 (응답 속도 매우 빠름)

---

### 📥 GET 요청 (간편 테스트용)

```
http://127.0.0.1:9880/tts?text=테스트입니다&text_lang=ko&ref_audio_path=123.wav&prompt_lang=ko&text_split_method=cut5&batch_size=1&media_type=wav&streaming_mode=0

```

---

## 3. 모델 관리 (Model Management)

실행 중인 모델(가중치)을 실시간으로 교체합니다.

### GPT 모델 변경

**Endpoint:** `/set_gpt_weights`

**Method:** `GET`

```
http://127.0.0.1:9880/set_gpt_weights?weights_path=GPT_SoVITS/pretrained_models/s1bert25hz.ckpt

```

### SoVITS 모델 변경

**Endpoint:** `/set_sovits_weights`

**Method:** `GET`

```
http://127.0.0.1:9880/set_sovits_weights?weights_path=GPT_SoVITS/pretrained_models/s2G488k.pth

```

---

## 4. 시스템 제어 (System Control)

**Endpoint:** `/control`

**Method:** `GET` / `POST`

**명령어 (command):**

* `restart`: 서버 재시작 (모델 리로드 등 필요 시)
* `exit`: 서버 프로세스 종료

**GET 예시:**

```
http://127.0.0.1:9880/control?command=restart

```

---

## 5. 응답 (Responses)

* **성공 (Success):**
* `/tts`: 오디오 바이너리 스트림 (wav, ogg, aac 등) 반환 (HTTP 200)
* 그 외: `{"message": "success"}` JSON 반환 (HTTP 200)


* **실패 (Failure):**
* 오류 메시지가 포함된 JSON 반환 (HTTP 400)
* 예: `{"message": "ref_audio_path is required"}`