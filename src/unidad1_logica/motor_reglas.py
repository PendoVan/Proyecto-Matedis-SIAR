"""
Módulo: motor_reglas.py
Descripción: Motor de reglas basado en lógica proposicional para decisiones automáticas.

Fundamento Matemático:
- Lógica proposicional: p ∧ q → r
- Tablas de verdad
- Modus ponens

Aplicación SIAR:
SI (lluvia_intensa ∧ camino_trocha) ENTONCES recomendar_ruta_alternativa
SI (alerta_confirmada ∧ ruta_afectada) ENTONCES actualizar_grafo
"""

from typing import List, Dict, Callable, Any
from dataclasses import dataclass
from enum import Enum


class OperadorLogico(Enum):
    """Operadores lógicos básicos."""
    Y = "AND"
    O = "OR"
    NO = "NOT"
    IMPLICA = "IMPLIES"


@dataclass
class Regla:
    """
    Representa una regla de producción: SI condiciones ENTONCES acciones
    
    Ejemplo:
    SI (precipitacion > 30 Y tipo_camino == "trocha") 
    ENTONCES (bloquear_ruta Y recomendar_alternativa)
    """
    id: str
    condiciones: List[Callable[[Dict], bool]]
    acciones: List[Callable[[Dict], Any]]
    prioridad: int = 0
    descripcion: str = ""
    
    def evaluar(self, contexto: Dict) -> bool:
        """
        Evalúa todas las condiciones (conjunción: AND).
        
        Args:
            contexto: Diccionario con datos del sistema
            
        Returns:
            True si todas las condiciones se cumplen
        """
        return all(condicion(contexto) for condicion in self.condiciones)
    
    def ejecutar(self, contexto: Dict) -> List[Any]:
        """
        Ejecuta todas las acciones de la regla.
        
        Args:
            contexto: Diccionario con datos del sistema
            
        Returns:
            Lista de resultados de cada acción
        """
        return [accion(contexto) for accion in self.acciones]


class MotorReglas:
    """
    Motor de inferencia basado en reglas de producción.
    
    Implementa forward chaining (encadenamiento hacia adelante):
    1. Evaluar todas las reglas
    2. Ejecutar las que se cumplen (en orden de prioridad)
    3. Repetir hasta que no se active ninguna regla nueva
    """
    
    def __init__(self):
        self.reglas: List[Regla] = []
        self.historial: List[Dict] = []
    
    def agregar_regla(self, regla: Regla):
        """Agrega una regla al motor."""
        self.reglas.append(regla)
        # Ordenar por prioridad (mayor primero)
        self.reglas.sort(key=lambda r: r.prioridad, reverse=True)
    
    def ejecutar(self, contexto: Dict, max_iteraciones: int = 10) -> Dict:
        """
        Ejecuta el motor de reglas hasta convergencia.
        
        Args:
            contexto: Estado inicial del sistema
            max_iteraciones: Límite de iteraciones (evitar bucles infinitos)
            
        Returns:
            Contexto actualizado después de aplicar todas las reglas
        """
        iteracion = 0
        reglas_disparadas = []
        
        while iteracion < max_iteraciones:
            reglas_activadas = 0
            
            for regla in self.reglas:
                # Evaluar condiciones
                if regla.evaluar(contexto):
                    # Evitar disparar la misma regla múltiples veces
                    if regla.id not in reglas_disparadas:
                        # Ejecutar acciones
                        resultados = regla.ejecutar(contexto)
                        
                        # Registrar
                        self.historial.append({
                            'iteracion': iteracion,
                            'regla_id': regla.id,
                            'descripcion': regla.descripcion,
                            'resultados': resultados
                        })
                        
                        reglas_disparadas.append(regla.id)
                        reglas_activadas += 1
            
            # Si no se activó ninguna regla, converger
            if reglas_activadas == 0:
                break
            
            iteracion += 1
        
        return contexto
    
    def explicar_decision(self) -> str:
        """
        Genera explicación de las decisiones tomadas.
        Útil para transparencia del sistema.
        """
        if not self.historial:
            return "No se ejecutaron reglas."
        
        explicacion = "📋 Reglas aplicadas:\n\n"
        for i, entrada in enumerate(self.historial, 1):
            explicacion += (f"{i}. [{entrada['regla_id']}] "
                          f"{entrada['descripcion']}\n")
        
        return explicacion
    
    def limpiar_historial(self):
        """Limpia el historial de ejecución."""
        self.historial.clear()


# ========== FÁBRICA DE REGLAS PARA SIAR ==========

