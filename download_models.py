import os
import urllib.request

def download_file(url, filename):
    print(f"Downloading {filename}...")
    urllib.request.urlretrieve(url, filename)
    print(f"Downloaded {filename}")

def main():
    base_url = "https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights"
    models = [
        "tiny_face_detector_model-weights_manifest.json",
        "tiny_face_detector_model-shard1",
        "face_landmark_68_model-weights_manifest.json",
        "face_landmark_68_model-shard1",
        "face_recognition_model-weights_manifest.json",
        "face_recognition_model-shard1",
        "face_recognition_model-shard2"  # Added missing shard
    ]

    # Create models directory if it doesn't exist
    os.makedirs("static/models", exist_ok=True)

    # Download each model file
    for model in models:
        url = f"{base_url}/{model}"
        filename = f"static/models/{model}"
        try:
            download_file(url, filename)
        except Exception as e:
            print(f"Error downloading {model}: {str(e)}")

if __name__ == "__main__":
    main()
