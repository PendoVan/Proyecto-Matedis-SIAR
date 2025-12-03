"""
Predicción Climática con Random Forest - Versión Mejorada
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from datetime import datetime
import os
import pickle

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
except ImportError:
    print("⚠️  Instala: pip install scikit-learn")


@dataclass
class PrediccionRiesgo:
    fecha: datetime
    probabilidad_lluvia: float
    riesgo_bloqueo: float
    fiabilidad_ajustada: float
    confianza: float
    recomendacion: str
    estacion: str = "General"


class IntegradorSENAMHI:
    
    def __init__(self):
        self.modelo = None
        self.scaler = StandardScaler()
    
    def preparar_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Agrega features temporales"""
        df = df.copy()
        df['dia_año'] = df['fecha'].dt.dayofyear
        df['sin_dia'] = np.sin(2 * np.pi * df['dia_año'] / 365.25)
        df['cos_dia'] = np.cos(2 * np.pi * df['dia_año'] / 365.25)
        df['epoca_lluvias'] = df['mes'].isin([11, 12, 1, 2, 3]).astype(int)
        
        df = df.sort_values('fecha')
        for col in ['precipitacion', 'temperatura']:
            df[f'{col}_ma7'] = df.groupby('estacion')[col].transform(
                lambda x: x.rolling(7, min_periods=1).mean()
            )
        
        df['precip_acum_7d'] = df.groupby('estacion')['precipitacion'].transform(
            lambda x: x.rolling(7, min_periods=1).sum()
        )
        
        return df
    
    def entrenar_modelo(self, ruta_csv: str = "data/clima/senamhi_procesado.csv"):
        """Entrena Random Forest"""
        print("\n" + "="*60)
        print("🌳 ENTRENANDO MODELO CON DATOS REALES")
        print("="*60 + "\n")
        
        df = pd.read_csv(ruta_csv, parse_dates=['fecha'])
        print(f"📊 Datos: {len(df):,} registros")
        
        df = self.preparar_features(df)
        
        features = [
            'temperatura', 'precipitacion', 'humedad', 'presion', 'viento',
            'mes', 'sin_dia', 'cos_dia', 'epoca_lluvias',
            'precipitacion_ma7', 'temperatura_ma7', 'precip_acum_7d'
        ]
        
        df_clean = df.dropna(subset=features + ['bloqueo'])
        X = df_clean[features].values
        y = df_clean['bloqueo'].values
        
        print(f"Bloqueos: {y.sum():,} ({y.mean()*100:.1f}%)\n")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        print("🔄 Entrenando...")
        self.modelo = RandomForestClassifier(
            n_estimators=100, max_depth=10, min_samples_split=20,
            class_weight='balanced', random_state=42, n_jobs=-1
        )
        self.modelo.fit(X_train_scaled, y_train)
        
        y_pred = self.modelo.predict(X_test_scaled)
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        print(f"\n✅ Precisión: {acc*100:.2f}%")
        print(f"   Precision: {prec*100:.2f}%")
        print(f"   Recall: {rec*100:.2f}%")
        print(f"   F1: {f1:.3f}")
        
        print("\n📈 Top 5 features:")
        importancias = sorted(zip(features, self.modelo.feature_importances_),
                            key=lambda x: x[1], reverse=True)
        for i, (feat, imp) in enumerate(importancias[:5], 1):
            print(f"   {i}. {feat}: {imp:.3f}")
        
        return {'accuracy': acc, 'precision': prec, 'recall': rec, 'f1': f1}
    
    def predecir_riesgo(self, temperatura: float, precipitacion: float,
                       humedad: float, presion: float, viento: float,
                       mes: int = None, estacion: str = "General"):
        """Predice riesgo de bloqueo"""
        if self.modelo is None:
            raise ValueError("⚠️  Primero entrena el modelo")
        
        if mes is None:
            mes = datetime.now().month
        
        dia_año = datetime.now().timetuple().tm_yday
        sin_dia = np.sin(2 * np.pi * dia_año / 365.25)
        cos_dia = np.cos(2 * np.pi * dia_año / 365.25)
        epoca_lluvias = int(mes in [11, 12, 1, 2, 3])
        
        X = np.array([[
            temperatura, precipitacion, humedad, presion, viento,
            mes, sin_dia, cos_dia, epoca_lluvias,
            precipitacion, temperatura, precipitacion * 3
        ]])
        
        X_scaled = self.scaler.transform(X)
        prob_bloqueo = float(self.modelo.predict_proba(X_scaled)[0][1])
        
        prob_lluvia = min(1.0, (precipitacion / 30) * (humedad / 100))
        fiab_base = 0.90
        fiab_ajustada = fiab_base * (1 - prob_bloqueo * 0.6)
        
        valores_normales = [
            10 <= temperatura <= 25, precipitacion < 40,
            40 <= humedad <= 90, 700 <= presion <= 800, viento < 18
        ]
        confianza = sum(valores_normales) / len(valores_normales)
        
        if prob_bloqueo > 0.7:
            rec = "🚨 RIESGO CRÍTICO"
        elif prob_bloqueo > 0.5:
            rec = "⛔ RIESGO ALTO"
        elif prob_bloqueo > 0.3:
            rec = "⚠️  RIESGO MODERADO"
        elif prob_bloqueo > 0.15:
            rec = "⚡ RIESGO BAJO"
        else:
            rec = "✅ RIESGO MÍNIMO"
        
        return PrediccionRiesgo(
            fecha=datetime.now(),
            probabilidad_lluvia=prob_lluvia,
            riesgo_bloqueo=prob_bloqueo,
            fiabilidad_ajustada=fiab_ajustada,
            confianza=confianza,
            recomendacion=rec,
            estacion=estacion
        )
    
    def predecir_riesgo_por_fecha(self, departamento: str, fecha_salida: datetime,
                                   ruta_csv: str = "data/clima/senamhi_procesado.csv") -> float:
        """
        Predice riesgo de bloqueo para una fecha específica.
        
        Args:
            departamento: Nombre del departamento
            fecha_salida: Fecha de salida (datetime object)
            ruta_csv: Ruta al archivo CSV con datos históricos
            
        Returns:
            float: Probabilidad de bloqueo (0.0 a 1.0)
        """
        if self.modelo is None:
            raise ValueError("⚠️  Primero entrena o carga el modelo")
        
        # Extraer mes y día del año de la fecha de salida
        mes = fecha_salida.month
        dia_año = fecha_salida.timetuple().tm_yday
        
        # Calcular features temporales
        sin_dia = np.sin(2 * np.pi * dia_año / 365.25)
        cos_dia = np.cos(2 * np.pi * dia_año / 365.25)
        epoca_lluvias = int(mes in [11, 12, 1, 2, 3])
        
        try:
            # Cargar datos históricos y obtener promedio mensual
            df = pd.read_csv(ruta_csv, parse_dates=['fecha'])
            
            # Filtrar por departamento si existe la columna
            if 'departamento' in df.columns or 'estacion' in df.columns:
                col_dept = 'departamento' if 'departamento' in df.columns else 'estacion'
                df_dept = df[df[col_dept].str.contains(departamento, case=False, na=False)]
                if len(df_dept) == 0:
                    # Si no hay datos del departamento, usar promedio general
                    df_dept = df
            else:
                df_dept = df
            
            # Filtrar por mes y calcular promedios
            df_dept['mes'] = pd.to_datetime(df_dept['fecha']).dt.month
            df_mes = df_dept[df_dept['mes'] == mes]
            
            if len(df_mes) > 0:
                # Usar promedios del mes específico
                temperatura = df_mes['temperatura'].mean()
                precipitacion = df_mes['precipitacion'].mean()
                humedad = df_mes['humedad'].mean()
                presion = df_mes['presion'].mean() if 'presion' in df_mes.columns else 750
                viento = df_mes['viento'].mean() if 'viento' in df_mes.columns else 5
            else:
                # Fallback: usar valores neutros
                temperatura = 18
                precipitacion = 10
                humedad = 70
                presion = 750
                viento = 5
                
        except Exception as e:
            print(f"⚠️  No se pudieron cargar datos históricos: {e}")
            print(f"   Usando valores por defecto para el mes {mes}")
            # Valores por defecto según época del año
            if epoca_lluvias:
                temperatura = 16
                precipitacion = 25
                humedad = 85
            else:
                temperatura = 20
                precipitacion = 5
                humedad = 65
            presion = 750
            viento = 8
        
        # Construir vector de features (debe coincidir con el entrenamiento)
        # Features: temperatura, precipitacion, humedad, presion, viento,
        #           mes, sin_dia, cos_dia, epoca_lluvias,
        #           precipitacion_ma7, temperatura_ma7, precip_acum_7d
        X = np.array([[
            temperatura,
            precipitacion,
            humedad,
            presion,
            viento,
            mes,
            sin_dia,
            cos_dia,
            epoca_lluvias,
            precipitacion,  # Aproximación: usar mismo valor para MA7
            temperatura,    # Aproximación: usar mismo valor para MA7
            precipitacion * 3  # Aproximación: acumulado 7 días
        ]])
        
        # Escalar y predecir
        X_scaled = self.scaler.transform(X)
        prob_bloqueo = float(self.modelo.predict_proba(X_scaled)[0][1])
        
        return prob_bloqueo
    
    def guardar_modelo(self, ruta: str = "data/modelos"):
        """Guarda modelo"""
        os.makedirs(ruta, exist_ok=True)
        with open(f"{ruta}/modelo_rf.pkl", 'wb') as f:
            pickle.dump(self.modelo, f)
        with open(f"{ruta}/scaler.pkl", 'wb') as f:
            pickle.dump(self.scaler, f)
        print(f"💾 Guardado en: {ruta}/")
    
    def cargar_modelo(self, ruta: str = "data/modelos"):
        """Carga modelo"""
        try:
            with open(f"{ruta}/modelo_rf.pkl", 'rb') as f:
                self.modelo = pickle.load(f)
            with open(f"{ruta}/scaler.pkl", 'rb') as f:
                self.scaler = pickle.load(f)
            print(f"✅ Modelo cargado")
            return True
        except:
            print(f"⚠️  No hay modelo entrenado")
            return False


if __name__ == "__main__":
    print("="*60)
    print("🌦️  ENTRENANDO PREDICTOR CLIMÁTICO")
    print("="*60 + "\n")
    
    predictor = IntegradorSENAMHI()
    predictor.entrenar_modelo()
    predictor.guardar_modelo()
    
    print("\n" + "="*60)
    print("🔮 PROBANDO PREDICCIONES")
    print("="*60 + "\n")
    
    # Día normal
    p1 = predictor.predecir_riesgo(17.2, 5.8, 75, 750, 5)
    print(f"☀️  Normal: {p1.riesgo_bloqueo*100:.1f}% - {p1.recomendacion}")
    
    # Lluvia
    p2 = predictor.predecir_riesgo(15, 20, 85, 745, 10)
    print(f"🌧️  Lluvia: {p2.riesgo_bloqueo*100:.1f}% - {p2.recomendacion}")
    
    # Tormenta
    p3 = predictor.predecir_riesgo(10, 40, 95, 740, 18)
    print(f"⛈️  Tormenta: {p3.riesgo_bloqueo*100:.1f}% - {p3.recomendacion}")
    
    print("\n✅ Listo! Ahora tu interfaz puede usar el modelo")