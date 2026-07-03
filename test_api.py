import requests
import sys

def test_api(url, image_path):
    print(f"Testing API at: {url}")
    print(f"Using image: {image_path}")
    
    try:
        with open(image_path, "rb") as f:
            files = {"file": f}
            data = {"prompt": "Describe this image in exquisite detail for a text-to-video generation model. Focus on the subject, lighting, camera angle, and potential motion."}
            
            print("Sending request... (this may take a few seconds as the model generates the text)")
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print("\n--- Success! ---")
                print(f"Original Prompt: {result['original_prompt']}")
                print(f"Extended Prompt: {result['extended_prompt']}")
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                
    except FileNotFoundError:
        print(f"Error: Could not find image file '{image_path}'")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_api.py <API_URL> <IMAGE_PATH>")
        print("Example: python test_api.py https://your-modal-workspace--qwen25-vl-image-to-video-fastapi-app-dev.modal.run ./test_image.jpg")
        sys.exit(1)
        
    api_url = sys.argv[1]
    image_path = sys.argv[2]
    
    test_api(api_url, image_path)
