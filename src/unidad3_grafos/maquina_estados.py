"""
Módulo: maquina_estados.py
Descripción: Implementación de máquinas de estado finitas (FSM) para gestionar
el ciclo de vida de alertas y logística.

Fundamento Matemático:
- Autómata Finito Determinista (DFA): M = (Q, Σ, δ, q0, F)
  * Q: Conjunto de estados
  * Σ: Alfabeto de entrada (eventos)
  * δ: Función de transición
  * q0: Estado inicial
  * F: Estados finales/aceptación
"""

from enum import Enum
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime





# ========== MÁQUINA DE ESTADOS PARA ALERTAS ==========

class EstadoAlerta(Enum):
    """Estados posibles de una alerta en el sistema."""
    EMITIDA = "emitida"                    # Alerta recién creada
    EN_VERIFICACION = "en_verificacion"    # Esperando confirmación de otros usuarios
    CONFIRMADA = "confirmada"              # Alerta verificada por múltiples fuentes
    EN_ATENCION = "en_atencion"           # Autoridades/cooperativa respondiendo
    RESUELTA = "resuelta"                  # Problema solucionado
    FALSA_ALARMA = "falsa_alarma"         # Alerta descartada
    EXPIRADA = "expirada"                  # Alerta sin confirmar en tiempo límite


class EventoAlerta(Enum):
    """Eventos que pueden ocurrir en el ciclo de vida de una alerta."""
    SOLICITAR_VERIFICACION = "solicitar_verificacion"
    CONFIRMAR = "confirmar"
    RECHAZAR = "rechazar"
    ATENDER = "atender"
    RESOLVER = "resolver"
    EXPIRAR = "expirar"


@dataclass
class Alerta:
    """
    Representa una alerta en el sistema.
    """
    id: str
    tipo: str  # "bloqueo_carretera", "lluvia_intensa", "emergencia_medica", etc.
    ubicacion: str
    descripcion: str
    emisor: str
    timestamp_creacion: datetime
    estado: EstadoAlerta = EstadoAlerta.EMITIDA
    confirmaciones: List[str] = field(default_factory=list)  # IDs de usuarios que confirmaron
    nivel_confianza: float = 0.3  # Inicial: 30%
    
    def __repr__(self):
        return (f"Alerta #{self.id} [{self.tipo}]\n"
                f"  Estado: {self.estado.value}\n"
                f"  Ubicación: {self.ubicacion}\n"
                f"  Confianza: {self.nivel_confianza:.0%}")


