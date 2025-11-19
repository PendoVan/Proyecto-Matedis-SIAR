"""
Módulo: grafo_peru_completo.py
Descripción: Grafo completo de Perú con 9 departamentos y distancias reales.
Incluye: Cajamarca, San Martín, Lima, Cusco, Puno, Arequipa, Junín, Ayacucho, Amazonas
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.unidad3_grafos.grafo_rutas import GrafoRutas, TipoCamino
import json


# Coordenadas GPS reales de capitales departamentales
COORDENADAS_DEPARTAMENTOS = {
    'Lima': {'lat': -12.0464, 'lon': -77.0428, 'poblacion': 9674755},
    'Cusco': {'lat': -13.5319, 'lon': -71.9675, 'poblacion': 437538},
    'Arequipa': {'lat': -16.4090, 'lon': -71.5375, 'poblacion': 1008290},
    'Puno': {'lat': -15.8422, 'lon': -70.0199, 'poblacion': 140839},
    'Ayacucho': {'lat': -13.1631, 'lon': -74.2236, 'poblacion': 180000},
    'Junín': {'lat': -12.0699, 'lon': -75.2048, 'poblacion': 430000},
    'Cajamarca': {'lat': -7.1614, 'lon': -78.5126, 'poblacion': 283767},
    'San Martín': {'lat': -6.4833, 'lon': -76.3667, 'poblacion': 62387},
    'Amazonas': {'lat': -5.7667, 'lon': -77.8667, 'poblacion': 32026}
}


# Rutas reales con distancias aproximadas (carretera)
RUTAS_PRINCIPALES = [
    # Eje costero (Panamericana)
    {'origen': 'Lima', 'destino': 'Arequipa', 'km': 1010, 'fiab': 0.92, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.08},
    {'origen': 'Arequipa', 'destino': 'Puno', 'km': 295, 'fiab': 0.88, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.15},
    
    # Eje Lima-Sierra
    {'origen': 'Lima', 'destino': 'Junín', 'km': 305, 'fiab': 0.85, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.18},
    {'origen': 'Lima', 'destino': 'Ayacucho', 'km': 565, 'fiab': 0.82, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.22},
    
    # Eje sierra central
    {'origen': 'Junín', 'destino': 'Cusco', 'km': 595, 'fiab': 0.78, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.28},
    {'origen': 'Junín', 'destino': 'Ayacucho', 'km': 255, 'fiab': 0.80, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.25},
    {'origen': 'Ayacucho', 'destino': 'Cusco', 'km': 590, 'fiab': 0.75, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.30},
    
    # Eje sur (Corredor turístico)
    {'origen': 'Cusco', 'destino': 'Puno', 'km': 389, 'fiab': 0.90, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.12},
    {'origen': 'Cusco', 'destino': 'Arequipa', 'km': 510, 'fiab': 0.86, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.16},
    
    # Eje norte (Selva)
    {'origen': 'Cajamarca', 'destino': 'Amazonas', 'km': 318, 'fiab': 0.70, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.35},
    {'origen': 'Amazonas', 'destino': 'San Martín', 'km': 420, 'fiab': 0.65, 'tipo': TipoCamino.TROCHA, 'riesgo': 0.42},
    {'origen': 'Cajamarca', 'destino': 'San Martín', 'km': 520, 'fiab': 0.68, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.38},
    
    # Conexiones costa-norte
    {'origen': 'Lima', 'destino': 'Cajamarca', 'km': 865, 'fiab': 0.83, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.20},
    
    # Rutas alternativas importantes
    {'origen': 'Puno', 'destino': 'Ayacucho', 'km': 680, 'fiab': 0.72, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.32},
    {'origen': 'San Martín', 'destino': 'Junín', 'km': 485, 'fiab': 0.70, 'tipo': TipoCamino.TROCHA, 'riesgo': 0.35}
]


def crear_grafo_peru_completo() -> GrafoRutas:
    """
    Crea el grafo completo de Perú con 9 departamentos.
    Incluye rutas principales con distancias reales.
    """
    print("🗺️  Creando grafo de Perú (9 departamentos)...\n")
    
    grafo = GrafoRutas()
    
    # Agregar nodos (departamentos)
    for depto, info in COORDENADAS_DEPARTAMENTOS.items():
        metadata = {
            'tipo': 'departamento',
            'latitud': info['lat'],
            'longitud': info['lon'],
            'poblacion': info['poblacion']
        }
        grafo.agregar_nodo(depto, metadata)
        print(f"✓ {depto:15s} | {info['lat']:7.4f}, {info['lon']:8.4f}")
    
    print(f"\n📍 {len(grafo.nodos)} departamentos agregados\n")
    
    # Agregar rutas
    print("🛣️  Agregando rutas principales:\n")
    
    for i, ruta in enumerate(RUTAS_PRINCIPALES, 1):
        grafo.agregar_camino(
            origen=ruta['origen'],
            destino=ruta['destino'],
            distancia_km=ruta['km'],
            fiabilidad=ruta['fiab'],
            tipo_camino=ruta['tipo'],
            riesgo_historico=ruta['riesgo']
        )
        
        print(f"{i:2d}. {ruta['origen']:12s} ↔ {ruta['destino']:12s} | "
              f"{ruta['km']:4d} km | Fiab: {ruta['fiab']:.0%} | {ruta['tipo'].value}")
    
    print(f"\n✅ Grafo completo: {len(grafo.nodos)} nodos, "
          f"{sum(len(v) for v in grafo.adyacencias.values()) // 2} rutas\n")
    
    return grafo


def exportar_coordenadas_json(ruta_archivo: str = "data/grafos/coordenadas_peru.json"):
    """Exporta las coordenadas para usar en el frontend."""
    os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
    
    with open(ruta_archivo, 'w', encoding='utf-8') as f:
        json.dump(COORDENADAS_DEPARTAMENTOS, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Coordenadas guardadas en: {ruta_archivo}")


def calcular_estadisticas_red(grafo: GrafoRutas):
    """Calcula estadísticas de la red vial."""
    print("\n" + "="*70)
    print("📊 ESTADÍSTICAS DE LA RED VIAL")
    print("="*70 + "\n")
    
    # Distancia total
    distancia_total = 0
    fiabilidad_promedio = 0
    num_rutas = 0
    
    tipos_camino = {}
    
    rutas_vistas = set()
    for origen, aristas in grafo.adyacencias.items():
        for arista in aristas:
            par = tuple(sorted([arista.origen, arista.destino]))
            if par not in rutas_vistas:
                distancia_total += arista.distancia_km
                fiabilidad_promedio += arista.fiabilidad
                num_rutas += 1
                
                tipo = arista.tipo_camino.value
                tipos_camino[tipo] = tipos_camino.get(tipo, 0) + 1
                
                rutas_vistas.add(par)
    
    fiabilidad_promedio /= num_rutas
    
    print(f"🌐 Cobertura de red:")
    print(f"   Departamentos: {len(grafo.nodos)}")
    print(f"   Rutas totales: {num_rutas}")
    print(f"   Distancia total: {distancia_total:,} km\n")
    
    print(f"📈 Calidad promedio:")
    print(f"   Fiabilidad media: {fiabilidad_promedio:.1%}\n")
    
    print(f"🛣️  Distribución por tipo de camino:")
    for tipo, cantidad in sorted(tipos_camino.items()):
        porcentaje = (cantidad / num_rutas) * 100
        print(f"   {tipo:12s}: {cantidad:2d} rutas ({porcentaje:.1f}%)")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    print("="*70)
    print(" "*20 + "GRAFO DE PERÚ")
    print(" "*15 + "Sistema de Rutas Nacional")
    print("="*70 + "\n")
    
    # Crear grafo
    grafo = crear_grafo_peru_completo()
    
    # Exportar coordenadas
    exportar_coordenadas_json()
    
    # Guardar grafo
    ruta_salida = "data/grafos/red_peru_completa.json"
    os.makedirs("data/grafos", exist_ok=True)
    grafo.exportar_json(ruta_salida)
    print(f"💾 Grafo guardado en: {ruta_salida}\n")
    
    # Estadísticas
    calcular_estadisticas_red(grafo)
    
    # Ejemplos de rutas
    print("🔍 EJEMPLOS DE RUTAS:\n")
    
    from src.unidad3_grafos.algoritmo_fiabilidad import AlgoritmoFiabilidad
    
    algoritmo = AlgoritmoFiabilidad(grafo)
    
    ejemplos = [
        ('Lima', 'Cusco'),
        ('Cajamarca', 'San Martín'),
        ('Lima', 'Puno'),
        ('Arequipa', 'Ayacucho')
    ]
    
    for origen, destino in ejemplos:
        try:
            ruta = algoritmo.encontrar_ruta_mas_fiable(origen, destino)
            if ruta:
                print(f"📍 {origen} → {destino}")
                print(f"   Ruta: {' → '.join(ruta.nodos)}")
                print(f"   Distancia: {ruta.distancia_total_km:.0f} km")
                print(f"   Fiabilidad: {ruta.fiabilidad_acumulada:.1%}")
                print(f"   Tiempo estimado: {ruta.tiempo_total_min//60}h {ruta.tiempo_total_min%60}min\n")
        except Exception as e:
            print(f"❌ No se pudo calcular ruta {origen} → {destino}: {e}\n")
    
    print("✅ PROCESO COMPLETADO")