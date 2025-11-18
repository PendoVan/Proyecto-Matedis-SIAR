"""
Módulo: grafo_rutas.py
Descripción: Implementación de un grafo ponderado para modelar la red de caminos rurales.
Cada arista tiene múltiples atributos: distancia, fiabilidad, riesgo de bloqueo.

Fundamento Matemático:
- Teoría de Grafos: G = (V, E) donde V son los nodos (pueblos/puntos) y E las aristas (caminos)
- Grafo ponderado con múltiples pesos por arista
"""

import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class TipoCamino(Enum):
    """Tipos de camino según su condición"""
    ASFALTADO = "asfaltado"
    AFIRMADO = "afirmado"
    TROCHA = "trocha"
    HERRADURA = "herradura"


@dataclass
class Arista:
    """
    Representa un camino entre dos puntos.
    
    Atributos:
        origen: Nodo de origen
        destino: Nodo de destino
        distancia_km: Distancia física en kilómetros
        fiabilidad: Probabilidad de tránsito exitoso (0.0 a 1.0)
        tipo_camino: Clasificación del camino
        riesgo_historico: Registro de bloqueos históricos (0.0 = sin riesgo, 1.0 = muy riesgoso)
        tiempo_estimado_min: Tiempo de viaje en minutos
    """
    origen: str
    destino: str
    distancia_km: float
    fiabilidad: float  # 0.0 a 1.0 (1.0 = 100% fiable)
    tipo_camino: TipoCamino
    riesgo_historico: float  # 0.0 a 1.0
    tiempo_estimado_min: int
    
    def calcular_peso_fiabilidad(self) -> float:
        """
        Calcula el 'costo' de usar esta ruta basado en fiabilidad.
        Menor peso = mejor ruta.
        
        Fórmula: peso = distancia / fiabilidad + (riesgo_historico * K)
        donde K es una constante de penalización.
        """
        K_RIESGO = 50  # Factor de penalización por riesgo
        
        # Evitar división por cero
        fiabilidad_ajustada = max(self.fiabilidad, 0.01)
        
        peso = (self.distancia_km / fiabilidad_ajustada) + (self.riesgo_historico * K_RIESGO)
        return peso
    
    def __repr__(self):
        return f"{self.origen} → {self.destino} ({self.distancia_km}km, fiab={self.fiabilidad:.2f})"


