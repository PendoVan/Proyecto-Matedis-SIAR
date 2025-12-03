"""
Script para diagnosticar rutas con backtracking
Ejecutar y pegar la salida para identificar el problema
"""
import sys
sys.path.insert(0, '.')

from src.unidad3_grafos.grafo_rutas import GrafoRutas
from src.unidad3_grafos.algoritmo_fiabilidad_geo import AlgoritmoFiabilidadGeo

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

def detectar_backtracking(ruta_nodos):
    """Detecta si hay nodos repetidos (backtracking)"""
    visitados = set()
    repetidos = []
    for i, nodo in enumerate(ruta_nodos):
        if nodo in visitados:
            repetidos.append((i, nodo))
        visitados.add(nodo)
    return repetidos

print("\n" + "="*80)
print("🔍 DIAGNÓSTICO DE BACKTRACKING EN RUTAS")
print("="*80 + "\n")

grafo = GrafoRutas.cargar_json("data/grafos/red_peru_24_departamentos.json")
algoritmo = AlgoritmoFiabilidadGeo(grafo, COORDENADAS)

# Probar rutas problemáticas comunes
rutas_test = [
    ("Cajamarca", "Loreto"),
    ("Cajamarca", "Ucayali"),
    ("Cajamarca", "Madre de Dios"),
    ("Lambayeque", "Loreto"),
    ("Lima", "Loreto"),
    ("Piura", "Loreto"),
]

print("Probando rutas comunes que podrían tener backtracking...\n")

for origen, destino in rutas_test:
    print(f"\n{'─'*80}")
    print(f"📍 {origen} → {destino}\n")
    
    try:
        ruta = algoritmo.encontrar_ruta_mas_fiable(origen, destino)
        if ruta:
            print(f"   Ruta: {' → '.join(ruta.nodos)}")
            print(f"   Distancia: {ruta.distancia_total_km:.0f} km")
            
            # Detectar backtracking
            repetidos = detectar_backtracking(ruta.nodos)
            if repetidos:
                print(f"\n   ⚠️  BACKTRACKING DETECTADO:")
                for pos, nodo in repetidos:
                    print(f"      • '{nodo}' aparece dos veces (2da vez en posición {pos})")
                print(f"\n   💡 SOLUCIÓN: Agregar conexión directa entre los nodos antes y después del backtrack")
            else:
                print(f"   ✅ Sin backtracking")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "="*80)
print("\n📋 Copia y pega la salida completa para identificar qué conexiones faltan")
print("="*80 + "\n")
