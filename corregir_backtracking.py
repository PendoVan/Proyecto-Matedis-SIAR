"""
Script para detectar y corregir TODOS los backtrackings automáticamente
"""
import sys
sys.path.insert(0, '.')

from src.unidad3_grafos.grafo_rutas import GrafoRutas
from src.unidad3_grafos.algoritmo_fiabilidad_geo import AlgoritmoFiabilidadGeo
import json
import math

COORDENADAS = {
    'Lima': {'lat': -12.0464, 'lon': -77.0428},
    'Callao': {'lat': -12.0565, 'lon': -77.1181},
    'Ica': {'lat': -14.0678, 'lon': -75.7286},
    'Arequipa': {'lat': -16.4090, 'lon': -71.5375},
    'Moquegua': {'lat': -17.1934, 'lon': -70.9336},
    'Tacna': {'lat': -18.0047, 'lon': -70.2453},
    'Tumbes': {'lat': -3.5669, 'lon': -80.4515},
    'Piura': {'lat': -5.1945, 'lon': -80.6328},
    'Lambayeque': {'lat': -6.7011, 'lon': -79.9061},
    'La Libertad': {'lat': -8.1116, 'lon': -79.0292},
    'Ancash': {'lat': -9.5267, 'lon': -77.5284},
    'Cajamarca': {'lat': -7.1614, 'lon': -78.5126},
    'Huánuco': {'lat': -9.9306, 'lon': -76.2422},
    'Pasco': {'lat': -10.6819, 'lon': -76.2561},
    'Junín': {'lat': -12.0699, 'lon': -75.2048},
    'Huancavelica': {'lat': -12.7872, 'lon': -74.9758},
    'Ayacucho': {'lat': -13.1631, 'lon': -74.2236},
    'Apurímac': {'lat': -13.6344, 'lon': -72.8831},
    'Cusco': {'lat': -13.5319, 'lon': -71.9675},
    'Puno': {'lat': -15.8422, 'lon': -70.0199},
    'Amazonas': {'lat': -5.7667, 'lon': -77.8667},
    'San Martín': {'lat': -6.4833, 'lon': -76.3667},
    'Loreto': {'lat': -3.7499, 'lon': -73.2540},
    'Ucayali': {'lat': -8.3791, 'lon': -74.5539},
    'Madre de Dios': {'lat': -12.5935, 'lon': -69.1892}
}

def calcular_distancia(lat1, lon1, lat2, lon2):
    """Calcula distancia Haversine"""
    R = 6371
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat/2)**2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def detectar_backtracking(nodos):
    """Detecta nodos repetidos"""
    visitados = {}
    for i, nodo in enumerate(nodos):
        if nodo in visitados:
            return True, visitados[nodo], i, nodo
        visitados[nodo] = i
    return False, None, None, None

print("\n" + "="*80)
print("🔍 BÚSQUEDA AUTOMÁTICA DE BACKTRACKINGS")
print("="*80 + "\n")

# Cargar grafo
grafo = GrafoRutas.cargar_json("data/grafos/red_peru_24_departamentos.json")
algoritmo = AlgoritmoFiabilidadGeo(grafo, COORDENADAS)

# Probar TODAS las combinaciones importantes
nodos_importantes = ['Lima', 'Lambayeque', 'Cajamarca', 'Piura', 'La Libertad',
                     'Loreto', 'San Martín', 'Ucayali', 'Madre de Dios', 
                     'Amazonas', 'Huánuco', 'Junín', 'Pasco', 'Cusco', 'Puno']

print(f"Probando {len(nodos_importantes)} × {len(nodos_importantes)} = {len(nodos_importantes)**2} rutas...\n")

problemas = []
conexiones_sugeridas = set()

for origen in nodos_importantes:
    for destino in nodos_importantes:
        if origen == destino:
            continue
        
        try:
            ruta = algoritmo.encontrar_ruta_mas_fiable(origen, destino)
            if ruta:
                tiene_back, pos1, pos2, nodo_rep = detectar_backtracking(ruta.nodos)
                if tiene_back:
                    # Encontrar qué conexión falta
                    nodo_antes = ruta.nodos[pos2-1]
                    nodo_despues = ruta.nodos[pos2+1] if pos2+1 < len(ruta.nodos) else None
                    
                    if nodo_despues and nodo_antes != nodo_despues:
                        # Sugerir conexión directa
                        conexion = tuple(sorted([nodo_antes, nodo_despues]))
                        conexiones_sugeridas.add(conexion)
                        
                        problemas.append({
                            'origen': origen,
                            'destino': destino,
                            'ruta': ' → '.join(ruta.nodos),
                            'nodo_repetido': nodo_rep,
                            'sugerencia': f"{nodo_antes} ↔ {nodo_despues}"
                        })
        except:
            pass

print(f"{'🔥 BACKTRACKINGS ENCONTRADOS' if problemas else '✅ NO SE ENCONTRARON BACKTRACKINGS'}")
print(f"Total: {len(problemas)} rutas con backtracking\n")

if problemas:
    print("Ejemplos de rutas problemáticas:")
    for p in problemas[:5]:  # Mostrar solo primeras 5
        print(f"\n   {p['origen']} → {p['destino']}")
        print(f"   Ruta: {p['ruta']}")
        print(f"   Nodo repetido: {p['nodo_repetido']}")
        print(f"   💡 Falta conexión: {p['sugerencia']}")
    
    if len(problemas) > 5:
        print(f"\n   ... y {len(problemas) - 5} más")

print(f"\n{'─'*80}")
print(f"\n📋 CONEXIONES QUE FALTAN ({len(conexiones_sugeridas)} totales):\n")

# Calcular distancias para las conexiones sugeridas
nuevas_conexiones = []
for nodo1, nodo2 in sorted(conexiones_sugeridas):
    if nodo1 in COORDENADAS and nodo2 in COORDENADAS:
        dist = calcular_distancia(
            COORDENADAS[nodo1]['lat'], COORDENADAS[nodo1]['lon'],
            COORDENADAS[nodo2]['lat'], COORDENADAS[nodo2]['lon']
        )
        nuevas_conexiones.append({
            'origen': nodo1,
            'destino': nodo2,
            'distancia_km': int(dist * 1.3),  # Factor carretera
            'fiabilidad': 0.75,  # Conservador
            'tipo_camino': 'afirmado',
            'riesgo_historico': 0.3,
            'tiempo_estimado_min': int(dist * 1.3)
        })
        print(f"   • {nodo1} ↔ {nodo2} ({int(dist * 1.3)} km)")

if nuevas_conexiones:
    print(f"\n{'─'*80}")
    print(f"\n¿Quieres agregar estas {len(nuevas_conexiones)} conexiones al grafo? (s/n): ", end='')
    respuesta = input().strip().lower()
    
    if respuesta == 's':
        # Cargar grafo actual
        with open("data/grafos/red_peru_24_departamentos.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Agregar nuevas conexiones
        data['aristas'].extend(nuevas_conexiones)
        
        # Guardar
        with open("data/grafos/red_peru_24_departamentos.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Grafo actualizado con {len(nuevas_conexiones)} nuevas conexiones!")
        print(f"   Total de aristas ahora: {len(data['aristas'])}")
        print(f"\n💡 El servidor debería recargar automáticamente.")
        print(f"   Refresca el navegador y prueba de nuevo.")
    else:
        print("\n❌ No se realizaron cambios")
else:
    print("\n✅ No se encontraron conexiones faltantes - El grafo está completo")

print("\n" + "="*80 + "\n")