class GrafoRutas:
    """
    Grafo no dirigido ponderado para representar la red de caminos.
    
    Estructura interna:
        - self.nodos: Set de nombres de nodos
        - self.adyacencias: Dict[str, List[Arista]] - lista de adyacencia
    """
    
    def __init__(self):
        self.nodos: set = set()
        self.adyacencias: Dict[str, List[Arista]] = {}
    
    def agregar_nodo(self, nombre: str, metadata: Optional[Dict] = None):
        """
        Agrega un nodo (pueblo, almacén, mercado) al grafo.
        
        Args:
            nombre: Identificador único del nodo
            metadata: Información adicional (coordenadas, población, etc.)
        """
        self.nodos.add(nombre)
        if nombre not in self.adyacencias:
            self.adyacencias[nombre] = []
        
        # Por ahora guardamos metadata en un atributo separado (opcional)
        if not hasattr(self, 'metadata'):
            self.metadata = {}
        if metadata:
            self.metadata[nombre] = metadata
    
    def agregar_camino(self, origen: str, destino: str, distancia_km: float,
                      fiabilidad: float, tipo_camino: TipoCamino,
                      riesgo_historico: float = 0.0, tiempo_estimado_min: int = None):
        """
        Agrega un camino bidireccional entre dos nodos.
        
        Args:
            origen, destino: Nodos a conectar
            distancia_km: Distancia física
            fiabilidad: Probabilidad de tránsito exitoso (0.0 a 1.0)
            tipo_camino: Clasificación del camino
            riesgo_historico: Histórico de bloqueos
            tiempo_estimado_min: Tiempo de viaje (si es None, se calcula automáticamente)
        """
        # Validaciones
        if origen not in self.nodos:
            self.agregar_nodo(origen)
        if destino not in self.nodos:
            self.agregar_nodo(destino)
        
        if not (0.0 <= fiabilidad <= 1.0):
            raise ValueError(f"Fiabilidad debe estar entre 0.0 y 1.0, recibido: {fiabilidad}")
        
        if not (0.0 <= riesgo_historico <= 1.0):
            raise ValueError(f"Riesgo histórico debe estar entre 0.0 y 1.0, recibido: {riesgo_historico}")
        
        # Calcular tiempo si no se proporciona (asumiendo velocidades promedio)
        if tiempo_estimado_min is None:
            velocidades = {
                TipoCamino.ASFALTADO: 60,     # km/h
                TipoCamino.AFIRMADO: 40,
                TipoCamino.TROCHA: 25,
                TipoCamino.HERRADURA: 5
            }
            velocidad = velocidades[tipo_camino]
            tiempo_estimado_min = int((distancia_km / velocidad) * 60)
        
        # Crear aristas (grafo no dirigido = dos aristas)
        arista_ida = Arista(
            origen=origen,
            destino=destino,
            distancia_km=distancia_km,
            fiabilidad=fiabilidad,
            tipo_camino=tipo_camino,
            riesgo_historico=riesgo_historico,
            tiempo_estimado_min=tiempo_estimado_min
        )
        
        arista_vuelta = Arista(
            origen=destino,
            destino=origen,
            distancia_km=distancia_km,
            fiabilidad=fiabilidad,
            tipo_camino=tipo_camino,
            riesgo_historico=riesgo_historico,
            tiempo_estimado_min=tiempo_estimado_min
        )
        
        self.adyacencias[origen].append(arista_ida)
        self.adyacencias[destino].append(arista_vuelta)
    
    def obtener_vecinos(self, nodo: str) -> List[Arista]:
        """Retorna todas las aristas que salen de un nodo."""
        return self.adyacencias.get(nodo, [])
    
    def actualizar_fiabilidad(self, origen: str, destino: str, nueva_fiabilidad: float):
        """
        Actualiza la fiabilidad de un camino (útil para alertas en tiempo real).
        
        Ejemplo: Si hay una alerta de lluvia, reducir fiabilidad de caminos afectados.
        """
        if not (0.0 <= nueva_fiabilidad <= 1.0):
            raise ValueError(f"Fiabilidad debe estar entre 0.0 y 1.0")
        
        # Actualizar ambas direcciones
        for arista in self.adyacencias.get(origen, []):
            if arista.destino == destino:
                arista.fiabilidad = nueva_fiabilidad
        
        for arista in self.adyacencias.get(destino, []):
            if arista.destino == origen:
                arista.fiabilidad = nueva_fiabilidad
    
    def exportar_json(self, ruta_archivo: str):
        """Guarda el grafo en formato JSON para persistencia."""
        data = {
            "nodos": list(self.nodos),
            "aristas": []
        }
        
        aristas_procesadas = set()
        for origen, aristas in self.adyacencias.items():
            for arista in aristas:
                # Evitar duplicados (grafo no dirigido)
                par = tuple(sorted([arista.origen, arista.destino]))
                if par not in aristas_procesadas:
                    data["aristas"].append({
                        "origen": arista.origen,
                        "destino": arista.destino,
                        "distancia_km": arista.distancia_km,
                        "fiabilidad": arista.fiabilidad,
                        "tipo_camino": arista.tipo_camino.value,
                        "riesgo_historico": arista.riesgo_historico,
                        "tiempo_estimado_min": arista.tiempo_estimado_min
                    })
                    aristas_procesadas.add(par)
        
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def cargar_json(cls, ruta_archivo: str) -> 'GrafoRutas':
        """Carga un grafo desde un archivo JSON."""
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        grafo = cls()
        
        # Cargar nodos
        for nodo in data["nodos"]:
            grafo.agregar_nodo(nodo)
        
        # Cargar aristas
        for arista_data in data["aristas"]:
            grafo.agregar_camino(
                origen=arista_data["origen"],
                destino=arista_data["destino"],
                distancia_km=arista_data["distancia_km"],
                fiabilidad=arista_data["fiabilidad"],
                tipo_camino=TipoCamino(arista_data["tipo_camino"]),
                riesgo_historico=arista_data.get("riesgo_historico", 0.0),
                tiempo_estimado_min=arista_data.get("tiempo_estimado_min")
            )
        
        return grafo
    
    def __repr__(self):
        return f"GrafoRutas(nodos={len(self.nodos)}, aristas={sum(len(v) for v in self.adyacencias.values()) // 2})"


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    # Crear grafo de ejemplo: Región de Ayacucho
    grafo = GrafoRutas()
    
    # Agregar caminos
    grafo.agregar_camino(
        origen="Ayacucho",
        destino="Huanta",
        distancia_km=47,
        fiabilidad=0.95,
        tipo_camino=TipoCamino.ASFALTADO,
        riesgo_historico=0.1
    )
    
    grafo.agregar_camino(
        origen="Huanta",
        destino="Sivia",
        distancia_km=85,
        fiabilidad=0.70,
        tipo_camino=TipoCamino.AFIRMADO,
        riesgo_historico=0.4  # Mayor riesgo histórico de bloqueos
    )
    
    grafo.agregar_camino(
        origen="Ayacucho",
        destino="San Miguel",
        distancia_km=135,
        fiabilidad=0.85,
        tipo_camino=TipoCamino.AFIRMADO,
        riesgo_historico=0.2
    )
    
    grafo.agregar_camino(
        origen="San Miguel",
        destino="Sivia",
        distancia_km=95,
        fiabilidad=0.80,
        tipo_camino=TipoCamino.TROCHA,
        riesgo_historico=0.3
    )
    
    # Mostrar información
    print(grafo)
    print("\n🛣️  Caminos desde Ayacucho:")
    for arista in grafo.obtener_vecinos("Ayacucho"):
        print(f"  - {arista}")
        print(f"    Peso fiabilidad: {arista.calcular_peso_fiabilidad():.2f}")
    
    # Guardar grafo
    grafo.exportar_json("data/grafos/red_ayacucho.json")
    print("\n✅ Grafo guardado en 'data/grafos/red_ayacucho.json'")
    
    # Simular actualización por alerta
    print("\n⚠️  ALERTA: Lluvia intensa en ruta Huanta-Sivia")
    grafo.actualizar_fiabilidad("Huanta", "Sivia", 0.40)
    print("   Nueva fiabilidad: 0.40")
    
    arista_afectada = [a for a in grafo.obtener_vecinos("Huanta") if a.destino == "Sivia"][0]
    print(f"   Nuevo peso: {arista_afectada.calcular_peso_fiabilidad():.2f}")