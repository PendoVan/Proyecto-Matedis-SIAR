"""
Módulo: firmas_digitales.py
Descripción: Implementación simplificada de firmas digitales usando RSA.
Permite autenticar mensajes y verificar su integridad.

Fundamento Matemático:
- Aritmética modular
- Teorema de Euler
- Exponenciación modular rápida
"""

import hashlib
from typing import Tuple


class GeneradorFirmas:
    """
    Implementa un sistema simplificado de firmas digitales.
    Usa principios de RSA pero con números pequeños para demostración.
    """
    
    def __init__(self):
        # Números primos pequeños para demostración
        # En producción se usarían primos de 2048+ bits
        self.p = 61
        self.q = 53
        self.n = self.p * self.q  # 3233
        self.phi = (self.p - 1) * (self.q - 1)  # 3120
    
    def generar_claves(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """
        Genera par de claves pública y privada.
        
        Returns:
            (clave_privada, clave_publica)
            Cada clave es una tupla (e, n) o (d, n)
        """
        # Elegir e (exponente público)
        # e debe ser coprimo con phi(n)
        e = 17  # Valor común en RSA
        
        # Calcular d (exponente privado)
        # d × e ≡ 1 (mod φ(n))
        d = self._inverso_modular(e, self.phi)
        
        clave_privada = (d, self.n)
        clave_publica = (e, self.n)
        
        return clave_privada, clave_publica
    
    def _inverso_modular(self, a: int, m: int) -> int:
        """
        Calcula el inverso modular de a mod m.
        Usa el algoritmo extendido de Euclides.
        """
        def euclides_extendido(a, b):
            if a == 0:
                return b, 0, 1
            gcd, x1, y1 = euclides_extendido(b % a, a)
            x = y1 - (b // a) * x1
            y = x1
            return gcd, x, y
        
        gcd, x, _ = euclides_extendido(a, m)
        if gcd != 1:
            raise ValueError("No existe inverso modular")
        return (x % m + m) % m
    
    def _exp_modular_rapida(self, base: int, exponente: int, modulo: int) -> int:
        """
        Calcula (base^exponente) mod modulo de forma eficiente.
        Usa exponenciación binaria.
        """
        resultado = 1
        base = base % modulo
        
        while exponente > 0:
            if exponente % 2 == 1:
                resultado = (resultado * base) % modulo
            exponente = exponente >> 1
            base = (base * base) % modulo
        
        return resultado
    
    def hash_mensaje(self, mensaje: str) -> int:
        """
        Genera un hash del mensaje para firmar.
        
        Args:
            mensaje: Texto a hashear
            
        Returns:
            Valor hash como entero
        """
        # Usar SHA-256
        hash_obj = hashlib.sha256(mensaje.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        # Convertir a entero y reducir módulo n
        hash_int = int(hash_hex, 16) % self.n
        
        return hash_int
    
    def firmar_mensaje(self, mensaje: str, clave_privada: Tuple[int, int]) -> int:
        """
        Firma un mensaje usando la clave privada.
        
        Args:
            mensaje: Texto a firmar
            clave_privada: Tupla (d, n)
            
        Returns:
            Firma digital (entero)
        """
        d, n = clave_privada
        
        # Hashear el mensaje
        hash_msg = self.hash_mensaje(mensaje)
        
        # Firmar: firma = hash^d mod n
        firma = self._exp_modular_rapida(hash_msg, d, n)
        
        return firma
    
    def verificar_firma(self, mensaje: str, firma: int, 
                       clave_publica: Tuple[int, int]) -> bool:
        """
        Verifica si una firma es válida.
        
        Args:
            mensaje: Texto original
            firma: Firma digital recibida
            clave_publica: Tupla (e, n)
            
        Returns:
            True si la firma es válida, False en caso contrario
        """
        e, n = clave_publica
        
        # Calcular hash del mensaje
        hash_msg = self.hash_mensaje(mensaje)
        
        # Verificar: hash_verificado = firma^e mod n
        hash_verificado = self._exp_modular_rapida(firma, e, n)
        
        return hash_msg == hash_verificado


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    print("="*70)
    print("🔐 FIRMAS DIGITALES - AUTENTICACIÓN DE MENSAJES")
    print("="*70 + "\n")
    
    firmador = GeneradorFirmas()
    
    # Generar claves
    print("📍 Paso 1: Generar par de claves")
    clave_privada, clave_publica = firmador.generar_claves()
    print(f"   Clave privada: {clave_privada}")
    print(f"   Clave pública:  {clave_publica}\n")
    
    # Firmar mensaje
    print("📍 Paso 2: Firmar mensaje")
    mensaje = "ALERTA: Puente caído en Km 45"
    print(f"   Mensaje: '{mensaje}'")
    
    firma = firmador.firmar_mensaje(mensaje, clave_privada)
    print(f"   Firma generada: {firma}\n")
    
    # Verificar firma válida
    print("📍 Paso 3: Verificar firma (mensaje auténtico)")
    es_valida = firmador.verificar_firma(mensaje, firma, clave_publica)
    print(f"   Firma válida: {es_valida}")
    print(f"   ✅ El mensaje es auténtico\n")
    
    # Intentar modificar mensaje
    print("="*70)
    print("📍 Paso 4: Detectar alteración de mensaje")
    print("="*70 + "\n")
    
    mensaje_alterado = "ALERTA: Puente caído en Km 50"  # Cambió el km
    print(f"   Mensaje original:  '{mensaje}'")
    print(f"   Mensaje alterado:  '{mensaje_alterado}'")
    
    es_valida_alterado = firmador.verificar_firma(mensaje_alterado, firma, clave_publica)
    print(f"   Firma válida: {es_valida_alterado}")
    print(f"   ⚠️  El mensaje fue alterado!\n")
    
    print("="*70)
    print("💡 CONCLUSIÓN")
    print("="*70)
    print("Las firmas digitales garantizan:")
    print("  ✓ Autenticidad: El mensaje viene de quien dice ser")
    print("  ✓ Integridad: El mensaje no fue alterado")
    print("  ✓ No repudio: El emisor no puede negar haberlo enviado")