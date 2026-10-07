import json
import urllib.request
import os

TOKEN = 'removed_for_security'
FILE_ID = '3ZDBpojNk9zmfHLycCMK5a'

with open("figma_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

screens = {
    "21:250": "home",
    "21:3525": "sending_alert",
    "21:3541": "sos_active",
    "21:3587": "situation_category",
    "21:3664": "fire_details",
    "21:3754": "sos_situation_worse",
    "21:3806": "safe"
}

svg_export_ids = []

def collect_vectors(node):
    if node["type"] in ["VECTOR", "BOOLEAN_OPERATION", "STAR", "LINE", "ELLIPSE", "REGULAR_POLYGON"]:
        svg_export_ids.append(node["id"])
    for child in node.get("children", []):
        collect_vectors(child)

for node_id in screens.keys():
    collect_vectors(data["nodes"][node_id]["document"])

print(f"Found {len(svg_export_ids)} vectors.")

# Re-download
if svg_export_ids:
    print("Fetching SVGs...")
    chunk_size = 50
    for i in range(0, len(svg_export_ids), chunk_size):
        chunk = svg_export_ids[i:i+chunk_size]
        ids_joined = ",".join(chunk)
        url = f'https://api.figma.com/v1/images/{FILE_ID}?ids={ids_joined}&format=svg'
        req = urllib.request.Request(url, headers={'X-Figma-Token': TOKEN})
        try:
            with urllib.request.urlopen(req) as response:
                img_data = json.loads(response.read().decode('utf-8'))
                images = img_data.get('images', {})
                for node_id, svg_url in images.items():
                    if svg_url:
                        safe_id = node_id.replace(':', '_')
                        svg_req = urllib.request.Request(svg_url)
                        with urllib.request.urlopen(svg_req) as svg_resp:
                            svg_content = svg_resp.read()
                            with open(f'svgs/{safe_id}.svg', 'wb') as f:
                                f.write(svg_content)
        except Exception as e:
            print(f'Error fetching chunk: {e}')
    print('Finished downloading SVGs.')
