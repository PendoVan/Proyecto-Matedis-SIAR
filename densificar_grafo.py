"""
Script para densificar el grafo automáticamente.
Conecta cada departamento con sus 4 vecinos más cercanos geográficamente.
Esto crea una red más natural y evita "saltos" extraños.
"""
import sys
sys.path.insert(0, '.')

from src.unidad3_grafos.grafo_rutas import GrafoRutas
import json
import math

# Coordenadas completas
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
    """Distancia Haversine"""
    R = 6371
    lat1, lon1 = math.radians(COORDENADAS[n1]['lat']), math.radians(COORDENADAS[n1]['lon'])
    lat2, lon2 = math.radians(COORDENADAS[n2]['lat']), math.radians(COORDENADAS[n2]['lon'])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

print("\n" + "="*80)
print("🌐 DENSIFICACIÓN DE GRAFO (K-NEAREST NEIGHBORS)")
print("="*80 + "\n")

# Cargar grafo actual
ruta_json = "data/grafos/red_peru_24_departamentos.json"
with open(ruta_json, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Crear conjunto de conexiones existentes para búsqueda rápida
conexiones_existentes = set()
for arista in data['aristas']:
    par = tuple(sorted([arista['origen'], arista['destino']]))
    conexiones_existentes.add(par)

print(f"Aristas actuales: {len(conexiones_existentes)}")

nuevas_aristas = []
K_VECINOS = 10  # AUMENTADO: Conectar con los 10 vecinos más cercanos (Alta densidad)

for nodo in data['nodos']:
    if nodo not in COORDENADAS:
        continue
        
    # Calcular distancia a todos los demás nodos
    distancias = []
    for otro in data['nodos']:
        if nodo != otro and otro in COORDENADAS:
            d = calc_dist(nodo, otro)
            distancias.append((d, otro))
    
    # Ordenar por distancia
    distancias.sort()
    
    # Tomar los K más cercanos
    vecinos = distancias[:K_VECINOS]
    
    # CASO ESPECIAL: Ucayali (Pucallpa) conecta con 12 para asegurar salida
    if nodo == 'Ucayali':
        vecinos = distancias[:12]


    
    for dist, vecino in vecinos:
        par = tuple(sorted([nodo, vecino]))
        
        # Si no existe la conexión, agregarla
        if par not in conexiones_existentes:
            dist_ruta = int(dist * 1.3)  # Factor de curvatura carretera
            
            nueva_arista = {
                "origen": nodo,
                "destino": vecino,
                "distancia_km": dist_ruta,
                "fiabilidad": 0.85,  # Valor por defecto bueno
                "tipo_camino": "afirmado",
                "riesgo_historico": 0.2,
                "tiempo_estimado_min": int(dist_ruta / 50 * 60)  # ~50 km/h promedio
            }
            
            nuevas_aristas.append(nueva_arista)
            conexiones_existentes.add(par)
            print(f"   + Nueva conexión: {nodo} ↔ {vecino} ({dist_ruta} km)")

if nuevas_aristas:
    data['aristas'].extend(nuevas_aristas)
    
    with open(ruta_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ Se agregaron {len(nuevas_aristas)} nuevas conexiones.")
    print(f"📊 Total final de aristas: {len(data['aristas'])}")
else:
    print("\n✅ El grafo ya está suficientemente denso.")

print("\n" + "="*80 + "\n")
