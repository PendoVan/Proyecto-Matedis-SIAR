"""
Módulo: bayes_actualizacion.py
Descripción: Implementación del Teorema de Bayes para actualización de confianza en alertas.

Fundamento Matemático:
P(A|B) = P(B|A) × P(A) / P(B)

Aplicación SIAR:
P(alerta_real | n_confirmaciones) aumenta con cada confirmación de usuarios distintos.

Referencia: Ya está aplicado "invisiblemente" en maquina_estados.py (línea 167),
pero este módulo lo explica explícitamente para fines académicos.
"""

from typing import List
from dataclasses import dataclass


@dataclass
class ConfiguracionBayes:
    """Configuración del modelo Bayesiano de alertas."""
    prior_alerta_real: float = 0.30  # P(alerta real) inicial: 30%
    veracidad_usuario: float = 0.85  # P(confirma | real) = 85%
    falso_positivo: float = 0.10    # P(confirma | falsa) = 10%


class ActualizadorConfianza:
    """
    Implementa actualización Bayesiana de confianza en alertas.
    
    Caso de uso:
    - Una alerta inicial tiene 30% de confianza (prior)
    - Cada usuario que la confirma aumenta la confianza
    - El sistema NO solo cuenta confirmaciones, sino que aplica Bayes
    """
    
    def __init__(self, config: ConfiguracionBayes = None):
        self.config = config or ConfiguracionBayes()
    
    def calcular_posterior(self, n_confirmaciones: int, 
                          n_rechazos: int = 0) -> float:
        """
        Calcula P(alerta_real | evidencia) usando Bayes.
        
        Args:
            n_confirmaciones: Número de usuarios que confirmaron
            n_rechazos: Número de usuarios que rechazaron
            
        Returns:
            Probabilidad posterior (0 a 1)
            
        Teorema de Bayes:
        P(real|conf) = P(conf|real) × P(real) / P(conf)
        
        donde:
        P(conf) = P(conf|real)×P(real) + P(conf|falsa)×P(falsa)
        """
        # Prior
        p_real = self.config.prior_alerta_real
        p_falsa = 1 - p_real
        
        # Likelihood (verosimilitud)
        # Probabilidad de obtener esta evidencia si la alerta ES real
        p_conf_dado_real = self.config.veracidad_usuario ** n_confirmaciones
        p_rech_dado_real = (1 - self.config.veracidad_usuario) ** n_rechazos
        p_evidencia_dado_real = p_conf_dado_real * p_rech_dado_real
        
        # Probabilidad de obtener esta evidencia si la alerta ES FALSA
        p_conf_dado_falsa = self.config.falso_positivo ** n_confirmaciones
        p_rech_dado_falsa = (1 - self.config.falso_positivo) ** n_rechazos
        p_evidencia_dado_falsa = p_conf_dado_falsa * p_rech_dado_falsa
        
        # Evidencia total (normalizador)
        p_evidencia = (p_evidencia_dado_real * p_real + 
                      p_evidencia_dado_falsa * p_falsa)
        
        # Evitar división por cero
        if p_evidencia == 0:
            return p_real
        
        # TEOREMA DE BAYES
        posterior = (p_evidencia_dado_real * p_real) / p_evidencia
        
        return min(0.99, posterior)  # Cap en 99%
    
    def explicar_actualizacion(self, n_confirmaciones: int) -> dict:
        """
        Genera explicación paso a paso de la actualización Bayesiana.
        Útil para la presentación del proyecto.
        """
        pasos = []
        
        # Paso 0: Prior
        conf_actual = self.config.prior_alerta_real
        pasos.append({
            'paso': 0,
            'evento': 'Alerta emitida',
            'confianza': conf_actual,
            'explicacion': f'Confianza inicial (prior): {conf_actual:.1%}'
        })
        
        # Pasos 1 a N: Confirmaciones
        for i in range(1, n_confirmaciones + 1):
            conf_nueva = self.calcular_posterior(i, 0)
            pasos.append({
                'paso': i,
                'evento': f'Usuario {i} confirma',
                'confianza': conf_nueva,
                'explicacion': f'Aplicando Bayes: {conf_actual:.1%} → {conf_nueva:.1%}'
            })
            conf_actual = conf_nueva
        
        return {
            'pasos': pasos,
            'confianza_final': conf_actual,
            'incremento_total': conf_actual - self.config.prior_alerta_real
        }


# ========== COMPARACIÓN CON ENFOQUE INGENUO ==========

def enfoque_ingenuo(n_confirmaciones: int, base: float = 0.30) -> float:
    """
    Enfoque ingenuo: cada confirmación suma 15%.
    PROBLEMA: No modela correctamente la incertidumbre.
    """
    return min(0.99, base + (n_confirmaciones * 0.15))


def comparar_enfoques(max_confirmaciones: int = 5):
    """
    Compara Bayes vs enfoque ingenuo para demostrar superioridad.
    """
    actualizador = ActualizadorConfianza()
    
    print("="*70)
    print("📊 COMPARACIÓN: BAYES vs ENFOQUE INGENUO")
    print("="*70 + "\n")
    
    print(f"{'Confirmaciones':<15} {'Bayes':<12} {'Ingenuo':<12} {'Diferencia':<12}")
    print("-"*70)
    
    for n in range(0, max_confirmaciones + 1):
        bayes = actualizador.calcular_posterior(n, 0)
        ingenuo = enfoque_ingenuo(n)
        diferencia = bayes - ingenuo
        
        print(f"{n:<15} {bayes:>10.1%} {ingenuo:>11.1%} {diferencia:>11.1%}")
    
    print("\n💡 Observaciones:")
    print("   • Bayes crece más rápido al inicio (información más valiosa)")
    print("   • Bayes se satura correctamente (límite asintótico)")
    print("   • Ingenuo es lineal y poco realista")


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    print("="*70)
    print("🎓 TEOREMA DE BAYES - Actualización de Confianza en Alertas")
    print("="*70 + "\n")
    
    actualizador = ActualizadorConfianza()
    
    # Caso 1: Evolución con 4 confirmaciones
    print("📍 Caso 1: Alerta con 4 confirmaciones sucesivas\n")
    resultado = actualizador.explicar_actualizacion(4)
    
    for paso_info in resultado['pasos']:
        print(f"  {paso_info['paso']}. {paso_info['evento']:<25} "
              f"Confianza: {paso_info['confianza']:>6.1%}")
    
    print(f"\n  ✅ Incremento total: {resultado['incremento_total']*100:+.1f}%")
    
    # Caso 2: Efecto de rechazos
    print("\n" + "="*70)
    print("📍 Caso 2: Efecto de rechazos\n")
    
    conf_solo_conf = actualizador.calcular_posterior(3, 0)
    conf_con_rech = actualizador.calcular_posterior(3, 2)
    
    print(f"  3 confirmaciones, 0 rechazos: {conf_solo_conf:.1%}")
    print(f"  3 confirmaciones, 2 rechazos: {conf_con_rech:.1%}")
    print(f"  Impacto de rechazos: {(conf_solo_conf - conf_con_rech)*100:.1f}%")
    
    # Comparación
    print("\n" + "="*70)
    comparar_enfoques(5)
    
    print("\n" + "="*70)
    print("✅ CONCLUSIÓN")
    print("="*70)
    print("El Teorema de Bayes permite:")
    print("  • Modelar correctamente la incertidumbre")
    print("  • Ponderar evidencia de forma óptima")
    print("  • Evitar sobre-confianza con pocas confirmaciones")
    print("\nEsto está implementado en maquina_estados.py (línea 167)")
    print("pero de forma simplificada. Este módulo lo explica completamente.")