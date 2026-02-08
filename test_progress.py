import requests
import time
import uuid
import os

# Configuration
BASE_URL = "http://127.0.0.1:8000"
INPUT_FILE = "test_audio_async.wav"

def generate_test_audio():
    import numpy as np
    import soundfile as sf
    sr = 44100
    duration = 5.0 
    t = np.linspace(0, duration, int(sr * duration))
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)
    sf.write(INPUT_FILE, audio, sr)
    print(f"Generated test audio: {INPUT_FILE}")

def run_async_test():
    generate_test_audio()
    
    request_id = str(uuid.uuid4())
    print(f"Starting async test with Request ID: {request_id}")
    
    # Send processing request
    try:
        with open(INPUT_FILE, "rb") as f:
            files = {"file": (INPUT_FILE, f, "audio/wav")}
            data = {"request_id": request_id, "level": "balanced"}
            
            print("Sending process request (non-blocking)...")
            response = requests.post(f"{BASE_URL}/process", files=files, data=data)
            
            if response.status_code == 200:
                print(f"Initial response: {response.json()}")
            else:
                print(f"Process request failed: {response.status_code} - {response.text}")
                return
                
    except Exception as e:
        print(f"Request error: {e}")
        return

    # Poll progress
    while True:
        try:
            resp = requests.get(f"{BASE_URL}/progress/{request_id}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"Progress: {data['progress']:.1f}% - {data['status']}")
                if data['progress'] >= 100:
                    break
            elif resp.status_code == 404:
                print("Waiting for task to appear...")
            else:
                print(f"Error checking progress: {resp.status_code}")
                break
            time.sleep(1)
        except Exception as e:
            print(f"Polling error: {e}")
            break

    # Download result
    try:
        print("Downloading final result...")
        resp = requests.get(f"{BASE_URL}/download/{request_id}")
        if resp.status_code == 200:
            print(f"Download successful. Received {len(resp.content)} bytes.")
            with open("async_output.wav", "wb") as out:
                out.write(resp.content)
        else:
            print(f"Download failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Download error: {e}")

    # Cleanup local files
    if os.path.exists(INPUT_FILE): os.remove(INPUT_FILE)
    if os.path.exists("async_output.wav"): os.remove("async_output.wav")

if __name__ == "__main__":
    run_async_test()
