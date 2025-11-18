"""
Módulo: api_siar.py
Descripción: API REST con FastAPI para el Sistema SIAR.
Expone endpoints para gestión de rutas, alertas y logística.

Ejecutar: uvicorn src.integracion.api_siar:app --reload
Acceder: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from pydantic import BaseModel # type: ignore
from typing import List, Optional, Dict
from datetime import datetime
import sys
import os

# Agregar src al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.unidad3_grafos.grafo_rutas import GrafoRutas, TipoCamino
from src.unidad3_grafos.algoritmo_fiabilidad import AlgoritmoFiabilidad, Ruta
from src.unidad3_grafos.maquina_estados import (
    MaquinaEstadosAlerta,
    MaquinaEstadosLogistica,
    Alerta,
    LoteCosecha,
    EstadoAlerta,
    EstadoLote,
    EventoAlerta,
    EventoLote
)


# ========== MODELOS PYDANTIC ==========

class NodoInfo(BaseModel):
    nombre: str
    tipo: Optional[str] = None
    poblacion: Optional[int] = None
    altitud: Optional[int] = None


class RutaResponse(BaseModel):
    nodos: List[str]
    distancia_km: float
    fiabilidad: float
    tiempo_min: int
    peso: float


class ComparacionRutasResponse(BaseModel):
    mas_fiable: RutaResponse
    mas_corta: RutaResponse
    mas_rapida: RutaResponse


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


class LoteCreate(BaseModel):
    producto: str
    cantidad_kg: float
    agricultor_id: str


class LoteResponse(BaseModel):
    id: str
    producto: str
    cantidad_kg: float
    agricultor_id: str
    estado: str
    timestamp: str


class EventoLoteRequest(BaseModel):
    evento: str  # "almacenar", "preparar_envio", "iniciar_transporte", "confirmar_entrega"


# ========== INICIALIZACIÓN ==========

app = FastAPI(
    title="SIAR API",
    description="Sistema de Información y Alerta Resiliente para Cooperativas Agrícolas",
    version="1.0.0"
)

# Configurar CORS para permitir peticiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar grafo
GRAFO_PATH = "data/grafos/red_ayacucho.json"
grafo = None
algoritmo = None

# Almacenamiento en memoria (en producción usarías base de datos)
alertas_db: Dict[str, Alerta] = {}
lotes_db: Dict[str, LoteCosecha] = {}
contador_alertas = 0
contador_lotes = 0

# Máquinas de estado
fsm_alertas = MaquinaEstadosAlerta()
fsm_logistica = MaquinaEstadosLogistica()


@app.on_event("startup")
async def startup_event():
    """Cargar datos al iniciar el servidor."""
    global grafo, algoritmo
    
    try:
        if os.path.exists(GRAFO_PATH):
            grafo = GrafoRutas.cargar_json(GRAFO_PATH)
            algoritmo = AlgoritmoFiabilidad(grafo)
            print(f"✅ Grafo cargado: {len(grafo.nodos)} nodos")
        else:
            print(f"⚠️  Archivo {GRAFO_PATH} no encontrado, creando grafo de ejemplo...")
            grafo = crear_grafo_ejemplo()
            algoritmo = AlgoritmoFiabilidad(grafo)
    except Exception as e:
        print(f"❌ Error cargando grafo: {e}")


def crear_grafo_ejemplo() -> GrafoRutas:
    """Crea un grafo de ejemplo si no existe el archivo."""
    grafo = GrafoRutas()
    grafo.agregar_camino("Ayacucho", "Huanta", 47, 0.95, TipoCamino.ASFALTADO, 0.1)
    grafo.agregar_camino("Huanta", "Sivia", 85, 0.70, TipoCamino.AFIRMADO, 0.4)
    grafo.agregar_camino("Ayacucho", "San Miguel", 135, 0.85, TipoCamino.AFIRMADO, 0.2)
    return grafo


def ruta_to_response(ruta: Ruta) -> RutaResponse:
    """Convierte objeto Ruta a RutaResponse."""
    return RutaResponse(
        nodos=ruta.nodos,
        distancia_km=ruta.distancia_total_km,
        fiabilidad=ruta.fiabilidad_acumulada,
        tiempo_min=ruta.tiempo_total_min,
        peso=ruta.peso_total
    )


# ========== ENDPOINTS: RUTAS ==========

@app.get("/", tags=["General"])
async def root():
    """Endpoint raíz."""
    return {
        "mensaje": "Bienvenido a SIAR API",
        "version": "1.0.0",
        "documentacion": "/docs"
    }


@app.get("/grafos/nodos", response_model=List[str], tags=["Grafos"])
async def obtener_nodos():
    """Lista todos los nodos (localidades) disponibles."""
    if grafo is None:
        raise HTTPException(status_code=503, detail="Grafo no disponible")
    return sorted(list(grafo.nodos))


@app.get("/grafos/info", tags=["Grafos"])
async def info_grafo():
    """Obtiene estadísticas de la red."""
    if grafo is None:
        raise HTTPException(status_code=503, detail="Grafo no disponible")
    
    num_aristas = sum(len(v) for v in grafo.adyacencias.values()) // 2
    
    # Calcular fiabilidad promedio
    fiabilidad_total = 0
    count = 0
    aristas_vistas = set()
    
    for origen, aristas in grafo.adyacencias.items():
        for arista in aristas:
            par = tuple(sorted([arista.origen, arista.destino]))
            if par not in aristas_vistas:
                fiabilidad_total += arista.fiabilidad
                count += 1
                aristas_vistas.add(par)
    
    fiabilidad_promedio = fiabilidad_total / count if count > 0 else 0
    
    return {
        "nodos": len(grafo.nodos),
        "aristas": num_aristas,
        "fiabilidad_promedio": round(fiabilidad_promedio, 2),
        "localidades": sorted(list(grafo.nodos))
    }


@app.get("/rutas/calcular", response_model=RutaResponse, tags=["Rutas"])
async def calcular_ruta(origen: str, destino: str):
    """
    Calcula la ruta más fiable entre dos puntos.
    
    - **origen**: Nodo de inicio
    - **destino**: Nodo de llegada
    """
    if algoritmo is None:
        raise HTTPException(status_code=503, detail="Algoritmo no disponible")
    
    if origen not in grafo.nodos:
        raise HTTPException(status_code=404, detail=f"Nodo '{origen}' no encontrado")
    if destino not in grafo.nodos:
        raise HTTPException(status_code=404, detail=f"Nodo '{destino}' no encontrado")
    
    try:
        ruta = algoritmo.encontrar_ruta_mas_fiable(origen, destino)
        if ruta is None:
            raise HTTPException(status_code=404, detail="No existe ruta entre los nodos")
        return ruta_to_response(ruta)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rutas/comparar", response_model=ComparacionRutasResponse, tags=["Rutas"])
async def comparar_rutas(origen: str, destino: str):
    """
    Compara diferentes criterios de optimización de rutas.
    
    - **origen**: Nodo de inicio
    - **destino**: Nodo de llegada
    """
    if algoritmo is None:
        raise HTTPException(status_code=503, detail="Algoritmo no disponible")
    
    try:
        comparacion = algoritmo.comparar_rutas(origen, destino)
        return ComparacionRutasResponse(
            mas_fiable=ruta_to_response(comparacion['mas_fiable']),
            mas_corta=ruta_to_response(comparacion['mas_corta']),
            mas_rapida=ruta_to_response(comparacion['mas_rapida'])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== ENDPOINTS: ALERTAS ==========

@app.post("/alertas/crear", response_model=AlertaResponse, tags=["Alertas"])
async def crear_alerta(alerta_data: AlertaCreate):
    """Crea una nueva alerta en el sistema."""
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
    
    # Si la alerta menciona una ruta, reducir su fiabilidad
    if "bloqueo" in alerta.tipo.lower() and grafo:
        # Lógica simple: buscar nodos mencionados
        for nodo in grafo.nodos:
            if nodo.lower() in alerta.ubicacion.lower():
                for vecino in grafo.obtener_vecinos(nodo):
                    if vecino.destino.lower() in alerta.ubicacion.lower():
                        grafo.actualizar_fiabilidad(nodo, vecino.destino, 0.3)
    
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
    """Lista todas las alertas activas (no resueltas)."""
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


@app.post("/alertas/{alerta_id}/confirmar", tags=["Alertas"])
async def confirmar_alerta(alerta_id: str, usuario_id: str):
    """Confirma una alerta (aumenta su nivel de confianza)."""
    if alerta_id not in alertas_db:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    alerta = alertas_db[alerta_id]
    
    if alerta.estado == EstadoAlerta.EMITIDA:
        fsm_alertas.procesar_evento(alerta, EventoAlerta.SOLICITAR_VERIFICACION)
    
    if usuario_id not in alerta.confirmaciones:
        alerta.confirmaciones.append(usuario_id)
        alerta.nivel_confianza = fsm_alertas._calcular_confianza(alerta)
    
    return {"mensaje": "Alerta confirmada", "confianza": alerta.nivel_confianza}


@app.post("/alertas/{alerta_id}/resolver", tags=["Alertas"])
async def resolver_alerta(alerta_id: str):
    """Marca una alerta como resuelta."""
    if alerta_id not in alertas_db:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    alerta = alertas_db[alerta_id]
    
    # Avanzar por los estados necesarios
    if alerta.estado == EstadoAlerta.EMITIDA:
        fsm_alertas.procesar_evento(alerta, EventoAlerta.SOLICITAR_VERIFICACION)
    if alerta.estado == EstadoAlerta.EN_VERIFICACION:
        fsm_alertas.procesar_evento(alerta, EventoAlerta.CONFIRMAR)
    if alerta.estado == EstadoAlerta.CONFIRMADA:
        fsm_alertas.procesar_evento(alerta, EventoAlerta.ATENDER)
    if alerta.estado == EstadoAlerta.EN_ATENCION:
        fsm_alertas.procesar_evento(alerta, EventoAlerta.RESOLVER)
    
    return {"mensaje": "Alerta resuelta", "estado": alerta.estado.value}


# ========== ENDPOINTS: LOGÍSTICA ==========

@app.post("/lotes/crear", response_model=LoteResponse, tags=["Logística"])
async def crear_lote(lote_data: LoteCreate):
    """Registra un nuevo lote de cosecha."""
    global contador_lotes
    contador_lotes += 1
    
    lote = LoteCosecha(
        id=f"LOT-{contador_lotes:04d}",
        producto=lote_data.producto,
        cantidad_kg=lote_data.cantidad_kg,
        agricultor_id=lote_data.agricultor_id
    )
    
    lotes_db[lote.id] = lote
    
    return LoteResponse(
        id=lote.id,
        producto=lote.producto,
        cantidad_kg=lote.cantidad_kg,
        agricultor_id=lote.agricultor_id,
        estado=lote.estado.value,
        timestamp=lote.timestamp_registro.isoformat()
    )


@app.get("/lotes/{lote_id}", response_model=LoteResponse, tags=["Logística"])
async def obtener_lote(lote_id: str):
    """Obtiene información de un lote específico."""
    if lote_id not in lotes_db:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    
    lote = lotes_db[lote_id]
    return LoteResponse(
        id=lote.id,
        producto=lote.producto,
        cantidad_kg=lote.cantidad_kg,
        agricultor_id=lote.agricultor_id,
        estado=lote.estado.value,
        timestamp=lote.timestamp_registro.isoformat()
    )


@app.post("/lotes/{lote_id}/avanzar", tags=["Logística"])
async def avanzar_lote(lote_id: str, evento_data: EventoLoteRequest):
    """Avanza el lote al siguiente estado en el flujo logístico."""
    if lote_id not in lotes_db:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    
    lote = lotes_db[lote_id]
    
    # Mapear string a EventoLote
    eventos = {
        "almacenar": EventoLote.ALMACENAR,
        "preparar_envio": EventoLote.PREPARAR_ENVIO,
        "iniciar_transporte": EventoLote.INICIAR_TRANSPORTE,
        "confirmar_entrega": EventoLote.CONFIRMAR_ENTREGA
    }
    
    if evento_data.evento not in eventos:
        raise HTTPException(status_code=400, detail="Evento inválido")
    
    evento = eventos[evento_data.evento]
    exito = fsm_logistica.procesar_evento(lote, evento)
    
    if not exito:
        raise HTTPException(status_code=400, detail="Transición inválida")
    
    return {"mensaje": "Lote actualizado", "nuevo_estado": lote.estado.value}


# ========== ENDPOINT DE PRUEBA ==========

@app.get("/test", tags=["Test"])
async def test_endpoint():
    """Endpoint de prueba para verificar que la API funciona."""
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "grafos_cargados": grafo is not None,
        "alertas_activas": len([a for a in alertas_db.values() if a.estado != EstadoAlerta.RESUELTA]),
        "lotes_registrados": len(lotes_db)
    }


if __name__ == "__main__":
    import uvicorn # type: ignore
    uvicorn.run(app, host="0.0.0.0", port=8000)