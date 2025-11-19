"""
Módulo: grafo_peru_24_departamentos.py
Descripción: Grafo completo del Perú con los 24 departamentos y sus conexiones principales.
Basado en la red vial real del país.
"""

import json
import os
from enum import Enum

class TipoCamino(Enum):
    """Tipos de camino según su condición"""
    ASFALTADO = "asfaltado"
    AFIRMADO = "afirmado"
    TROCHA = "trocha"
    HERRADURA = "herradura"


# ========== COORDENADAS GPS DE LOS 24 DEPARTAMENTOS ==========
COORDENADAS_PERU = {
    # COSTA
    'Lima': {'lat': -12.0464, 'lon': -77.0428, 'poblacion': 9674755, 'region': 'costa'},
    'Callao': {'lat': -12.0565, 'lon': -77.1181, 'poblacion': 1010315, 'region': 'costa'},
    'Ica': {'lat': -14.0678, 'lon': -75.7286, 'poblacion': 430800, 'region': 'costa'},
    'Arequipa': {'lat': -16.4090, 'lon': -71.5375, 'poblacion': 1008290, 'region': 'costa'},
    'Moquegua': {'lat': -17.1934, 'lon': -70.9336, 'poblacion': 185000, 'region': 'costa'},
    'Tacna': {'lat': -18.0047, 'lon': -70.2453, 'poblacion': 330000, 'region': 'costa'},
    'Tumbes': {'lat': -3.5669, 'lon': -80.4515, 'poblacion': 240000, 'region': 'costa'},
    'Piura': {'lat': -5.1945, 'lon': -80.6328, 'poblacion': 730000, 'region': 'costa'},
    'Lambayeque': {'lat': -6.7011, 'lon': -79.9061, 'poblacion': 282000, 'region': 'costa'},
    'La Libertad': {'lat': -8.1116, 'lon': -79.0292, 'poblacion': 938000, 'region': 'costa'},
    'Ancash': {'lat': -9.5267, 'lon': -77.5284, 'poblacion': 1150000, 'region': 'costa-sierra'},
    
    # SIERRA
    'Cajamarca': {'lat': -7.1614, 'lon': -78.5126, 'poblacion': 283767, 'region': 'sierra'},
    'Huánuco': {'lat': -9.9306, 'lon': -76.2422, 'poblacion': 79000, 'region': 'sierra'},
    'Pasco': {'lat': -10.6819, 'lon': -76.2561, 'poblacion': 270000, 'region': 'sierra'},
    'Junín': {'lat': -12.0699, 'lon': -75.2048, 'poblacion': 430000, 'region': 'sierra'},
    'Huancavelica': {'lat': -12.7872, 'lon': -74.9758, 'poblacion': 50000, 'region': 'sierra'},
    'Ayacucho': {'lat': -13.1631, 'lon': -74.2236, 'poblacion': 180000, 'region': 'sierra'},
    'Apurímac': {'lat': -13.6344, 'lon': -72.8831, 'poblacion': 120000, 'region': 'sierra'},
    'Cusco': {'lat': -13.5319, 'lon': -71.9675, 'poblacion': 437538, 'region': 'sierra'},
    'Puno': {'lat': -15.8422, 'lon': -70.0199, 'poblacion': 140839, 'region': 'sierra'},
    
    # SELVA
    'Amazonas': {'lat': -5.7667, 'lon': -77.8667, 'poblacion': 32026, 'region': 'selva'},
    'San Martín': {'lat': -6.4833, 'lon': -76.3667, 'poblacion': 62387, 'region': 'selva'},
    'Loreto': {'lat': -3.7499, 'lon': -73.2540, 'poblacion': 492000, 'region': 'selva'},
    'Ucayali': {'lat': -8.3791, 'lon': -74.5539, 'poblacion': 502000, 'region': 'selva'},
    'Madre de Dios': {'lat': -12.5935, 'lon': -69.1892, 'poblacion': 130000, 'region': 'selva'}
}


