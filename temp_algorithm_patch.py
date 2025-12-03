# Este fragmento debe reemplazar las líneas 116-118 en algoritmo_fiabilidad.py

# CÓDIGO A REEMPLAZAR (líneas 116-118):
#                 # Calcular nuevo peso
#                 peso_arista = arista.calcular_peso_fiabilidad()
#                 nuevo_peso = peso_actual + peso_arista

# NUEVO CÓDIGO:
                # Calcular nuevo peso (dinámico o estático)
                if fecha_salida and hora_salida and predictor_clima:
                    # Modo dinámico: obtener riesgo climático
                    try:
                        riesgo_clima = predictor_clima.predecir_riesgo_por_fecha(
                            departamento=nodo_actual,
                            fecha_salida=fecha_salida
                        )
                    except Exception as e:
                        print(f"⚠️  Error en predicción climática para {nodo_actual}: {e}")
                        riesgo_clima = 0.0
                    
                    peso_arista = arista.calcular_peso_dinamico(
                        fecha_salida=fecha_salida,
                        hora_salida=hora_salida,
                        riesgo_clima=riesgo_clima
                    )
                else:
                    # Modo estático (backward compatibility)
                    peso_arista = arista.calcular_peso_fiabilidad()
                nuevo_peso = peso_actual + peso_arista
