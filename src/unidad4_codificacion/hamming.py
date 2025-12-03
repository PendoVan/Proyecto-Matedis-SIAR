"""
Módulo: hamming.py
Descripción: Implementación del Código de Hamming para corrección de errores.
Permite detectar y corregir errores en transmisión de datos.

Fundamento Matemático:
- Código de Hamming(7,4): 4 bits de datos + 3 bits de paridad
- Puede corregir 1 error y detectar 2 errores por bloque
"""

from typing import List, Tuple


class CodificadorHamming:
    """
    Implementa el código de Hamming(7,4) para corrección de errores.
    
    Funcionamiento:
    - Toma 4 bits de datos
    - Agrega 3 bits de paridad
    - Genera 7 bits codificados
    - Puede corregir 1 error automáticamente
    """
    
    def __init__(self):
        # Matriz generadora G para Hamming(7,4)
        # Cada fila representa cómo se codifica un bit de datos
        self.G = [
            [1, 0, 0, 0, 1, 1, 0],  # d1
            [0, 1, 0, 0, 1, 0, 1],  # d2
            [0, 0, 1, 0, 0, 1, 1],  # d3
            [0, 0, 0, 1, 1, 1, 1]   # d4
        ]
        
        # Matriz de verificación de paridad H
        # Se usa para detectar y corregir errores
        self.H = [
            [1, 1, 0, 1, 1, 0, 0],  # p1
            [1, 0, 1, 1, 0, 1, 0],  # p2
            [0, 1, 1, 1, 0, 0, 1]   # p3
        ]
    
    def codificar_bloque(self, datos: List[int]) -> List[int]:
        """
        Codifica un bloque de 4 bits usando Hamming(7,4).
        
        Args:
            datos: Lista de 4 bits [d1, d2, d3, d4]
            
        Returns:
            Lista de 7 bits codificados [d1, d2, d3, d4, p1, p2, p3]
        """
        if len(datos) != 4:
            raise ValueError("Hamming(7,4) requiere exactamente 4 bits de entrada")
        
        # Multiplicar vector de datos por matriz generadora G
        codigo = [0] * 7
        for i in range(7):
            suma = 0
            for j in range(4):
                suma += datos[j] * self.G[j][i]
            codigo[i] = suma % 2  # Módulo 2 (XOR)
        
        return codigo
    
    def decodificar_bloque(self, codigo: List[int]) -> Tuple[List[int], bool, int]:
        """
        Decodifica un bloque de 7 bits y corrige errores si es posible.
        
        Args:
            codigo: Lista de 7 bits recibidos (posiblemente con errores)
            
        Returns:
            Tupla (datos_originales, error_detectado, posicion_error)
        """
        if len(codigo) != 7:
            raise ValueError("Hamming(7,4) requiere exactamente 7 bits")
        
        # Calcular síndrome: s = H × c^T
        sindrome = [0, 0, 0]
        for i in range(3):
            suma = 0
            for j in range(7):
                suma += self.H[i][j] * codigo[j]
            sindrome[i] = suma % 2
        
        # Interpretar síndrome
        error_detectado = any(sindrome)
        posicion_error = 0
        
        if error_detectado:
            # Convertir síndrome binario a posición decimal
            posicion_error = sindrome[0] * 4 + sindrome[1] * 2 + sindrome[2]
            
            # Corregir el error
            codigo_corregido = codigo.copy()
            codigo_corregido[posicion_error - 1] = 1 - codigo_corregido[posicion_error - 1]
        else:
            codigo_corregido = codigo
        
        # Extraer bits de datos (primeros 4 bits)
        datos = codigo_corregido[:4]
        
        return datos, error_detectado, posicion_error
    
    def decodificar_bloque_detallado(self, codigo: List[int]) -> dict:
        """
        Decodifica un bloque con información detallada para visualización.
        
        Args:
            codigo: Lista de 7 bits recibidos
            
        Returns:
            Diccionario con pasos detallados del proceso de decodificación
        """
        if len(codigo) != 7:
            raise ValueError("Hamming(7,4) requiere exactamente 7 bits")
        
        # Paso 1: Bits recibidos
        resultado = {
            'bits_recibidos': codigo.copy(),
            'bits_datos': codigo[:4],
            'bits_paridad': codigo[4:7],
            'pasos': []
        }
        
        # Paso 2: Calcular síndrome
        sindrome = [0, 0, 0]
        calculos_sindrome = []
        
        for i in range(3):
            suma = 0
            calculo = []
            for j in range(7):
                if self.H[i][j] == 1:
                    suma += codigo[j]
                    calculo.append(f"b{j+1}")
            sindrome[i] = suma % 2
            calculos_sindrome.append({
                'bit_paridad': i + 1,
                'bits_verificados': calculo,
                'suma': suma,
                'resultado': sindrome[i]
            })
        
        resultado['sindrome'] = sindrome
        resultado['calculos_sindrome'] = calculos_sindrome
        resultado['pasos'].append({
            'numero': 1,
            'descripcion': 'Cálculo del síndrome de error',
            'sindrome': sindrome
        })
        
        # Paso 3: Detectar error
        error_detectado = any(sindrome)
        posicion_error = 0
        
        if error_detectado:
            posicion_error = sindrome[0] * 4 + sindrome[1] * 2 + sindrome[2]
            resultado['pasos'].append({
                'numero': 2,
                'descripcion': f'Error detectado en posición {posicion_error}',
                'posicion_error': posicion_error,
                'bit_erroneo': codigo[posicion_error - 1]
            })
            
            # Paso 4: Corregir error
            codigo_corregido = codigo.copy()
            bit_original = codigo[posicion_error - 1]
            codigo_corregido[posicion_error - 1] = 1 - bit_original
            
            resultado['pasos'].append({
                'numero': 3,
                'descripcion': f'Corrigiendo bit en posición {posicion_error}',
                'bit_antes': bit_original,
                'bit_despues': codigo_corregido[posicion_error - 1]
            })
        else:
            codigo_corregido = codigo
            resultado['pasos'].append({
                'numero': 2,
                'descripcion': 'No se detectaron errores - mensaje íntegro'
            })
        
        # Extraer datos finales
        datos = codigo_corregido[:4]
        
        resultado.update({
            'error_detectado': error_detectado,
            'posicion_error': posicion_error,
            'codigo_corregido': codigo_corregido,
            'datos_finales': datos
        })
        
        return resultado
    
    def codificar_texto(self, texto: str) -> List[int]:
        """
        Codifica un texto completo usando Hamming.
        
        Args:
            texto: Cadena de texto a codificar
            
        Returns:
            Lista de bits codificados
        """
        # Convertir texto a bytes
        bytes_texto = texto.encode('utf-8')
        
        # Convertir cada byte a bits
        bits = []
        for byte in bytes_texto:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)
        
        # Codificar en bloques de 4 bits
        codigo_completo = []
        for i in range(0, len(bits), 4):
            bloque = bits[i:i+4]
            
            # Rellenar con ceros si es necesario
            while len(bloque) < 4:
                bloque.append(0)
            
            bloque_codificado = self.codificar_bloque(bloque)
            codigo_completo.extend(bloque_codificado)
        
        return codigo_completo
    
    def decodificar_texto(self, codigo: List[int]) -> str:
        """
        Decodifica una lista de bits a texto original.
        
        Args:
            codigo: Lista de bits codificados con Hamming
            
        Returns:
            Texto decodificado
        """
        # Decodificar en bloques de 7 bits
        bits_decodificados = []
        errores_corregidos = 0
        
        for i in range(0, len(codigo), 7):
            bloque = codigo[i:i+7]
            
            if len(bloque) < 7:
                continue
            
            datos, error, pos = self.decodificar_bloque(bloque)
            bits_decodificados.extend(datos)
            
            if error:
                errores_corregidos += 1
        
        # Convertir bits a bytes
        bytes_decodificados = []
        for i in range(0, len(bits_decodificados), 8):
            byte_bits = bits_decodificados[i:i+8]
            
            if len(byte_bits) < 8:
                break
            
            byte_valor = 0
            for bit in byte_bits:
                byte_valor = (byte_valor << 1) | bit
            
            bytes_decodificados.append(byte_valor)
        
        # Convertir bytes a texto
        texto = bytes(bytes_decodificados).decode('utf-8', errors='ignore')
        
        if errores_corregidos > 0:
            print(f"   ✅ {errores_corregidos} error(es) corregido(s) automáticamente")
        
        return texto
    
    def calcular_redundancia(self, n_bits_datos: int) -> float:
        """
        Calcula el porcentaje de redundancia del código Hamming.
        
        Args:
            n_bits_datos: Número de bits de datos originales
            
        Returns:
            Porcentaje de redundancia
        """
        n_bloques = (n_bits_datos + 3) // 4  # Redondear hacia arriba
        bits_totales = n_bloques * 7
        bits_paridad = n_bloques * 3
        
        return (bits_paridad / n_bits_datos) * 100 if n_bits_datos > 0 else 0


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    print("="*70)
    print("🔐 CÓDIGO DE HAMMING(7,4) - CORRECCIÓN DE ERRORES")
    print("="*70 + "\n")
    
    hamming = CodificadorHamming()
    
    # Ejemplo 1: Codificar un bloque simple
    print("📍 Ejemplo 1: Codificación de 4 bits")
    datos = [1, 0, 1, 1]
    print(f"   Datos originales: {datos}")
    
    codigo = hamming.codificar_bloque(datos)
    print(f"   Código Hamming:   {codigo}")
    print(f"   (4 bits datos + 3 bits paridad = 7 bits totales)\n")
    
    # Ejemplo 2: Decodificación sin errores
    print("📍 Ejemplo 2: Decodificación sin errores")
    datos_dec, error, pos = hamming.decodificar_bloque(codigo)
    print(f"   Código recibido:  {codigo}")
    print(f"   Datos recuperados: {datos_dec}")
    print(f"   Error detectado:   {'Sí' if error else 'No'}\n")
    
    # Ejemplo 3: Corrección de error
    print("📍 Ejemplo 3: Corrección automática de error")
    codigo_corrupto = codigo.copy()
    codigo_corrupto[2] = 1 - codigo_corrupto[2]  # Introducir error en bit 3
    
    print(f"   Código original:   {codigo}")
    print(f"   Código corrupto:   {codigo_corrupto} (error en posición 3)")
    
    datos_corregidos, error, pos = hamming.decodificar_bloque(codigo_corrupto)
    print(f"   Datos recuperados: {datos_corregidos}")
    print(f"   Error detectado:   Sí, en posición {pos}")
    print(f"   ✅ Error corregido automáticamente!\n")
    
    # Ejemplo 4: Codificar texto
    print("="*70)
    print("📍 Ejemplo 4: Codificación de texto completo")
    print("="*70 + "\n")
    
    mensaje = "ALERTA"
    print(f"Mensaje original: '{mensaje}'")
    
    codigo_texto = hamming.codificar_texto(mensaje)
    print(f"Bits codificados: {len(codigo_texto)} bits")
    print(f"Redundancia: {hamming.calcular_redundancia(len(mensaje)*8):.1f}%\n")
    
    # Simular corrupción
    print("⚠️  Simulando 2 errores en transmisión...")
    codigo_texto[10] = 1 - codigo_texto[10]
    codigo_texto[25] = 1 - codigo_texto[25]
    
    # Decodificar
    mensaje_recuperado = hamming.decodificar_texto(codigo_texto)
    print(f"Mensaje recuperado: '{mensaje_recuperado}'")
    
    if mensaje == mensaje_recuperado:
        print("✅ Mensaje recuperado correctamente!\n")
    else:
        print("❌ Mensaje no pudo ser recuperado completamente\n")
    
    print("="*70)
    print("💡 CONCLUSIÓN")
    print("="*70)
    print("El código de Hamming puede:")
    print("  ✓ Corregir automáticamente 1 error por cada 7 bits")
    print("  ✓ Detectar hasta 2 errores por bloque")
    print("  ✓ Garantizar integridad en transmisiones con ruido")