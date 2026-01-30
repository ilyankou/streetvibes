import math
import requests
from geopy.geocoders import Nominatim
from shapely.geometry import shape, LineString
from shapely.ops import unary_union, linemerge
from pyproj import Geod

def measure_length_m(line):
    geod = Geod(ellps='WGS84')
    if line.geom_type == 'LineString':
        lons, lats = zip(*line.coords)
        return geod.line_length(lons, lats)
    elif line.geom_type == 'MultiLineString':
        total = 0
        for ls in line.geoms:
            lons, lats = zip(*ls.coords)
            total += geod.line_length(lons, lats)
        return total
    else:
        raise ValueError("Geometry must be LineString or MultiLineString")

def overpass_street_lines(name: str, south: float, west: float, north: float, east: float):
    url = 'https://overpass-api.de/api/interpreter'
    query_osm = f"""
    [out:json];
    way["highway"]["name"="{name}"]({south},{west},{north},{east});
    (._; >;);
    out geom;
    """
    resp = requests.post(url, data={'data': query_osm}, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    nodes = {}
    for el in data.get('elements', []):
        if el['type'] == 'node':
            nodes[el['id']] = (float(el['lon']), float(el['lat']))

    lines = []
    for el in data.get('elements', []):
        if el['type'] == 'way':
            geom = el.get('geometry')
            if geom:
                coords = [(g['lon'], g['lat']) for g in geom]
            else:
                coords = [nodes[nid] for nid in el.get('nodes', []) if nid in nodes]
            if len(coords) >= 2:
                lines.append(LineString(coords))
    return lines

def get_street_geometry(query: str, search_radius_m: float = 2000.0):
    
    # 1. Nominatim
    geolocator = Nominatim(user_agent='streetvibes')
    loc = geolocator.geocode(query, exactly_one=True, geometry='geojson')
    if loc is None:
        raise ValueError(f'No Nominatim result for query: {query}')

    raw = loc.raw
    name = raw.get('name')
    osm_id = raw.get('osm_id')
    geom_geojson = raw.get('geojson')
    
    if not name:
        raise ValueError('Nominatim result has no name field')
    if not geom_geojson:
        raise ValueError('Nominatim result has no geojson geometry')
        
    nominatim_line = shape(geom_geojson)
    lat0, lon0 = loc.latitude, loc.longitude

    # 2. Build BBox for Overpass
    deg_lat = search_radius_m / 110540.0
    deg_lon = search_radius_m / (111320.0 * math.cos(math.radians(lat0)) + 1e-9)

    south, north = lat0 - deg_lat, lat0 + deg_lat
    west, east = lon0 - deg_lon, lon0 + deg_lon

    # 3. Overpass Fetch
    segments = overpass_street_lines(name, south, west, north, east)

    # 4. Merge
    if segments:
        merged_input = unary_union(segments)
        if merged_input.geom_type == 'LineString':
            line = merged_input
        else:
            try:
                merged = linemerge(merged_input)
            except Exception:
                merged = merged_input
            if merged.geom_type == 'MultiLineString':
                line = max(merged.geoms, key=lambda g: g.length)
            else:
                line = merged
    else:
        line = nominatim_line

    return line, name, osm_id

def sample_points_on_line(line, n_points: int):
    if n_points < 2:
         # Fallback for short segments or single point request
         return [line.centroid]
    
    fractions = [i / (n_points - 1) for i in range(n_points)]
    return [line.interpolate(frac, normalized=True) for frac in fractions]
