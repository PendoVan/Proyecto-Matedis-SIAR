"""
Script: demo_sistema_completo.py
Descripción: Demostración completa del Sistema SIAR
Muestra todas las funcionalidades integradas para la presentación.

Ejecutar: python scripts/demo_sistema_completo.py
"""

import sys
import os
from datetime import datetime
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.unidad3_grafos.grafo_rutas import GrafoRutas, TipoCamino
from src.unidad3_grafos.algoritmo_fiabilidad import AlgoritmoFiabilidad
from src.unidad3_grafos.maquina_estados import (
    MaquinaEstadosAlerta,
    MaquinaEstadosLogistica,
    Alerta,
    LoteCosecha,
    EstadoAlerta,
    EventoAlerta,
    EstadoLote,
    EventoLote
)


def imprimir_seccion(titulo: str):
    """Imprime una sección con formato."""
    print("\n" + "="*80)
    print(f"🎯 {titulo}")
    print("="*80 + "\n")


def demo_grafos_basico():
    """Demo 1: Creación y visualización de grafos."""
    imprimir_seccion("DEMO 1: RED DE CAMINOS RURALES")
    
    print("📍 Cargando red vial de Ayacucho desde archivo JSON...\n")
    grafo = GrafoRutas.cargar_json("data/grafos/red_ayacucho.json")
    
    print(f"✅ Grafo cargado: {grafo}")
    print(f"   Nodos: {', '.join(sorted(grafo.nodos))}\n")
    
    print("🛣️  Caminos desde Ayacucho:")
    for arista in grafo.obtener_vecinos("Ayacucho"):
        print(f"   → {arista.destino:12s} | {arista.distancia_km:3.0f} km | "
              f"Fiab: {arista.fiabilidad:.0%} | {arista.tipo_camino.value:10s} | "
              f"Tiempo: {arista.tiempo_estimado_min} min")


def demo_algoritmo_rutas():
    """Demo 2: Algoritmo de ruta más fiable."""
    imprimir_seccion("DEMO 2: CÁLCULO DE RUTA MÁS FIABLE")
    
    grafo = GrafoRutas.cargar_json("data/grafos/red_ayacucho.json")
    algoritmo = AlgoritmoFiabilidad(grafo)
    
    origen = "Ayacucho"
    destino = "Sivia"
    
    print(f"🔍 Buscando ruta óptima: {origen} → {destino}\n")
    
    # Comparar diferentes criterios
    comparacion = algoritmo.comparar_rutas(origen, destino)
    
    print("📊 COMPARACIÓN DE CRITERIOS:\n")
    
    # Ruta más fiable
    ruta_fiable = comparacion['mas_fiable']
    print("1️⃣  RUTA MÁS FIABLE (optimizada por seguridad):")
    print(f"   Camino: {' → '.join(ruta_fiable.nodos)}")
    print(f"   📏 Distancia: {ruta_fiable.distancia_total_km:.1f} km")
    print(f"   ✅ Fiabilidad: {ruta_fiable.fiabilidad_acumulada:.2%}")
    print(f"   ⏱️  Tiempo: {ruta_fiable.tiempo_total_min} min")
    print(f"   💰 Peso (costo): {ruta_fiable.peso_total:.2f}\n")
    
    # Ruta más corta
    ruta_corta = comparacion['mas_corta']
    print("2️⃣  RUTA MÁS CORTA (optimizada por distancia):")
    print(f"   Camino: {' → '.join(ruta_corta.nodos)}")
    print(f"   📏 Distancia: {ruta_corta.distancia_total_km:.1f} km")
    print(f"   ✅ Fiabilidad: {ruta_corta.fiabilidad_acumulada:.2%}")
    print(f"   ⏱️  Tiempo: {ruta_corta.tiempo_total_min} min\n")
    
    # Ruta más rápida
    ruta_rapida = comparacion['mas_rapida']
    print("3️⃣  RUTA MÁS RÁPIDA (optimizada por tiempo):")
    print(f"   Camino: {' → '.join(ruta_rapida.nodos)}")
    print(f"   📏 Distancia: {ruta_rapida.distancia_total_km:.1f} km")
    print(f"   ✅ Fiabilidad: {ruta_rapida.fiabilidad_acumulada:.2%}")
    print(f"   ⏱️  Tiempo: {ruta_rapida.tiempo_total_min} min\n")
    
    print("💡 ANÁLISIS:")
    print(f"   La ruta más fiable tiene {ruta_fiable.fiabilidad_acumulada:.2%} de probabilidad de éxito")
    print(f"   vs {ruta_corta.fiabilidad_acumulada:.2%} de la ruta más corta.")
    
    diferencia_km = ruta_fiable.distancia_total_km - ruta_corta.distancia_total_km
    if diferencia_km > 0:
        print(f"   📊 Trade-off: +{diferencia_km:.1f} km pero +{(ruta_fiable.fiabilidad_acumulada - ruta_corta.fiabilidad_acumulada)*100:.1f}% más fiable")


