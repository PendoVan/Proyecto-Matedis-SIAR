"""
Script de prueba para verificar la optimización geográfica de rutas.
Compara rutas antes y después del parche.
"""

import sys
sys.path.insert(0, '.')

from src.unidad3_grafos.grafo_rutas import GrafoRutas
from src.unidad3_grafos.algoritmo_fiabilidad import AlgoritmoFiabilidad
from src.unidad3_grafos.algoritmo_fiabilidad_geo import AlgoritmoFiabilidadGeo

# Coordenadas de departamentos
COORDENADAS = {
    'Lima': {'lat': -12.0464, 'lon': -77.0428},
    'Cajamarca': {'lat': -7.1614, 'lon': -78.5126},
    'Loreto': {'lat': -3.7499, 'lon': -73.2540},
    'Ucayali': {'lat': -8.3791, 'lon': -74.5539},
    'Madre de Dios': {'lat': -12.5935, 'lon': -69.1892},
    'Pucallpa': {'lat': -8.3791, 'lon': -74.5539},  # alias de Ucayali
}

print("\n" + "="*70)
print("🧪 PRUEBA DE OPTIMIZACIÓN GEOGRÁFICA DE RUTAS")
print("="*70 + "\n")

# Cargar grafo
try:
    grafo = GrafoRutas.cargar_json("data/grafos/red_peru_24_departamentos.json")
    print(f"✅ Grafo cargado: {len(grafo.nodos)} departamentos\n")
except Exception as e:
    print(f"❌ Error cargando grafo: {e}")
    sys.exit(1)

# Crear ambos algoritmos
algo_original = AlgoritmoFiabilidad(grafo)
algo_geo = AlgoritmoFiabilidadGeo(grafo, COORDENADAS)

# Configurar el algoritmo geográfico
print("Configuración del algoritmo geográfico:")
print(f"  - Penalización habilitada: {algo_geo.ENABLE_DIRECTION_PENALTY}")
print(f"  - Fuerza de penalización: {algo_geo.DIRECTION_PENALTY_STRENGTH * 100}%")
print(f"  - Ángulo mínimo de desviación: {algo_geo.MIN_DEVIATION_ANGLE}°\n")

# Casos de prueba
test_cases = [
    ("Lima", "Loreto"),
    ("Lima", "Ucayali"),
    ("Lima",  "Madre de Dios"),
]

for origen, destino in test_cases:
    print("-" * 70)
    print(f"📍 Ruta: {origen} → {destino}\n")
    
    # Ruta con algoritmo original
    try:
        ruta_original = algo_original.encontrar_ruta_mas_fiable(origen, destino)
        if ruta_original:
            print(f"  🔵 Algoritmo ORIGINAL:")
            print(f"     Camino: {' → '.join(ruta_original.nodos)}")
            print(f"     Distancia: {ruta_original.distancia_total_km:.1f} km")
            print(f"     Fiabilidad: {ruta_original.fiabilidad_acumulada:.2%}")
            print(f"     Peso: {ruta_original.peso_total:.2f}\n")
        else:
            print("  ❌ No se encontró ruta (algoritmo original)\n")
    except Exception as e:
        print(f"  ❌ Error (original): {e}\n")
    
    # Ruta con algoritmo geográfico
    try:
        ruta_geo = algo_geo.encontrar_ruta_mas_fiable(origen, destino)
        if ruta_geo:
            print(f"  🟢 Algoritmo CON OPTIMIZACIÓN GEOGRÁFICA:")
            print(f"     Camino: {' → '.join(ruta_geo.nodos)}")
            print(f"     Distancia: {ruta_geo.distancia_total_km:.1f} km")
            print(f"     Fiabilidad: {ruta_geo.fiabilidad_acumulada:.2%}")
            print(f"     Peso: {ruta_geo.peso_total:.2f}\n")
            
            # Comparar
            if ruta_original and ruta_original.nodos != ruta_geo.nodos:
                print("  ✨ ¡RUTA MEJORADA! El algoritmo geográfico encontró un camino diferente")
            elif ruta_original and ruta_original.nodos == ruta_geo.nodos:
                print("  ℹ️  Misma ruta -route directa sin desvíos innecesarios")
        else:
            print("  ❌ No se encontró ruta (algoritmo geo)\n")
    except Exception as e:
        print(f"  ❌ Error (geo): {e}\n")

print("\n" + "="*70)
print("✅ Prueba completada")
print("="*70 + "\n")