class MaquinaEstadosAlerta:
    """
    FSM para gestionar el flujo de estados de una alerta.
    
    Diagrama de transiciones:
    
    EMITIDA → EN_VERIFICACION → CONFIRMADA → EN_ATENCION → RESUELTA
       ↓              ↓              ↓
    EXPIRADA    FALSA_ALARMA   FALSA_ALARMA
    """
    
    def __init__(self):
        # Definir transiciones válidas: {estado_actual: {evento: estado_siguiente}}
        self.transiciones: Dict[EstadoAlerta, Dict[EventoAlerta, EstadoAlerta]] = {
            EstadoAlerta.EMITIDA: {
                EventoAlerta.SOLICITAR_VERIFICACION: EstadoAlerta.EN_VERIFICACION,
                EventoAlerta.EXPIRAR: EstadoAlerta.EXPIRADA
            },
            EstadoAlerta.EN_VERIFICACION: {
                EventoAlerta.CONFIRMAR: EstadoAlerta.CONFIRMADA,
                EventoAlerta.RECHAZAR: EstadoAlerta.FALSA_ALARMA,
                EventoAlerta.EXPIRAR: EstadoAlerta.EXPIRADA
            },
            EstadoAlerta.CONFIRMADA: {
                EventoAlerta.ATENDER: EstadoAlerta.EN_ATENCION,
                EventoAlerta.RECHAZAR: EstadoAlerta.FALSA_ALARMA
            },
            EstadoAlerta.EN_ATENCION: {
                EventoAlerta.RESOLVER: EstadoAlerta.RESUELTA
            },
            # Estados finales no tienen transiciones
            EstadoAlerta.RESUELTA: {},
            EstadoAlerta.FALSA_ALARMA: {},
            EstadoAlerta.EXPIRADA: {}
        }
        
        # Callbacks opcionales para ejecutar al entrar en un estado
        self.callbacks: Dict[EstadoAlerta, List[Callable]] = {}
    
    def procesar_evento(self, alerta: Alerta, evento: EventoAlerta, 
                       usuario_id: Optional[str] = None) -> bool:
        """
        Procesa un evento para cambiar el estado de una alerta.
        
        Args:
            alerta: La alerta a modificar
            evento: El evento que ocurrió
            usuario_id: ID del usuario que generó el evento (para confirmaciones)
            
        Returns:
            True si la transición fue exitosa, False si no es válida
        """
        estado_actual = alerta.estado
        
        # Verificar si la transición es válida
        if evento not in self.transiciones.get(estado_actual, {}):
            print(f"⚠️  Transición inválida: {estado_actual.value} -[{evento.value}]-> ?")
            return False
        
        # Ejecutar transición
        nuevo_estado = self.transiciones[estado_actual][evento]
        alerta.estado = nuevo_estado
        
        # Lógica adicional según el evento
        if evento == EventoAlerta.CONFIRMAR and usuario_id:
            if usuario_id not in alerta.confirmaciones:
                alerta.confirmaciones.append(usuario_id)
                # Actualizar nivel de confianza usando Teorema de Bayes (simplificado)
                alerta.nivel_confianza = self._calcular_confianza(alerta)
        
        # Ejecutar callbacks registrados
        if nuevo_estado in self.callbacks:
            for callback in self.callbacks[nuevo_estado]:
                callback(alerta)
        
        print(f"✅ Transición exitosa: {estado_actual.value} → {nuevo_estado.value}")
        return True
    
    def _calcular_confianza(self, alerta: Alerta) -> float:
        """
        Calcula el nivel de confianza basado en confirmaciones.
        
        Aplicación de Teorema de Bayes (simplificado):
        P(alerta_real | n_confirmaciones) aumenta con cada confirmación
        
        Fórmula simplificada: confianza = 1 - (1 - p_inicial)^n
        donde n es el número de confirmaciones
        """
        p_inicial = 0.3  # Prior: 30% de confianza inicial
        n_confirmaciones = len(alerta.confirmaciones)
        
        # Cada confirmación reduce la probabilidad de ser falsa
        confianza = 1 - ((1 - p_inicial) ** (n_confirmaciones + 1))
        return min(confianza, 0.99)  # Cap en 99%
    
    def registrar_callback(self, estado: EstadoAlerta, callback: Callable):
        """Registra una función a ejecutar al entrar en un estado."""
        if estado not in self.callbacks:
            self.callbacks[estado] = []
        self.callbacks[estado].append(callback)
    
    def obtener_estados_posibles(self, estado_actual: EstadoAlerta) -> List[EstadoAlerta]:
        """Retorna los estados alcanzables desde el estado actual."""
        return list(self.transiciones.get(estado_actual, {}).values())


# ========== MÁQUINA DE ESTADOS PARA LOGÍSTICA ==========

class EstadoLote(Enum):
    """Estados de un lote de cosecha en el sistema logístico."""
    REGISTRADO = "registrado"
    EN_ALMACEN = "en_almacen"
    LISTO_ENVIO = "listo_envio"
    EN_TRANSITO = "en_transito"
    ENTREGADO = "entregado"
    RECHAZADO = "rechazado"  # Calidad no aceptada


class EventoLote(Enum):
    """Eventos del ciclo logístico."""
    ALMACENAR = "almacenar"
    PREPARAR_ENVIO = "preparar_envio"
    INICIAR_TRANSPORTE = "iniciar_transporte"
    CONFIRMAR_ENTREGA = "confirmar_entrega"
    RECHAZAR_CALIDAD = "rechazar_calidad"


@dataclass
class LoteCosecha:
    """Representa un lote de productos de la cooperativa."""
    id: str
    producto: str  # "papa", "quinua", "café"
    cantidad_kg: float
    agricultor_id: str
    estado: EstadoLote = EstadoLote.REGISTRADO
    ruta_asignada: Optional[List[str]] = None
    timestamp_registro: datetime = field(default_factory=datetime.now)


