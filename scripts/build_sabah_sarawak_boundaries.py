#!/usr/bin/env python3
"""
Build the runtime Sabah/Sarawak ADM2 boundary fixture from geoBoundaries.

Source:
  https://www.geoboundaries.org/api/current/gbOpen/MYS/ADM2/

The script downloads the simplified Malaysia ADM2 GeoJSON from the pinned
geoBoundaries release, keeps only Sabah/Sarawak districts, and writes the small
runtime FeatureCollection used by GeographyResolver.
"""

import json
import urllib.request
from pathlib import Path


SOURCE_URL = (
    "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/"
    "releaseData/gbOpen/MYS/ADM2/geoBoundaries-MYS-ADM2_simplified.geojson"
)
OUTPUT_PATH = Path("Info/reference/sabah_sarawak_adm2.geojson")

SABAH_DISTRICTS = {
    "Beaufort", "Beluran", "Kalabakan", "Keningau", "Kinabatangan",
    "Kota Belud", "Kota Kinabalu", "Kota Marudu", "Kuala Penyu", "Kudat",
    "Kunak", "Lahad Datu", "Nabawan / Persiangan", "Papar", "Penampang",
    "Pitas", "Putatan", "Ranau", "Sandakan", "Semporna", "Sipitang",
    "Tambunan", "Tawau", "Telupid", "Tenom", "Tongod", "Tuaran",
}

SARAWAK_DISTRICTS = {
    "Asajaya", "Bau", "Belaga", "Beluru", "Betong", "Bintulu",
    "Bukit Mabong", "Dalat", "Daro", "Julau", "Kabong", "Kanowit",
    "Kapit", "Kuching", "Lawas", "Limbang", "Lubok Antu", "Lundu",
    "Maradong", "Marudi", "Matu", "Miri", "Mukah", "Pakan", "Pusa",
    "Samarahan", "Saratok", "Sarikei", "Sebauh", "Selangau", "Serian",
    "Sibu", "Simunjan", "Song", "Sri Aman", "Subis", "Tanjung Manis",
    "Tatau", "Tebedu", "Telang Usan",
}


def geometry_bbox(geometry):
    points = []

    def walk(value):
        if isinstance(value, list) and value and isinstance(value[0], (int, float)):
            points.append(value)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(geometry.get("coordinates", []))
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return [min(xs), min(ys), max(xs), max(ys)]


def state_for_district(name):
    if name in SABAH_DISTRICTS:
        return "Sabah"
    if name in SARAWAK_DISTRICTS:
        return "Sarawak"
    return None


def main():
    with urllib.request.urlopen(SOURCE_URL, timeout=120) as response:
        source = json.load(response)

    features = []
    for feature in source.get("features", []):
        name = feature.get("properties", {}).get("shapeName")
        state = state_for_district(name)
        if not state:
            continue
        geometry = feature.get("geometry")
        features.append(
            {
                "type": "Feature",
                "bbox": geometry_bbox(geometry),
                "properties": {
                    "state": state,
                    "district": name,
                    "source_shape_id": feature.get("properties", {}).get("shapeID"),
                },
                "geometry": geometry,
            }
        )

    output = {
        "type": "FeatureCollection",
        "name": "sabah_sarawak_adm2_geoboundaries_simplified",
        "metadata": {
            "source_organization": "geoBoundaries / William & Mary geoLab",
            "source_url": "https://www.geoboundaries.org/api/current/gbOpen/MYS/ADM2/",
            "download_url": SOURCE_URL,
            "license": "Creative Commons Attribution 3.0 License",
            "retrieval_date": "2026-06-10",
            "administrative_level": "ADM2 district",
            "original_format": "GeoJSON simplified",
            "filtering": "Kept Sabah and Sarawak ADM2 district features only; kept state, district, source_shape_id, bbox, and geometry.",
            "feature_count": len(features),
        },
        "features": sorted(features, key=lambda item: (item["properties"]["state"], item["properties"]["district"])),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    print(f"Wrote {len(features)} features to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
