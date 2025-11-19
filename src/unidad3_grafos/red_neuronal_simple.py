"""
Módulo: red_neuronal_simple.py
Descripción: Red neuronal simple implementada desde cero con NumPy.
Alternativa ligera a TensorFlow para predicción de bloqueos.

SOLO requiere: pip install numpy pandas
"""

import numpy as np # type: ignore
import pandas as pd # type: ignore
from typing import Tuple, List
from datetime import datetime, timedelta
import json
import os


class RedNeuronalSimple:
    """
    Red neuronal feedforward implementada con NumPy puro.
    Arquitectura: 5 → 8 → 4 → 1
    """
    
    def __init__(self, input_size=5, hidden_size1=8, hidden_size2=4):
        """Inicializa pesos aleatorios."""
        # Pesos capa 1
        self.W1 = np.random.randn(input_size, hidden_size1) * 0.5
        self.b1 = np.zeros((1, hidden_size1))
        
        # Pesos capa 2
        self.W2 = np.random.randn(hidden_size1, hidden_size2) * 0.5
        self.b2 = np.zeros((1, hidden_size2))
        
        # Pesos capa 3
        self.W3 = np.random.randn(hidden_size2, 1) * 0.5
        self.b3 = np.zeros((1, 1))
        
        # Para normalización
        self.mean = None
        self.std = None
    
    def sigmoid(self, x):
        """Función de activación sigmoid."""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def relu(self, x):
        """Función de activación ReLU."""
        return np.maximum(0, x)
    
    def forward(self, X):
        """Propagación hacia adelante."""
        # Capa 1
        self.z1 = np.dot(X, self.W1) + self.b1
        self.a1 = self.relu(self.z1)
        
        # Capa 2
        self.z2 = np.dot(self.a1, self.W2) + self.b2
        self.a2 = self.relu(self.z2)
        
        # Capa 3 (salida)
        self.z3 = np.dot(self.a2, self.W3) + self.b3
        self.a3 = self.sigmoid(self.z3)
        
        return self.a3
    
    def backward(self, X, y, learning_rate=0.01):
        """Retropropagación para actualizar pesos."""
        m = X.shape[0]
        
        # Gradiente capa 3
        dz3 = self.a3 - y.reshape(-1, 1)
        dW3 = np.dot(self.a2.T, dz3) / m
        db3 = np.sum(dz3, axis=0, keepdims=True) / m
        
        # Gradiente capa 2
        da2 = np.dot(dz3, self.W3.T)
        dz2 = da2 * (self.z2 > 0)
        dW2 = np.dot(self.a1.T, dz2) / m
        db2 = np.sum(dz2, axis=0, keepdims=True) / m
        
        # Gradiente capa 1
        da1 = np.dot(dz2, self.W2.T)
        dz1 = da1 * (self.z1 > 0)
        dW1 = np.dot(X.T, dz1) / m
        db1 = np.sum(dz1, axis=0, keepdims=True) / m
        
        # Actualizar pesos
        self.W3 -= learning_rate * dW3
        self.b3 -= learning_rate * db3
        self.W2 -= learning_rate * dW2
        self.b2 -= learning_rate * db2
        self.W1 -= learning_rate * dW1
        self.b1 -= learning_rate * db1
    
    def normalizar(self, X, ajustar=True):
        """Normaliza los datos."""
        if ajustar:
            self.mean = np.mean(X, axis=0)
            self.std = np.std(X, axis=0) + 1e-8
        return (X - self.mean) / self.std
    
    def entrenar(self, X, y, epochs=100, learning_rate=0.1, verbose=True):
        """
        Entrena la red neuronal.
        
        Args:
            X: Datos de entrada (N x 5)
            y: Etiquetas (N,)
            epochs: Número de épocas
            learning_rate: Tasa de aprendizaje
        """
        # Normalizar datos
        X_norm = self.normalizar(X, ajustar=True)
        
        # Historial de pérdida
        loss_history = []
        
        print(f"🎓 Entrenando red neuronal ({epochs} épocas)...")
        
        for epoch in range(epochs):
            # Forward pass
            predictions = self.forward(X_norm)
            
            # Calcular pérdida (binary cross-entropy)
            epsilon = 1e-8
            loss = -np.mean(
                y * np.log(predictions + epsilon) + 
                (1 - y) * np.log(1 - predictions + epsilon)
            )
            loss_history.append(loss)
            
            # Backward pass
            self.backward(X_norm, y, learning_rate)
            
            # Mostrar progreso
            if verbose and (epoch + 1) % 10 == 0:
                accuracy = self.calcular_accuracy(X, y)
                print(f"   Época {epoch+1}/{epochs} - Loss: {loss:.4f} - Accuracy: {accuracy:.2%}")
        
        print(f"✅ Entrenamiento completado")
        return loss_history
    
    def predecir(self, X):
        """Realiza predicciones."""
        X_norm = self.normalizar(X, ajustar=False)
        predictions = self.forward(X_norm)
        return predictions.flatten()
    
    def calcular_accuracy(self, X, y):
        """Calcula precisión."""
        predictions = self.predecir(X)
        pred_labels = (predictions > 0.5).astype(int)
        return np.mean(pred_labels == y)
    
    def guardar_modelo(self, ruta="data/modelos/red_neuronal_simple.npz"):
        """Guarda los pesos del modelo."""
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        np.savez(
            ruta,
            W1=self.W1, b1=self.b1,
            W2=self.W2, b2=self.b2,
            W3=self.W3, b3=self.b3,
            mean=self.mean, std=self.std
        )
        print(f"✅ Modelo guardado en: {ruta}")
    
    def cargar_modelo(self, ruta="data/modelos/red_neuronal_simple.npz"):
        """Carga pesos del modelo."""
        data = np.load(ruta)
        self.W1 = data['W1']
        self.b1 = data['b1']
        self.W2 = data['W2']
        self.b2 = data['b2']
        self.W3 = data['W3']
        self.b3 = data['b3']
        self.mean = data['mean']
        self.std = data['std']
        print(f"✅ Modelo cargado desde: {ruta}")


