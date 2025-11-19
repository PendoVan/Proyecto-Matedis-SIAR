"""
Procesador de datos reales SENAMHI
Convierte archivos .txt a CSV para entrenamiento
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import os

class ProcesadorSENAMHI:
    
    ESTACIONES = {
        # San Martín
        "qc00000310": {"nombre": "El Porvenir", "departamento": "San Martin"},

        # Cajamarca
        "qc00000352": {"nombre": "Cutervo", "departamento": "Cajamarca"},

        # Lima
        "qc00000543": {"nombre": "San Juan de Lurigancho", "departamento": "Lima"},
        
        # Cusco
        "qc00000607": {"nombre": "Granja Kcayra", "departamento": "Cusco"},

        # Junín
        "qc00000608": {"nombre": "Visques", "departamento": "Junín"},
        
        # Puno
        "qc00000708": {"nombre": "Puno", "departamento": "Puno"},
        
        # Arequipa
        "qc00000839": {"nombre": "La Pampilla", "departamento": "Arequipa"},
        
        # Amazonas
        "qc00152210": {"nombre": "Magunchal", "departamento": "Amazonas"},
        
        # Ayacucho
        "qc00156211": {"nombre": "Vilcashuaman", "departamento": "Ayacucho"},
    }
    
    def leer_archivo_senamhi(self, ruta_archivo: str) -> pd.DataFrame:
        """Lee archivo .txt del SENAMHI"""
        print(f"📂 Leyendo: {Path(ruta_archivo).name}")
        
        nombre_archivo = Path(ruta_archivo).stem
        info_estacion = self.ESTACIONES.get(nombre_archivo, {
            "nombre": nombre_archivo, 
            "departamento": "Desconocido"
        })
        
        datos = []
        with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
            for linea in f:
                partes = linea.strip().split()
                if len(partes) >= 6:
                    try:
                        año, mes, dia = int(partes[0]), int(partes[1]), int(partes[2])
                        precipitacion = float(partes[3])
                        temp_max = float(partes[4])
                        temp_min = float(partes[5])
                        
                        # Filtrar datos faltantes
                        if temp_max == -99.9 or temp_min == -99.9:
                            continue
                        
                        fecha = datetime(año, mes, dia)
                        temp_promedio = (temp_max + temp_min) / 2
                        
                        datos.append({
                            'fecha': fecha,
                            'año': año,
                            'mes': mes,
                            'temperatura': temp_promedio,
                            'precipitacion': max(0, precipitacion),
                            'estacion': info_estacion['nombre'],
                            'departamento': info_estacion['departamento']
                        })
                    except (ValueError, IndexError):
                        continue
        
        return pd.DataFrame(datos)
    
    def estimar_variables(self, df: pd.DataFrame) -> pd.DataFrame:
        """Estima humedad, presión, viento y calcula bloqueo"""
        df = df.copy()
        
        # Humedad (más con lluvia, menos con calor)
        df['humedad'] = 50 + (df['precipitacion'] * 2) + ((20 - df['temperatura']) * 1.5)
        df['humedad'] = df['humedad'].clip(20, 100)
        
        # Presión (aproximación por altitud sierra)
        df['presion'] = 750 + np.random.normal(0, 5, len(df))
        
        # Viento (más en época seca)
        es_epoca_lluvias = df['mes'].isin([11, 12, 1, 2, 3])
        df['viento'] = np.where(es_epoca_lluvias, 
                                np.random.exponential(4, len(df)),
                                np.random.exponential(6, len(df)))
        df['viento'] = df['viento'].clip(0, 25)
        
        # Variable objetivo: bloqueo (basado en condiciones extremas)
        df['bloqueo'] = ((df['precipitacion'] > 25) | 
                         (df['temperatura'] < 5) | 
                         (df['viento'] > 15)).astype(int)
        
        return df
    
    def procesar_multiples(self, directorio: str) -> pd.DataFrame:
        """Procesa todos los .txt en un directorio"""
        print(f"\n{'='*60}")
        print("📊 PROCESANDO DATOS SENAMHI")
        print(f"{'='*60}\n")
        print(f"Buscando en: {directorio}\n")
        
        # Buscar archivos .txt
        ruta = Path(directorio)
        if not ruta.exists():
            print(f"❌ ERROR: La carpeta {directorio} no existe")
            print(f"\nCrea la carpeta y pon ahí tus archivos .txt del SENAMHI")
            return pd.DataFrame()
        
        archivos = list(ruta.glob("*.txt"))
        
        if not archivos:
            print(f"❌ No se encontraron archivos .txt en {directorio}")
            print(f"\nVerifica que:")
            print(f"  1. Los archivos estén en la carpeta correcta")
            print(f"  2. Tengan extensión .txt")
            print(f"  3. La ruta sea correcta")
            return pd.DataFrame()
        
        print(f"✅ Encontrados {len(archivos)} archivos\n")
        
        dataframes = []
        for archivo in archivos:
            try:
                df = self.leer_archivo_senamhi(str(archivo))
                if not df.empty:
                    df = self.estimar_variables(df)
                    dataframes.append(df)
                    print(f"  ✅ {len(df):,} registros - {df['estacion'].iloc[0]}")
                else:
                    print(f"  ⚠️  {archivo.name}: Sin datos válidos")
            except Exception as e:
                print(f"  ❌ Error en {archivo.name}: {e}")
        
        if not dataframes:
            print(f"\n❌ No se pudo procesar ningún archivo")
            return pd.DataFrame()
        
        df_completo = pd.concat(dataframes, ignore_index=True)
        df_completo = df_completo.sort_values('fecha').reset_index(drop=True)
        
        print(f"\n{'='*60}")
        print(f"✅ TOTAL: {len(df_completo):,} registros procesados")
        print(f"   Fechas: {df_completo['fecha'].min()} a {df_completo['fecha'].max()}")
        print(f"   Estaciones: {df_completo['estacion'].nunique()}")
        print(f"   Departamentos: {', '.join(df_completo['departamento'].unique())}")
        print(f"   Bloqueos: {df_completo['bloqueo'].sum():,} ({df_completo['bloqueo'].mean()*100:.1f}%)")
        print(f"{'='*60}\n")
        
        return df_completo
    
    def guardar(self, df: pd.DataFrame, ruta_salida: str):
        """Guarda el DataFrame procesado"""
        os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
        df.to_csv(ruta_salida, index=False, encoding='utf-8')
        print(f"💾 Guardado en: {ruta_salida}")
        print(f"   Tamaño: {os.path.getsize(ruta_salida) / 1024:.1f} KB\n")


if __name__ == "__main__":
    # Ejecutar procesamiento
    procesador = ProcesadorSENAMHI()
    
    directorio = "data/raw/senamhi"  
    
    df = procesador.procesar_multiples(directorio)
    
    if not df.empty:
        # Guardar datos procesados
        procesador.guardar(df, "data/clima/senamhi_procesado.csv")
        print("✅ ¡Listo! Ahora puedes entrenar el modelo con:")
        print("   python src/unidad3_grafos/prediccion_climatica.py")
    else:
        print("\n💡 Pasos para solucionar:")
        print("   1. Crea la carpeta: data/raw/senamhi")
        print("   2. Copia ahí tus archivos .txt del SENAMHI")
        print("   3. Ejecuta de nuevo este script")