# ========== RUTAS PRINCIPALES DEL PERÚ ==========
RUTAS_PERU = [
    # ===== EJE COSTERO (PANAMERICANA) =====
    {'origen': 'Tumbes', 'destino': 'Piura', 'km': 285, 'fiab': 0.92, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.08},
    {'origen': 'Piura', 'destino': 'Lambayeque', 'km': 210, 'fiab': 0.93, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.07},
    {'origen': 'Lambayeque', 'destino': 'La Libertad', 'km': 205, 'fiab': 0.94, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.06},
    {'origen': 'La Libertad', 'destino': 'Ancash', 'km': 302, 'fiab': 0.90, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.10},
    {'origen': 'Ancash', 'destino': 'Lima', 'km': 408, 'fiab': 0.93, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.07},
    {'origen': 'Lima', 'destino': 'Callao', 'km': 15, 'fiab': 0.98, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.02},
    {'origen': 'Lima', 'destino': 'Ica', 'km': 305, 'fiab': 0.95, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.05},
    {'origen': 'Ica', 'destino': 'Arequipa', 'km': 710, 'fiab': 0.92, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.08},
    {'origen': 'Arequipa', 'destino': 'Moquegua', 'km': 215, 'fiab': 0.91, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.09},
    {'origen': 'Moquegua', 'destino': 'Tacna', 'km': 145, 'fiab': 0.93, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.07},
    
    # ===== CONEXIONES COSTA-SIERRA =====
    {'origen': 'Lima', 'destino': 'Junín', 'km': 305, 'fiab': 0.85, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.18},
    {'origen': 'Lima', 'destino': 'Huancavelica', 'km': 450, 'fiab': 0.78, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.25},
    {'origen': 'Lima', 'destino': 'Ayacucho', 'km': 565, 'fiab': 0.82, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.22},
    {'origen': 'La Libertad', 'destino': 'Cajamarca', 'km': 300, 'fiab': 0.86, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.16},
    {'origen': 'Ancash', 'destino': 'Huánuco', 'km': 155, 'fiab': 0.83, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.20},
    {'origen': 'Ica', 'destino': 'Huancavelica', 'km': 265, 'fiab': 0.75, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.30},
    
    # ===== CORREDOR SIERRA CENTRAL =====
    {'origen': 'Cajamarca', 'destino': 'Huánuco', 'km': 445, 'fiab': 0.74, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.32},
    {'origen': 'Huánuco', 'destino': 'Pasco', 'km': 105, 'fiab': 0.80, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.22},
    {'origen': 'Pasco', 'destino': 'Junín', 'km': 130, 'fiab': 0.85, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.18},
    {'origen': 'Junín', 'destino': 'Huancavelica', 'km': 147, 'fiab': 0.78, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.26},
    {'origen': 'Huancavelica', 'destino': 'Ayacucho', 'km': 245, 'fiab': 0.72, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.32},
    {'origen': 'Ayacucho', 'destino': 'Apurímac', 'km': 265, 'fiab': 0.70, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.35},
    {'origen': 'Apurímac', 'destino': 'Cusco', 'km': 195, 'fiab': 0.82, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.20},
    
    # ===== CORREDOR SIERRA SUR =====
    {'origen': 'Arequipa', 'destino': 'Puno', 'km': 295, 'fiab': 0.88, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.15},
    {'origen': 'Cusco', 'destino': 'Puno', 'km': 389, 'fiab': 0.90, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.12},
    {'origen': 'Cusco', 'destino': 'Arequipa', 'km': 510, 'fiab': 0.86, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.16},
    {'origen': 'Ayacucho', 'destino': 'Cusco', 'km': 590, 'fiab': 0.75, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.30},
    {'origen': 'Junín', 'destino': 'Cusco', 'km': 595, 'fiab': 0.78, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.28},
    {'origen': 'Puno', 'destino': 'Ayacucho', 'km': 680, 'fiab': 0.72, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.32},
    
    # ===== CONEXIONES SELVA =====
    {'origen': 'Tumbes', 'destino': 'Loreto', 'km': 1450, 'fiab': 0.60, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.45},
    {'origen': 'Piura', 'destino': 'Cajamarca', 'km': 365, 'fiab': 0.81, 'tipo': TipoCamino.ASFALTADO, 'riesgo': 0.22},
    {'origen': 'Cajamarca', 'destino': 'Amazonas', 'km': 318, 'fiab': 0.70, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.35},
    {'origen': 'Amazonas', 'destino': 'San Martín', 'km': 420, 'fiab': 0.65, 'tipo': TipoCamino.TROCHA, 'riesgo': 0.42},
    {'origen': 'Cajamarca', 'destino': 'San Martín', 'km': 520, 'fiab': 0.68, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.38},
    {'origen': 'San Martín', 'destino': 'Loreto', 'km': 585, 'fiab': 0.62, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.43},
    {'origen': 'Huánuco', 'destino': 'Ucayali', 'km': 455, 'fiab': 0.67, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.40},
    {'origen': 'Junín', 'destino': 'San Martín', 'km': 485, 'fiab': 0.70, 'tipo': TipoCamino.TROCHA, 'riesgo': 0.35},
    {'origen': 'Ucayali', 'destino': 'Loreto', 'km': 620, 'fiab': 0.58, 'tipo': TipoCamino.TROCHA, 'riesgo': 0.48},
    {'origen': 'Cusco', 'destino': 'Madre de Dios', 'km': 530, 'fiab': 0.63, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.42},
    {'origen': 'Ucayali', 'destino': 'Madre de Dios', 'km': 690, 'fiab': 0.55, 'tipo': TipoCamino.TROCHA, 'riesgo': 0.50},
    {'origen': 'Puno', 'destino': 'Madre de Dios', 'km': 720, 'fiab': 0.60, 'tipo': TipoCamino.AFIRMADO, 'riesgo': 0.45}
]


