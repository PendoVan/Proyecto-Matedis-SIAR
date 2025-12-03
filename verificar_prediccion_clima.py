import sys
import os
from datetime import datetime

# Agregar directorio src al path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from unidad3_grafos.grafo_rutas import GrafoRutas, TipoCamino
from unidad3_grafos.algoritmo_fiabilidad import AlgoritmoFiabilidad
from unidad3_grafos.prediccion_climatica import IntegradorSENAMHI

def test_prediccion_clima():
    print("\n" + "="*50)
    print("🧪 TEST 1: Predicción Climática por Fecha")
    print("="*50)
    
    predictor = IntegradorSENAMHI()
    
    # Intentar cargar modelo, si no existe, entrenar uno rápido
    if not predictor.cargar_modelo("data/modelos"):
        print("⚠️  Modelo no encontrado, entrenando uno temporal...")
        predictor.entrenar_modelo("data/clima/senamhi_procesado.csv")
    
    # Probar predicción para una fecha de lluvia (Enero)
    fecha_lluvia = datetime(2025, 1, 15)
    riesgo_enero = predictor.predecir_riesgo_por_fecha("Cusco", fecha_lluvia)
    print(f"📅 Riesgo en Cusco (Enero): {riesgo_enero:.2%}")
    
    # Probar predicción para una fecha seca (Julio)
    fecha_seca = datetime(2025, 7, 15)
    riesgo_julio = predictor.predecir_riesgo_por_fecha("Cusco", fecha_seca)
    print(f"📅 Riesgo en Cusco (Julio): {riesgo_julio:.2%}")
    
    if riesgo_enero > riesgo_julio:
        print("✅ Lógica correcta: Más riesgo en temporada de lluvias")
    else:
        print("❌ ALERTA: La lógica de riesgo estacional no parece correcta")
        
    return predictor

def test_rutas_con_clima(predictor):
    print("\n" + "="*50)
    print("🧪 TEST 2: Rutas con Influencia Climática")
    print("="*50)
    
    # Crear grafo simple
    grafo = GrafoRutas()
    
    # Ruta 1: Corta pero vulnerable a lluvias (trocha)
    grafo.agregar_camino("A", "B", 100, 0.90, TipoCamino.TROCHA)
    
    # Ruta 2: Larga pero segura (asfaltado)
    grafo.agregar_camino("A", "C", 50, 0.95, TipoCamino.ASFALTADO)
    grafo.agregar_camino("C", "B", 100, 0.95, TipoCamino.ASFALTADO)
    
    algoritmo = AlgoritmoFiabilidad(grafo)
    
    # Caso 1: Sin fecha (debería preferir la corta si la fiabilidad es suficiente)
    print("\n--- Caso 1: Sin fecha específica ---")
    ruta_base = algoritmo.encontrar_ruta_mas_fiable("A", "B")
    print(f"Ruta elegida: {ruta_base.nodos} (Distancia: {ruta_base.distancia_total_km}km)")
    
    # Caso 2: En temporada de lluvias (Enero)
    # La trocha debería ser penalizada
    print("\n--- Caso 2: Temporada de lluvias (Enero) ---")
    fecha_lluvia = "2025-01-15"
    ruta_lluvia = algoritmo.encontrar_ruta_mas_fiable("A", "B", fecha_lluvia, "12:00", predictor)
    print(f"Ruta elegida: {ruta_lluvia.nodos} (Distancia: {ruta_lluvia.distancia_total_km}km)")
    
    if len(ruta_lluvia.nodos) > 2: # Si eligió A->C->B
        print("✅ El algoritmo desvió la ruta por lluvia (evitó trocha)")
    else:
        print("⚠️ El algoritmo mantuvo la ruta directa (¿penalización insuficiente?)")

if __name__ == "__main__":
    try:
        predictor = test_prediccion_clima()
        test_rutas_con_clima(predictor)
        print("\n✅ Verificación completada exitosamente")
    except Exception as e:
        print(f"\n❌ Error durante la verificación: {e}")
        import traceback
        traceback.print_exc()
