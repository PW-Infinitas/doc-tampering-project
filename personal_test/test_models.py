import time
import json
from pathlib import Path
from PIL import Image
from google import genai

PROJECT = "infinitas-ds-ai-poc"
LOCATION = "us-central1"
IMAGE_PATH = Path(__file__).parent / "test_image.jpg"
PROMPT = "Describe what's in this image."

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]

def test_model(client: genai.Client, model_name: str, image: Image.Image, prompt: str) -> dict:
    start = time.perf_counter()
    response = client.models.generate_content(
        model=model_name,
        contents=[prompt, image],
    )
    elapsed = round(time.perf_counter() - start, 2)
    return {
        "model": model_name,
        "response": response.text,
        "latency_s": elapsed,
    }

def main() -> None:
    client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)
    image = Image.open(IMAGE_PATH)

    results = []
    for model_name in MODELS:
        print(f"\n{'='*60}")
        print(f"Model: {model_name}")
        print("="*60)
        try:
            result = test_model(client, model_name, image, PROMPT)
            print(result["response"])
            print(f"\n[latency: {result['latency_s']}s]")
            results.append(result)
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"model": model_name, "error": str(e)})

    output_path = Path(__file__).parent / "results.json"
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\nResults saved to {output_path}")

if __name__ == "__main__":
    main()