def demo_maquina_estados_alertas():
    """Demo 3: Sistema de alertas con FSM."""
    imprimir_seccion("DEMO 3: SISTEMA DE ALERTAS COMUNITARIAS")
    
    print("🚨 Simulando ciclo de vida de una alerta...\n")
    
    # Crear alerta
    alerta = Alerta(
        id="ALR-2024-001",
        tipo="bloqueo_carretera",
        ubicacion="Ruta Huanta-Sivia Km 32",
        descripcion="Deslizamiento de tierra bloqueando ambos carriles",
        emisor="AGR-042",
        timestamp_creacion=datetime.now()
    )
    
    fsm = MaquinaEstadosAlerta()
    
    print(f"📝 Alerta creada:")
    print(f"   ID: {alerta.id}")
    print(f"   Tipo: {alerta.tipo}")
    print(f"   Ubicación: {alerta.ubicacion}")
    print(f"   Estado inicial: {alerta.estado.value}")
    print(f"   Confianza inicial: {alerta.nivel_confianza:.0%}\n")
    
    # Flujo de verificación
    print("🔄 Proceso de verificación:\n")
    
    # Paso 1: Solicitar verificación
    fsm.procesar_evento(alerta, EventoAlerta.SOLICITAR_VERIFICACION)
    print(f"   1. {alerta.estado.value:20s} | Confianza: {alerta.nivel_confianza:.0%}")
    
    # Paso 2: Primera confirmación
    alerta.confirmaciones.append("AGR-105")
    alerta.nivel_confianza = fsm._calcular_confianza(alerta)
    print(f"      → Usuario AGR-105 confirma")
    print(f"        Confianza: {alerta.nivel_confianza:.0%}")
    
    # Paso 3: Segunda confirmación
    alerta.confirmaciones.append("TRANS-23")
    alerta.nivel_confianza = fsm._calcular_confianza(alerta)
    print(f"      → Usuario TRANS-23 confirma")
    print(f"        Confianza: {alerta.nivel_confianza:.0%}")
    
    # Paso 4: Confirmar alerta
    fsm.procesar_evento(alerta, EventoAlerta.CONFIRMAR)
    print(f"\n   2. {alerta.estado.value:20s} | Confianza: {alerta.nivel_confianza:.0%}")
    
    # Paso 5: Atender
    fsm.procesar_evento(alerta, EventoAlerta.ATENDER)
    print(f"   3. {alerta.estado.value:20s} | Autoridades respondiendo")
    
    # Paso 6: Resolver
    fsm.procesar_evento(alerta, EventoAlerta.RESOLVER)
    print(f"   4. {alerta.estado.value:20s} | Camino despejado\n")
    
    print(f"✅ Alerta procesada exitosamente")
    print(f"   Confirmaciones totales: {len(alerta.confirmaciones)}")
    print(f"   Confianza final: {alerta.nivel_confianza:.0%}")


def demo_actualizacion_dinamica():
    """Demo 4: Actualización de fiabilidad por alertas."""
    imprimir_seccion("DEMO 4: ACTUALIZACIÓN DINÁMICA DE RUTAS")
    
    grafo = GrafoRutas.cargar_json("data/grafos/red_ayacucho.json")
    algoritmo = AlgoritmoFiabilidad(grafo)
    
    origen = "Ayacucho"
    destino = "Sivia"
    
    print("📍 Situación inicial:\n")
    ruta_inicial = algoritmo.encontrar_ruta_mas_fiable(origen, destino)
    print(f"Ruta recomendada: {' → '.join(ruta_inicial.nodos)}")
    print(f"Fiabilidad: {ruta_inicial.fiabilidad_acumulada:.2%}\n")
    
    print("⚠️  ¡ALERTA RECIBIDA!")
    print("   Bloqueo en: Huanta → Sivia")
    print("   Reduciendo fiabilidad de 70% → 30%\n")
    
    # Actualizar fiabilidad
    grafo.actualizar_fiabilidad("Huanta", "Sivia", 0.30)
    
    print("🔄 Recalculando ruta...\n")
    ruta_actualizada = algoritmo.encontrar_ruta_mas_fiable(origen, destino)
    
    print(f"📍 Nueva ruta recomendada: {' → '.join(ruta_actualizada.nodos)}")
    print(f"Fiabilidad: {ruta_actualizada.fiabilidad_acumulada:.2%}\n")
    
    if ruta_inicial.nodos != ruta_actualizada.nodos:
        print("✅ Sistema adaptó la ruta automáticamente para evitar el bloqueo")
    else:
        print("ℹ️  La ruta se mantiene (es la única opción disponible)")