def crear_grafo_peru_completo():
    """Crea el grafo completo con 24 departamentos."""
    print("="*70)
    print("🗺️  CREANDO GRAFO DE PERÚ COMPLETO")
    print("   24 Departamentos - Red Vial Nacional")
    print("="*70 + "\n")
    
    # Crear estructura JSON directamente
    grafo_data = {
        "nodos": list(COORDENADAS_PERU.keys()),
        "aristas": []
    }
    
    # Agregar metadata
    metadata = {}
    print("📍 Agregando departamentos...\n")
    for depto, info in COORDENADAS_PERU.items():
        metadata[depto] = {
            'tipo': 'departamento',
            'latitud': info['lat'],
            'longitud': info['lon'],
            'poblacion': info['poblacion'],
            'region': info['region']
        }
        print(f"  ✓ {depto:20s} | {info['region']:12s} | {info['poblacion']:>8,} hab")
    
    print(f"\n✅ {len(grafo_data['nodos'])} departamentos agregados\n")
    
    # Agregar rutas
    print("🛣️  Agregando rutas principales...\n")
    
    for i, ruta in enumerate(RUTAS_PERU, 1):
        arista = {
            "origen": ruta['origen'],
            "destino": ruta['destino'],
            "distancia_km": ruta['km'],
            "fiabilidad": ruta['fiab'],
            "tipo_camino": ruta['tipo'].value,
            "riesgo_historico": ruta['riesgo'],
            "tiempo_estimado_min": int((ruta['km'] / 60) * 60)  # Estimado
        }
        grafo_data["aristas"].append(arista)
        
        print(f"  {i:2d}. {ruta['origen']:15s} ↔ {ruta['destino']:15s} | "
              f"{ruta['km']:4d} km | {ruta['fiab']:.0%} | {ruta['tipo'].value}")
    
    print(f"\n✅ {len(RUTAS_PERU)} rutas principales agregadas\n")
    
    return grafo_data, metadata


def calcular_estadisticas(grafo_data):
    """Calcula y muestra estadísticas de la red."""
    print("="*70)
    print("📊 ESTADÍSTICAS DE LA RED VIAL")
    print("="*70 + "\n")
    
    # Contar por región
    regiones = {}
    for depto, info in COORDENADAS_PERU.items():
        region = info['region']
        regiones[region] = regiones.get(region, 0) + 1
    
    print("🌍 Distribución geográfica:")
    for region, count in sorted(regiones.items()):
        print(f"   {region.capitalize():15s}: {count:2d} departamentos")
    
    # Estadísticas de rutas
    num_rutas = len(grafo_data["aristas"])
    distancia_total = sum(a["distancia_km"] for a in grafo_data["aristas"])
    fiabilidad_promedio = sum(a["fiabilidad"] for a in grafo_data["aristas"]) / num_rutas
    
    tipos_camino = {}
    for arista in grafo_data["aristas"]:
        tipo = arista["tipo_camino"]
        tipos_camino[tipo] = tipos_camino.get(tipo, 0) + 1
    
    print(f"\n📏 Red vial:")
    print(f"   Rutas totales: {num_rutas}")
    print(f"   Distancia total: {distancia_total:,} km")
    print(f"   Fiabilidad promedio: {fiabilidad_promedio:.1%}")
    
    print(f"\n🛣️  Distribución por tipo de camino:")
    for tipo, cantidad in sorted(tipos_camino.items()):
        porcentaje = (cantidad / num_rutas) * 100
        print(f"   {tipo.capitalize():15s}: {cantidad:2d} rutas ({porcentaje:5.1f}%)")
    
    print("\n" + "="*70 + "\n")


def exportar_datos(grafo_data):
    """Exporta el grafo y las coordenadas."""
    # Exportar grafo
    ruta_grafo = "data/grafos/red_peru_24_departamentos.json"
    os.makedirs("data/grafos", exist_ok=True)
    with open(ruta_grafo, 'w', encoding='utf-8') as f:
        json.dump(grafo_data, f, indent=2, ensure_ascii=False)
    print(f"💾 Grafo guardado en: {ruta_grafo}")
    
    # Exportar coordenadas
    ruta_coords = "data/grafos/coordenadas_peru_24.json"
    with open(ruta_coords, 'w', encoding='utf-8') as f:
        json.dump(COORDENADAS_PERU, f, indent=2, ensure_ascii=False)
    print(f"💾 Coordenadas guardadas en: {ruta_coords}\n")


if __name__ == "__main__":
    # Crear grafo
    grafo_data, metadata = crear_grafo_peru_completo()
    
    # Estadísticas
    calcular_estadisticas(grafo_data)
    
    # Exportar
    exportar_datos(grafo_data)
    
    print("="*70)
    print("✅ GRAFO DE PERÚ COMPLETO CREADO")
    print("="*70)
    print("\nPara usar este grafo en tu API:")
    print("1. El archivo JSON ya está en data/grafos/red_peru_24_departamentos.json")
    print("2. Actualiza api_siar.py para cargar este archivo en lugar de red_peru_completa.json")
    print("3. Actualiza el frontend para usar coordenadas_peru_24.json")