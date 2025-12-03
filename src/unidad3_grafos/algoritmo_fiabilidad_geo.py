"""
Módulo: algoritmo_fiabilidad_geo.py
Descripción: Extensión del algoritmo de fiabilidad con penalización geográfica
para evitar desvíos innecesarios en las rutas.

Esta extensión usa coordenadas GPS para detectar cuando una ruta se desvía
del camino directo y aplica una penalización proporcional.
"""

import heapq
import math
from typing import Dict, List, Tuple, Optional
from src.unidad3_grafos.algoritmo_fiabilidad import AlgoritmoFiabilidad, Ruta
from src.unidad3_grafos.grafo_rutas import GrafoRutas


class AlgoritmoFiabilidadGeo(AlgoritmoFiabilidad):
    """
    Extiende AlgoritmoFiabilidad con penalización basada en dirección geográfica.
    """
    
    def __init__(self, grafo: GrafoRutas, coordenadas: Optional[Dict] = None):
        super().__init__(grafo)
        
        # Coordenadas GPS de los nodos (dep -> {lat, lon})
        self.coordenadas = coordenadas or {}
        
        # Configuración de penalización geográfica
        self.ENABLE_DIRECTION_PENALTY = True  # Activar penalización por dirección
        self.DIRECTION_PENALTY_STRENGTH = 0.4  # Fuerza de la penalización (40% máximo)
        self.MIN_DEVIATION_ANGLE = 45  # Ángulo mínimo de desviación para penalizar (grados)
    
    def calcular_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula el rumbo (bearing) desde punto 1 hacia punto 2 en grados.
        
        El bearing es el ángulo respecto al norte (0° = norte, 90° = este, 180° = sur, 270° = oeste).
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lon = math.radians(lon2 - lon1)
        
        # Fórmula de bearing
        y = math.sin(delta_lon) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon))
        
        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)
        
        # Normalizar a 0-360
        return (bearing_deg + 360) % 360
    
    def calcular_distancia_haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula distancia real entre dos puntos usando Haversine.
        """
        R = 6371  # Radio de la Tierra en km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def calcular_penalizacion_direccion(self, nodo_actual: str, vecino: str, 
                                       destino: str) -> float:
        """
        Calcula la penalización por desviación geográfica.
        
        Args:
            nodo_actual: Nodo donde estamos
            vecino: Nodo candidato
            destino: Destino final
            
        Returns:
            float: Factor de penalización (0.0 = sin penalización, hasta DIRECTION_PENALTY_STRENGTH)
        """
        if not self.ENABLE_DIRECTION_PENALTY or not self.coordenadas:
            return 0.0
        
        # Verificar que tenemos coordenadas para todos los nodos
        if (nodo_actual not in self.coordenadas or 
            vecino not in self.coordenadas or 
            destino not in self.coordenadas):
            return 0.0
        
        # Coordenadas
        coord_actual = self.coordenadas[nodo_actual]
        coord_vecino = self.coordenadas[vecino]
        coord_destino = self.coordenadas[destino]
        
        # Bearing ideal (dirección hacia el destino)
        bearing_objetivo = self.calcular_bearing(
            coord_actual['lat'], coord_actual['lon'],
            coord_destino['lat'], coord_destino['lon']
        )
        
        # Bearing de la arista actual (hacia el vecino)
        bearing_arista = self.calcular_bearing(
            coord_actual['lat'], coord_actual['lon'],
            coord_vecino['lat'], coord_vecino['lon']
        )
        
        # Desviación angular
        desviacion_angular = abs(bearing_objetivo - bearing_arista)
        if desviacion_angular > 180:
            desviacion_angular = 360 - desviacion_angular
        
        # Solo penalizar si la desviación es significativa
        if desviacion_angular < self.MIN_DEVIATION_ANGLE:
            return 0.0
        
        # Calcular si nos estamos acercando o alejando del destino
        dist_antes = self.calcular_distancia_haversine(
            coord_actual['lat'], coord_actual['lon'],
            coord_destino['lat'], coord_destino['lon']
        )
        
        dist_despues = self.calcular_distancia_haversine(
            coord_vecino['lat'], coord_vecino['lon'],
            coord_destino['lat'], coord_destino['lon']
        )
        
        # Progreso: positivo si nos acercamos, negativo si nos alejamos
        progreso = (dist_antes - dist_despues) / dist_antes if dist_antes > 0 else 0
        
        # Penalización: mayor cuando nos desviamos Y no hacemos progreso
        # Normalizar desviación angular a 0-1 (donde 90° = 0.5, 180° = 1.0)
        factor_desviacion = desviacion_angular / 180.0
        
        # Si nos alejamos del destino, penalizar más fuertemente
        if progreso < 0:
            penalizacion = factor_desviacion * self.DIRECTION_PENALTY_STRENGTH * (1 - progreso)
        else:
            # Si nos acercamos, penalizar proporcionalmente a la desviación
            penalizacion = factor_desviacion * self.DIRECTION_PENALTY_STRENGTH * 0.5
        
        return penalizacion
    
    def encontrar_ruta_mas_fiable(self, origen: str, destino: str, 
                                   fecha_salida=None, hora_salida=None,
                                   predictor_clima=None) -> Optional[Ruta]:
        """
        Encuentra la ruta más fiable con penalización geográfica.
        
        Sobrescribe el método padre para incluir penalización por dirección.
        """
        if origen not in self.grafo.nodos:
            raise ValueError(f"Nodo origen '{origen}' no existe en el grafo")
        if destino not in self.grafo.nodos:
            raise ValueError(f"Nodo destino '{destino}' no existe en el grafo")
        
        # Estructuras de datos para Dijkstra
        pesos = {nodo: float('inf') for nodo in self.grafo.nodos}
        pesos[origen] = 0
        
        # Para reconstruir el camino
        previos: Dict[str, Tuple[str, any]] = {}
        
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
                
                # Calcular peso base
                if fecha_salida and hora_salida and predictor_clima:
                    try:
                        riesgo_clima = predictor_clima.predecir_riesgo_por_fecha(
                            departamento=nodo_actual,
                            fecha_salida=fecha_salida
                        )
                    except Exception as e:
                        riesgo_clima = 0.0
                    
                    peso_base = arista.calcular_peso_dinamico(
                        fecha_salida=fecha_salida,
                        hora_salida=hora_salida,
                        riesgo_clima=riesgo_clima
                    )
                else:
                    peso_base = arista.calcular_peso_fiabilidad()
                
                # 🔥 NUEVA FUNCIONALIDAD: Aplicar penalización geográfica
                penalizacion = self.calcular_penalizacion_direccion(nodo_actual, vecino, destino)
                peso_arista = peso_base * (1 + penalizacion)
                
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
