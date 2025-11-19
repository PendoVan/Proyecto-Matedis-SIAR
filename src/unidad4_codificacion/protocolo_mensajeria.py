"""
Protocolo de Mensajería Resiliente con Hamming
Demuestra corrección de errores en alertas críticas
"""

import sys
import os
sys.path.append('..')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.unidad4_codificacion.hamming import CodificadorHamming
from src.unidad4_codificacion.firmas_digitales import GeneradorFirmas
import json

class ProtocoloResiliente:
    """
    Protocolo que combina Hamming + Firmas para mensajes críticos.
    Diseñado para zonas con mala conectividad.
    """
    
    def __init__(self):
        self.hamming = CodificadorHamming()
        self.firmador = GeneradorFirmas()
        self.clave_privada, self.clave_publica = self.firmador.generar_claves()
    
    def enviar_alerta(self, tipo: str, ubicacion: str, descripcion: str) -> dict:
        """
        Codifica una alerta para transmisión resiliente.
        
        Proceso:
        1. Serializar mensaje
        2. Codificar con Hamming (protección contra errores)
        3. Firmar digitalmente (autenticidad)
        """
        # 1. Crear mensaje
        mensaje = {
            'tipo': tipo,
            'ubicacion': ubicacion,
            'descripcion': descripcion,
            'timestamp': '2024-11-19T10:30:00'
        }
        
        mensaje_str = json.dumps(mensaje)
        
        # 2. Codificar con Hamming (protección)
        mensaje_codificado = self.hamming.codificar_texto(mensaje_str)
        
        # 3. Firmar (autenticidad)
        firma = self.firmador.firmar_mensaje(mensaje_str, self.clave_privada)
        
        print(f"\n📡 ENVIANDO ALERTA")
        print(f"   Tipo: {tipo}")
        print(f"   Ubicación: {ubicacion}")
        print(f"   Tamaño original: {len(mensaje_str)} caracteres")
        print(f"   Tamaño codificado: {len(mensaje_codificado)} bits")
        print(f"   Redundancia: {(len(mensaje_codificado)/len(mensaje_str)/8 - 1)*100:.1f}%")
        
        return {
            'mensaje_codificado': mensaje_codificado,
            'firma': firma,
            'clave_publica': self.clave_publica
        }
    
    def recibir_alerta(self, paquete: dict, simular_errores: int = 0):
        """
        Decodifica y verifica una alerta recibida.
        
        Args:
            paquete: Diccionario con mensaje_codificado, firma, clave_publica
            simular_errores: Número de bits a corromper para demostrar corrección
        """
        mensaje_codificado = paquete['mensaje_codificado']
        
        # Simular corrupción de datos (mala señal)
        if simular_errores > 0:
            print(f"\n⚠️  SIMULANDO {simular_errores} ERROR(ES) EN TRANSMISIÓN...")
            mensaje_corrupto = self._corromper_bits(mensaje_codificado, simular_errores)
            print(f"   Bits corruptos: {simular_errores}/{len(mensaje_codificado)}")
        else:
            mensaje_corrupto = mensaje_codificado
        
        # Decodificar con Hamming (corrección automática)
        try:
            mensaje_decodificado = self.hamming.decodificar_texto(mensaje_corrupto)
            print(f"\n✅ MENSAJE RECIBIDO Y CORREGIDO")
            
            # Verificar firma
            firma_valida = self.firmador.verificar_firma(
                mensaje_decodificado, 
                paquete['firma'], 
                paquete['clave_publica']
            )
            
            if firma_valida:
                print(f"🔐 Firma verificada: Mensaje auténtico")
            else:
                print(f"⚠️  Firma inválida: Posible alteración")
            
            mensaje_json = json.loads(mensaje_decodificado)
            
            print(f"\n📥 ALERTA DECODIFICADA:")
            print(f"   Tipo: {mensaje_json['tipo']}")
            print(f"   Ubicación: {mensaje_json['ubicacion']}")
            print(f"   Descripción: {mensaje_json['descripcion']}")
            
            return mensaje_json
            
        except Exception as e:
            print(f"❌ Error irrecuperable en mensaje: {e}")
            return None
    
    def _corromper_bits(self, bits: list, num_errores: int) -> list:
        """Introduce errores aleatorios para simular mala señal."""
        import random
        bits_corruptos = bits.copy()
        posiciones = random.sample(range(len(bits)), num_errores)
        
        for pos in posiciones:
            bits_corruptos[pos] = 1 - bits_corruptos[pos]  # Invertir bit
        
        return bits_corruptos


# ========== DEMO ==========
if __name__ == "__main__":
    print("="*70)
    print("🛡️  PROTOCOLO DE MENSAJERÍA RESILIENTE")
    print("   Corrección de Errores + Firmas Digitales")
    print("="*70)
    
    protocolo = ProtocoloResiliente()
    
    # Escenario 1: Transmisión perfecta
    print("\n📍 ESCENARIO 1: Transmisión sin errores")
    paquete = protocolo.enviar_alerta(
        tipo="BLOQUEO_CARRETERA",
        ubicacion="Km 45 Ayacucho-Huanta",
        descripcion="Huaico bloquea vía. Tránsito interrumpido."
    )
    protocolo.recibir_alerta(paquete, simular_errores=0)
    
    # Escenario 2: Transmisión con errores (señal débil)
    print("\n" + "="*70)
    print("📍 ESCENARIO 2: Transmisión con errores (señal débil)")
    paquete2 = protocolo.enviar_alerta(
        tipo="EMERGENCIA_MEDICA",
        ubicacion="Comunidad San Pedro",
        descripcion="Requiere ambulancia urgente"
    )
    protocolo.recibir_alerta(paquete2, simular_errores=3)
    
    print("\n" + "="*70)
    print("✅ DEMOSTRACIÓN COMPLETADA")
    print("="*70)
    print("\n💡 CONCLUSIÓN:")
    print("   El sistema puede corregir automáticamente hasta 1 error")
    print("   por cada bloque de 7 bits, garantizando la integridad")
    print("   de mensajes críticos incluso con señal débil.")