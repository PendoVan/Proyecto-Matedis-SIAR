import requests
import json

# Test de creación de alerta FSM
url = "http://localhost:8000/fsm/alertas/crear"

data = {
    "departamento": "Lima",
    "coordenadas": {
        "lat": -12.0463,
        "lon": -77.0428
    },
    "tipo": "CLIMA",
    "descripcion": "Ll uvia intensa en zona metropolitana",
    "fiabilidad": 0.6,
    "metadata": {
        "precipitacion": 60,
        "temperatura": 18,
        "viento": 25
    }
}

print("🧪 Probando endpoint: POST /fsm/alertas/crear\n")
print(f"📤 Datos enviados:")
print(json.dumps(data, indent=2))
print()

try:
    response = requests.post(url, json=data)
    print(f"📊 Status Code: {response.status_code}")
    print(f"📄 Respuesta:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"❌ Error: {e}")
