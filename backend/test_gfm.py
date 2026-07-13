import requests

API_KEY = "77dc8206-59be-4785-94ae-d9d564a60879"

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

url = "https://data-api.globalforestwatch.org/dataset/gfw_integrated_alerts/latest/query"

# Your Amazon Wildlife Reserve bounding box as GeoJSON geometry
geometry = {
    "type": "Polygon",
    "coordinates": [[
        [-62.3, -3.55],
        [-62.1, -3.55],
        [-62.1, -3.35],
        [-62.3, -3.35],
        [-62.3, -3.55]
    ]]
}

payload = {
    "sql": """
        SELECT latitude, longitude, gfw_integrated_alerts__confidence, gfw_integrated_alerts__date
        FROM data
        WHERE gfw_integrated_alerts__date >= '2026-06-01'
        LIMIT 10
    """,
    "geometry": geometry
}

response = requests.post(url, json=payload, headers=headers)
print("Status Code:", response.status_code)
print("Response:", response.json())