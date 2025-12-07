import base64
import requests

def ollama_llava_image(prompt: str, image_path: str, model="llava"):
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    payload = {
        "model": model,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False
    }

    resp = requests.post("http://localhost:11434/api/generate", json=payload)
    resp.raise_for_status()
    return resp.json()["response"]

def ollama_text(prompt: str, model: str = 'llama3.1'):
    payload = {
        'model': model,
        'prompt': prompt,
        'stream': False,
    }
    resp = requests.post('http://localhost:11434/api/generate', json=payload)
    resp.raise_for_status()
    return resp.json()['response']

def build_street_summary_prompt(vibes, street_name='this street'):
    header = (
        f"You are an urban planner. You are given descriptions of ~{len(vibes)} "
        f"viewpoints along {street_name}. Each description is from an image-based "
        "model (LLaVA) and may be noisy.\n\n"
        "Tasks:\n"
        "1. Infer the overall character of the street.\n"
        "2. Comment on: land use, walkability, traffic, greenery, safety, "
        "   maintenance, socio-economic cues.\n"
        "3. Highlight any clear variation along the street.\n"
        "4. Be concise but specific. Do not repeat or mention each segment by their number; summarise patterns.\n\n"
        "Segment-level descriptions:\n"
    )
    body = "\n\n".join(
        f">>> Segment {i+1}: {v['vibe']}"
        for i, v in enumerate(vibes)
    )
    return header + "\n" + body