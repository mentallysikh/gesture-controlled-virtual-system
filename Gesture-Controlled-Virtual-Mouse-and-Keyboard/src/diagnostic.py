import requests
import json

# Your API Key
API_KEY = "AIzaSyD-VmK_jvneDbLsG1eOmNpcgjQFfT2UZgo"

def test_connection():
    print(f"🔑 Testing API Key: {API_KEY[:10]}...")
    
    # 1. Check 'v1beta' endpoint
    print("\n--- CHECKING V1BETA ENDPOINT ---")
    url_beta = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    try:
        response = requests.get(url_beta)
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! Available models:")
            for model in data.get('models', []):
                if 'generateContent' in model.get('supportedGenerationMethods', []):
                    print(f"   - {model['name']}")
        else:
            print(f"❌ Failed ({response.status_code}): {response.text[:100]}...")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

    # 2. Check 'v1' endpoint (Stable)
    print("\n--- CHECKING V1 ENDPOINT ---")
    url_v1 = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"
    try:
        response = requests.get(url_v1)
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! Available models:")
            for model in data.get('models', []):
                if 'generateContent' in model.get('supportedGenerationMethods', []):
                    print(f"   - {model['name']}")
        else:
            print(f"❌ Failed ({response.status_code}): {response.text[:100]}...")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_connection()
