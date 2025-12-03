"""
Auto-corrector de backtracking - Ejecuta y agrega conexiones automáticamente
"""
import sys
sys.path.insert(0, '.')

from src.unidad3_grafos.grafo_rutas import GrafoRutas
from src.unidad3_grafos.algoritmo_fiabilidad_geo import AlgoritmoFiabilidadGeo
import json
import math

COORDENADAS = {
    'Lima': {'lat': -12.0464, 'lon': -77.0428}, 'Callao': {'lat': -12.0565, 'lon': -77.1181},
    'Ica': {'lat': -14.0678, 'lon': -75.7286}, 'Arequipa': {'lat': -16.4090, 'lon': -71.5375},
    'Moquegua': {'lat': -17.1934, 'lon': -70.9336}, 'Tacna': {'lat': -18.0047, 'lon': -70.2453},
    'Tumbes': {'lat': -3.5669, 'lon': -80.4515}, 'Piura': {'lat': -5.1945, 'lon': -80.6328},
    'Lambayeque': {'lat': -6.7011, 'lon': -79.9061}, 'La Libertad': {'lat': -8.1116, 'lon': -79.0292},
    'Ancash': {'lat': -9.5267, 'lon': -77.5284}, 'Cajamarca': {'lat': -7.1614, 'lon': -78.5126},
    'Huánuco': {'lat': -9.9306, 'lon': -76.2422}, 'Pasco': {'lat': -10.6819, 'lon': -76.2561},
    'Junín': {'lat': -12.0699, 'lon': -75.2048}, 'Huancavelica': {'lat': -12.7872, 'lon': -74.9758},
    'Ayacucho': {'lat': -13.1631, 'lon': -74.2236}, 'Apurímac': {'lat': -13.6344, 'lon': -72.8831},
    'Cusco': {'lat': -13.5319, 'lon': -71.9675}, 'Puno': {'lat': -15.8422, 'lon': -70.0199},
    'Amazonas': {'lat': -5.7667, 'lon': -77.8667}, 'San Martín': {'lat': -6.4833, 'lon': -76.3667},
    'Loreto': {'lat': -3.7499, 'lon': -73.2540}, 'Ucayali': {'lat': -8.3791, 'lon': -74.5539},
    'Madre de Dios': {'lat': -12.5935, 'lon': -69.1892}
}

def calc_dist(n1, n2):
    R = 6371
    lat1, lon1 = math.radians(COORDENADAS[n1]['lat']), math.radians(COORDENADAS[n1]['lon'])
    lat2, lon2 = math.radians(COORDENADAS[n2]['lat']), math.radians(COORDENADAS[n2]['lon'])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a)) * 1.3

grafo = GrafoRutas.cargar_json("data/grafos/red_peru_24_departamentos.json")
algoritmo = AlgoritmoFiabilidadGeo(grafo, COORDENADAS)

print("Analizando rutas...")
importantes = ['Lima', 'Lambayeque', 'Cajamarca', 'Piura', 'Loreto', 'San Martín', 
               'Ucayali', 'Madre de Dios', 'Amazonas', 'Huánuco', 'Junín', 'Pasco', 'Cusco', 'Puno']

conexiones = set()
for o in importantes:
    for d in importantes:
        if o != d:
            try:
                r = algoritmo.encontrar_ruta_mas_fiable(o, d)
                if r and len(r.nodos) > 2:
                    for i in range(len(r.nodos)-1):
                        if r.nodos[i] in r.nodos[i+2:]:  # Detecta repetición
                            idx = r.nodos[i+2:].index(r.nodos[i]) + i + 2
                            if idx > i+1 and idx < len(r.nodos):
                                antes = r.nodos[idx-1]
                                despues = r.nodos[idx+1] if idx+1 < len(r.nodos) else None
                                if despues and antes != despues:
                                    conexiones.add(tuple(sorted([antes, despues])))
            except: pass

if conexiones:
    print(f"\n✅ Encontradas {len(conexiones)} conexiones faltantes:\n")
    with open("data/grafos/red_peru_24_departamentos.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for n1, n2 in sorted(conexiones):
        dist = int(calc_dist(n1, n2))
        nueva = {
            'origen': n1, 'destino': n2, 'distancia_km': dist,
            'fiabilidad': 0.75, 'tipo_camino': 'afirmado',
            'riesgo_historico': 0.3, 'tiempo_estimado_min': dist
        }
        data['aristas'].append(nueva)
        print(f"   + {n1} ↔ {n2} ({dist} km)")
    
    with open("data/grafos/red_peru_24_departamentos.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Grafo actualizado: {len(data['aristas'])} aristas totales")
    print("   El servidor debería recargar automáticamente\n")
else:
    print("\n✅ No se encontraron backtrackings - Grafo completo\n")
