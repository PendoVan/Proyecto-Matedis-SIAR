"""
Script: generar_grafo_demo.py
Descripción: Genera un grafo de demostración con datos realistas de la región de Ayacucho.
"""

import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.unidad3_grafos.grafo_rutas import GrafoRutas, TipoCamino


def crear_grafo_ayacucho() -> GrafoRutas:
    """
    Crea un grafo representando la red vial de Ayacucho.
    
    Basado en datos aproximados de distancias y condiciones reales.
    """
    grafo = GrafoRutas()
    
    # Definir nodos con metadata
    nodos_metadata = {
        "Ayacucho": {"tipo": "capital", "poblacion": 180000, "altitud": 2746},
        "Huanta": {"tipo": "ciudad", "poblacion": 45000, "altitud": 2628},
        "San Miguel": {"tipo": "ciudad", "poblacion": 8000, "altitud": 2660},
        "Tambo": {"tipo": "pueblo", "poblacion": 3000, "altitud": 3200},
        "Sivia": {"tipo": "pueblo", "poblacion": 5000, "altitud": 580},
        "Quinua": {"tipo": "pueblo_historico", "poblacion": 2500, "altitud": 3300},
        "Huamanga": {"tipo": "distrito", "poblacion": 90000, "altitud": 2746}
    }
    
    for nodo, metadata in nodos_metadata.items():
        grafo.agregar_nodo(nodo, metadata)
    
    # Agregar caminos principales
    caminos = [
        # Desde Ayacucho
        {
            "origen": "Ayacucho",
            "destino": "Huanta",
            "distancia_km": 47,
            "fiabilidad": 0.95,
            "tipo": TipoCamino.ASFALTADO,
            "riesgo": 0.1
        },
        {
            "origen": "Ayacucho",
            "destino": "Quinua",
            "distancia_km": 37,
            "fiabilidad": 0.90,
            "tipo": TipoCamino.ASFALTADO,
            "riesgo": 0.15
        },
        {
            "origen": "Ayacucho",
            "destino": "San Miguel",
            "distancia_km": 135,
            "fiabilidad": 0.85,
            "tipo": TipoCamino.AFIRMADO,
            "riesgo": 0.25
        },
        {
            "origen": "Ayacucho",
            "destino": "Tambo",
            "distancia_km": 95,
            "fiabilidad": 0.80,
            "tipo": TipoCamino.AFIRMADO,
            "riesgo": 0.30
        },
        
        # Desde Huanta
        {
            "origen": "Huanta",
            "destino": "Sivia",
            "distancia_km": 85,
            "fiabilidad": 0.70,
            "tipo": TipoCamino.AFIRMADO,
            "riesgo": 0.45
        },
        {
            "origen": "Huanta",
            "destino": "Tambo",
            "distancia_km": 60,
            "fiabilidad": 0.75,
            "tipo": TipoCamino.AFIRMADO,
            "riesgo": 0.35
        },
        
        # Desde San Miguel
        {
            "origen": "San Miguel",
            "destino": "Tambo",
            "distancia_km": 45,
            "fiabilidad": 0.80,
            "tipo": TipoCamino.TROCHA,
            "riesgo": 0.30
        },
        {
            "origen": "San Miguel",
            "destino": "Sivia",
            "distancia_km": 95,
            "fiabilidad": 0.75,
            "tipo": TipoCamino.TROCHA,
            "riesgo": 0.40
        },
        
        # Rutas alternativas
        {
            "origen": "Quinua",
            "destino": "Tambo",
            "distancia_km": 70,
            "fiabilidad": 0.65,
            "tipo": TipoCamino.TROCHA,
            "riesgo": 0.50
        }
    ]
    
    # Agregar todos los caminos
    for camino in caminos:
        grafo.agregar_camino(
            origen=camino["origen"],
            destino=camino["destino"],
            distancia_km=camino["distancia_km"],
            fiabilidad=camino["fiabilidad"],
            tipo_camino=camino["tipo"],
            riesgo_historico=camino["riesgo"]
        )
    
    return grafo


if __name__ == "__main__":
    print("🗺️  Generando grafo de demostración: Red Vial de Ayacucho\n")
    
    grafo = crear_grafo_ayacucho()
    
    print(f"✅ Grafo creado:")
    print(f"   - Nodos: {len(grafo.nodos)}")
    print(f"   - Aristas: {sum(len(v) for v in grafo.adyacencias.values()) // 2}")
    
    # Guardar
    ruta_salida = "data/grafos/red_ayacucho.json"
    grafo.exportar_json(ruta_salida)
    print(f"\n💾 Grafo guardado en: {ruta_salida}")
    
    # Mostrar algunos caminos
    print("\n📍 Muestra de caminos desde Ayacucho:")
    for arista in grafo.obtener_vecinos("Ayacucho"):
        print(f"   → {arista.destino}: {arista.distancia_km}km "
              f"(fiab={arista.fiabilidad:.0%}, {arista.tipo_camino.value})")