class MaquinaEstadosLogistica:
    """FSM para gestionar el flujo logístico de productos."""
    
    def __init__(self):
        self.transiciones: Dict[EstadoLote, Dict[EventoLote, EstadoLote]] = {
            EstadoLote.REGISTRADO: {
                EventoLote.ALMACENAR: EstadoLote.EN_ALMACEN,
                EventoLote.RECHAZAR_CALIDAD: EstadoLote.RECHAZADO
            },
            EstadoLote.EN_ALMACEN: {
                EventoLote.PREPARAR_ENVIO: EstadoLote.LISTO_ENVIO
            },
            EstadoLote.LISTO_ENVIO: {
                EventoLote.INICIAR_TRANSPORTE: EstadoLote.EN_TRANSITO
            },
            EstadoLote.EN_TRANSITO: {
                EventoLote.CONFIRMAR_ENTREGA: EstadoLote.ENTREGADO
            },
            EstadoLote.ENTREGADO: {},
            EstadoLote.RECHAZADO: {}
        }
    
    def procesar_evento(self, lote: LoteCosecha, evento: EventoLote) -> bool:
        """Procesa un evento del ciclo logístico."""
        estado_actual = lote.estado
        
        if evento not in self.transiciones.get(estado_actual, {}):
            return False
        
        nuevo_estado = self.transiciones[estado_actual][evento]
        lote.estado = nuevo_estado
        
        print(f"📦 Lote #{lote.id}: {estado_actual.value} → {nuevo_estado.value}")
        return True


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    print("="*60)
    print("🚨 SIMULACIÓN: MÁQUINA DE ESTADOS DE ALERTA\n")
    
    # Crear alerta
    alerta = Alerta(
        id="ALR-001",
        tipo="bloqueo_carretera",
        ubicacion="Ruta Huanta-Sivia Km 32",
        descripcion="Deslizamiento de tierra por lluvia",
        emisor="USER-123",
        timestamp_creacion=datetime.now()
    )
    
    print(f"🆕 Alerta creada:\n{alerta}\n")
    
    # Crear máquina de estados
    fsm_alerta = MaquinaEstadosAlerta()
    
    # Registrar callback
    def notificar_confirmacion(alerta):
        print(f"   📧 Notificación enviada a autoridades sobre {alerta.id}")
    
    fsm_alerta.registrar_callback(EstadoAlerta.CONFIRMADA, notificar_confirmacion)
    
    # Simular flujo de eventos
    print("📍 Flujo de eventos:\n")
    
    fsm_alerta.procesar_evento(alerta, EventoAlerta.SOLICITAR_VERIFICACION)
    print(f"{alerta}\n")
    
    fsm_alerta.procesar_evento(alerta, EventoAlerta.CONFIRMAR, usuario_id="USER-456")
    print(f"{alerta}\n")
    
    fsm_alerta.procesar_evento(alerta, EventoAlerta.CONFIRMAR, usuario_id="USER-789")
    print(f"{alerta}\n")
    
    fsm_alerta.procesar_evento(alerta, EventoAlerta.ATENDER)
    print(f"{alerta}\n")
    
    fsm_alerta.procesar_evento(alerta, EventoAlerta.RESOLVER)
    print(f"{alerta}\n")
    
    # Intentar transición inválida
    print("❌ Intentando transición inválida:")
    fsm_alerta.procesar_evento(alerta, EventoAlerta.CONFIRMAR)
    
    print("\n" + "="*60)
    print("📦 SIMULACIÓN: MÁQUINA DE ESTADOS LOGÍSTICA\n")
    
    lote = LoteCosecha(
        id="LOT-001",
        producto="quinua",
        cantidad_kg=500,
        agricultor_id="AGR-042"
    )
    
    fsm_logistica = MaquinaEstadosLogistica()
    
    print(f"Lote inicial: {lote.estado.value}\n")
    
    fsm_logistica.procesar_evento(lote, EventoLote.ALMACENAR)
    fsm_logistica.procesar_evento(lote, EventoLote.PREPARAR_ENVIO)
    fsm_logistica.procesar_evento(lote, EventoLote.INICIAR_TRANSPORTE)
    fsm_logistica.procesar_evento(lote, EventoLote.CONFIRMAR_ENTREGA)
    
    print(f"\n✅ Lote final: {lote.estado.value}")