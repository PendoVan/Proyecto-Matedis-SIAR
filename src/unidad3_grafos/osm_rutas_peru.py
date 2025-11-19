"""
Módulo: osm_rutas_peru.py
Descripción: Integración con OpenStreetMap para obtener rutas reales de Perú.
Convierte datos OSM en el formato del GrafoRutas de SIAR.

Instalación requerida:
pip install osmnx geopandas folium networkx
"""

import osmnx as ox # type: ignore
import networkx as nx # type: ignore
import folium # type: ignore
from typing import List, Tuple, Optional, Dict
import json
from dataclasses import dataclass
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.unidad3_grafos.grafo_rutas import GrafoRutas, TipoCamino, Arista


@dataclass
class CoordenadaGPS:
    """Representa una coordenada geográfica."""
    latitud: float
    longitud: float
    nombre: str
    
    def to_tuple(self) -> Tuple[float, float]:
        return (self.latitud, self.longitud)


class IntegradorOSM:
    """
    Integra datos de OpenStreetMap con el sistema SIAR.
    Descarga redes viales reales y las convierte al formato GrafoRutas.
    """
    
    # Coordenadas de ciudades de Ayacucho
    COORDENADAS_AYACUCHO = {
        "Ayacucho": CoordenadaGPS(-13.1631, -74.2236, "Ayacucho"),
        "Huanta": CoordenadaGPS(-12.9394, -74.2472, "Huanta"),
        "San Miguel": CoordenadaGPS(-13.0122, -73.9808, "San Miguel"),
        "Tambo": CoordenadaGPS(-14.7986, -73.9186, "Tambo"),
        "Quinua": CoordenadaGPS(-13.0500, -74.1333, "Quinua"),
        "Sivia": CoordenadaGPS(-12.4500, -73.7833, "Sivia")
    }
    
    def __init__(self):
        self.grafo_osm = None
        self.grafo_siar = GrafoRutas()
        self.nodos_mapeados = {}  # Mapeo de nodos OSM a nombres de ciudades
    
    def descargar_region(self, nombre_region: str = "Ayacucho, Peru", 
                         tipo_red: str = "drive") -> nx.MultiDiGraph:
        """
        Descarga la red vial de una región desde OpenStreetMap.
        
        Args:
            nombre_region: Nombre de la región (ciudad, provincia, país)
            tipo_red: Tipo de red ('drive', 'walk', 'bike', 'all')
            
        Returns:
            Grafo de NetworkX con la red vial
        """
        print(f"📡 Descargando red vial de {nombre_region} desde OpenStreetMap...")
        
        try:
            # Descargar grafo de la región
            self.grafo_osm = ox.graph_from_place(
                nombre_region, 
                network_type=tipo_red,
                simplify=True
            )
            
            num_nodos = len(self.grafo_osm.nodes)
            num_aristas = len(self.grafo_osm.edges)
            
            print(f"✅ Red descargada: {num_nodos} nodos, {num_aristas} aristas")
            return self.grafo_osm
            
        except Exception as e:
            print(f"❌ Error descargando región: {e}")
            return None
    
    def descargar_ruta_entre_ciudades(self, origen: str, destino: str) -> nx.MultiDiGraph:
        """
        Descarga la red vial entre dos ciudades específicas.
        
        Args:
            origen: Nombre de la ciudad de origen
            destino: Nombre de la ciudad de destino
        """
        print(f"📡 Descargando ruta: {origen} → {destino}")
        
        try:
            coord_origen = self.COORDENADAS_AYACUCHO[origen]
            coord_destino = self.COORDENADAS_AYACUCHO[destino]
            
            # Calcular bounding box que incluya ambas ciudades
            norte = max(coord_origen.latitud, coord_destino.latitud) + 0.5
            sur = min(coord_origen.latitud, coord_destino.latitud) - 0.5
            este = max(coord_origen.longitud, coord_destino.longitud) + 0.5
            oeste = min(coord_origen.longitud, coord_destino.longitud) - 0.5
            
            # Descargar grafo del área
            self.grafo_osm = ox.graph_from_bbox(
                norte, sur, este, oeste,
                network_type='drive',
                simplify=True
            )
            
            print(f"✅ Red descargada para {origen} → {destino}")
            return self.grafo_osm
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def encontrar_nodo_mas_cercano(self, ciudad: str) -> int:
        """
        Encuentra el nodo OSM más cercano a una ciudad.
        
        Args:
            ciudad: Nombre de la ciudad
            
        Returns:
            ID del nodo OSM más cercano
        """
        if ciudad not in self.COORDENADAS_AYACUCHO:
            raise ValueError(f"Ciudad {ciudad} no encontrada")
        
        coord = self.COORDENADAS_AYACUCHO[ciudad]
        nodo_id = ox.distance.nearest_nodes(
            self.grafo_osm, 
            coord.longitud, 
            coord.latitud
        )
        
        self.nodos_mapeados[nodo_id] = ciudad
        return nodo_id
    
    def calcular_ruta_osm(self, origen: str, destino: str) -> Optional[List[int]]:
        """
        Calcula la ruta más corta entre dos ciudades usando OSM.
        
        Args:
            origen: Ciudad de origen
            destino: Ciudad de destino
            
        Returns:
            Lista de IDs de nodos que forman la ruta
        """
        if self.grafo_osm is None:
            print("⚠️  Primero debes descargar la red con descargar_region()")
            return None
        
        try:
            nodo_origen = self.encontrar_nodo_mas_cercano(origen)
            nodo_destino = self.encontrar_nodo_mas_cercano(destino)
            
            # Calcular ruta más corta
            ruta = nx.shortest_path(
                self.grafo_osm, 
                nodo_origen, 
                nodo_destino,
                weight='length'
            )
            
            return ruta
            
        except nx.NetworkXNoPath:
            print(f"❌ No existe ruta entre {origen} y {destino}")
            return None
        except Exception as e:
            print(f"❌ Error calculando ruta: {e}")
            return None
    
    def convertir_a_grafo_siar(self) -> GrafoRutas:
        """
        Convierte el grafo OSM al formato GrafoRutas de SIAR.
        Simplifica la red y agrega atributos de fiabilidad.
        """
        if self.grafo_osm is None:
            raise ValueError("Primero debes descargar la red OSM")
        
        print("🔄 Convirtiendo grafo OSM a formato SIAR...")
        
        # Crear nodos principales (ciudades)
        for ciudad, coord in self.COORDENADAS_AYACUCHO.items():
            metadata = {
                "tipo": "ciudad",
                "latitud": coord.latitud,
                "longitud": coord.longitud
            }
            self.grafo_siar.agregar_nodo(ciudad, metadata)
        
        # Calcular rutas entre todas las ciudades
        ciudades = list(self.COORDENADAS_AYACUCHO.keys())
        
        for i, origen in enumerate(ciudades):
            for destino in ciudades[i+1:]:
                try:
                    ruta = self.calcular_ruta_osm(origen, destino)
                    
                    if ruta:
                        # Calcular distancia total de la ruta
                        distancia_total = 0
                        for j in range(len(ruta) - 1):
                            u, v = ruta[j], ruta[j+1]
                            
                            # Obtener todas las aristas entre u y v
                            if self.grafo_osm.has_edge(u, v):
                                edge_data = self.grafo_osm.get_edge_data(u, v)
                                # Puede haber múltiples aristas, tomar la primera
                                distancia = list(edge_data.values())[0].get('length', 0)
                                distancia_total += distancia
                        
                        distancia_km = distancia_total / 1000  # Convertir a km
                        
                        # Estimar tipo de camino y fiabilidad basado en características OSM
                        tipo_camino = self._inferir_tipo_camino(ruta)
                        fiabilidad = self._calcular_fiabilidad(tipo_camino, distancia_km)
                        riesgo = self._calcular_riesgo_historico(origen, destino)
                        
                        self.grafo_siar.agregar_camino(
                            origen=origen,
                            destino=destino,
                            distancia_km=distancia_km,
                            fiabilidad=fiabilidad,
                            tipo_camino=tipo_camino,
                            riesgo_historico=riesgo
                        )
                        
                        print(f"✓ {origen} → {destino}: {distancia_km:.1f} km")
                        
                except Exception as e:
                    print(f"⚠️  No se pudo conectar {origen} → {destino}: {e}")
        
        print(f"✅ Grafo SIAR creado con {len(self.grafo_siar.nodos)} nodos")
        return self.grafo_siar
    
    def _inferir_tipo_camino(self, ruta: List[int]) -> TipoCamino:
        """
        Infiere el tipo de camino basándose en atributos OSM.
        """
        # Analizar las aristas de la ruta
        tipos_highway = []
        
        for i in range(len(ruta) - 1):
            u, v = ruta[i], ruta[i+1]
            if self.grafo_osm.has_edge(u, v):
                edge_data = self.grafo_osm.get_edge_data(u, v)
                highway = list(edge_data.values())[0].get('highway', 'unclassified')
                tipos_highway.append(highway)
        
        # Determinar tipo predominante
        if any(h in ['motorway', 'trunk', 'primary'] for h in tipos_highway):
            return TipoCamino.ASFALTADO
        elif any(h in ['secondary', 'tertiary'] for h in tipos_highway):
            return TipoCamino.AFIRMADO
        elif any(h in ['unclassified', 'residential'] for h in tipos_highway):
            return TipoCamino.TROCHA
        else:
            return TipoCamino.HERRADURA
    
    def _calcular_fiabilidad(self, tipo_camino: TipoCamino, distancia_km: float) -> float:
        """
        Calcula la fiabilidad estimada basándose en tipo de camino y distancia.
        """
        fiabilidades_base = {
            TipoCamino.ASFALTADO: 0.95,
            TipoCamino.AFIRMADO: 0.80,
            TipoCamino.TROCHA: 0.65,
            TipoCamino.HERRADURA: 0.50
        }
        
        fiabilidad_base = fiabilidades_base[tipo_camino]
        
        # Reducir fiabilidad para distancias muy largas
        factor_distancia = max(0.8, 1 - (distancia_km / 500))
        
        return min(0.99, fiabilidad_base * factor_distancia)
    
    def _calcular_riesgo_historico(self, origen: str, destino: str) -> float:
        """
        Calcula el riesgo histórico de bloqueos (valores predefinidos).
        En producción, esto vendría de una base de datos de incidentes.
        """
        # Rutas conocidas con alto riesgo
        rutas_riesgosas = {
            ("Huanta", "Sivia"): 0.45,
            ("Sivia", "Huanta"): 0.45,
            ("Quinua", "Tambo"): 0.50,
            ("Tambo", "Quinua"): 0.50
        }
        
        return rutas_riesgosas.get((origen, destino), 0.15)
    
    def visualizar_ruta(self, origen: str, destino: str, 
                       guardar_como: str = "data/mapas/ruta_osm.html"):
        """
        Visualiza una ruta en un mapa interactivo con Folium.
        
        Args:
            origen: Ciudad de origen
            destino: Ciudad de destino
            guardar_como: Ruta donde guardar el HTML del mapa
        """
        if self.grafo_osm is None:
            print("⚠️  Primero debes descargar la red")
            return
        
        try:
            ruta = self.calcular_ruta_osm(origen, destino)
            
            if not ruta:
                return
            
            # Crear mapa centrado en la ruta
            coord_origen = self.COORDENADAS_AYACUCHO[origen]
            
            mapa = folium.Map(
                location=[coord_origen.latitud, coord_origen.longitud],
                zoom_start=9,
                tiles='OpenStreetMap'
            )
            
            # Dibujar la ruta
            coords_ruta = []
            for node_id in ruta:
                node_data = self.grafo_osm.nodes[node_id]
                coords_ruta.append([node_data['y'], node_data['x']])
            
            folium.PolyLine(
                coords_ruta,
                color='blue',
                weight=5,
                opacity=0.7,
                tooltip=f"Ruta: {origen} → {destino}"
            ).add_to(mapa)
            
            # Marcar origen y destino
            coord_destino = self.COORDENADAS_AYACUCHO[destino]
            
            folium.Marker(
                [coord_origen.latitud, coord_origen.longitud],
                popup=origen,
                icon=folium.Icon(color='green', icon='play')
            ).add_to(mapa)
            
            folium.Marker(
                [coord_destino.latitud, coord_destino.longitud],
                popup=destino,
                icon=folium.Icon(color='red', icon='stop')
            ).add_to(mapa)
            
            # Guardar mapa
            os.makedirs(os.path.dirname(guardar_como), exist_ok=True)
            mapa.save(guardar_como)
            
            print(f"✅ Mapa guardado en: {guardar_como}")
            print(f"   Abre el archivo en tu navegador para ver la ruta")
            
        except Exception as e:
            print(f"❌ Error visualizando ruta: {e}")


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    print("="*70)
    print("🗺️  INTEGRACIÓN OPENSTREETMAP + SIAR")
    print("="*70 + "\n")
    
    integrador = IntegradorOSM()
    
    # Opción 1: Descargar región completa (puede tardar)
    print("📍 Método 1: Descargar región de Ayacucho\n")
    # grafo_osm = integrador.descargar_region("Ayacucho, Peru")
    
    # Opción 2: Descargar solo área entre dos ciudades (más rápido)
    print("📍 Método 2: Descargar área específica\n")
    grafo_osm = integrador.descargar_ruta_entre_ciudades("Ayacucho", "Huanta")
    
    if grafo_osm:
        print("\n🔄 Convirtiendo a formato SIAR...\n")
        grafo_siar = integrador.convertir_a_grafo_siar()
        
        # Guardar grafo
        ruta_salida = "data/grafos/red_ayacucho_osm.json"
        grafo_siar.exportar_json(ruta_salida)
        print(f"\n💾 Grafo guardado en: {ruta_salida}")
        
        # Visualizar ruta
        print("\n🗺️  Generando visualización...\n")
        integrador.visualizar_ruta("Ayacucho", "Huanta")
        
        print("\n✅ Proceso completado")
        print("📊 Estadísticas:")
        print(f"   - Nodos SIAR: {len(grafo_siar.nodos)}")
        print(f"   - Rutas calculadas: {sum(len(v) for v in grafo_siar.adyacencias.values()) // 2}")