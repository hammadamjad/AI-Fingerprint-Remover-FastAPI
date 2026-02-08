import requests
import time
import sys
import os

def test_process_endpoint():
    print("Testing /process endpoint...")
    url = "http://127.0.0.1:8000/process"
    
    # Create a dummy test file
    with open("test_audio.wav", "wb") as f:
        # Minimal WAV header + silence
        # This might not be a valid audio file for the processor (which expects real audio),
        # but the request handling part can be tested. 
        # Ideally we need a real helper or valid small wav.
        # Let's try to generate a valid small wav using existing logic if possible or just use a dummy text file renamed
        # detailed processing might fail on "dummy" wav, but we can catch that error.
        f.write(b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00')

    files = {'file': ('test_audio.wav', open('test_audio.wav', 'rb'), 'audio/wav')}
    data = {'level': 'balanced'}

    try:
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            output_filename = "processed_test_audio.wav"
            with open(output_filename, 'wb') as f:
                f.write(response.content)
            print(f"SUCCESS: File processed and downloaded to {output_filename}")
            if os.path.exists(output_filename):
                os.remove(output_filename)
        else:
            print(f"FAILURE: Status {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"ERROR: Could not connect to server or other error: {e}")
    finally:
        if os.path.exists("test_audio.wav"):
            os.remove("test_audio.wav")

if __name__ == "__main__":
    test_process_endpoint()
