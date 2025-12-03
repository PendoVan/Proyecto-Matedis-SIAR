"""
Verificación visual completa - Prueba de rutas mejoradas
"""
import sys
sys.path.insert(0, '.')

from src.unidad3_grafos.grafo_rutas import GrafoRutas
from src.unidad3_grafos.algoritmo_fiabilidad_geo import AlgoritmoFiabilidadGeo

# Todas las coordenadas
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

print("\n" + "="*80)
print("🧪 VERIFICACIÓN COMPLETA DEL SISTEMA DE RUTAS")
print("="*80 + "\n")

# Cargar grafo
try:
    grafo = GrafoRutas.cargar_json("data/grafos/red_peru_24_departamentos.json")
    print(f"✅ Grafo cargado correctamente")
    print(f"   📊 Nodos: {len(grafo.nodos)}")
    print(f"   📊 Aristas: {sum(len(v) for v in grafo.adyacencias.values()) // 2}\n")
except Exception as e:
    print(f"❌ Error cargando grafo: {e}")
    sys.exit(1)

# Crear algoritmo
algoritmo = AlgoritmoFiabilidadGeo(grafo, COORDENADAS)
print(f"✅ Algoritmo geográfico inicializado")
print(f"   🎯 Penalización activa: {algoritmo.ENABLE_DIRECTION_PENALTY}")
print(f"   🎯 Fuerza: {algoritmo.DIRECTION_PENALTY_STRENGTH * 100}%\n")

# Casos de prueba
casos_prueba = [
    ("Lambayeque", "Loreto", "Caso reportado por el usuario"),
    ("Lima", "Loreto", "Ruta desde capital"),
    ("Lima", "Madre de Dios", "Ruta a selva sur"),
]

for i, (origen, destino, descripcion) in enumerate(casos_prueba, 1):
    print("─" * 80)
    print(f"\n🧪 CASO {i}: {origen} → {destino}")
    print(f"   ({descripcion})\n")
    
    try:
        comp = algoritmo.comparar_rutas(origen, destino)
        
        # Verificar si las rutas son diferentes
        rutas_diferentes = False
        if comp['mas_fiable'] and comp['mas_corta'] and comp['mas_rapida']:
            nodos_fiable = comp['mas_fiable'].nodos
            nodos_corta = comp['mas_corta'].nodos
            nodos_rapida = comp['mas_rapida'].nodos
            
            if nodos_fiable != nodos_corta or nodos_corta != nodos_rapida:
                rutas_diferentes = True
        
        # Mostrar resultados
        print("   🟢 MÁS FIABLE:")
        if comp['mas_fiable']:
            r = comp['mas_fiable']
            print(f"      Ruta: {' → '.join(r.nodos)}")
            print(f"      📏 {r.distancia_total_km:.0f} km | 🎯 {r.fiabilidad_acumulada:.1%} fiab | ⏱️ {r.tiempo_total_min} min")
        
        print("\n   🔵 MÁS CORTA:")
        if comp['mas_corta']:
            r = comp['mas_corta']
            print(f"      Ruta: {' → '.join(r.nodos)}")
            print(f"      📏 {r.distancia_total_km:.0f} km | 🎯 {r.fiabilidad_acumulada:.1%} fiab | ⏱️ {r.tiempo_total_min} min")
        
        print("\n   🟡 MÁS RÁPIDA:")
        if comp['mas_rapida']:
            r = comp['mas_rapida']
            print(f"      Ruta: {' → '.join(r.nodos)}")
            print(f"      📏 {r.distancia_total_km:.0f} km | 🎯 {r.fiabilidad_acumulada:.1%} fiab | ⏱️ {r.tiempo_total_min} min")
        
        # Veredicto
        print()
        if rutas_diferentes:
            print("   ✅ RESULTADO: Las rutas son DIFERENTES - Sistema funcionando correctamente")
        else:
            print("   ⚠️  RESULTADO: Las rutas son IDÉNTICAS - Puede necesitar más conexiones")
        print()
        
    except Exception as e:
        print(f"   ❌ Error: {e}\n")

print("="*80)
print("\n📋 RESUMEN:")
print("   • Si ves rutas DIFERENTES → El sistema está funcionando correctamente ✅")
print("   • Si ves rutas IDÉNTICAS → Necesitas agregar más conexiones al grafo ⚠️")
print("\n💡 PRÓXIMO PASO:")
print("   Abre http://localhost:8000 y prueba las mismas rutas en el frontend")
print("="*80 + "\n")
