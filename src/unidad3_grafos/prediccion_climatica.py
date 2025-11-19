"""
Módulo: prediccion_climatica.py
Descripción: Integración con datos SENAMHI (Servicio Nacional de Meteorología 
e Hidrología del Perú) para predicción climática usando redes neuronales.

Predice:
- Probabilidad de lluvia intensa
- Riesgo de bloqueo de carreteras
- Fiabilidad de rutas según condiciones climáticas

Instalación requerida:
pip install pandas numpy scikit-learn tensorflow requests
"""

import numpy as np # type: ignore
import pandas as pd # type: ignore
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os

# Para la red neuronal
try:
    from sklearn.preprocessing import StandardScaler # type: ignore
    from sklearn.model_selection import train_test_split # type: ignore
    import tensorflow as tf # type: ignore
    from tensorflow import keras # type: ignore
    from tensorflow.keras import layers # type: ignore
except ImportError:
    print("⚠️  Instala: pip install tensorflow scikit-learn")


@dataclass
class DatoClimatico:
    """Representa una observación climática."""
    fecha: datetime
    temperatura: float  # °C
    precipitacion: float  # mm
    humedad: float  # %
    presion: float  # hPa
    viento: float  # m/s
    estacion: str
    
    def to_dict(self) -> Dict:
        return {
            'fecha': self.fecha.isoformat(),
            'temperatura': self.temperatura,
            'precipitacion': self.precipitacion,
            'humedad': self.humedad,
            'presion': self.presion,
            'viento': self.viento,
            'estacion': self.estacion
        }


@dataclass
class PrediccionRiesgo:
    """Resultado de la predicción de riesgo."""
    fecha: datetime
    probabilidad_lluvia: float  # 0-1
    riesgo_bloqueo: float  # 0-1
    fiabilidad_ajustada: float  # 0-1
    confianza: float  # 0-1
    recomendacion: str


