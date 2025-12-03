"""
Máquina de Estados Finitos (FSM) para Gestión de Alertas
Sistema SIAR - Universidad
Ejecución: python src.integracion.maquina_estados.py
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel
import uuid


class EstadoAlerta(str, Enum):
    """Estados posibles de una alerta"""
    NORMAL = "NORMAL"
    ALERTA = "ALERTA"
    CRITICO = "CRÍTICO"
    RESUELTO = "RESUELTO"


class TipoAlerta(str, Enum):
    """Tipos de alertas"""
    CLIMA = "CLIMA"
    TRAFICO = "TRAFICO"
    CARRETERA = "CARRETERA"


class TransicionHistorial(BaseModel):
    """Registro de una transición de estado"""
    timestamp: str
    estado_anterior: Optional[str]
    estado_nuevo: str
    evento: str
    razon: str


class Coordenadas(BaseModel):
    """Coordenadas geográficas"""
    lat: float
    lon: float


class MetadataAlerta(BaseModel):
    """Metadata adicional de la alerta"""
    precipitacion: float = 0.0  # mm
    temperatura: float = 20.0   # °C
    viento: float = 0.0         # km/h


class Alerta(BaseModel):
    """Modelo de una alerta"""
    id: str
    departamento: str
    coordenadas: Coordenadas
    tipo: TipoAlerta
    descripcion: str
    estado_actual: EstadoAlerta
    fiabilidad: float  # 0-1
    severidad: float   # 0-1
    creado_en: str
    actualizado_en: str
    historial: List[TransicionHistorial]
    mensaje_hamming: Optional[str] = None
    metadata: MetadataAlerta


class MaquinaEstadosAlerta:
    """
    Máquina de Estados Finitos para gestión de alertas.
    
    Estados: NORMAL → ALERTA → CRÍTICO → RESUELTO
    """
    
    # Transiciones válidas: estado_actual -> [estados_permitidos]
    TRANSICIONES_VALIDAS = {
        EstadoAlerta.NORMAL: [EstadoAlerta.ALERTA, EstadoAlerta.CRITICO],
        EstadoAlerta.ALERTA: [EstadoAlerta.NORMAL, EstadoAlerta.CRITICO, EstadoAlerta.RESUELTO],
        EstadoAlerta.CRITICO: [EstadoAlerta.ALERTA, EstadoAlerta.RESUELTO],
        EstadoAlerta.RESUELTO: []  # Estado final
    }
    
    def __init__(self):
        """Inicializa la FSM con almacenamiento en memoria"""
        self.alertas: Dict[str, Alerta] = {}
    
    def generar_id_alerta(self) -> str:
        """Genera un ID único para la alerta"""
        return f"ALT-{uuid.uuid4().hex[:8].upper()}"
    
    def crear_alerta(
        self,
        departamento: str,
        coordenadas: Dict[str, float],
        tipo: str,
        descripcion: str,
        fiabilidad: float,
        metadata: Dict[str, float]
    ) -> Alerta:
        """
        Crea una nueva alerta y determina su estado inicial.
        
        Args:
            departamento: Nombre del departamento
            coordenadas: {"lat": -12.0, "lon": -77.0}
            tipo: CLIMA, TRAFICO o CARRETERA
            descripcion: Descripción de la alerta
            fiabilidad: Nivel de fiabilidad 0-1
            metadata: Datos adicionales (precipitación, temperatura, etc.)
        
        Returns:
            Alerta creada
        """
        alerta_id = self.generar_id_alerta()
        timestamp = datetime.now().isoformat()
        
        # Determinar estado inicial basado en condiciones
        estado_inicial = self._determinar_estado_inicial(fiabilidad, metadata)
        
        # Calcular severidad
        severidad = self._calcular_severidad(fiabilidad, metadata)
        
        # Crear alerta
        alerta = Alerta(
            id=alerta_id,
            departamento=departamento,
            coordenadas=Coordenadas(**coordenadas),
            tipo=TipoAlerta(tipo),
            descripcion=descripcion,
            estado_actual=estado_inicial,
            fiabilidad=fiabilidad,
            severidad=severidad,
            creado_en=timestamp,
            actualizado_en=timestamp,
            historial=[
                TransicionHistorial(
                    timestamp=timestamp,
                    estado_anterior=None,
                    estado_nuevo=estado_inicial.value,
                    evento="crear_alerta",
                    razon=f"Alerta creada en estado {estado_inicial.value}"
                )
            ],
            metadata=MetadataAlerta(**metadata)
        )
        
        # Guardar en memoria
        self.alertas[alerta_id] = alerta
        
        return alerta
    
    def _determinar_estado_inicial(self, fiabilidad: float, metadata: Dict) -> EstadoAlerta:
        """Determina el estado inicial basado en las condiciones"""
        precipitacion = metadata.get('precipitacion', 0)
        
        if fiabilidad < 0.4 or precipitacion > 100:
            return EstadoAlerta.CRITICO
        elif fiabilidad < 0.7 or precipitacion > 50:
            return EstadoAlerta.ALERTA
        else:
            return EstadoAlerta.NORMAL
    
    def _calcular_severidad(self, fiabilidad: float, metadata: Dict) -> float:
        """Calcula la severidad de la alerta (0-1)"""
        precipitacion = metadata.get('precipitacion', 0)
        temperatura = metadata.get('temperatura', 20)
        viento = metadata.get('viento', 0)
        
        # Componentes de severidad
        severidad_fiabilidad = 1 - fiabilidad  # Invertir: menos fiabilidad = más severidad
        severidad_precipitacion = min(precipitacion / 150, 1.0)  # Normalizar a 0-1
        severidad_temperatura = 0.0
        
        # Temperaturas extremas
        if temperatura < 5 or temperatura > 35:
            severidad_temperatura = 0.5
        
        severidad_viento = min(viento / 80, 1.0)  # Vientos sobre 80 km/h son críticos
        
        # Promedio ponderado
        severidad = (
            severidad_fiabilidad * 0.4 +
            severidad_precipitacion * 0.3 +
            severidad_temperatura * 0.15 +
            severidad_viento * 0.15
        )
        
        return round(severidad, 2)
    
    def validar_transicion(self, estado_actual: EstadoAlerta, estado_nuevo: EstadoAlerta) -> bool:
        """
        Valida si una transición es permitida.
        
        Args:
            estado_actual: Estado actual de la alerta
            estado_nuevo: Estado al que se quiere transicionar
        
        Returns:
            True si la transición es válida
        """
        return estado_nuevo in self.TRANSICIONES_VALIDAS.get(estado_actual, [])
    
    def transicion(
        self,
        alerta_id: str,
        estado_nuevo: EstadoAlerta,
        evento: str,
        razon: str
    ) -> Tuple[bool, str, Optional[Alerta]]:
        """
        Ejecuta una transición de estado.
        
        Args:
            alerta_id: ID de la alerta
            estado_nuevo: Nuevo estado deseado
            evento: Nombre del evento que causa la transición
            razon: Razón de la transición
        
        Returns:
            (éxito, mensaje, alerta_actualizada)
        """
        # Verificar que la alerta existe
        if alerta_id not in self.alertas:
            return False, f"Alerta {alerta_id} no encontrada", None
        
        alerta = self.alertas[alerta_id]
        estado_actual = alerta.estado_actual
        
        # Validar transición
        if not self.validar_transicion(estado_actual, estado_nuevo):
            return False, f"Transición no permitida de {estado_actual.value} a {estado_nuevo.value}", None
        
        # Ejecutar transición
        timestamp = datetime.now().isoformat()
        
        # Agregar al historial
        transicion_registro = TransicionHistorial(
            timestamp=timestamp,
            estado_anterior=estado_actual.value,
            estado_nuevo=estado_nuevo.value,
            evento=evento,
            razon=razon
        )
        
        alerta.historial.append(transicion_registro)
        alerta.estado_actual = estado_nuevo
        alerta.actualizado_en = timestamp
        
        return True, f"Transición exitosa: {estado_actual.value} → {estado_nuevo.value}", alerta
    
    def evaluar_transicion_automatica(self, alerta: Alerta) -> Optional[EstadoAlerta]:
        """
        Evalúa si una alerta debe cambiar de estado automáticamente.
        
        Args:
            alerta: Alerta a evaluar
        
        Returns:
            Nuevo estado si debe cambiar, None si no
        """
        fiabilidad = alerta.fiabilidad
        precipitacion = alerta.metadata.precipitacion
        estado_actual = alerta.estado_actual
        
        # No evaluar alertas resueltas
        if estado_actual == EstadoAlerta.RESUELTO:
            return None
        
        # Desde NORMAL
        if estado_actual == EstadoAlerta.NORMAL:
            if fiabilidad < 0.4 or precipitacion > 100:
                return EstadoAlerta.CRITICO
            elif fiabilidad < 0.7 or precipitacion > 50:
                return EstadoAlerta.ALERTA
        
        # Desde ALERTA
        elif estado_actual == EstadoAlerta.ALERTA:
            if fiabilidad < 0.5 or precipitacion > 100:
                return EstadoAlerta.CRITICO
            elif fiabilidad > 0.7 and precipitacion < 30:
                return EstadoAlerta.NORMAL
        
        # Desde CRÍTICO
        elif estado_actual == EstadoAlerta.CRITICO:
            if fiabilidad > 0.5 and precipitacion < 80:
                return EstadoAlerta.ALERTA
        
        return None
    
    def evaluar_todas_las_alertas(self) -> List[Dict]:
        """
        Evalúa todas las alertas activas y ejecuta transiciones automáticas.
        
        Returns:
            Lista de transiciones ejecutadas
        """
        transiciones_ejecutadas = []
        
        for alerta_id, alerta in self.alertas.items():
            # No evaluar alertas resueltas
            if alerta.estado_actual == EstadoAlerta.RESUELTO:
                continue
            
            estado_nuevo = self.evaluar_transicion_automatica(alerta)
            
            if estado_nuevo:
                exito, mensaje, alerta_actualizada = self.transicion(
                    alerta_id,
                    estado_nuevo,
                    evento="evaluacion_automatica",
                    razon=f"Cambio automático: fiabilidad={alerta.fiabilidad}, precipitación={alerta.metadata.precipitacion}mm"
                )
                
                if exito:
                    transiciones_ejecutadas.append({
                        "id": alerta_id,
                        "de": alerta.estado_actual.value,
                        "a": estado_nuevo.value,
                        "razon": mensaje
                    })
        
        return transiciones_ejecutadas
    
    def obtener_alerta(self, alerta_id: str) -> Optional[Alerta]:
        """Obtiene una alerta por ID"""
        return self.alertas.get(alerta_id)
    
    def listar_alertas(
        self,
        estado: Optional[str] = None,
        departamento: Optional[str] = None
    ) -> List[Alerta]:
        """
        Lista alertas con filtros opcionales.
        
        Args:
            estado: Filtrar por estado (NORMAL, ALERTA, CRÍTICO, RESUELTO)
            departamento: Filtrar por departamento
        
        Returns:
            Lista de alertas filtradas
        """
        alertas = list(self.alertas.values())
        
        if estado:
            alertas = [a for a in alertas if a.estado_actual.value == estado]
        
        if departamento:
            alertas = [a for a in alertas if a.departamento == departamento]
        
        return alertas
    
    def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas de las alertas"""
        total = len(self.alertas)
        
        por_estado = {
            "NORMAL": 0,
            "ALERTA": 0,
            "CRÍTICO": 0,
            "RESUELTO": 0
        }
        
        por_tipo = {
            "CLIMA": 0,
            "TRAFICO": 0,
            "CARRETERA": 0
        }
        
        severidad_promedio = 0.0
        
        for alerta in self.alertas.values():
            por_estado[alerta.estado_actual.value] += 1
            por_tipo[alerta.tipo.value] += 1
            severidad_promedio += alerta.severidad
        
        if total > 0:
            severidad_promedio /= total
        
        return {
            "total": total,
            "por_estado": por_estado,
            "por_tipo": por_tipo,
            "severidad_promedio": round(severidad_promedio, 2)
        }


# Instancia global de la FSM
fsm_alertas = MaquinaEstadosAlerta()