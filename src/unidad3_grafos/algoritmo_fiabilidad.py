"""
Módulo: algoritmo_fiabilidad.py
Descripción: Implementación de algoritmo de camino más fiable (Dijkstra modificado).
En lugar de buscar el camino más corto, buscamos el camino con menor "costo de fiabilidad".

Fundamento Matemático:
- Algoritmo de Dijkstra: Encuentra el camino de peso mínimo en un grafo ponderado
- Modificación: El peso no es distancia, sino una función de fiabilidad y riesgo
- Complejidad: O((V + E) log V) con heap
"""

import heapq
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Importación flexible para ejecución directa y como módulo
try:
    from .grafo_rutas import GrafoRutas, Arista
except ImportError:
    from grafo_rutas import GrafoRutas, Arista


@dataclass
class Ruta:
    """
    Representa una ruta completa entre dos puntos.
    
    Atributos:
        nodos: Lista ordenada de nodos en la ruta
        distancia_total_km: Suma de distancias
        fiabilidad_acumulada: Producto de fiabilidades (probabilidad de éxito)
        peso_total: Costo total según la función de fiabilidad
        tiempo_total_min: Tiempo estimado total
        aristas: Lista de aristas que conforman la ruta
    """
    nodos: List[str]
    distancia_total_km: float
    fiabilidad_acumulada: float
    peso_total: float
    tiempo_total_min: int
    aristas: List[Arista]
    
    def __repr__(self):
        ruta_str = " → ".join(self.nodos)
        return (f"Ruta: {ruta_str}\n"
                f"  Distancia: {self.distancia_total_km:.1f} km\n"
                f"  Fiabilidad: {self.fiabilidad_acumulada:.2%}\n"
                f"  Peso: {self.peso_total:.2f}\n"
                f"  Tiempo: {self.tiempo_total_min} min")


