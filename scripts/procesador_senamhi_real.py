"""
Módulo: procesador_senamhi_real.py
Descripción: Procesa archivos CSV reales del SENAMHI y entrena red neuronal.
Compatible con el formato oficial de SENAMHI Perú.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def limpiar_csv_senamhi(ruta_csv: str) -> pd.DataFrame:
    """
    Procesa CSV del SENAMHI con su formato específico.
    
    Formato SENAMHI:
    - Líneas 1-2: Metadatos (ignorar)
    - Línea 3: Estación
    - Línea 4: Departamento
    - Línea 5: Coordenadas
    - Línea 6: Tipo y código
    - Línea 7: Headers
    - Línea 8+: Datos
    """
    print(f"📂 Procesando: {ruta_csv}\n")
    
    # Leer metadatos (primeras líneas)
    with open(ruta_csv, 'r', encoding='utf-8') as f:
        lineas = f.readlines()
    
    # Extraer información de estación
    estacion = lineas[2].split(':')[1].strip()
    departamento = lineas[3].split(',')[1].strip()
    
    print(f"📍 Estación: {estacion}")
    print(f"📍 Departamento: {departamento}\n")
    
    # Leer datos (saltar las 7 primeras líneas)
    df = pd.read_csv(ruta_csv, skiprows=7, encoding='utf-8')
    
    # Renombrar columnas
    df.columns = ['fecha', 'temp_max', 'temp_min', 'humedad', 'precipitacion']
    
    # Convertir fecha
    df['fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d')
    
    # Limpiar datos
    df['precipitacion'] = df['precipitacion'].replace('T', 0.05)  # Trazas = 0.05mm
    df['precipitacion'] = df['precipitacion'].replace('S/D', np.nan)
    df['precipitacion'] = pd.to_numeric(df['precipitacion'], errors='coerce')
    
    # Calcular temperatura promedio
    df['temperatura'] = (df['temp_max'] + df['temp_min']) / 2
    
    # Limpiar valores nulos
    df = df.dropna()
    
    # Agregar columnas adicionales
    df['estacion'] = estacion
    df['departamento'] = departamento
    df['mes'] = df['fecha'].dt.month
    df['dia_semana'] = df['fecha'].dt.dayofweek
    
    # Valores por defecto para entrenamiento
    df['presion'] = 1010  # Presión estándar
    df['viento'] = 5  # Velocidad promedio
    
    print(f"✅ Datos procesados: {len(df)} registros")
    print(f"   Periodo: {df['fecha'].min().date()} a {df['fecha'].max().date()}\n")
    
    return df


def agregar_etiquetas_bloqueo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega la columna 'bloqueo' basándose en condiciones climáticas extremas.
    
    Criterios:
    - Precipitación > 25 mm/día → Bloqueo probable
    - Temperatura < 5°C → Riesgo de hielo
    - Temperatura > 35°C → Riesgo
    - Precipitación > 40 mm/día → Bloqueo casi seguro
    """
    print("🔍 Calculando etiquetas de bloqueo...\n")
    
    df['bloqueo'] = 0
    
    # Reglas para bloqueos
    df.loc[df['precipitacion'] > 40, 'bloqueo'] = 1
    df.loc[(df['precipitacion'] > 25) & (df['temperatura'] < 15), 'bloqueo'] = 1
    df.loc[df['temperatura'] < 5, 'bloqueo'] = 1
    df.loc[df['temperatura'] > 35, 'bloqueo'] = 1
    
    num_bloqueos = df['bloqueo'].sum()
    porcentaje = (num_bloqueos / len(df)) * 100
    
    print(f"📊 Bloqueos detectados: {num_bloqueos} ({porcentaje:.1f}%)")
    
    # Distribución por mes
    print(f"\n📅 Bloqueos por mes:")
    bloqueos_mes = df[df['bloqueo'] == 1].groupby('mes').size()
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
             'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    
    for mes_num, count in bloqueos_mes.items():
        print(f"   {meses[mes_num-1]}: {count}")
    
    return df


def combinar_multiples_estaciones(rutas_csv: list) -> pd.DataFrame:
    """
    Combina datos de múltiples estaciones SENAMHI.
    """
    print("="*70)
    print("🌍 COMBINANDO MÚLTIPLES ESTACIONES")
    print("="*70 + "\n")
    
    dfs = []
    
    for ruta in rutas_csv:
        if os.path.exists(ruta):
            df = limpiar_csv_senamhi(ruta)
            dfs.append(df)
        else:
            print(f"⚠️  Archivo no encontrado: {ruta}\n")
    
    if not dfs:
        raise ValueError("No se encontraron archivos CSV válidos")
    
    df_combinado = pd.concat(dfs, ignore_index=True)
    
    print(f"\n✅ Combinación completada:")
    print(f"   Total registros: {len(df_combinado)}")
    print(f"   Estaciones: {df_combinado['estacion'].nunique()}")
    print(f"   Departamentos: {', '.join(df_combinado['departamento'].unique())}\n")
    
    return df_combinado


