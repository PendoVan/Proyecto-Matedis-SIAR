"""
Módulo: api_siar.py
Descripción: API REST completa para SIAR con 9 departamentos del Perú.
Incluye: Rutas, Alertas, Predicción Climática, Árbol de Decisión

Ejecutar: python -m uvicorn src.integracion.api_siar:app --reload
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
from src.unidad3_grafos.prediccion_climatica import IntegradorSENAMHI
from src.unidad3_grafos.maquina_estados import (
    MaquinaEstadosAlerta, MaquinaEstadosLogistica,
    Alerta, LoteCosecha, EstadoAlerta, EstadoLote,
    EventoAlerta, EventoLote
)

# Intentar importar red neuronal
try:
    from src.unidad3_grafos.red_neuronal_tensorflow import RedNeuronalClima
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
    departamento: Optional[str] = "Lima"


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

class AlertaGeo(BaseModel):
    """Alerta con coordenadas geográficas"""
    tipo: str
    ubicacion: str  # Texto descriptivo
    lat: float      # 👈 NUEVO
    lon: float      # 👈 NUEVO
    descripcion: str
    simular_errores: int = 0

class AlertaGeoResponse(BaseModel):
    """Respuesta con alerta codificada y posición"""
    alerta_id: str
    lat: float
    lon: float
    tipo: str
    ubicacion: str
    descripcion: str
    estado: str
    bits_codificados: int
    errores_corregidos: int
    firma_valida: bool
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
modelo_rn: Optional[RedNeuronalClima] = None
clasificador: Optional[ClasificadorRutas] = None
predictor_clima: Optional[IntegradorSENAMHI] = None

alertas_db: Dict[str, Alerta] = {}
lotes_db: Dict[str, LoteCosecha] = {}
contador_alertas = 0
contador_lotes = 0

fsm_alertas = MaquinaEstadosAlerta()
fsm_logistica = MaquinaEstadosLogistica()

# Coordenadas de departamentos
COORDENADAS = {
    # COSTA
    'Lima': {'lat': -12.0464, 'lon': -77.0428, 'region': 'costa'},
    'Callao': {'lat': -12.0565, 'lon': -77.1181, 'region': 'costa'},
    'Ica': {'lat': -14.0678, 'lon': -75.7286, 'region': 'costa'},
    'Arequipa': {'lat': -16.4090, 'lon': -71.5375, 'region': 'costa'},
    'Moquegua': {'lat': -17.1934, 'lon': -70.9336, 'region': 'costa'},
    'Tacna': {'lat': -18.0047, 'lon': -70.2453, 'region': 'costa'},
    'Tumbes': {'lat': -3.5669, 'lon': -80.4515, 'region': 'costa'},
    'Piura': {'lat': -5.1945, 'lon': -80.6328, 'region': 'costa'},
    'Lambayeque': {'lat': -6.7011, 'lon': -79.9061, 'region': 'costa'},
    'La Libertad': {'lat': -8.1116, 'lon': -79.0292, 'region': 'costa'},
    'Ancash': {'lat': -9.5267, 'lon': -77.5284, 'region': 'costa-sierra'},
    
    # SIERRA
    'Cajamarca': {'lat': -7.1614, 'lon': -78.5126, 'region': 'sierra'},
    'Huánuco': {'lat': -9.9306, 'lon': -76.2422, 'region': 'sierra'},
    'Pasco': {'lat': -10.6819, 'lon': -76.2561, 'region': 'sierra'},
    'Junín': {'lat': -12.0699, 'lon': -75.2048, 'region': 'sierra'},
    'Huancavelica': {'lat': -12.7872, 'lon': -74.9758, 'region': 'sierra'},
    'Ayacucho': {'lat': -13.1631, 'lon': -74.2236, 'region': 'sierra'},
    'Apurímac': {'lat': -13.6344, 'lon': -72.8831, 'region': 'sierra'},  # 👈 Este faltaba!
    'Cusco': {'lat': -13.5319, 'lon': -71.9675, 'region': 'sierra'},
    'Puno': {'lat': -15.8422, 'lon': -70.0199, 'region': 'sierra'},
    
    # SELVA
    'Amazonas': {'lat': -5.7667, 'lon': -77.8667, 'region': 'selva'},
    'San Martín': {'lat': -6.4833, 'lon': -76.3667, 'region': 'selva'},
    'Loreto': {'lat': -3.7499, 'lon': -73.2540, 'region': 'selva'},
    'Ucayali': {'lat': -8.3791, 'lon': -74.5539, 'region': 'selva'},
    'Madre de Dios': {'lat': -12.5935, 'lon': -69.1892, 'region': 'selva'}
}


@app.on_event("startup")
async def startup_event():
    """Cargar datos al iniciar."""
    global grafo, algoritmo, modelo_rn, clasificador, predictor_clima
    
    print("\n" + "="*70)
    print("🚀 INICIANDO SIAR API")
    print("="*70 + "\n")
    
    # Cargar grafo
    try:
        ruta_grafo = "data/grafos/red_peru_24_departamentos.json"
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
            modelo_rn = RedNeuronalClima()
            if modelo_rn.cargar_modelo("data/modelos"):
                print(f"✅ Red neuronal TensorFlow cargada")
            else:
                modelo_rn = None
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
    
    try:
        global predictor_clima
        predictor_clima = IntegradorSENAMHI()
        if predictor_clima.cargar_modelo("data/modelos"):
            print(f"✅ Predictor climático cargado")
        else:
            print(f"⚠️  Predictor climático no disponible (entrenar primero)")
    except Exception as e:
        print(f"⚠️  Error cargando predictor: {e}")

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
    """Predice riesgo considerando factores regionales."""
    
    # Factores de ajuste por región
    FACTORES_REGIONALES = {
        'costa': {'lluvia_critica': 30, 'riesgo_base': 0.10},
        'sierra': {'lluvia_critica': 20, 'riesgo_base': 0.25},
        'selva': {'lluvia_critica': 50, 'riesgo_base': 0.35},
        'costa-sierra': {'lluvia_critica': 25, 'riesgo_base': 0.18}
    }
    
    # Obtener región del departamento
    if datos.departamento in COORDENADAS:
        # Cargar metadata del departamento desde coordenadas
        region = COORDENADAS[datos.departamento].get('region', 'costa')
    else:
        region = 'costa'  # Default
    
    factor_regional = FACTORES_REGIONALES.get(region, FACTORES_REGIONALES['costa'])
    
    # Ajustar predicción
    if predictor_clima and predictor_clima.modelo:
        pred = predictor_clima.predecir_riesgo(
            temperatura=datos.temperatura,
            precipitacion=datos.precipitacion,
            humedad=datos.humedad,
            presion=datos.presion or 750,
            viento=datos.viento or 5
        )
        
        # 👇 AJUSTE REGIONAL
        riesgo_ajustado = pred.riesgo_bloqueo * (1 + factor_regional['riesgo_base'])
        
        return PrediccionResponse(
            probabilidad_bloqueo=min(1.0, riesgo_ajustado),
            clasificacion=_clasificar_riesgo(riesgo_ajustado),
            recomendacion=f"{pred.recomendacion} (Región: {region.capitalize()})",
            fiabilidad_ajustada=pred.fiabilidad_ajustada
        )
    
    # Fallback con ajuste regional
    prob_bloqueo = factor_regional['riesgo_base']
    
    if datos.precipitacion > factor_regional['lluvia_critica']:
        prob_bloqueo += 0.4


def _clasificar_riesgo(prob: float) -> str:
    """Clasifica el nivel de riesgo."""
    if prob > 0.7:
        return "PELIGROSA"
    elif prob > 0.4:
        return "MODERADA"
    else:
        return "SEGURA"


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

@app.post("/alertas/crear-geo", response_model=AlertaGeoResponse, tags=["Alertas"])
async def crear_alerta_geo(alerta: AlertaGeo):
    """
    Crea una alerta geoespacial con Hamming + Firmas.
    
    Proceso:
    1. Recibe coordenadas del clic en mapa
    2. Codifica mensaje con Hamming
    3. Firma digitalmente
    4. Simula errores de transmisión
    5. Decodifica y corrige
    6. Guarda en BD y retorna para mostrar en mapa
    """
    global contador_alertas
    contador_alertas += 1
    
    # 1. Crear paquete resiliente
    paquete = protocolo_resiliente.enviar_alerta(
        tipo=alerta.tipo,
        ubicacion=alerta.ubicacion,
        descripcion=alerta.descripcion
    )
    
    # 2. Simular errores
    mensaje_codificado = paquete['mensaje_codificado']
    errores_corregidos = 0
    
    if alerta.simular_errores > 0:
        import random
        posiciones = random.sample(range(len(mensaje_codificado)), alerta.simular_errores)
        for pos in posiciones:
            mensaje_codificado[pos] = 1 - mensaje_codificado[pos]
        paquete['mensaje_codificado'] = mensaje_codificado
    
    # 3. Decodificar
    mensaje_recuperado = protocolo_resiliente.recibir_alerta(paquete, 0)
    
    if mensaje_recuperado:
        errores_corregidos = alerta.simular_errores
    
    # 4. Crear alerta en BD
    alerta_obj = Alerta(
        id=f"GEO-{contador_alertas:04d}",
        tipo=alerta.tipo,
        ubicacion=alerta.ubicacion,
        descripcion=alerta.descripcion,
        emisor="USUARIO-WEB",
        timestamp_creacion=datetime.now()
    )
    
    alertas_db[alerta_obj.id] = alerta_obj
    
    # 5. Retornar para mostrar en mapa
    return AlertaGeoResponse(
        alerta_id=alerta_obj.id,
        lat=alerta.lat,
        lon=alerta.lon,
        tipo=alerta.tipo,
        ubicacion=alerta.ubicacion,
        descripcion=alerta.descripcion,
        estado=alerta_obj.estado.value,
        bits_codificados=len(paquete['mensaje_codificado']),
        errores_corregidos=errores_corregidos,
        firma_valida=mensaje_recuperado is not None,
        timestamp=alerta_obj.timestamp_creacion.isoformat()
    )

@app.get("/alertas/mapa", tags=["Alertas"])
async def obtener_alertas_mapa():
    """Retorna todas las alertas para mostrar en el mapa."""
    return [
        {
            'id': alerta.id,
            'tipo': alerta.tipo,
            'ubicacion': alerta.ubicacion,
            'descripcion': alerta.descripcion,
            'estado': alerta.estado.value,
            'confianza': alerta.nivel_confianza,
            # Si tuvieras coordenadas guardadas:
            # 'lat': alerta.lat,
            # 'lon': alerta.lon
        }
        for alerta in alertas_db.values()
    ]

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

from src.unidad4_codificacion.protocolo_mensajeria import ProtocoloResiliente

# Variable global
protocolo_resiliente = ProtocoloResiliente()

class MensajeResiliente(BaseModel):
    tipo: str
    ubicacion: str
    descripcion: str
    simular_errores: int = 0

class DemoResponse(BaseModel):
    mensaje_original: dict
    bits_codificados: int
    redundancia: float
    errores_simulados: int
    errores_corregidos: int
    mensaje_recuperado: dict
    firma_valida: bool

@app.post("/demo/codificacion", response_model=DemoResponse, tags=["Demo"])
async def demo_codificacion(mensaje: MensajeResiliente):
    """
    Demuestra corrección de errores con Hamming + Firmas digitales.
    
    Esta es una demostración académica de la Unidad IV del proyecto.
    """
    import json
    import random
    
    # Enviar (codificar + firmar)
    paquete = protocolo_resiliente.enviar_alerta(
        tipo=mensaje.tipo,
        ubicacion=mensaje.ubicacion,
        descripcion=mensaje.descripcion
    )
    
    # Simular errores
    mensaje_codificado = paquete['mensaje_codificado']
    if mensaje.simular_errores > 0:
        posiciones = random.sample(range(len(mensaje_codificado)), mensaje.simular_errores)
        for pos in posiciones:
            mensaje_codificado[pos] = 1 - mensaje_codificado[pos]
    
    paquete['mensaje_codificado'] = mensaje_codificado
    
    # Recibir (decodificar + verificar)
    mensaje_decodificado = protocolo_resiliente.recibir_alerta(paquete, 0)
    
    # Calcular errores corregidos
    errores_corregidos = mensaje.simular_errores if mensaje_decodificado else 0
    
    return DemoResponse(
        mensaje_original={
            "tipo": mensaje.tipo,
            "ubicacion": mensaje.ubicacion,
            "descripcion": mensaje.descripcion
        },
        bits_codificados=len(paquete['mensaje_codificado']),
        redundancia=75.0,  # Hamming(7,4) tiene ~75% redundancia
        errores_simulados=mensaje.simular_errores,
        errores_corregidos=errores_corregidos,
        mensaje_recuperado=mensaje_decodificado or {},
        firma_valida=mensaje_decodificado is not None
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)