# Sabah/Sarawak Boundary Data

Runtime file: `Info/reference/sabah_sarawak_adm2.geojson`

## Source

- Source organization: geoBoundaries / William & Mary geoLab
- Source metadata URL: https://www.geoboundaries.org/api/current/gbOpen/MYS/ADM2/
- Download URL: https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/MYS/ADM2/geoBoundaries-MYS-ADM2_simplified.geojson
- License: Creative Commons Attribution 3.0 License
- Retrieval date: 2026-06-10
- Administrative level: ADM2 district
- Original format: simplified GeoJSON

## Processing

The production runtime dataset is generated with:

```powershell
python scripts/build_sabah_sarawak_boundaries.py
```

The script filters the Malaysia ADM2 GeoJSON to Sabah and Sarawak district
features only. It keeps only:

- `state`
- `district`
- `source_shape_id`
- `bbox`
- `geometry`

No manually invented rectangular city bounding boxes are used. Districts without
a confirmed business route bucket remain fail-closed as `REVIEW_REQUIRED`.