def entrenar_con_datos_senamhi(df: pd.DataFrame):
    """
    Entrena la red neuronal con datos reales del SENAMHI.
    """
    print("="*70)
    print("🧠 ENTRENANDO RED NEURONAL CON DATOS REALES")
    print("="*70 + "\n")
    
    # Agregar etiquetas
    df = agregar_etiquetas_bloqueo(df)
    
    # Preparar datos para entrenamiento
    features = ['temperatura', 'precipitacion', 'humedad', 'presion', 'viento']
    X = df[features].values
    y = df['bloqueo'].values
    
    print(f"📊 Conjunto de datos:")
    print(f"   Muestras totales: {len(X)}")
    print(f"   Características: {len(features)}")
    print(f"   Bloqueos: {y.sum()} ({y.mean()*100:.1f}%)\n")
    
    # Entrenar con TensorFlow (si está disponible)
    try:
        from src.unidad3_grafos.prediccion_climatica import IntegradorSENAMHI
        
        integrador = IntegradorSENAMHI()
        metricas = integrador.entrenar_modelo(df, epochs=50, batch_size=32)
        
        # Guardar modelo
        integrador.guardar_modelo("data/modelos/prediccion_senamhi_real.h5")
        
        print(f"\n✅ Modelo entrenado con datos reales")
        print(f"   Precisión: {metricas['accuracy']*100:.2f}%")
        print(f"   AUC: {metricas['auc']:.3f}")
        
        return integrador
        
    except ImportError:
        print("⚠️  TensorFlow no disponible, usando red neuronal simple...\n")
        
        from src.unidad3_grafos.red_neuronal_simple import RedNeuronalSimple
        
        modelo = RedNeuronalSimple()
        modelo.entrenar(X, y, epochs=100, learning_rate=0.1)
        modelo.guardar_modelo("data/modelos/red_neuronal_senamhi.npz")
        
        print(f"\n✅ Modelo simple entrenado con datos reales")
        
        return modelo


def exportar_datos_limpios(df: pd.DataFrame, ruta_salida: str = "data/clima/senamhi_procesado.csv"):
    """Exporta los datos procesados para uso futuro."""
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    df.to_csv(ruta_salida, index=False, encoding='utf-8')
    print(f"\n💾 Datos procesados guardados en: {ruta_salida}")


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Procesar datos SENAMHI')
    parser.add_argument('--csv', type=str, help='Ruta a un CSV de SENAMHI')
    parser.add_argument('--carpeta', type=str, help='Carpeta con múltiples CSVs')
    parser.add_argument('--entrenar', action='store_true', help='Entrenar modelo')
    
    args = parser.parse_args()
    
    print("="*70)
    print("🌦️  PROCESADOR DE DATOS SENAMHI")
    print("="*70 + "\n")
    
    if args.csv:
        # Procesar un solo archivo
        df = limpiar_csv_senamhi(args.csv)
        df = agregar_etiquetas_bloqueo(df)
        
        # Mostrar muestra
        print("\n📋 Muestra de datos procesados:")
        print(df[['fecha', 'temperatura', 'precipitacion', 'humedad', 'bloqueo']].head(10))
        
        # Exportar
        exportar_datos_limpios(df)
        
        # Entrenar si se solicita
        if args.entrenar:
            entrenar_con_datos_senamhi(df)
    
    elif args.carpeta:
        # Procesar múltiples archivos
        import glob
        
        archivos = glob.glob(f"{args.carpeta}/*.csv")
        print(f"📂 Encontrados {len(archivos)} archivos CSV\n")
        
        df = combinar_multiples_estaciones(archivos)
        
        # Exportar
        exportar_datos_limpios(df, "data/clima/senamhi_completo.csv")
        
        # Entrenar
        if args.entrenar:
            entrenar_con_datos_senamhi(df)
    
    else:
        # Usar archivo de ejemplo
        print("💡 Uso:")
        print("   python procesador_senamhi_real.py --csv data/clima/san_juan_cajamarca.csv")
        print("   python procesador_senamhi_real.py --carpeta data/clima --entrenar")
        print("\n📝 Asegúrate de tener los CSVs del SENAMHI en data/clima/\n")
        
        # Crear datos de ejemplo si no hay archivos
        ejemplo_csv = "data/clima/san_juan_cajamarca.csv"
        if os.path.exists(ejemplo_csv):
            print(f"✅ Procesando archivo de ejemplo...\n")
            df = limpiar_csv_senamhi(ejemplo_csv)
            df = agregar_etiquetas_bloqueo(df)
            exportar_datos_limpios(df)
            
            if input("\n¿Entrenar modelo con estos datos? (s/n): ").lower() == 's':
                entrenar_con_datos_senamhi(df)
        else:
            print(f"⚠️  No se encontró archivo de ejemplo en: {ejemplo_csv}")
            print("   Copia tu CSV del SENAMHI a esa ubicación")
    
    print("\n" + "="*70)
    print("✅ PROCESO COMPLETADO")
    print("="*70)