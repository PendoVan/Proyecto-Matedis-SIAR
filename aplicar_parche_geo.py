"""
Script para aplicar el parche de optimización geográfica a SIAR API.
Ejecutar: python aplicar_parche_geo.py
"""

import os

# Ruta al archivo API
api_path = "src/integracion/api_siar.py"

print("🔧 Aplicando parche de optimización geográfica...")

# Leer el archivo
with open(api_path, 'r', encoding='utf-8') as f:
    contenido = f.read()

# Aplicar modificaciones

# 1. Agregar import del nuevo algoritmo
old_import = "from src.unidad3_grafos.algoritmo_fiabilidad import AlgoritmoFiabilidad, Ruta"
new_import = """from src.unidad3_grafos.algoritmo_fiabilidad import Ruta
from src.unidad3_grafos.algoritmo_fiabilidad_geo import AlgoritmoFiabilidadGeo  # 🔥 Algoritmo con penalización geográfica"""

if old_import in contenido:
    contenido = contenido.replace(old_import, new_import)
    print("✅ Import actualizado")
else:
    print("⚠️  Import no encontrado")

# 2. Cambiar la inicialización del algoritmo en startup
old_init = "algoritmo = AlgoritmoFiabilidad(grafo)"
new_init = "algoritmo = AlgoritmoFiabilidadGeo(grafo, COORDENADAS)  # 🔥 Usa algoritmo con optimización geográfica"

contenido = contenido.replace(old_init, new_init)
print("✅ Inicialización del algoritmo actualizada")

# Guardar el archivo modificado
with open(api_path, 'w', encoding='utf-8') as f:
    f.write(contenido)

print("\n✅ Parche aplicado exitosamente!")
print("\nDetalles del cambio:")
print("  - Algoritmo base: AlgoritmoFiabilidad")
print("  - Algoritmo nuevo: AlgoritmoFiabilidadGeo")
print("  - Función nueva: Penalización geográfica por desvíos")
print("\nPara probar:")
print("  python -m uvicorn src.integracion.api_siar:app --reload")