class ReglasRouting:
    """Reglas específicas para enrutamiento en SIAR."""
    
    @staticmethod
    def crear_reglas_basicas() -> List[Regla]:
        """Crea conjunto básico de reglas para SIAR."""
        reglas = []
        
        # REGLA 1: Bloqueo por lluvia intensa
        reglas.append(Regla(
            id="R1_LLUVIA_INTENSA",
            condiciones=[
                lambda ctx: ctx.get('precipitacion', 0) > 30,
                lambda ctx: ctx.get('tipo_camino') in ['trocha', 'herradura']
            ],
            acciones=[
                lambda ctx: ctx.update({'ruta_bloqueada': True}),
                lambda ctx: ctx.update({'motivo_bloqueo': 'Lluvia intensa + camino precario'})
            ],
            prioridad=100,
            descripcion="Bloquear ruta si hay lluvia intensa en camino precario"
        ))
        
        # REGLA 2: Alerta confirmada = actualizar grafo
        reglas.append(Regla(
            id="R2_ALERTA_CONFIRMADA",
            condiciones=[
                lambda ctx: ctx.get('alerta_confirmada', False),
                lambda ctx: ctx.get('ruta_afectada') is not None
            ],
            acciones=[
                lambda ctx: ctx.update({'actualizar_grafo': True}),
                lambda ctx: ctx.update({'fiabilidad_nueva': 0.3})
            ],
            prioridad=90,
            descripcion="Actualizar fiabilidad de ruta si alerta está confirmada"
        ))
        
        # REGLA 3: Hora nocturna = reducir fiabilidad
        reglas.append(Regla(
            id="R3_VIAJE_NOCTURNO",
            condiciones=[
                lambda ctx: ctx.get('hora', 12) < 6 or ctx.get('hora', 12) > 20
            ],
            acciones=[
                lambda ctx: ctx.update({
                    'factor_nocturno': 0.8,
                    'advertencia': 'Viaje nocturno: mayor riesgo'
                })
            ],
            prioridad=50,
            descripcion="Penalizar viajes nocturnos"
        ))
        
        # REGLA 4: Época de lluvias = rutas alternativas
        reglas.append(Regla(
            id="R4_EPOCA_LLUVIAS",
            condiciones=[
                lambda ctx: ctx.get('mes', 1) in [11, 12, 1, 2, 3],
                lambda ctx: ctx.get('tipo_camino') != 'asfaltado'
            ],
            acciones=[
                lambda ctx: ctx.update({'recomendar_alternativa': True}),
                lambda ctx: ctx.update({'motivo': 'Época de lluvias'})
            ],
            prioridad=70,
            descripcion="Recomendar ruta alternativa en época de lluvias"
        ))
        
        # REGLA 5: Múltiples alertas en ruta = bloqueo preventivo
        reglas.append(Regla(
            id="R5_MULTIPLES_ALERTAS",
            condiciones=[
                lambda ctx: ctx.get('num_alertas_activas', 0) >= 2
            ],
            acciones=[
                lambda ctx: ctx.update({'bloqueo_preventivo': True}),
                lambda ctx: ctx.update({'nivel_riesgo': 'ALTO'})
            ],
            prioridad=95,
            descripcion="Bloqueo preventivo si hay múltiples alertas"
        ))
        
        return reglas


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    print("="*70)
    print("⚙️  MOTOR DE REGLAS - Lógica Proposicional Aplicada")
    print("="*70 + "\n")
    
    # Crear motor
    motor = MotorReglas()
    
    # Cargar reglas
    reglas = ReglasRouting.crear_reglas_basicas()
    for regla in reglas:
        motor.agregar_regla(regla)
    
    print(f"✅ {len(motor.reglas)} reglas cargadas\n")
    
    # ESCENARIO 1: Día normal
    print("="*70)
    print("📍 ESCENARIO 1: Día normal (sin alertas)")
    print("="*70 + "\n")
    
    contexto1 = {
        'precipitacion': 5,
        'tipo_camino': 'asfaltado',
        'hora': 14,
        'mes': 7,
        'num_alertas_activas': 0
    }
    
    motor.limpiar_historial()
    resultado1 = motor.ejecutar(contexto1)
    
    print("Contexto inicial:", contexto1)
    print("\nDecisiones tomadas:")
    print(motor.explicar_decision())
    print("Resultado:", resultado1)
    
    # ESCENARIO 2: Lluvia intensa en trocha
    print("\n" + "="*70)
    print("📍 ESCENARIO 2: Lluvia intensa en trocha")
    print("="*70 + "\n")
    
    contexto2 = {
        'precipitacion': 45,
        'tipo_camino': 'trocha',
        'hora': 10,
        'mes': 2,  # Febrero = época de lluvias
        'num_alertas_activas': 0
    }
    
    motor.limpiar_historial()
    resultado2 = motor.ejecutar(contexto2)
    
    print("Contexto inicial:", contexto2)
    print("\nDecisiones tomadas:")
    print(motor.explicar_decision())
    
    print("\n🚨 Estado final:")
    print(f"   Ruta bloqueada: {resultado2.get('ruta_bloqueada', False)}")
    print(f"   Motivo: {resultado2.get('motivo_bloqueo', 'N/A')}")
    print(f"   Recomendar alternativa: {resultado2.get('recomendar_alternativa', False)}")
    
    # ESCENARIO 3: Múltiples alertas
    print("\n" + "="*70)
    print("📍 ESCENARIO 3: Múltiples alertas activas")
    print("="*70 + "\n")
    
    contexto3 = {
        'precipitacion': 10,
        'tipo_camino': 'afirmado',
        'hora': 22,  # Noche
        'mes': 6,
        'num_alertas_activas': 3,
        'alerta_confirmada': True,
        'ruta_afectada': 'Ayacucho-Huanta'
    }
    
    motor.limpiar_historial()
    resultado3 = motor.ejecutar(contexto3)
    
    print("Contexto inicial:", contexto3)
    print("\nDecisiones tomadas:")
    print(motor.explicar_decision())
    
    print("\n🚨 Estado final:")
    print(f"   Bloqueo preventivo: {resultado3.get('bloqueo_preventivo', False)}")
    print(f"   Nivel de riesgo: {resultado3.get('nivel_riesgo', 'N/A')}")
    print(f"   Actualizar grafo: {resultado3.get('actualizar_grafo', False)}")
    print(f"   Factor nocturno: {resultado3.get('factor_nocturno', 1.0)}")
    
    print("\n" + "="*70)
    print("✅ CONCLUSIÓN")
    print("="*70)
    print("El motor de reglas permite:")
    print("  • Codificar conocimiento experto como reglas SI-ENTONCES")
    print("  • Decisiones automáticas transparentes")
    print("  • Explicabilidad: siempre sabes por qué se tomó una decisión")
    print("\nEsto complementa los algoritmos de grafos con lógica de negocio.")