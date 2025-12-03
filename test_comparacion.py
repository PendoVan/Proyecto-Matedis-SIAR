"""
Prueba rápida de comparación de rutas con el grafo actualizado
"""
import sys
sys.path.insert(0, '.')

from src.unidad3_grafos.grafo_rutas import GrafoRutas
from src.unidad3_grafos.algoritmo_fiabilidad_geo import AlgoritmoFiabilidadGeo

# Coordenadas
COORDENADAS = {
    'Lambayeque': {'lat': -6.7011, 'lon': -79.9061},
    'Loreto': {'lat': -3.7499, 'lon': -73.2540},
    'Cajamarca': {'lat': -7.1614, 'lon': -78.5126},
    'San Martín': {'lat': -6.4833, 'lon': -76.3667},
    'Amazonas': {'lat': -5.7667, 'lon': -77.8667},
    'La Libertad': {'lat': -8.1116, 'lon': -79.0292},
}

# Cargar grafo
grafo = GrafoRutas.cargar_json("data/grafos/red_peru_24_departamentos.json")
algoritmo = AlgoritmoFiabilidadGeo(grafo, COORDENADAS)

print("\n" + "="*70)
print("COMPARACIÓN DE RUTAS: Lambayeque → Loreto")
print("="*70 + "\n")

# Comparar rutas
comparacion = algoritmo.comparar_rutas("Lambayeque", "Loreto")

print("🟢 MÁS FIABLE:")
if comparacion['mas_fiable']:
    r = comparacion['mas_fiable']
    print(f"   Ruta: {' → '.join(r.nodos)}")
    print(f"   Distancia: {r.distancia_total_km:.1f} km")
    print(f"   Fiabilidad: {r.fiabilidad_acumulada:.2%}")
    print(f"   Tiempo: {r.tiempo_total_min} min\n")

print("🔵 MÁS CORTA:")
if comparacion['mas_corta']:
    r = comparacion['mas_corta']
    print(f"   Ruta: {' → '.join(r.nodos)}")
    print(f"   Distancia: {r.distancia_total_km:.1f} km")
    print(f"   Fiabilidad: {r.fiabilidad_acumulada:.2%}")
    print(f"   Tiempo: {r.tiempo_total_min} min\n")

print("🟡 MÁS RÁPIDA:")
if comparacion['mas_rapida']:
    r = comparacion['mas_rapida']
    print(f"   Ruta: {' → '.join(r.nodos)}")
    print(f"   Distancia: {r.distancia_total_km:.1f} km")
    print(f"   Fiabilidad: {r.fiabilidad_acumulada:.2%}")
    print(f"   Tiempo: {r.tiempo_total_min} min\n")

# Verificar si son diferentes
if (comparacion['mas_fiable'].nodos == comparacion['mas_corta'].nodos == 
    comparacion['mas_rapida'].nodos):
    print("⚠️  Las tres rutas son IDÉNTICAS - Aún faltan conexiones alternativas")
else:
    print("✅ Las rutas son DIFERENTES - Grafo mejorado correctamente")

print("\n" + "="*70)
print(f"Total de nodos en el grafo: {len(grafo.nodos)}")
print(f"Total de aristas: {sum(len(v) for v in grafo.adyacencias.values()) // 2}")
print("="*70 + "\n")