def generar_datos_entrenamiento(n_samples=1000):
    """Genera datos sintéticos para entrenamiento."""
    np.random.seed(42)
    
    datos = []
    for _ in range(n_samples):
        # Generar características
        temperatura = np.random.normal(18, 5)
        precipitacion = np.random.exponential(10)
        humedad = np.random.normal(70, 15)
        presion = np.random.normal(1010, 10)
        viento = np.random.exponential(5)
        
        # Determinar bloqueo (lógica simple pero efectiva)
        bloqueo = int(
            (precipitacion > 30) or 
            (viento > 20) or
            (temperatura < 5 and precipitacion > 10)
        )
        
        datos.append([temperatura, precipitacion, humedad, presion, viento, bloqueo])
    
    df = pd.DataFrame(datos, columns=['temperatura', 'precipitacion', 'humedad', 
                                      'presion', 'viento', 'bloqueo'])
    return df


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    print("="*70)
    print("🧠 RED NEURONAL SIMPLE (Sin TensorFlow)")
    print("="*70 + "\n")
    
    # 1. Generar datos
    print("📊 Generando datos de entrenamiento...\n")
    df = generar_datos_entrenamiento(n_samples=2000)
    
    print(f"Datos generados: {len(df)} muestras")
    print(f"Bloqueos: {df['bloqueo'].sum()} ({df['bloqueo'].mean()*100:.1f}%)\n")
    
    # Guardar datos
    os.makedirs("data/clima", exist_ok=True)
    df.to_csv("data/clima/datos_entrenamiento.csv", index=False)
    
    # 2. Preparar datos
    X = df[['temperatura', 'precipitacion', 'humedad', 'presion', 'viento']].values
    y = df['bloqueo'].values
    
    # Dividir en train/test
    split = int(0.8 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    # 3. Crear y entrenar modelo
    print("🎓 Entrenando modelo...\n")
    modelo = RedNeuronalSimple()
    loss_history = modelo.entrenar(X_train, y_train, epochs=100, learning_rate=0.1)
    
    # 4. Evaluar
    print("\n📊 Evaluando en datos de prueba...")
    accuracy_test = modelo.calcular_accuracy(X_test, y_test)
    print(f"   Precisión en test: {accuracy_test:.2%}\n")
    
    # 5. Guardar modelo
    modelo.guardar_modelo()
    
    # 6. Hacer predicciones de ejemplo
    print("="*70)
    print("🔮 EJEMPLOS DE PREDICCIÓN")
    print("="*70 + "\n")
    
    escenarios = [
        {
            "nombre": "Día normal",
            "datos": [20, 0, 60, 1013, 5],
            "emoji": "☀️"
        },
        {
            "nombre": "Lluvia moderada",
            "datos": [16, 15, 80, 1008, 10],
            "emoji": "🌧️"
        },
        {
            "nombre": "Tormenta severa",
            "datos": [12, 40, 95, 1000, 25],
            "emoji": "⛈️"
        },
        {
            "nombre": "Clima frío extremo",
            "datos": [2, 20, 70, 1015, 8],
            "emoji": "❄️"
        }
    ]
    
    for escenario in escenarios:
        X_pred = np.array([escenario["datos"]])
        prob = modelo.predecir(X_pred)[0]
        
        print(f"{escenario['emoji']} {escenario['nombre']}")
        print(f"   Temperatura: {escenario['datos'][0]}°C")
        print(f"   Precipitación: {escenario['datos'][1]}mm")
        print(f"   Riesgo de bloqueo: {prob*100:.1f}%")
        
        if prob > 0.7:
            print(f"   ⛔ ALTO RIESGO")
        elif prob > 0.4:
            print(f"   ⚠️  RIESGO MODERADO")
        else:
            print(f"   ✅ RIESGO BAJO")
        print()
    
    print("="*70)
    print("✅ DEMOSTRACIÓN COMPLETADA")
    print("="*70)