import os
import requests
from pathlib import Path

def point2bbox(p, buffer=0.0002):
    south, north = p.y - buffer, p.y + buffer
    west, east = p.x - buffer, p.x + buffer
    return f'{round(west, 5)},{round(south, 5)},{round(east, 5)},{round(north, 5)}'

def get_images_from_mapillary(p, out_dir: str, n_images: int = 1):
    token = os.environ.get('MAPILLARY_TOKEN')
    if not token:
        raise RuntimeError('MAPILLARY_TOKEN env var not set. See https://www.mapillary.com/developer/api-documentation/')

    bbox = point2bbox(p)

    url = 'https://graph.mapillary.com/images'
    params = {
        'access_token': token,
        'fields': 'id,geometry,computed_geometry,captured_at,thumb_1024_url',
        'bbox': bbox,
        'limit': 50,
    }

    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json().get('data', [])

    # Get the most recent n_images among 50 captured
    data = sorted(
        data,
        key=lambda img: int(img.get('captured_at') or 0),
        reverse=True
    )[:n_images]

    out_paths = []
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    for img in data:
        img_id = img['id']
        thumb_url = img.get('thumb_1024_url')
        if not thumb_url:
            continue

        out_path = Path(out_dir) / f'{img_id}.jpg'
        
        # Don't redownload if exists
        if not out_path.exists():
            r = requests.get(thumb_url, timeout=10)
            r.raise_for_status()
            with open(out_path, 'wb') as f:
                f.write(r.content)

        out_paths.append(str(out_path))

    return out_paths
