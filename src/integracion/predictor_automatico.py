"""
Módulo: predictor_automatico.py
Descripción: Sistema automático que usa la red neuronal para predecir 
bloqueos en rutas y generar alertas preventivas.

Ejecutar: python -m src.integracion.predictor_automatico
"""

import sys
import os
import time
import schedule
from datetime import datetime
from typing import List, Dict
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.stdout.reconfigure(encoding='utf-8')
from src.unidad3_grafos.grafo_rutas import GrafoRutas
from src.unidad3_grafos.prediccion_climatica import IntegradorSENAMHI


class PredictorAutomatico:
    """
    Sistema automático de predicción de bloqueos.
    
    Funcionalidad:
    1. Escanea todas las rutas del grafo
    2. Consulta datos climáticos simulados/reales
    3. Usa red neuronal para predecir riesgo de bloqueo
    4. Genera alertas automáticas si el riesgo supera umbral
    """
    
    def __init__(self, ruta_grafo: str = "data/grafos/red_peru_24_departamentos.json",
                 api_url: str = "http://localhost:8000"):
        """
        Inicializa el predictor.
        
        Args:
            ruta_grafo: Path al archivo JSON del grafo
            api_url: URL base de la API SIAR
        """
        # Cargar grafo
        self.grafo = GrafoRutas.cargar_json(ruta_grafo)
        print(f"✅ Grafo cargado: {len(self.grafo.nodos)} departamentos\n")
        
        # Cargar predictor climático
        self.predictor = IntegradorSENAMHI()
        if not self.predictor.cargar_modelo("data/modelos"):
            print("⚠️  Modelo no encontrado, entrenando uno nuevo...")
            self.predictor.entrenar_modelo()
            self.predictor.guardar_modelo()
        
        self.api_url = api_url
        self.umbral_riesgo_alto = 0.7  # 70% probabilidad
        self.umbral_riesgo_moderado = 0.5  # 50%
        
        # Historial de alertas para evitar duplicados
        self.alertas_generadas = set()
    
    def obtener_clima_simulado(self, departamento: str) -> Dict:
        """
        Genera datos climáticos simulados para un departamento.
        
        En producción, esto consultaría una API meteorológica real.
        """
        import random
        
        # Simular variabilidad por región
        regiones = {
            'costa': {'temp': (18, 28), 'precip': (0, 10), 'humedad': (60, 80)},
            'sierra': {'temp': (8, 18), 'precip': (5, 35), 'humedad': (50, 90)},
            'selva': {'temp': (22, 32), 'precip': (10, 60), 'humedad': (70, 95)}
        }
        
        # Asignar región (simplificado)
        if departamento in ['Lima', 'Ica', 'Arequipa', 'Moquegua', 'Tacna']:
            region = 'costa'
        elif departamento in ['Cusco', 'Puno', 'Ayacucho', 'Junín', 'Cajamarca']:
            region = 'sierra'
        else:
            region = 'selva'
        
        rangos = regiones[region]
        
        # Simular época de lluvias (nov-mar)
        mes_actual = datetime.now().month
        es_epoca_lluvias = mes_actual in [11, 12, 1, 2, 3]
        factor_lluvia = 2.0 if es_epoca_lluvias else 1.0
        
        return {
            'temperatura': random.uniform(*rangos['temp']),
            'precipitacion': random.uniform(*rangos['precip']) * factor_lluvia,
            'humedad': random.uniform(*rangos['humedad']),
            'presion': random.uniform(740, 1015),
            'viento': random.exponential(8),
            'departamento': departamento
        }
    
    def predecir_riesgo_ruta(self, origen: str, destino: str) -> Dict:
        """
        Predice el riesgo de bloqueo en una ruta específica.
        
        Returns:
            Dict con departamentos afectados y sus riesgos
        """
        print(f"\n🔍 Analizando ruta: {origen} → {destino}")
        
        # Calcular ruta
        try:
            response = requests.get(
                f"{self.api_url}/rutas/calcular",
                params={'origen': origen, 'destino': destino},
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"   ⚠️  Error obteniendo ruta: {response.status_code}")
                return {}
            
            ruta = response.json()
            departamentos_ruta = ruta['nodos']
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {}
        
        # Analizar clima en cada departamento de la ruta
        riesgos = {}
        
        for depto in departamentos_ruta:
            clima = self.obtener_clima_simulado(depto)
            
            # Predecir con red neuronal
            prediccion = self.predictor.predecir_riesgo(
                temperatura=clima['temperatura'],
                precipitacion=clima['precipitacion'],
                humedad=clima['humedad'],
                presion=clima['presion'],
                viento=clima['viento']
            )
            
            riesgos[depto] = {
                'riesgo_bloqueo': prediccion.riesgo_bloqueo,
                'clima': clima,
                'recomendacion': prediccion.recomendacion
            }
            
            # Log si hay riesgo significativo
            if prediccion.riesgo_bloqueo > self.umbral_riesgo_moderado:
                print(f"   ⚠️  {depto}: Riesgo {prediccion.riesgo_bloqueo*100:.1f}% "
                      f"(Precip: {clima['precipitacion']:.1f}mm)")
        
        return riesgos
    
    def escanear_todas_las_rutas(self):
        """
        Escanea todas las rutas del sistema y genera alertas predictivas.
        """
        print("\n" + "="*70)
        print(f"🤖 ESCANEO AUTOMÁTICO DE RUTAS")
        print(f"   Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # Lista de rutas críticas a monitorear
        rutas_criticas = [
            ('Lima', 'Cusco'),
            ('Lima', 'Arequipa'),
            ('Cusco', 'Puno'),
            ('Ayacucho', 'Cusco'),
            ('Cajamarca', 'San Martín'),
            ('Lima', 'Junín'),
            ('Arequipa', 'Puno')
        ]
        
        alertas_nuevas = 0
        
        for origen, destino in rutas_criticas:
            riesgos = self.predecir_riesgo_ruta(origen, destino)
            
            # Generar alertas para zonas de alto riesgo
            for depto, info in riesgos.items():
                riesgo = info['riesgo_bloqueo']
                
                if riesgo > self.umbral_riesgo_alto:
                    # Evitar alertas duplicadas
                    alerta_id = f"{depto}_{datetime.now().strftime('%Y%m%d')}"
                    
                    if alerta_id not in self.alertas_generadas:
                        self.generar_alerta_automatica(
                            departamento=depto,
                            riesgo=riesgo,
                            clima=info['clima'],
                            ruta_afectada=f"{origen}-{destino}"
                        )
                        self.alertas_generadas.add(alerta_id)
                        alertas_nuevas += 1
        
        print(f"\n✅ Escaneo completado: {alertas_nuevas} alerta(s) nueva(s)")
    
    def generar_alerta_automatica(self, departamento: str, riesgo: float,
                                  clima: Dict, ruta_afectada: str):
        """
        Genera una alerta predictiva en el sistema.
        """
        print(f"\n🚨 GENERANDO ALERTA PREDICTIVA")
        print(f"   Departamento: {departamento}")
        print(f"   Ruta afectada: {ruta_afectada}")
        print(f"   Riesgo: {riesgo*100:.1f}%")
        
        # Determinar tipo de alerta
        if clima['precipitacion'] > 35:
            tipo = "LLUVIA_INTENSA"
            desc = f"Predicción: Lluvia intensa ({clima['precipitacion']:.1f}mm). Alto riesgo de bloqueo."
        elif clima['viento'] > 20:
            tipo = "VIENTO_FUERTE"
            desc = f"Predicción: Vientos fuertes ({clima['viento']:.1f}km/h). Riesgo de caída de árboles."
        else:
            tipo = "RIESGO_BLOQUEO"
            desc = f"Predicción automática: Condiciones adversas detectadas. Riesgo de bloqueo {riesgo*100:.0f}%."
        
        # Intentar crear alerta en la API
        try:
            response = requests.post(
                f"{self.api_url}/alertas/crear",
                json={
                    "tipo": tipo,
                    "ubicacion": f"{departamento} - Ruta {ruta_afectada}",
                    "descripcion": desc,
                    "emisor": "SISTEMA_AUTOMATICO"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                alerta = response.json()
                print(f"   ✅ Alerta creada: {alerta['id']}")
                print(f"   Estado: {alerta['estado']}")
                print(f"   📍 Los usuarios podrán confirmar/rechazar esta predicción")
            else:
                print(f"   ⚠️  Error creando alerta: {response.status_code}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    def ejecutar_monitoreo_continuo(self, intervalo_horas: int = 6):
        """
        Ejecuta el monitoreo continuo cada X horas.
        
        Args:
            intervalo_horas: Cada cuántas horas escanear
        """
        print("\n" + "="*70)
        print("🤖 INICIANDO MONITOREO AUTOMÁTICO")
        print("="*70)
        print(f"   Intervalo: Cada {intervalo_horas} horas")
        print(f"   Rutas monitoreadas: Rutas críticas del sistema")
        print(f"   Umbral riesgo alto: {self.umbral_riesgo_alto*100:.0f}%")
        print("="*70 + "\n")
        
        # Ejecutar inmediatamente
        self.escanear_todas_las_rutas()
        
        # Programar ejecuciones periódicas
        schedule.every(intervalo_horas).hours.do(self.escanear_todas_las_rutas)
        
        print(f"\n⏰ Próximo escaneo en {intervalo_horas} horas")
        print("   Presiona Ctrl+C para detener\n")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
        except KeyboardInterrupt:
            print("\n\n⏸️  Monitoreo detenido por el usuario")


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Sistema de predicción automática de bloqueos en rutas"
    )
    parser.add_argument(
        '--modo',
        choices=['escaneo', 'continuo'],
        default='escaneo',
        help="Modo: escaneo único o monitoreo continuo"
    )
    parser.add_argument(
        '--intervalo',
        type=int,
        default=6,
        help="Intervalo en horas para modo continuo (default: 6)"
    )
    
    args = parser.parse_args()
    
    predictor = PredictorAutomatico()
    
    if args.modo == 'escaneo':
        predictor.escanear_todas_las_rutas()
    else:
        predictor.ejecutar_monitoreo_continuo(intervalo_horas=args.intervalo)


if __name__ == "__main__":
    main()