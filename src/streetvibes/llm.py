import base64
import json
from typing import Optional

import requests

def ask_vlm(prompt: str, image_path: str, model="llava"):
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

def ask_llm(prompt: str, model: str = 'llama3.1', response_format: Optional[str] = None):
    if response_format == "json":
        prompt = (
            "Return only JSON. Do not include any extra text.\n\n"
            f"{prompt}"
        )
    payload = {
        'model': model,
        'prompt': prompt,
        'stream': False,
    }
    if response_format:
        payload['format'] = response_format
    resp = requests.post('http://localhost:11434/api/generate', json=payload)
    resp.raise_for_status()
    response_text = resp.json()['response']
    if response_format == "json":
        return json.loads(response_text)
    return response_text

def build_street_summary_prompt(
    vibes,
    street_name: str = 'this street',
    structured: bool = False,
    text_prompt: Optional[str] = None,
    text_keys: Optional[list[str]] = None,
):
    if text_prompt:
        header = text_prompt.strip() + "\n\n"
    else:
        header = (
            f"You are an urban planner. You are given descriptions of ~{len(vibes)} "
            f"viewpoints along {street_name}. Each description is from an image-based "
            "model and may be noisy.\n\n"
            "Provide a concise one-paragraph summary of the street's character, covering: "
            "land use, walkability, traffic, greenery, safety, maintenance, and socio-economic cues. "
            "Highlight key variations but avoid repeating segment details.\n\n"
        )
    if structured:
        keys = text_keys or [
            "summary",
            "land_use",
            "walkability",
            "traffic",
            "greenery",
            "safety",
            "maintenance",
            "socio_economic",
            "variations",
        ]
        header += (
            "Return a JSON object with the following keys: "
            f"{', '.join(keys)}. "
            "Each value should be a short string. "
            "The summary must be one paragraph.\n\n"
        )
    header += "Segment-level descriptions:\n"
    body = "\n\n".join(
        f">>> Segment {i+1}: {v['vibe']}"
            for i, v in enumerate(vibes)
    )
    return header + "\n" + body
