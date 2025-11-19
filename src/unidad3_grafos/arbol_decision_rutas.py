"""
Módulo: arbol_decision_rutas.py
Descripción: Clasificador de rutas usando Árbol de Decisión.
Clasifica rutas como: SEGURA, MODERADA, PELIGROSA

Fundamento Matemático:
- Árbol de Decisión (CART): Classification and Regression Trees
- Criterio de división: Gini o Entropía
- Ventaja: Interpretable, visualizable
"""

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
from typing import Dict, List
import os


class ClasificadorRutas:
    """
    Clasifica rutas en categorías de seguridad usando árbol de decisión.
    
    Características (features):
    - Precipitación (mm)
    - Temperatura (°C)
    - Tipo de camino (0=herradura, 1=trocha, 2=afirmado, 3=asfaltado)
    - Mes del año (1-12)
    - Riesgo histórico (0-1)
    - Hora del día (0-23)
    
    Clases:
    - 0: SEGURA (fiabilidad > 80%)
    - 1: MODERADA (fiabilidad 60-80%)
    - 2: PELIGROSA (fiabilidad < 60%)
    """
    
    def __init__(self, max_depth=5):
        self.modelo = DecisionTreeClassifier(
            max_depth=max_depth,
            criterion='gini',
            random_state=42
        )
        self.feature_names = [
            'precipitacion_mm',
            'temperatura_c',
            'tipo_camino',
            'mes',
            'riesgo_historico',
            'hora'
        ]
        self.class_names = ['SEGURA', 'MODERADA', 'PELIGROSA']
        self.entrenado = False
    
    def generar_datos_entrenamiento(self, n_samples=2000):
        """
        Genera datos sintéticos para entrenamiento.
        En producción usarías datos históricos reales.
        """
        np.random.seed(42)
        
        datos = []
        
        for _ in range(n_samples):
            # Generar características
            mes = np.random.randint(1, 13)
            es_epoca_lluvias = mes in [11, 12, 1, 2, 3]
            
            precipitacion = np.random.exponential(15 if es_epoca_lluvias else 3)
            temperatura = np.random.normal(18 if es_epoca_lluvias else 22, 4)
            tipo_camino = np.random.choice([0, 1, 2, 3], p=[0.1, 0.3, 0.4, 0.2])
            riesgo_historico = np.random.beta(2, 5)  # Más valores bajos
            hora = np.random.randint(0, 24)
            
            # Determinar clase basada en reglas lógicas
            fiabilidad_base = [0.5, 0.65, 0.8, 0.95][tipo_camino]
            
            # Ajustar por clima
            if precipitacion > 30:
                fiabilidad_base *= 0.6
            elif precipitacion > 15:
                fiabilidad_base *= 0.8
            
            if temperatura < 5 or temperatura > 35:
                fiabilidad_base *= 0.85
            
            if riesgo_historico > 0.5:
                fiabilidad_base *= 0.7
            
            # Hora de riesgo (noche)
            if hora < 6 or hora > 20:
                fiabilidad_base *= 0.9
            
            # Clasificar
            if fiabilidad_base > 0.8:
                clase = 0  # SEGURA
            elif fiabilidad_base > 0.6:
                clase = 1  # MODERADA
            else:
                clase = 2  # PELIGROSA
            
            datos.append([precipitacion, temperatura, tipo_camino, 
                         mes, riesgo_historico, hora, clase])
        
        df = pd.DataFrame(datos, columns=self.feature_names + ['clase'])
        
        print(f"📊 Datos generados: {len(df)} muestras")
        print(f"\nDistribución de clases:")
        for i, nombre in enumerate(self.class_names):
            count = (df['clase'] == i).sum()
            pct = count / len(df) * 100
            print(f"   {nombre:10s}: {count:4d} ({pct:5.1f}%)")
        
        return df
    
    def entrenar(self, X, y):
        """
        Entrena el árbol de decisión.
        
        Args:
            X: Features (N x 6)
            y: Clases (N,)
        """
        print("\n🌳 Entrenando árbol de decisión...\n")
        
        # Dividir datos
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Entrenar
        self.modelo.fit(X_train, y_train)
        self.entrenado = True
        
        # Evaluar
        y_pred = self.modelo.predict(X_test)
        accuracy = (y_pred == y_test).mean()
        
        print(f"✅ Entrenamiento completado")
        print(f"   Precisión en test: {accuracy:.2%}\n")
        
        # Reporte detallado
        print("📈 Reporte de clasificación:\n")
        print(classification_report(y_test, y_pred, 
                                   target_names=self.class_names,
                                   zero_division=0))
        
        # Matriz de confusión
        cm = confusion_matrix(y_test, y_pred)
        print("\n🎯 Matriz de confusión:")
        print(f"{'':15s} {'Pred SEGURA':>12s} {'Pred MODERADA':>14s} {'Pred PELIGROSA':>15s}")
        for i, nombre in enumerate(self.class_names):
            print(f"Real {nombre:9s} {cm[i][0]:12d} {cm[i][1]:14d} {cm[i][2]:15d}")
        
        return accuracy
    
    def predecir(self, precipitacion, temperatura, tipo_camino, 
                mes, riesgo_historico, hora):
        """
        Predice la clase de seguridad de una ruta.
        
        Returns:
            (clase_numerica, nombre_clase, probabilidades)
        """
        if not self.entrenado:
            raise ValueError("Modelo no entrenado")
        
        X = np.array([[precipitacion, temperatura, tipo_camino, 
                      mes, riesgo_historico, hora]])
        
        clase = self.modelo.predict(X)[0]
        probas = self.modelo.predict_proba(X)[0]
        
        return int(clase), self.class_names[clase], probas
    
    def obtener_reglas(self):
        """Extrae las reglas del árbol en texto."""
        if not self.entrenado:
            raise ValueError("Modelo no entrenado")
        
        reglas = export_text(self.modelo, feature_names=self.feature_names)
        return reglas
    
    def visualizar_arbol(self, guardar_en="data/visualizaciones/arbol_decision.png"):
        """Visualiza el árbol de decisión."""
        if not self.entrenado:
            raise ValueError("Modelo no entrenado")
        
        plt.figure(figsize=(20, 10))
        plot_tree(
            self.modelo,
            feature_names=self.feature_names,
            class_names=self.class_names,
            filled=True,
            rounded=True,
            fontsize=10
        )
        
        os.makedirs(os.path.dirname(guardar_en), exist_ok=True)
        plt.savefig(guardar_en, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"🎨 Árbol visualizado guardado en: {guardar_en}")
    
    def importancia_features(self):
        """Muestra la importancia de cada característica."""
        if not self.entrenado:
            raise ValueError("Modelo no entrenado")
        
        importancias = self.modelo.feature_importances_
        
        print("\n📊 IMPORTANCIA DE CARACTERÍSTICAS:\n")
        
        features_ordenadas = sorted(
            zip(self.feature_names, importancias),
            key=lambda x: x[1],
            reverse=True
        )
        
        for feature, importancia in features_ordenadas:
            barra = '█' * int(importancia * 50)
            print(f"   {feature:20s} {importancia:6.3f} {barra}")


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    print("="*70)
    print("🌳 CLASIFICADOR DE RUTAS CON ÁRBOL DE DECISIÓN")
    print("="*70 + "\n")
    
    # 1. Crear clasificador
    clasificador = ClasificadorRutas(max_depth=5)
    
    # 2. Generar datos de entrenamiento
    df = clasificador.generar_datos_entrenamiento(n_samples=3000)
    
    X = df[clasificador.feature_names].values
    y = df['clase'].values
    
    # 3. Entrenar
    accuracy = clasificador.entrenar(X, y)
    
    # 4. Mostrar reglas
    print("\n" + "="*70)
    print("📋 REGLAS DEL ÁRBOL DE DECISIÓN")
    print("="*70 + "\n")
    reglas = clasificador.obtener_reglas()
    print(reglas)
    
    # 5. Importancia de características
    clasificador.importancia_features()
    
    # 6. Visualizar árbol
    try:
        clasificador.visualizar_arbol()
    except Exception as e:
        print(f"\n⚠️  No se pudo visualizar árbol: {e}")
        print("   (Requiere matplotlib instalado)")
    
    # 7. Ejemplos de predicción
    print("\n" + "="*70)
    print("🔮 EJEMPLOS DE PREDICCIÓN")
    print("="*70 + "\n")
    
    escenarios = [
        {
            'nombre': 'Día soleado en carretera asfaltada',
            'datos': (0, 22, 3, 7, 0.1, 14),  # precip, temp, tipo, mes, riesgo, hora
            'emoji': '☀️'
        },
        {
            'nombre': 'Lluvia intensa en trocha',
            'datos': (40, 16, 1, 2, 0.4, 20),
            'emoji': '🌧️'
        },
        {
            'nombre': 'Noche fría en camino afirmado',
            'datos': (5, 3, 2, 6, 0.25, 2),
            'emoji': '🌙'
        },
        {
            'nombre': 'Tormenta en época de lluvias',
            'datos': (55, 15, 1, 1, 0.6, 18),
            'emoji': '⛈️'
        }
    ]
    
    for escenario in escenarios:
        clase_num, clase_nombre, probas = clasificador.predecir(*escenario['datos'])
        
        print(f"{escenario['emoji']} {escenario['nombre']}")
        print(f"   Clasificación: {clase_nombre}")
        print(f"   Probabilidades:")
        for i, nombre in enumerate(clasificador.class_names):
            print(f"      {nombre:10s}: {probas[i]*100:5.1f}%")
        print()
    
    print("="*70)
    print("✅ DEMOSTRACIÓN COMPLETADA")
    print("="*70)