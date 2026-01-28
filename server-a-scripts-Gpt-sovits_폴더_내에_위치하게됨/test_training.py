import requests
import time
import json
import sys

# Configuration
API_URL = "http://localhost:10002"
MODEL_NAME = "dry_run_test_01"
UPLOAD_PATH = "/opt/GPT-SoVITS/ref_audio/target_voice_folder" # CHANGE THIS to a real path on Server A if needed, or create a dummy folder
VERSION = "v2"

def test_start_training():
    print(f"1. Sending Training Request (Dry Run)...")
    payload = {
        "model_name": MODEL_NAME,
        "upload_path": UPLOAD_PATH,
        "version": VERSION,
        "batch_size": 4,
        "dry_run": True # IMPORTANT: Dry run mode
    }
    
    try:
        response = requests.post(f"{API_URL}/api/train/start", json=payload)
        response.raise_for_status()
        print("   Success!", response.json())
        return True
    except requests.exceptions.RequestException as e:
        print(f"   Failed to start training: {e}")
        if response.content:
            print(f"   Response: {response.content.decode()}")
        return False

def test_check_status():
    print(f"\n2. Checking Status loops...")
    for i in range(10):
        try:
            response = requests.get(f"{API_URL}/api/train/status/{MODEL_NAME}")
            response.raise_for_status()
            data = response.json()
            print(f"   [{i+1}/10] Status: {data['status']}, Progress: {data['progress']}, Msg: {data.get('message')}")
            
            if data['status'] in ["completed", "failed"]:
                print(f"   Final Status reached: {data['status']}")
                return
                
        except Exception as e:
            print(f"   Error checking status: {e}")
        
        time.sleep(2)

def test_get_log():
    print(f"\n3. Retrieving Log...")
    try:
        response = requests.get(f"{API_URL}/api/train/log/{MODEL_NAME}")
        response.raise_for_status()
        data = response.json()
        print("   Log Content Preview (First 200 chars):")
        print("   " + "-"*40)
        print(data['log'][:500] + "...")
        print("   " + "-"*40)
    except Exception as e:
        print(f"   Failed to get log: {e}")

if __name__ == "__main__":
    print("--- Testing GPT-SoVITS Training API ---")
    
    # 0. Check connection
    try:
        requests.get(f"{API_URL}/docs", timeout=2)
    except:
        print(f"Error: Could not connect to {API_URL}. Is training_api.py running?")
        sys.exit(1)

    if test_start_training():
        test_check_status()
        test_get_log()
    
    print("\n--- Test Finished ---")