def demo_logistica():
    """Demo 5: Sistema logístico."""
    imprimir_seccion("DEMO 5: GESTIÓN LOGÍSTICA DE COSECHAS")
    
    print("📦 Simulando flujo logístico de un lote de quinua...\n")
    
    # Crear lote
    lote = LoteCosecha(
        id="LOT-2024-QUI-001",
        producto="quinua",
        cantidad_kg=500,
        agricultor_id="AGR-042"
    )
    
    fsm_logistica = MaquinaEstadosLogistica()
    
    print(f"🌾 Lote creado:")
    print(f"   ID: {lote.id}")
    print(f"   Producto: {lote.producto}")
    print(f"   Cantidad: {lote.cantidad_kg} kg")
    print(f"   Agricultor: {lote.agricultor_id}\n")
    
    print("🔄 Ciclo logístico:\n")
    
    # Flujo de estados
    estados = [
        (EventoLote.ALMACENAR, "Lote recibido en almacén cooperativa"),
        (EventoLote.PREPARAR_ENVIO, "Empaquetado y etiquetado completado"),
        (EventoLote.INICIAR_TRANSPORTE, "Camión en ruta a mercado mayorista"),
        (EventoLote.CONFIRMAR_ENTREGA, "Entrega confirmada, pago procesado")
    ]
    
    for i, (evento, descripcion) in enumerate(estados, 1):
        fsm_logistica.procesar_evento(lote, evento)
        print(f"   {i}. {lote.estado.value:15s} → {descripcion}")
    
    print(f"\n✅ Proceso completado exitosamente")


def demo_estadisticas():
    """Demo 6: Estadísticas del sistema."""
    imprimir_seccion("DEMO 6: ESTADÍSTICAS DEL SISTEMA")
    
    grafo = GrafoRutas.cargar_json("data/grafos/red_ayacucho.json")
    
    print("📊 Métricas de la red:\n")
    
    # Contar tipos de caminos
    tipos_camino = {}
    distancia_total = 0
    fiabilidad_promedio = 0
    num_aristas = 0
    
    aristas_procesadas = set()
    for origen, aristas in grafo.adyacencias.items():
        for arista in aristas:
            par = tuple(sorted([arista.origen, arista.destino]))
            if par not in aristas_procesadas:
                tipos_camino[arista.tipo_camino.value] = tipos_camino.get(arista.tipo_camino.value, 0) + 1
                distancia_total += arista.distancia_km
                fiabilidad_promedio += arista.fiabilidad
                num_aristas += 1
                aristas_procesadas.add(par)
    
    fiabilidad_promedio /= num_aristas
    
    print(f"🗺️  Red de caminos:")
    print(f"   Nodos (localidades): {len(grafo.nodos)}")
    print(f"   Aristas (caminos): {num_aristas}")
    print(f"   Distancia total: {distancia_total:.0f} km\n")
    
    print(f"📈 Calidad de la red:")
    print(f"   Fiabilidad promedio: {fiabilidad_promedio:.1%}")
    for tipo, cantidad in sorted(tipos_camino.items()):
        print(f"   Caminos {tipo}: {cantidad}")
    
    print(f"\n🎯 Capacidad del sistema:")
    print(f"   Rutas posibles entre cualquier par de nodos: {len(grafo.nodos) * (len(grafo.nodos) - 1) // 2}")
    print(f"   Tiempo promedio de cálculo: < 100ms (Dijkstra)")


def main():
    """Función principal que ejecuta todas las demos."""
    print("\n" + "🌾"*40)
    print(" "*15 + "SISTEMA SIAR")
    print(" "*5 + "Sistema de Información y Alerta Resiliente")
    print(" "*10 + "para Cooperativas Agrícolas Rurales")
    print("🌾"*40)
    
    print("\n📚 Fundamentos Matemáticos Aplicados:")
    print("   • Unidad III: Teoría de Grafos (Dijkstra modificado)")
    print("   • Unidad III: Autómatas Finitos Deterministas (FSM)")
    print("   • Unidad I: Teorema de Bayes (actualización de confianza)")
    
    try:
        # Ejecutar demos
        demo_grafos_basico()
        input("\n⏸️  Presiona ENTER para continuar...")
        
        demo_algoritmo_rutas()
        input("\n⏸️  Presiona ENTER para continuar...")
        
        demo_maquina_estados_alertas()
        input("\n⏸️  Presiona ENTER para continuar...")
        
        demo_actualizacion_dinamica()
        input("\n⏸️  Presiona ENTER para continuar...")
        
        demo_logistica()
        input("\n⏸️  Presiona ENTER para continuar...")
        
        demo_estadisticas()
        
        # Resumen final
        imprimir_seccion("RESUMEN DE CAPACIDADES")
        print("✅ Gestión de red de caminos rurales con múltiples métricas")
        print("✅ Algoritmo de ruta óptima considerando fiabilidad")
        print("✅ Sistema de alertas colaborativo con verificación social")
        print("✅ Actualización dinámica de rutas ante incidentes")
        print("✅ Gestión logística completa de cosechas")
        print("✅ Trazabilidad y estados bien definidos (FSM)")
        
        print("\n🎓 Impacto Social:")
        print("   • Reduce pérdidas de cosechas por mala planificación de rutas")
        print("   • Mejora comunicación en zonas rurales sin cobertura estable")
        print("   • Empodera a agricultores con información en tiempo real")
        print("   • Aumenta confiabilidad del sistema cooperativo")
        
        print("\n" + "="*80)
        print("✅ DEMOSTRACIÓN COMPLETADA")
        print("="*80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n❌ Demo interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error durante la demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()