class IntegradorSENAMHI:
    """
    Integra datos climáticos del SENAMHI para mejorar predicciones de rutas.
    """
    
    # Estaciones SENAMHI en Ayacucho (ejemplos)
    ESTACIONES = {
        "Ayacucho": {"codigo": "000401", "lat": -13.16, "lon": -74.22},
        "Huanta": {"codigo": "000402", "lat": -12.94, "lon": -74.25},
        "San Miguel": {"codigo": "000403", "lat": -13.01, "lon": -73.98}
    }
    
    def __init__(self):
        self.datos_historicos = []
        self.scaler = StandardScaler()
        self.modelo = None
    
    def generar_datos_simulados(self, dias: int = 365) -> pd.DataFrame:
        """
        Genera datos climáticos simulados para entrenamiento.
        En producción, estos datos vendrían del API de SENAMHI.
        
        Args:
            dias: Número de días de datos a generar
        """
        print(f"🌦️  Generando {dias} días de datos climáticos simulados...")
        
        fechas = [datetime.now() - timedelta(days=x) for x in range(dias)]
        
        datos = []
        for fecha in fechas:
            # Simular patrones estacionales (época de lluvias Nov-Marzo)
            mes = fecha.month
            es_epoca_lluvias = mes in [11, 12, 1, 2, 3]
            
            # Generar datos con distribuciones realistas
            temperatura = np.random.normal(
                18 if es_epoca_lluvias else 22, 
                3
            )
            
            precipitacion = np.random.exponential(
                15 if es_epoca_lluvias else 2
            )
            
            humedad = np.random.normal(
                75 if es_epoca_lluvias else 55,
                10
            )
            
            presion = np.random.normal(1010, 5)
            viento = np.random.exponential(3)
            
            # Determinar si hubo bloqueo (basado en condiciones extremas)
            bloqueo = int(
                (precipitacion > 25) or 
                (viento > 15) or
                (temperatura < 5)
            )
            
            datos.append({
                'fecha': fecha,
                'temperatura': temperatura,
                'precipitacion': precipitacion,
                'humedad': humedad,
                'presion': presion,
                'viento': viento,
                'bloqueo': bloqueo,
                'estacion': 'Ayacucho'
            })
        
        df = pd.DataFrame(datos)
        print(f"✅ Datos generados: {len(df)} registros")
        print(f"   Bloqueos: {df['bloqueo'].sum()} ({df['bloqueo'].mean()*100:.1f}%)")
        
        return df
    
    def descargar_datos_senamhi(self, estacion: str, 
                                fecha_inicio: str, 
                                fecha_fin: str) -> pd.DataFrame:
        """
        Descarga datos reales del SENAMHI.
        
        NOTA: El SENAMHI no tiene una API pública oficial.
        En producción usarías web scraping o datos descargados manualmente.
        
        Args:
            estacion: Código de estación
            fecha_inicio: Fecha inicio (YYYY-MM-DD)
            fecha_fin: Fecha fin (YYYY-MM-DD)
        """
        print(f"⚠️  SENAMHI no tiene API pública oficial.")
        print(f"   Opciones:")
        print(f"   1. Descargar datos desde: https://www.senamhi.gob.pe/")
        print(f"   2. Usar datos simulados para el prototipo")
        print(f"   3. Implementar web scraping (requiere permisos)")
        
        # Por ahora, usar datos simulados
        return self.generar_datos_simulados()
    
    def cargar_datos_csv(self, ruta_archivo: str) -> pd.DataFrame:
        """
        Carga datos climáticos desde un CSV.
        Formato esperado: fecha,temperatura,precipitacion,humedad,presion,viento,bloqueo
        """
        try:
            df = pd.read_csv(ruta_archivo, parse_dates=['fecha'])
            print(f"✅ Datos cargados desde: {ruta_archivo}")
            print(f"   Registros: {len(df)}")
            return df
        except FileNotFoundError:
            print(f"⚠️  Archivo {ruta_archivo} no encontrado")
            print(f"   Generando datos simulados...")
            return self.generar_datos_simulados()
    
    def preparar_datos_entrenamiento(self, df: pd.DataFrame) -> Tuple:
        """
        Prepara datos para entrenar la red neuronal.
        
        Returns:
            (X_train, X_test, y_train, y_test)
        """
        print("🔄 Preparando datos para entrenamiento...")
        
        # Features (variables independientes)
        features = ['temperatura', 'precipitacion', 'humedad', 'presion', 'viento']
        X = df[features].values
        
        # Target (variable a predecir: bloqueo sí/no)
        y = df['bloqueo'].values
        
        # Normalizar features
        X_scaled = self.scaler.fit_transform(X)
        
        # Dividir en entrenamiento y prueba (80-20)
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        print(f"✅ Datos preparados:")
        print(f"   Entrenamiento: {len(X_train)} muestras")
        print(f"   Prueba: {len(X_test)} muestras")
        
        return X_train, X_test, y_train, y_test
    
    def crear_modelo_red_neuronal(self, input_dim: int = 5) -> keras.Model:
        """
        Crea una red neuronal simple para predicción de bloqueos.
        
        Arquitectura:
        - Capa de entrada: 5 neuronas (temperatura, precipitación, etc.)
        - Capa oculta 1: 16 neuronas + ReLU + Dropout
        - Capa oculta 2: 8 neuronas + ReLU + Dropout
        - Capa de salida: 1 neurona + Sigmoid (probabilidad 0-1)
        """
        print("🧠 Creando red neuronal...")
        
        modelo = keras.Sequential([
            # Capa de entrada
            layers.Dense(16, activation='relu', input_dim=input_dim),
            layers.Dropout(0.2),
            
            # Capa oculta
            layers.Dense(8, activation='relu'),
            layers.Dropout(0.2),
            
            # Capa de salida
            layers.Dense(1, activation='sigmoid')
        ])
        
        # Compilar modelo
        modelo.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy', 'AUC']
        )
        
        print("✅ Modelo creado")
        modelo.summary()
        
        return modelo
    
    def entrenar_modelo(self, df: pd.DataFrame, 
                       epochs: int = 50,
                       batch_size: int = 32) -> Dict:
        """
        Entrena la red neuronal con datos históricos.
        
        Returns:
            Diccionario con métricas de entrenamiento
        """
        print("\n" + "="*60)
        print("🎓 ENTRENANDO RED NEURONAL")
        print("="*60 + "\n")
        
        # Preparar datos
        X_train, X_test, y_train, y_test = self.preparar_datos_entrenamiento(df)
        
        # Crear modelo
        self.modelo = self.crear_modelo_red_neuronal()
        
        # Entrenar
        print("\n🔄 Entrenando modelo...")
        history = self.modelo.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=1
        )
        
        # Evaluar en datos de prueba
        print("\n📊 Evaluando en datos de prueba...")
        loss, accuracy, auc = self.modelo.evaluate(X_test, y_test, verbose=0)
        
        print(f"\n✅ Entrenamiento completado:")
        print(f"   Precisión: {accuracy*100:.2f}%")
        print(f"   AUC: {auc:.3f}")
        print(f"   Loss: {loss:.4f}")
        
        return {
            'accuracy': accuracy,
            'auc': auc,
            'loss': loss,
            'history': history.history
        }
    
    def predecir_riesgo(self, temperatura: float, precipitacion: float,
                       humedad: float, presion: float, viento: float) -> PrediccionRiesgo:
        """
        Predice el riesgo de bloqueo dadas las condiciones climáticas.
        
        Args:
            temperatura: Temperatura en °C
            precipitacion: Precipitación en mm
            humedad: Humedad relativa en %
            presion: Presión atmosférica en hPa
            viento: Velocidad del viento en m/s
            
        Returns:
            PrediccionRiesgo con probabilidades y recomendaciones
        """
        if self.modelo is None:
            raise ValueError("Primero debes entrenar el modelo")
        
        # Preparar datos de entrada
        X = np.array([[temperatura, precipitacion, humedad, presion, viento]])
        X_scaled = self.scaler.transform(X)
        
        # Predecir
        probabilidad_bloqueo = float(self.modelo.predict(X_scaled, verbose=0)[0][0])
        
        # Calcular probabilidad de lluvia basada en precipitación y humedad
        prob_lluvia = min(1.0, (precipitacion / 25) * (humedad / 100))
        
        # Calcular fiabilidad ajustada (reduce con riesgo de bloqueo)
        fiabilidad_base = 0.85
        fiabilidad_ajustada = fiabilidad_base * (1 - probabilidad_bloqueo * 0.5)
        
        # Confianza de la predicción (basada en cuán extremos son los valores)
        valores_normales = [
            abs(temperatura - 20) < 10,
            precipitacion < 50,
            abs(humedad - 65) < 30,
            abs(presion - 1010) < 20,
            viento < 20
        ]
        confianza = sum(valores_normales) / len(valores_normales)
        
        # Generar recomendación
        if probabilidad_bloqueo > 0.7:
            recomendacion = "⛔ ALTO RIESGO: Evitar viaje si es posible"
        elif probabilidad_bloqueo > 0.4:
            recomendacion = "⚠️  RIESGO MODERADO: Considerar ruta alternativa"
        elif probabilidad_bloqueo > 0.2:
            recomendacion = "⚡ RIESGO BAJO: Viajar con precaución"
        else:
            recomendacion = "✅ RIESGO MÍNIMO: Condiciones favorables"
        
        return PrediccionRiesgo(
            fecha=datetime.now(),
            probabilidad_lluvia=prob_lluvia,
            riesgo_bloqueo=probabilidad_bloqueo,
            fiabilidad_ajustada=fiabilidad_ajustada,
            confianza=confianza,
            recomendacion=recomendacion
        )
    
    def guardar_modelo(self, ruta: str = "data/modelos/prediccion_clima.h5"):
        """Guarda el modelo entrenado."""
        if self.modelo is None:
            print("⚠️  No hay modelo para guardar")
            return
        
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        self.modelo.save(ruta)
        
        # Guardar también el scaler
        import pickle
        scaler_path = ruta.replace('.h5', '_scaler.pkl')
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        print(f"✅ Modelo guardado en: {ruta}")
    
    def cargar_modelo(self, ruta: str = "data/modelos/prediccion_clima.h5"):
        """Carga un modelo previamente entrenado."""
        try:
            self.modelo = keras.models.load_model(ruta)
            
            # Cargar scaler
            import pickle
            scaler_path = ruta.replace('.h5', '_scaler.pkl')
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            
            print(f"✅ Modelo cargado desde: {ruta}")
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    print("="*70)
    print("🌦️  PREDICCIÓN CLIMÁTICA CON RED NEURONAL")
    print("="*70 + "\n")
    
    integrador = IntegradorSENAMHI()
    
    # 1. Generar/cargar datos
    print("📊 Paso 1: Obtener datos climáticos\n")
    df = integrador.generar_datos_simulados(dias=730)  # 2 años
    
    # Guardar datos para referencia
    os.makedirs("data/clima", exist_ok=True)
    df.to_csv("data/clima/datos_simulados.csv", index=False)
    print(f"💾 Datos guardados en: data/clima/datos_simulados.csv\n")
    
    # 2. Entrenar modelo
    print("🎓 Paso 2: Entrenar red neuronal\n")
    metricas = integrador.entrenar_modelo(df, epochs=30)
    
    # 3. Guardar modelo
    integrador.guardar_modelo()
    
    # 4. Hacer predicciones
    print("\n" + "="*70)
    print("🔮 EJEMPLOS DE PREDICCIÓN")
    print("="*70 + "\n")
    
    # Escenario 1: Condiciones normales
    print("📍 Escenario 1: Día soleado normal")
    pred1 = integrador.predecir_riesgo(
        temperatura=22,
        precipitacion=0,
        humedad=60,
        presion=1013,
        viento=5
    )
    print(f"   Riesgo de bloqueo: {pred1.riesgo_bloqueo*100:.1f}%")
    print(f"   Fiabilidad de ruta: {pred1.fiabilidad_ajustada*100:.1f}%")
    print(f"   {pred1.recomendacion}\n")
    
    # Escenario 2: Lluvia intensa
    print("📍 Escenario 2: Lluvia intensa")
    pred2 = integrador.predecir_riesgo(
        temperatura=15,
        precipitacion=35,
        humedad=95,
        presion=1005,
        viento=12
    )
    print(f"   Riesgo de bloqueo: {pred2.riesgo_bloqueo*100:.1f}%")
    print(f"   Fiabilidad de ruta: {pred2.fiabilidad_ajustada*100:.1f}%")
    print(f"   {pred2.recomendacion}\n")
    
    # Escenario 3: Condiciones extremas
    print("📍 Escenario 3: Tormenta severa")
    pred3 = integrador.predecir_riesgo(
        temperatura=8,
        precipitacion=50,
        humedad=98,
        presion=995,
        viento=20
    )
    print(f"   Riesgo de bloqueo: {pred3.riesgo_bloqueo*100:.1f}%")
    print(f"   Fiabilidad de ruta: {pred3.fiabilidad_ajustada*100:.1f}%")
    print(f"   {pred3.recomendacion}\n")
    
    print("="*70)
    print("✅ DEMOSTRACIÓN COMPLETADA")
    print("="*70)