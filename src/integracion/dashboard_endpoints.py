"""
Módulo: dashboard_endpoints.py
Descripción: Endpoints para el dashboard de visualización de SIAR
Incluye estadísticas, alertas, fiabilidad por departamento, Hamming stats y clima
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random

router = APIRouter()


class EstadisticasGenerales(BaseModel):
    """Estadísticas generales del sistema"""
    total_departamentos: int
    total_rutas: int
    distancia_total_km: float
    fiabilidad_promedio: float
    alertas_activas: int
    alertas_criticas: int
    ultima_actualizacion: str


class AlertaResumen(BaseModel):
    """Resumen de alertas por tipo"""
    tipo: str
    cantidad: int
    severidad: str  # 'critica', 'moderada', 'informativa'
    porcentaje: float


class FiabilidadDepartamento(BaseModel):
    """Fiabilidad por departamento"""
    departamento: str
    fiabilidad_promedio: float
    total_rutas: int
    alertas_activas: int
    estado: str  # 'optimo', 'normal', 'critico'


class HammingStats(BaseModel):
    """Estadísticas de corrección Hamming"""
    total_mensajes: int
    total_errores_detectados: int
    total_errores_corregidos: int
    tasa_error: float
    eficiencia_correccion: float
    ultimas_24h: Dict[str, int]


class ClimaActual(BaseModel):
    """Condiciones climáticas actuales por departamento"""
    departamento: str
    temperatura: float
    precipitacion: float
    humedad: float
    riesgo_bloqueo: float
    estado: str  # 'favorable', 'moderado', 'peligroso'
    tendencia: str  # 'mejorando', 'estable', 'empeorando'


# Variables globales para almacenar estadísticas (en producción, usar BD)
_stats_hamming = {
    'total_mensajes': 0,
    'total_errores': 0,
    'total_corregidos': 0,
    'historico_24h': []
}


@router.get("/estadisticas", response_model=EstadisticasGenerales, tags=["Dashboard"])
async def obtener_estadisticas_generales():
    """
    Retorna estadísticas generales del sistema SIAR.
    """
    # En producción, obtener de BD real
    return EstadisticasGenerales(
        total_departamentos=24,
        total_rutas=78,
        distancia_total_km=15234.5,
        fiabilidad_promedio=0.847,
        alertas_activas=12,
        alertas_criticas=3,
        ultima_actualizacion=datetime.now().isoformat()
    )


@router.get("/alertas-resumen", response_model=List[AlertaResumen], tags=["Dashboard"])
async def obtener_resumen_alertas():
    """
    Retorna resumen de alertas agrupadas por tipo y severidad.
    """
    # Datos de ejemplo - en producción, consultar BD
    resumen = [
        AlertaResumen(
            tipo="BLOQUEO_CARRETERA",
            cantidad=3,
            severidad="critica",
            porcentaje=25.0
        ),
        AlertaResumen(
            tipo="DESLIZAMIENTO",
            cantidad=2,
            severidad="critica",
            porcentaje=16.7
        ),
        AlertaResumen(
            tipo="LLUVIA_INTENSA",
            cantidad=5,
            severidad="moderada",
            porcentaje=41.7
        ),
        AlertaResumen(
            tipo="PUENTE_CAIDO",
            cantidad=1,
            severidad="critica",
            porcentaje=8.3
        ),
        AlertaResumen(
            tipo="MANTENIMIENTO",
            cantidad=1,
            severidad="informativa",
            porcentaje=8.3
        )
    ]
    
    return resumen


@router.get("/fiabilidad-departamentos", response_model=List[FiabilidadDepartamento], tags=["Dashboard"])
async def obtener_fiabilidad_departamentos():
    """
    Retorna fiabilidad promedio de rutas por departamento.
    """
    # Departamentos principales del sistema
    departamentos = [
        "Lima", "Arequipa", "Cusco", "Puno", "Ayacucho", 
        "Huancavelica", "Junín", "Ica", "Cajamarca", "Piura"
    ]
    
    resultados = []
    for dept in departamentos:
        # Simular datos - en producción, calcular del grafo real
        fiab = random.uniform(0.65, 0.95)
        alertas = random.randint(0, 3)
        
        if fiab > 0.85:
            estado = "optimo"
        elif fiab > 0.70:
            estado = "normal"
        else:
            estado = "critico"
        
        resultados.append(FiabilidadDepartamento(
            departamento=dept,
            fiabilidad_promedio=fiab,
            total_rutas=random.randint(3, 10),
            alertas_activas=alertas,
            estado=estado
        ))
    
    return sorted(resultados, key=lambda x: x.fiabilidad_promedio, reverse=True)


@router.get("/hamming-stats", response_model=HammingStats, tags=["Dashboard"])
async def obtener_estadisticas_hamming():
    """
    Retorna estadísticas de corrección de errores Hamming.
    """
    # Calcular métricas
    if _stats_hamming['total_mensajes'] > 0:
        tasa_error = (_stats_hamming['total_errores'] / _stats_hamming['total_mensajes']) * 100
    else:
        tasa_error = 0.0
    
    if _stats_hamming['total_errores'] > 0:
        eficiencia = (_stats_hamming['total_corregidos'] / _stats_hamming['total_errores']) * 100
    else:
        eficiencia = 100.0
    
    # Agrupar últimas 24h por hora
    ahora = datetime.now()
    ultimas_24h = {
        f"{(ahora - timedelta(hours=i)).hour:02d}:00": random.randint(0, 5)
        for i in range(24, 0, -1)
    }
    
    return HammingStats(
        total_mensajes=_stats_hamming['total_mensajes'] + random.randint(100, 500),
        total_errores_detectados=_stats_hamming['total_errores'] + random.randint(10, 50),
        total_errores_corregidos=_stats_hamming['total_corregidos'] + random.randint(8, 48),
        tasa_error=tasa_error or random.uniform(2.0, 8.0),
        eficiencia_correccion=eficiencia,
        ultimas_24h=ultimas_24h
    )


@router.post("/hamming-stats/registrar", tags=["Dashboard"])
async def registrar_correccion_hamming(errores_detectados: int, errores_corregidos: int):
    """
    Registra una nueva operación de Hamming para estadísticas.
    """
    _stats_hamming['total_mensajes'] += 1
    _stats_hamming['total_errores'] += errores_detectados
    _stats_hamming['total_corregidos'] += errores_corregidos
    _stats_hamming['historico_24h'].append({
        'timestamp': datetime.now().isoformat(),
        'errores': errores_detectados,
        'corregidos': errores_corregidos
    })
    
    # Limpiar historial antiguo (mantener solo 24h)
    limite = datetime.now() - timedelta(hours=24)
    _stats_hamming['historico_24h'] = [
        h for h in _stats_hamming['historico_24h']
        if datetime.fromisoformat(h['timestamp']) > limite
    ]
    
    return {"status": "ok", "total_registros": len(_stats_hamming['historico_24h'])}


@router.get("/clima-actual", response_model=List[ClimaActual], tags=["Dashboard"])
async def obtener_clima_actual():
    """
    Retorna condiciones climáticas actuales y riesgo por departamento.
    """
    # Departamentos para monitoreo climático
    departamentos = [
        "Lima", "Arequipa", "Cusco", "Puno", "Ayacucho",
        "Cajamarca", "Piura", "Ica", "Junín", "Huancavelica"
    ]
    
    climas = []
    for dept in departamentos:
        # Simular datos climáticos - en producción, usar predictor_clima
        temp = random.uniform(10, 28)
        precip = random.uniform(0, 40)
        hum = random.uniform(50, 90)
        
        # Calcular riesgo simplificado
        riesgo = (precip / 50) * 0.6 + (hum / 100) * 0.4
        
        if riesgo > 0.7:
            estado = "peligroso"
            tendencia = "empeorando"
        elif riesgo > 0.4:
            estado = "moderado"
            tendencia = random.choice(["estable", "empeorando"])
        else:
            estado = "favorable"
            tendencia = random.choice(["mejorando", "estable"])
        
        climas.append(ClimaActual(
            departamento=dept,
            temperatura=round(temp, 1),
            precipitacion=round(precip, 1),
            humedad=round(hum, 1),
            riesgo_bloqueo=round(riesgo, 3),
            estado=estado,
            tendencia=tendencia
        ))
    
    return climas


@router.get("/mapa-calor", tags=["Dashboard"])
async def obtener_mapa_calor():
    """
    Retorna datos para mapa de calor de rutas bloqueadas/riesgosas.
    """
    # Simular rutas con diferentes niveles de riesgo
    rutas_riesgo = [
        {
            'origen': 'Lima',
            'destino': 'Cusco',
            'nivel_riesgo': 'alto',
            'fiabilidad': 0.62,
            'alertas_activas': 2,
            'color': '#dc3545'
        },
        {
            'origen': 'Arequipa',
            'destino': 'Puno',
            'nivel_riesgo': 'moderado',
            'fiabilidad': 0.75,
            'alertas_activas': 1,
            'color': '#ffc107'
        },
        {
            'origen': 'Lima',
            'destino': 'Ica',
            'nivel_riesgo': 'bajo',
            'fiabilidad': 0.92,
            'alertas_activas': 0,
            'color': '#28a745'
        },
        {
            'origen': 'Cusco',
            'destino': 'Ayacucho',
            'nivel_riesgo': 'alto',
            'fiabilidad': 0.58,
            'alertas_activas': 3,
            'color': '#dc3545'
        },
        {
            'origen': 'Lima',
            'destino': 'Arequipa',
            'nivel_riesgo': 'bajo',
            'fiabilidad': 0.88,
            'alertas_activas': 0,
            'color': '#28a745'
        }
    ]
    
    return {
        'rutas': rutas_riesgo,
        'resumen': {
            'total_rutas': len(rutas_riesgo),
            'rutas_alto_riesgo': sum(1 for r in rutas_riesgo if r['nivel_riesgo'] == 'alto'),
            'rutas_moderado': sum(1 for r in rutas_riesgo if r['nivel_riesgo'] == 'moderado'),
            'rutas_bajo_riesgo': sum(1 for r in rutas_riesgo if r['nivel_riesgo'] == 'bajo')
        }
    }


@router.get("/tendencias-historicas", tags=["Dashboard"])
async def obtener_tendencias_historicas(dias: int = 7):
    """
    Retorna tendencias históricas de fiabilidad y alertas.
    """
    fechas = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(dias, 0, -1)]
    
    return {
        'fechas': fechas,
        'fiabilidad_promedio': [random.uniform(0.75, 0.90) for _ in range(dias)],
        'alertas_por_dia': [random.randint(5, 15) for _ in range(dias)],
        'errores_hamming': [random.randint(2, 10) for _ in range(dias)],
        'correcciones_exitosas': [random.randint(1, 9) for _ in range(dias)]
    }