class AlgoritmoFiabilidad:
    """
    Implementa el algoritmo de Dijkstra modificado para encontrar
    la ruta más fiable (no necesariamente la más corta).
    """
    
    def __init__(self, grafo: GrafoRutas):
        self.grafo = grafo
    
    def encontrar_ruta_mas_fiable(self, origen: str, destino: str, 
                                 fecha_salida=None, hora_salida=None,
                                 predictor_clima=None) -> Optional[Ruta]:
        """
        Encuentra la ruta con menor peso de fiabilidad entre origen y destino.
        
        Args:
            origen: Nodo de inicio
            destino: Nodo de llegada
            fecha_salida: Fecha para predicción climática
            hora_salida: Hora para tráfico
            predictor_clima: Instancia de IntegradorSENAMHI
            
        Returns:
            Objeto Ruta con el camino óptimo, o None si no existe camino
        """
        if origen not in self.grafo.nodos:
            raise ValueError(f"Nodo origen '{origen}' no existe en el grafo")
        if destino not in self.grafo.nodos:
            raise ValueError(f"Nodo destino '{destino}' no existe en el grafo")
        
        # Estructuras de datos para Dijkstra
        pesos = {nodo: float('inf') for nodo in self.grafo.nodos}
        pesos[origen] = 0
        
        # Para reconstruir el camino
        previos: Dict[str, Tuple[str, Arista]] = {}  # nodo -> (nodo_previo, arista_usada)
        
        # Min-heap: (peso_acumulado, nodo_actual)
        heap = [(0, origen)]
        visitados = set()
        
        while heap:
            peso_actual, nodo_actual = heapq.heappop(heap)
            
            # Si ya llegamos al destino, podemos terminar
            if nodo_actual == destino:
                break
            
            # Si ya visitamos este nodo, continuar
            if nodo_actual in visitados:
                continue
            
            visitados.add(nodo_actual)
            
            # Explorar vecinos
            for arista in self.grafo.obtener_vecinos(nodo_actual):
                vecino = arista.destino
                
                if vecino in visitados:
                    continue
                
                # Calcular nuevo peso
                if predictor_clima and fecha_salida:
                    peso_arista = arista.calcular_peso_dinamico(fecha_salida, hora_salida, predictor_clima)
                else:
                    peso_arista = arista.calcular_peso_fiabilidad()
                
                # Aplicar penalización geográfica si existe (AlgoritmoFiabilidadGeo)
                if hasattr(self, 'calcular_penalizacion_direccion'):
                    penalizacion = self.calcular_penalizacion_direccion(nodo_actual, vecino, destino)
                    peso_arista *= (1 + penalizacion)

                nuevo_peso = peso_actual + peso_arista
                
                # Si encontramos un camino mejor, actualizar
                if nuevo_peso < pesos[vecino]:
                    pesos[vecino] = nuevo_peso
                    previos[vecino] = (nodo_actual, arista)
                    heapq.heappush(heap, (nuevo_peso, vecino))
        
        # Si no hay camino al destino
        if pesos[destino] == float('inf'):
            return None
        
        # Reconstruir ruta
        return self._reconstruir_ruta(origen, destino, previos, pesos[destino])
    
    def _reconstruir_ruta(self, origen: str, destino: str, 
                         previos: Dict[str, Tuple[str, Arista]], 
                         peso_total: float) -> Ruta:
        """
        Reconstruye la ruta completa desde el diccionario de nodos previos.
        """
        nodos = []
        aristas = []
        nodo_actual = destino
        
        # Reconstruir hacia atrás
        while nodo_actual != origen:
            nodos.append(nodo_actual)
            nodo_previo, arista_usada = previos[nodo_actual]
            aristas.append(arista_usada)
            nodo_actual = nodo_previo
        
        nodos.append(origen)
        
        # Invertir para que vaya de origen a destino
        nodos.reverse()
        aristas.reverse()
        
        # Calcular métricas
        distancia_total = sum(a.distancia_km for a in aristas)
        tiempo_total = sum(a.tiempo_estimado_min for a in aristas)
        
        # Fiabilidad acumulada es el producto de todas las fiabilidades
        fiabilidad_acumulada = 1.0
        for arista in aristas:
            fiabilidad_acumulada *= arista.fiabilidad
        
        return Ruta(
            nodos=nodos,
            distancia_total_km=distancia_total,
            fiabilidad_acumulada=fiabilidad_acumulada,
            peso_total=peso_total,
            tiempo_total_min=tiempo_total,
            aristas=aristas
        )
    
    def encontrar_k_rutas_mas_fiables(self, origen: str, destino: str, k: int = 3) -> List[Ruta]:
        """
        Encuentra las k rutas más fiables usando el algoritmo de Yen.
        (Versión simplificada - implementación completa opcional)
        
        Por ahora retorna solo la mejor ruta.
        """
        mejor_ruta = self.encontrar_ruta_mas_fiable(origen, destino)
        return [mejor_ruta] if mejor_ruta else []
    
    def comparar_rutas(self, origen: str, destino: str, 
                      fecha_salida=None, hora_salida=None, predictor_clima=None) -> Dict:
        """
        Compara diferentes criterios de optimización:
        - Ruta más fiable (considera clima y tráfico si hay fecha/hora)
        - Ruta más corta (distancia)
        - Ruta más rápida (tiempo)
        
        Útil para la presentación del proyecto.
        """
        # Ruta más fiable (ya implementada)
        ruta_fiable = self.encontrar_ruta_mas_fiable(origen, destino, fecha_salida, hora_salida, predictor_clima)
        
        # Ruta más corta (Dijkstra clásico con peso = distancia)
        ruta_corta = self._dijkstra_clasico(origen, destino, criterio='distancia')
        
        # Ruta más rápida (Dijkstra con peso = tiempo)
        ruta_rapida = self._dijkstra_clasico(origen, destino, criterio='tiempo')
        
        return {
            'mas_fiable': ruta_fiable,
            'mas_corta': ruta_corta,
            'mas_rapida': ruta_rapida
        }
    
    def _dijkstra_clasico(self, origen: str, destino: str, criterio: str = 'distancia') -> Optional[Ruta]:
        """
        Dijkstra clásico con diferentes criterios de peso.
        """
        pesos = {nodo: float('inf') for nodo in self.grafo.nodos}
        pesos[origen] = 0
        previos: Dict[str, Tuple[str, Arista]] = {}
        heap = [(0, origen)]
        visitados = set()
        
        while heap:
            peso_actual, nodo_actual = heapq.heappop(heap)
            
            if nodo_actual == destino:
                break
            
            if nodo_actual in visitados:
                continue
            
            visitados.add(nodo_actual)
            
            for arista in self.grafo.obtener_vecinos(nodo_actual):
                vecino = arista.destino
                
                if vecino in visitados:
                    continue
                
                # Seleccionar peso según criterio
                if criterio == 'distancia':
                    peso_arista = arista.distancia_km
                elif criterio == 'tiempo':
                    peso_arista = arista.tiempo_estimado_min
                else:
                    peso_arista = arista.calcular_peso_fiabilidad()
                
                nuevo_peso = peso_actual + peso_arista
                
                if nuevo_peso < pesos[vecino]:
                    pesos[vecino] = nuevo_peso
                    previos[vecino] = (nodo_actual, arista)
                    heapq.heappush(heap, (nuevo_peso, vecino))
        
        if pesos[destino] == float('inf'):
            return None
        
        return self._reconstruir_ruta(origen, destino, previos, pesos[destino])


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    from grafo_rutas import GrafoRutas, TipoCamino
    
    # Crear grafo de ejemplo más complejo
    grafo = GrafoRutas()
    
    # Red de caminos: Ayacucho - Huanta - Sivia
    #                          \_ San Miguel _/
    
    grafo.agregar_camino("Ayacucho", "Huanta", 47, 0.95, TipoCamino.ASFALTADO, 0.1)
    grafo.agregar_camino("Huanta", "Sivia", 85, 0.70, TipoCamino.AFIRMADO, 0.4)
    grafo.agregar_camino("Ayacucho", "San Miguel", 135, 0.85, TipoCamino.AFIRMADO, 0.2)
    grafo.agregar_camino("San Miguel", "Sivia", 95, 0.80, TipoCamino.TROCHA, 0.3)
    
    # Crear algoritmo
    algoritmo = AlgoritmoFiabilidad(grafo)
    
    # Encontrar ruta más fiable
    print("🔍 Buscando ruta más fiable: Ayacucho → Sivia\n")
    ruta = algoritmo.encontrar_ruta_mas_fiable("Ayacucho", "Sivia")
    
    if ruta:
        print(ruta)
        print("\n📊 Detalles de cada tramo:")
        for i, arista in enumerate(ruta.aristas, 1):
            print(f"  {i}. {arista.origen} → {arista.destino}")
            print(f"     - Distancia: {arista.distancia_km} km")
            print(f"     - Fiabilidad: {arista.fiabilidad:.2%}")
            print(f"     - Tipo: {arista.tipo_camino.value}")
            print(f"     - Peso: {arista.calcular_peso_fiabilidad():.2f}\n")
    
    # Comparar con otras rutas
    print("\n" + "="*60)
    print("📈 COMPARACIÓN DE CRITERIOS\n")
    comparacion = algoritmo.comparar_rutas("Ayacucho", "Sivia")
    
    print("1️⃣  RUTA MÁS FIABLE:")
    print(f"   {' → '.join(comparacion['mas_fiable'].nodos)}")
    print(f"   Fiabilidad: {comparacion['mas_fiable'].fiabilidad_acumulada:.2%}")
    print(f"   Distancia: {comparacion['mas_fiable'].distancia_total_km} km\n")
    
    print("2️⃣  RUTA MÁS CORTA:")
    print(f"   {' → '.join(comparacion['mas_corta'].nodos)}")
    print(f"   Distancia: {comparacion['mas_corta'].distancia_total_km} km")
    print(f"   Fiabilidad: {comparacion['mas_corta'].fiabilidad_acumulada:.2%}\n")
    
    print("3️⃣  RUTA MÁS RÁPIDA:")
    print(f"   {' → '.join(comparacion['mas_rapida'].nodos)}")
    print(f"   Tiempo: {comparacion['mas_rapida'].tiempo_total_min} min")
    print(f"   Fiabilidad: {comparacion['mas_rapida'].fiabilidad_acumulada:.2%}")