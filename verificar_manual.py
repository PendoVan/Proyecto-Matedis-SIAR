import sys
import os
import asyncio
from datetime import datetime

# Agregar directorio src al path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from integracion.api_siar import predecir_clima, PrediccionClima, startup_event

async def test_manual_prediction():
    print("\n" + "="*50)
    print("🧪 TEST: Predicción Climática Manual")
    print("="*50)
    
    # Inicializar componentes (cargar modelos)
    await startup_event()
    
    with open("verification_output.txt", "w", encoding="utf-8") as f:
        # Caso 1: Predicción para Enero (Lluvia)
        f.write("\n--- Caso 1: Enero (Temporada de Lluvias) ---\n")
        datos_enero = PrediccionClima(
            temperatura=18,
            precipitacion=20, # Lluvia moderada
            humedad=85,
            presion=1010,
            viento=10,
            departamento="Cusco",
            mes=1 # Enero
        )
        
        res_enero = await predecir_clima(datos_enero)
        f.write(f"Probabilidad de Bloqueo: {res_enero.probabilidad_bloqueo:.2%}\n")
        f.write(f"Recomendación: {res_enero.recomendacion}\n")
        
        # Caso 2: Predicción para Julio (Seco)
        f.write("\n--- Caso 2: Julio (Temporada Seca) ---\n")
        datos_julio = PrediccionClima(
            temperatura=18,
            precipitacion=0, # Sin lluvia
            humedad=40,
            presion=1010,
            viento=10,
            departamento="Cusco",
            mes=7 # Julio
        )
        
        res_julio = await predecir_clima(datos_julio)
        f.write(f"Probabilidad de Bloqueo: {res_julio.probabilidad_bloqueo:.2%}\n")
        f.write(f"Recomendación: {res_julio.recomendacion}\n")
        
        if res_enero.probabilidad_bloqueo > res_julio.probabilidad_bloqueo:
            f.write("\n✅ Lógica correcta: Mayor riesgo en Enero que en Julio\n")
        else:
            f.write("\n❌ ALERTA: La predicción no parece sensible al mes/lluvia\n")

if __name__ == "__main__":
    asyncio.run(test_manual_prediction())
