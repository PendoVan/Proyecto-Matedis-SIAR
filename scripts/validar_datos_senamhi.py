"""
Script para validar la calidad de los datos SENAMHI
Verifica si los eventos de bloqueo son reales o simulados
"""

import pandas as pd
import os

def validar_datos_senamhi():
    ruta_csv = "data/clima/senamhi_procesado.csv"
    
    if not os.path.exists(ruta_csv):
        print(f"❌ ERROR: No se encuentra el archivo {ruta_csv}")
        return
    
    print("="*60)
    print("🔍 VALIDACIÓN DE DATOS SENAMHI")
    print("="*60)
    
    # Cargar datos
    print("\n📥 Cargando datos...")
    df = pd.read_csv(ruta_csv, parse_dates=['fecha'])
    print(f"✅ Cargados {len(df):,} registros\n")
    
    # 1. Verificar eventos de bloqueo
    bloqueos = df[df['bloqueo'] == 1]
    print("="*60)
    print("📊 ESTADÍSTICAS GENERALES")
    print("="*60)
    print(f"Total registros:        {len(df):,}")
    print(f"Eventos de bloqueo:     {len(bloqueos):,}")
    print(f"Porcentaje de bloqueos: {len(bloqueos)/len(df)*100:.2f}%")
    
    # 2.Mostrar primeros events de bloqueo
    if len(bloqueos) > 0:
        print("\n" + "="*60)
        print("🚨 PRIMEROS 15 EVENTOS DE BLOQUEO")
        print("="*60)
        columnas = ['fecha', 'departamento', 'temperatura', 'precipitacion', 'humedad', 'viento']
        print(bloqueos[columnas].head(15).to_string(index=False))
        
        # 3. Distribución por departamento
        print("\n" + "="*60)
        print("📍 DISTRIBUCIÓN POR DEPARTAMENTO")
        print("="*60)
        if 'departamento' in df.columns:
            dept_stats = df.groupby('departamento')['bloqueo'].agg([
                ('Total Registros', 'count'),
                ('Total Bloqueos', 'sum'),
                ('% Bloqueos', lambda x: x.mean() * 100)
            ]).round(2)
            dept_stats = dept_stats.sort_values('Total Bloqueos', ascending=False)
            print(dept_stats.to_string())
        else:
            print("⚠️  No hay columna 'departamento'")
        
        # 4. Verificar si son datos reales o simulados
        print("\n" + "="*60)
        print("🔬 ANÁLISIS DE PATRONES (Validación de Realismo)")
        print("="*60)
        
        # Precipitación
        precip_normal = df[df['bloqueo'] == 0]['precipitacion'].mean()
        precip_bloqueo = bloqueos['precipitacion'].mean()
        ratio_precip = precip_bloqueo / precip_normal if precip_normal > 0 else 0
        
        print(f"Precipitación promedio:")
        print(f"  Días normales:  {precip_normal:.2f} mm")
        print(f"  Días de bloqueo: {precip_bloqueo:.2f} mm")
        print(f"  Ratio:          {ratio_precip:.2f}x")
       
        # Viento
        if 'viento' in df.columns:
            viento_normal = df[df['bloqueo'] == 0]['viento'].mean()
            viento_bloqueo = bloqueos['viento'].mean()
            ratio_viento = viento_bloqueo / viento_normal if viento_normal > 0 else 0
            
            print(f"\nViento promedio:")
            print(f"  Días normales:   {viento_normal:.2f} m/s")
            print(f"  Días de bloqueo: {viento_bloqueo:.2f} m/s")
            print(f"  Ratio:           {ratio_viento:.2f}x")
        
        # Temperatura
        temp_normal = df[df['bloqueo'] == 0]['temperatura'].mean()
        temp_bloqueo = bloqueos['temperatura'].mean()
        
        print(f"\nTemperatura promedio:")
        print(f"  Días normales:   {temp_normal:.2f}°C")
        print(f"  Días de bloqueo: {temp_bloqueo:.2f}°C")
        print(f"  Diferencia:      {abs(temp_normal - temp_bloqueo):.2f}°C")
        
        # Evaluación
        print("\n" + "="*60)
        print("✅ EVALUACIÓN DE CALIDAD DE DATOS")
        print("="*60)
        
        problemas = []
        
        if len(bloqueos) == 0:
            problemas.append("❌ No hay eventos de bloqueo etiquetados")
        elif len(bloqueos) / len(df) > 0.3:
            problemas.append(f"⚠️  Porcentaje de bloqueos muy alto ({len(bloqueos)/len(df)*100:.1f}%)")
        
        if ratio_precip < 1.3:
            problemas.append(f"⚠️  Precipitación en bloqueos no es mucho mayor ({ratio_precip:.2f}x esperado >1.5x)")
        
        if 'viento' in df.columns and ratio_viento < 1.2:
            problemas.append(f"⚠️  Viento en bloqueos no es mayor ({ratio_viento:.2f}x)")
        
        if problemas:
            print("POSIBLES PROBLEMAS DETECTADOS:")
            for p in problemas:
                print(f"  {p}")
            print("\n🔴 CONCLUSIÓN: Los datos pueden ser SIMULADOS/ALEATORIOS")
            print("   Recomendación: Etiquetar manualmente eventos históricos conocidos")
        else:
            print("✅ Los datos parecen tener eventos REALES")
            print(f"   - Precipitación {ratio_precip:.1f}x mayor en bloqueos")
            if 'viento' in df.columns:
                print(f"   - Viento {ratio_viento:.1f}x mayor en bloqueos")
            print("\n🟢 CONCLUSIÓN: Datos aptos para entrenamiento")
        
        # 5. Estadísticas temporales
        print("\n" + "="*60)
        print("📅 DISTRIBUCIÓN TEMPORAL")
        print("="*60)
        bloqueos_mes = df.groupby('mes')['bloqueo'].agg([
            ('Total', 'sum'),
            ('% del Total', lambda x: x.sum() / len(bloqueos) * 100 if len(bloqueos) > 0 else 0)
        ]).round(2)
        meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        bloqueos_mes.index = [meses[i-1] for i in bloqueos_mes.index]
        print(bloqueos_mes.to_string())
        
    else:
        print("\n❌ ERROR CRÍTICO: No hay eventos de bloqueo (bloqueo=1) en los datos")
        print("   No se puede entrenar el modelo sin eventos etiquetados")
    
    print("\n" + "="*60)
    print("✅ VALIDACIÓN COMPLETADA")
    print("="*60)

if __name__ == "__main__":
    validar_datos_senamhi()
