"""
Módulo: api_siar_final.py
Descripción: API REST completa para SIAR con 9 departamentos del Perú.
Incluye: Rutas, Alertas, Predicción Climática, Árbol de Decisión

Ejecutar: python -m uvicorn src.integracion.api_siar_final:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.unidad3_grafos.grafo_rutas import GrafoRutas, TipoCamino
from src.unidad3_grafos.algoritmo_fiabilidad import AlgoritmoFiabilidad, Ruta
from src.unidad3_grafos.maquina_estados import (
    MaquinaEstadosAlerta, MaquinaEstadosLogistica,
    Alerta, LoteCosecha, EstadoAlerta, EstadoLote,
    EventoAlerta, EventoLote
)

# Intentar importar red neuronal
try:
    from src.unidad3_grafos.red_neuronal_simple import RedNeuronalSimple
    RED_NEURONAL_DISPONIBLE = True
except:
    RED_NEURONAL_DISPONIBLE = False

# Intentar importar árbol de decisión
try:
    from src.unidad3_grafos.arbol_decision_rutas import ClasificadorRutas
    ARBOL_DISPONIBLE = True
except:
    ARBOL_DISPONIBLE = False


# ========== MODELOS PYDANTIC ==========

class RutaResponse(BaseModel):
    nodos: List[str]
    distancia_km: float
    fiabilidad: float
    tiempo_min: int
    peso: float
    clasificacion: Optional[str] = None
    geometry: Optional[List[List[float]]] = None  # Coordenadas reales de la ruta


class ComparacionRutasResponse(BaseModel):
    mas_fiable: RutaResponse
    mas_corta: RutaResponse
    mas_rapida: RutaResponse


class PrediccionClima(BaseModel):
    temperatura: float
    precipitacion: float
    humedad: float
    presion: Optional[float] = 1010
    viento: Optional[float] = 5


class PrediccionResponse(BaseModel):
    probabilidad_bloqueo: float
    clasificacion: str
    recomendacion: str
    fiabilidad_ajustada: float


class AlertaCreate(BaseModel):
    tipo: str
    ubicacion: str
    descripcion: str
    emisor: str


class AlertaResponse(BaseModel):
    id: str
    tipo: str
    ubicacion: str
    descripcion: str
    estado: str
    nivel_confianza: float
    confirmaciones: int
    timestamp: str


# ========== INICIALIZACIÓN ==========

app = FastAPI(
    title="SIAR API - Sistema Nacional",
    description="API REST para gestión de rutas, alertas y predicción climática en 9 departamentos del Perú",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales
grafo: Optional[GrafoRutas] = None
algoritmo: Optional[AlgoritmoFiabilidad] = None
modelo_rn: Optional[RedNeuronalSimple] = None
clasificador: Optional[ClasificadorRutas] = None

alertas_db: Dict[str, Alerta] = {}
lotes_db: Dict[str, LoteCosecha] = {}
contador_alertas = 0
contador_lotes = 0

fsm_alertas = MaquinaEstadosAlerta()
fsm_logistica = MaquinaEstadosLogistica()

# Coordenadas de departamentos
COORDENADAS = {
    'Lima': {'lat': -12.0464, 'lon': -77.0428},
    'Cusco': {'lat': -13.5319, 'lon': -71.9675},
    'Arequipa': {'lat': -16.4090, 'lon': -71.5375},
    'Puno': {'lat': -15.8422, 'lon': -70.0199},
    'Ayacucho': {'lat': -13.1631, 'lon': -74.2236},
    'Junín': {'lat': -12.0699, 'lon': -75.2048},
    'Cajamarca': {'lat': -7.1614, 'lon': -78.5126},
    'San Martín': {'lat': -6.4833, 'lon': -76.3667},
    'Amazonas': {'lat': -5.7667, 'lon': -77.8667}
}


@app.on_event("startup")
async def startup_event():
    """Cargar datos al iniciar."""
    global grafo, algoritmo, modelo_rn, clasificador
    
    print("\n" + "="*70)
    print("🚀 INICIANDO SIAR API")
    print("="*70 + "\n")
    
    # Cargar grafo
    try:
        ruta_grafo = "data/grafos/red_peru_completa.json"
        if os.path.exists(ruta_grafo):
            grafo = GrafoRutas.cargar_json(ruta_grafo)
            algoritmo = AlgoritmoFiabilidad(grafo)
            print(f"✅ Grafo cargado: {len(grafo.nodos)} departamentos")
        else:
            print(f"⚠️  Creando grafo de ejemplo...")
            grafo = crear_grafo_ejemplo()
            algoritmo = AlgoritmoFiabilidad(grafo)
    except Exception as e:
        print(f"❌ Error cargando grafo: {e}")
        grafo = crear_grafo_ejemplo()
        algoritmo = AlgoritmoFiabilidad(grafo)
    
    # Cargar modelo de red neuronal
    if RED_NEURONAL_DISPONIBLE:
        try:
            ruta_modelo = "data/modelos/red_neuronal_senamhi.npz"
            if os.path.exists(ruta_modelo):
                modelo_rn = RedNeuronalSimple()
                modelo_rn.cargar_modelo(ruta_modelo)
                print(f"✅ Red neuronal cargada")
            else:
                print(f"ℹ️  Red neuronal no cargada (modelo no encontrado)")
        except Exception as e:
            print(f"⚠️  Red neuronal no disponible: {e}")
    
    # Cargar clasificador
    if ARBOL_DISPONIBLE:
        try:
            clasificador = ClasificadorRutas(max_depth=5)
            # Entrenar con datos sintéticos si no hay modelo
            df = clasificador.generar_datos_entrenamiento(1000)
            X = df[clasificador.feature_names].values
            y = df['clase'].values
            clasificador.entrenar(X, y)
            print(f"✅ Árbol de decisión entrenado")
        except Exception as e:
            print(f"⚠️  Árbol de decisión no disponible: {e}")
    
    print("\n" + "="*70)
    print("✅ API LISTA")
    print("="*70 + "\n")


def crear_grafo_ejemplo() -> GrafoRutas:
    """Crea grafo de ejemplo si no existe archivo."""
    grafo = GrafoRutas()
    
    for depto in COORDENADAS.keys():
        grafo.agregar_nodo(depto)
    
    # Rutas principales
    rutas = [
        ('Lima', 'Cusco', 1100, 0.85),
        ('Lima', 'Arequipa', 1010, 0.90),
        ('Cusco', 'Puno', 389, 0.88),
        ('Lima', 'Cajamarca', 865, 0.83)
    ]
    
    for origen, destino, km, fiab in rutas:
        grafo.agregar_camino(origen, destino, km, fiab, TipoCamino.ASFALTADO, 0.15)
    
    return grafo


def ruta_to_response(ruta: Ruta, clasificacion: str = None) -> RutaResponse:
    """Convierte Ruta a RutaResponse."""
    return RutaResponse(
        nodos=ruta.nodos,
        distancia_km=ruta.distancia_total_km,
        fiabilidad=ruta.fiabilidad_acumulada,
        tiempo_min=ruta.tiempo_total_min,
        peso=ruta.peso_total,
        clasificacion=clasificacion
    )


# ========== ENDPOINTS ==========

@app.get("/", tags=["General"])
async def root():
    """Endpoint raíz."""
    return {
        "nombre": "SIAR API - Sistema Nacional",
        "version": "2.0.0",
        "departamentos": len(COORDENADAS),
        "documentacion": "/docs",
        "estado": "operativo"
    }


@app.get("/grafos/nodos", response_model=List[str], tags=["Grafos"])
async def obtener_nodos():
    """Lista todos los departamentos disponibles."""
    if grafo is None:
        raise HTTPException(status_code=503, detail="Grafo no disponible")
    return sorted(list(grafo.nodos))


@app.get("/grafos/coordenadas", tags=["Grafos"])
async def obtener_coordenadas():
    """Obtiene coordenadas GPS de todos los departamentos."""
    return COORDENADAS


@app.get("/grafos/info", tags=["Grafos"])
async def info_grafo():
    """Estadísticas de la red vial."""
    if grafo is None:
        raise HTTPException(status_code=503, detail="Grafo no disponible")
    
    num_aristas = sum(len(v) for v in grafo.adyacencias.values()) // 2
    
    return {
        "departamentos": len(grafo.nodos),
        "rutas": num_aristas,
        "modelos_activos": {
            "red_neuronal": modelo_rn is not None,
            "arbol_decision": clasificador is not None
        }
    }


@app.get("/rutas/calcular", response_model=RutaResponse, tags=["Rutas"])
async def calcular_ruta(origen: str, destino: str):
    """Calcula la ruta más fiable entre dos departamentos."""
    if algoritmo is None:
        raise HTTPException(status_code=503, detail="Algoritmo no disponible")
    
    if origen not in grafo.nodos:
        raise HTTPException(status_code=404, detail=f"Departamento '{origen}' no encontrado")
    if destino not in grafo.nodos:
        raise HTTPException(status_code=404, detail=f"Departamento '{destino}' no encontrado")
    
    try:
        ruta = algoritmo.encontrar_ruta_mas_fiable(origen, destino)
        if ruta is None:
            raise HTTPException(status_code=404, detail="No existe ruta")
        
        # Obtener geometría REAL usando OSRM
        geometry = None
        try:
            import requests
            
            # Obtener coordenadas de cada nodo de la ruta
            coords_str = ";".join([
                f"{COORDENADAS[nodo]['lon']},{COORDENADAS[nodo]['lat']}" 
                for nodo in ruta.nodos
            ])
            
            # Llamar a OSRM
            url = f"http://router.project-osrm.org/route/v1/driving/{coords_str}"
            params = {'overview': 'full', 'geometries': 'geojson'}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 'Ok':
                    # Convertir lon,lat a lat,lon
                    coords = data['routes'][0]['geometry']['coordinates']
                    geometry = [[c[1], c[0]] for c in coords]
                    print(f"✅ OSRM: {len(geometry)} puntos de geometría")
        except Exception as e:
            print(f"⚠️  No se pudo obtener geometría OSRM: {e}")
            # Fallback: usar coords de nodos
            geometry = [[COORDENADAS[n]['lat'], COORDENADAS[n]['lon']] for n in ruta.nodos]
        
        # Clasificar ruta si hay árbol disponible
        clasificacion = None
        if clasificador and clasificador.entrenado:
            clase_num, clase_nombre, _ = clasificador.predecir(
                precipitacion=5, temperatura=20, tipo_camino=2,
                mes=6, riesgo_historico=0.2, hora=12
            )
            clasificacion = clase_nombre
        
        # IMPORTANTE: Crear respuesta con geometry
        return RutaResponse(
            nodos=ruta.nodos,
            distancia_km=ruta.distancia_total_km,
            fiabilidad=ruta.fiabilidad_acumulada,
            tiempo_min=ruta.tiempo_total_min,
            peso=ruta.peso_total,
            clasificacion=clasificacion,
            geometry=geometry  # ← ESTO ES LO QUE FALTABA
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rutas/comparar", response_model=ComparacionRutasResponse, tags=["Rutas"])
async def comparar_rutas(origen: str, destino: str):
    """Compara diferentes criterios de optimización."""
    if algoritmo is None:
        raise HTTPException(status_code=503, detail="Algoritmo no disponible")
    
    try:
        import requests
        
        comparacion = algoritmo.comparar_rutas(origen, destino)
        
        # Función auxiliar para obtener geometría
        def obtener_geometria(ruta):
            try:
                coords_str = ";".join([
                    f"{COORDENADAS[nodo]['lon']},{COORDENADAS[nodo]['lat']}" 
                    for nodo in ruta.nodos
                ])
                
                url = f"http://router.project-osrm.org/route/v1/driving/{coords_str}"
                params = {'overview': 'full', 'geometries': 'geojson'}
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data['code'] == 'Ok':
                        coords = data['routes'][0]['geometry']['coordinates']
                        return [[c[1], c[0]] for c in coords]
            except:
                pass
            
            # Fallback
            return [[COORDENADAS[n]['lat'], COORDENADAS[n]['lon']] for n in ruta.nodos]
        
        # Obtener geometría para cada ruta
        geom_fiable = obtener_geometria(comparacion['mas_fiable'])
        geom_corta = obtener_geometria(comparacion['mas_corta'])
        geom_rapida = obtener_geometria(comparacion['mas_rapida'])
        
        return ComparacionRutasResponse(
            mas_fiable=RutaResponse(
                nodos=comparacion['mas_fiable'].nodos,
                distancia_km=comparacion['mas_fiable'].distancia_total_km,
                fiabilidad=comparacion['mas_fiable'].fiabilidad_acumulada,
                tiempo_min=comparacion['mas_fiable'].tiempo_total_min,
                peso=comparacion['mas_fiable'].peso_total,
                geometry=geom_fiable
            ),
            mas_corta=RutaResponse(
                nodos=comparacion['mas_corta'].nodos,
                distancia_km=comparacion['mas_corta'].distancia_total_km,
                fiabilidad=comparacion['mas_corta'].fiabilidad_acumulada,
                tiempo_min=comparacion['mas_corta'].tiempo_total_min,
                peso=comparacion['mas_corta'].peso_total,
                geometry=geom_corta
            ),
            mas_rapida=RutaResponse(
                nodos=comparacion['mas_rapida'].nodos,
                distancia_km=comparacion['mas_rapida'].distancia_total_km,
                fiabilidad=comparacion['mas_rapida'].fiabilidad_acumulada,
                tiempo_min=comparacion['mas_rapida'].tiempo_total_min,
                peso=comparacion['mas_rapida'].peso_total,
                geometry=geom_rapida
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/prediccion/clima", response_model=PrediccionResponse, tags=["Predicción"])
async def predecir_clima(datos: PrediccionClima):
    """Predice riesgo de bloqueo basado en condiciones climáticas."""
    
    # Predicción simple por defecto
    prob_bloqueo = 0.0
    
    if datos.precipitacion > 30:
        prob_bloqueo += 0.4
    if datos.temperatura < 5 or datos.temperatura > 35:
        prob_bloqueo += 0.3
    if datos.humedad > 90:
        prob_bloqueo += 0.2
    
    prob_bloqueo = min(1.0, prob_bloqueo)
    
    # Usar red neuronal si está disponible
    if modelo_rn is not None:
        try:
            import numpy as np
            X = np.array([[datos.temperatura, datos.precipitacion, 
                          datos.humedad, datos.presion, datos.viento]])
            prob_bloqueo = float(modelo_rn.predecir(X)[0])
        except:
            pass
    
    # Clasificación
    if prob_bloqueo > 0.7:
        clasificacion = "PELIGROSA"
        recomendacion = "⛔ ALTO RIESGO: Evitar viaje"
    elif prob_bloqueo > 0.4:
        clasificacion = "MODERADA"
        recomendacion = "⚠️  RIESGO MODERADO: Precaución"
    else:
        clasificacion = "SEGURA"
        recomendacion = "✅ RIESGO BAJO: Condiciones favorables"
    
    fiabilidad_ajustada = 0.85 * (1 - prob_bloqueo * 0.5)
    
    return PrediccionResponse(
        probabilidad_bloqueo=prob_bloqueo,
        clasificacion=clasificacion,
        recomendacion=recomendacion,
        fiabilidad_ajustada=fiabilidad_ajustada
    )


@app.post("/alertas/crear", response_model=AlertaResponse, tags=["Alertas"])
async def crear_alerta(alerta_data: AlertaCreate):
    """Crea una nueva alerta."""
    global contador_alertas
    contador_alertas += 1
    
    alerta = Alerta(
        id=f"ALR-{contador_alertas:04d}",
        tipo=alerta_data.tipo,
        ubicacion=alerta_data.ubicacion,
        descripcion=alerta_data.descripcion,
        emisor=alerta_data.emisor,
        timestamp_creacion=datetime.now()
    )
    
    alertas_db[alerta.id] = alerta
    
    return AlertaResponse(
        id=alerta.id,
        tipo=alerta.tipo,
        ubicacion=alerta.ubicacion,
        descripcion=alerta.descripcion,
        estado=alerta.estado.value,
        nivel_confianza=alerta.nivel_confianza,
        confirmaciones=len(alerta.confirmaciones),
        timestamp=alerta.timestamp_creacion.isoformat()
    )


@app.get("/alertas/activas", response_model=List[AlertaResponse], tags=["Alertas"])
async def obtener_alertas_activas():
    """Lista alertas activas."""
    alertas_activas = [
        AlertaResponse(
            id=alerta.id,
            tipo=alerta.tipo,
            ubicacion=alerta.ubicacion,
            descripcion=alerta.descripcion,
            estado=alerta.estado.value,
            nivel_confianza=alerta.nivel_confianza,
            confirmaciones=len(alerta.confirmaciones),
            timestamp=alerta.timestamp_creacion.isoformat()
        )
        for alerta in alertas_db.values()
        if alerta.estado not in [EstadoAlerta.RESUELTA, EstadoAlerta.FALSA_ALARMA]
    ]
    return alertas_activas


@app.get("/test", tags=["Test"])
async def test_endpoint():
    """Endpoint de prueba."""
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "grafo_activo": grafo is not None,
        "departamentos": len(COORDENADAS),
        "alertas": len(alertas_db),
        "modelos": {
            "red_neuronal": RED_NEURONAL_DISPONIBLE and modelo_rn is not None,
            "arbol_decision": ARBOL_DISPONIBLE and clasificador is not None
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)