from tqdm import tqdm
from .geo import get_street_geometry, sample_points_on_line, measure_length_m
from .images import point2bbox, get_images_from_mapillary
from .llm import ollama_llava_image, ollama_text, build_street_summary_prompt

def run_pipeline(query, n_points, n_images_per_point, out_dir, vision_model, text_model):
    print(f"🔎 Locating '{query}'...")
    line, name, osm_id = get_street_geometry(query)
    length = measure_length_m(line)
    print(f"📍 Found '{name}' (OSM ID: {osm_id}).")
    print(f"📏 Length of this + adjacent road segments: {length:.0f} meters.")

    print(f"🎰 Sampling {n_points} points along the street...")
    points = sample_points_on_line(line, n_points)

    print("📸 Downloading Mapillary images...")
    image_paths = []
    for p in tqdm(points, unit="loc"):
        bbox = point2bbox(p)
        paths = get_images_from_mapillary(bbox, out_dir, n_images=n_images_per_point)
        image_paths.extend(paths)

    if not image_paths:
        print("❌ No images found on Mapillary for this location.")
        return

    print(f"🌋 Analysing {len(image_paths)} images with {vision_model}...")
    
    vision_prompt = (
        "You are an urban planner. Describe the vibe of this street. "
        "Comment on walkability, traffic, greenery, safety, and socio-economic cues. "
        "Be concise and precise."
    )
    
    vibes = []
    for path in tqdm(image_paths, unit="img"):
        try:
            analysis = ollama_llava_image(vision_prompt, path, model=vision_model)
            vibes.append({'image': path, 'vibe': analysis})
        except Exception as e:
            print(f"   Error processing {path}: {e}")

    print(f"📝 Synthesizing summary with {text_model}...")
    summary_prompt = build_street_summary_prompt(vibes, street_name=name)
    final_summary = ollama_text(summary_prompt, model=text_model)

    return final_summary