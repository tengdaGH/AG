---
name: common_image_generation
description: Generating high-fidelity AI avatars and custom image assets. Uses the built-in generate_image tool first, falling back to Gemini for capacity issues.
---

# Global Image Generation Skill

> [!IMPORTANT]
> **Primary path**: Always try the built-in `generate_image` tool first.
> **Fallback only**: If the built-in tool returns a `503 / MODEL_CAPACITY_EXHAUSTED` error, fall back to the user's personal `GEMINI_API_KEY` using the REST pattern below.
> Do NOT download generic stock photos from external APIs like RandomUser.

## Primary: Built-in Tool

Use the system `generate_image` tool directly. No API key needed.

## Fallback: Personal Gemini API (when built-in is unavailable)

### Prerequisites
- `GEMINI_API_KEY` set in the backend `.env` file.
- The `requests` and `python-dotenv` packages installed.

### Python Code Pattern (REST API)
```python
import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

def generate_ultra_image(prompt: str, output_path: str, aspect_ratio="1:1"):
    """
    Generates an image using the Gemini Ultra plan via REST API.
    aspect_ratio options: "1:1", "3:4", "4:3", "16:9"
    """
    print(f"Generating image: {prompt}")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-ultra-generate-001:predict?key={API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "instances": [
            {
                "prompt": prompt
            }
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": aspect_ratio,
            "outputOptions": {
                "mimeType": "image/jpeg"
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if "predictions" in data and len(data["predictions"]) > 0:
            b64_img = data["predictions"][0]["bytesBase64Encoded"]
            img_data = base64.b64decode(b64_img)
            with open(output_path, "wb") as f:
                f.write(img_data)
            print(f"Successfully saved to {output_path}")
        else:
            print(f"Failed to generate: no predictions. {data}")
    else:
        print(f"Failed to generate: {response.status_code} {response.text}")

```

## Prompting Best Practices
- Use terms like `Professional realistic headshot`, `well-lit`, `high quality photography` for avatars.
- State the `aspect ratio` in the prompt and enforce via `parameters.aspectRatio`.
- For avatars, specify `neutral academic background` or `casual but neat attire` to fit the TOEFL context.

## Item-Specific Style Guidelines

### Listen and Repeat (Speaking Task 4)
- **Style**: **Cartoon Illustration**.
- **Visuals**: Simple flat illustration, muted colors, educational textbook feel.
- **Content**: Bird's eye view of scenes (e.g., zoo, park, campus) with specific objects or areas highlighted using **teal/turquoise circles** and directional **teal arrows**.
- **Avoid**: Photorealistic stock photos for this specific task type.

