"""
Tests unitarios para el módulo grafo_rutas.py
Ejecutar con: python -m pytest tests/test_grafo_rutas.py -v
"""

import pytest # type: ignore
import sys
import os

# Agregar src al path para poder importar
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ✅ IMPORTACIONES CORREGIDAS - Ahora usan imports absolutos
from src.unidad3_grafos.grafo_rutas import GrafoRutas, TipoCamino, Arista
from src.unidad3_grafos.algoritmo_fiabilidad import AlgoritmoFiabilidad, Ruta
from src.unidad3_grafos.maquina_estados import (
    MaquinaEstadosAlerta, 
    MaquinaEstadosLogistica,
    Alerta,
    LoteCosecha,
    EstadoAlerta,
    EstadoLote,
    EventoAlerta,
    EventoLote
)


class TestGrafoRutas:
    """Suite de tests para la clase GrafoRutas."""
    
    @pytest.fixture
    def grafo_simple(self):
        """Fixture: Crea un grafo simple para tests."""
        grafo = GrafoRutas()
        grafo.agregar_camino(
            "A", "B", 
            distancia_km=10, 
            fiabilidad=0.9, 
            tipo_camino=TipoCamino.ASFALTADO
        )
        grafo.agregar_camino(
            "B", "C", 
            distancia_km=20, 
            fiabilidad=0.8, 
            tipo_camino=TipoCamino.AFIRMADO
        )
        return grafo
    
    def test_agregar_nodos(self):
        """Test: Agregar nodos al grafo."""
        grafo = GrafoRutas()
        grafo.agregar_nodo("Ayacucho")
        grafo.agregar_nodo("Huanta")
        
        assert "Ayacucho" in grafo.nodos
        assert "Huanta" in grafo.nodos
        assert len(grafo.nodos) == 2
    
    def test_agregar_camino(self, grafo_simple):
        """Test: Agregar camino crea nodos y aristas bidireccionales."""
        assert len(grafo_simple.nodos) == 3  # A, B, C
        
        # Verificar bidireccionalidad
        vecinos_b = grafo_simple.obtener_vecinos("B")
        destinos = [a.destino for a in vecinos_b]
        assert "A" in destinos
        assert "C" in destinos

    def test_fiabilidad_invalida(self):
        """Test: Fiabilidad fuera de rango debe lanzar error."""
        grafo = GrafoRutas()
        
        with pytest.raises(ValueError):
            grafo.agregar_camino(
                "A", "B", 
                distancia_km=10, 
                fiabilidad=1.5,  # Inválido
                tipo_camino=TipoCamino.ASFALTADO
            )
        
        with pytest.raises(ValueError):
            grafo.agregar_camino(
                "A", "B", 
                distancia_km=10, 
                fiabilidad=-0.2,  # Inválido
                tipo_camino=TipoCamino.ASFALTADO
            )

    def test_calcular_peso_fiabilidad(self):
        """Test: Cálculo de peso basado en fiabilidad."""
        arista = Arista(
            origen="A",
            destino="B",
            distancia_km=100,
            fiabilidad=0.5,
            tipo_camino=TipoCamino.AFIRMADO,
            riesgo_historico=0.2,
            tiempo_estimado_min=150
        )
        
        peso = arista.calcular_peso_fiabilidad()
        # peso = 100/0.5 + 0.2*50 = 200 + 10 = 210
        assert peso == 210.0

    def test_actualizar_fiabilidad(self, grafo_simple):
        """Test: Actualizar fiabilidad de un camino."""
        grafo_simple.actualizar_fiabilidad("A", "B", 0.5)
        
        # Verificar en ambas direcciones
        arista_ab = [a for a in grafo_simple.obtener_vecinos("A") if a.destino == "B"][0]
        arista_ba = [a for a in grafo_simple.obtener_vecinos("B") if a.destino == "A"][0]
        
        assert arista_ab.fiabilidad == 0.5
        assert arista_ba.fiabilidad == 0.5

    def test_exportar_cargar_json(self, grafo_simple, tmp_path):
        """Test: Persistencia en JSON."""
        archivo = tmp_path / "test_grafo.json"
        
        # Exportar
        grafo_simple.exportar_json(str(archivo))
        assert archivo.exists()
        
        # Cargar
        grafo_cargado = GrafoRutas.cargar_json(str(archivo))
        
        assert len(grafo_cargado.nodos) == len(grafo_simple.nodos)
        assert grafo_cargado.nodos == grafo_simple.nodos

    def test_obtener_vecinos(self, grafo_simple):
        """Test: Obtener vecinos de un nodo."""
        vecinos_b = grafo_simple.obtener_vecinos("B")
        
        assert len(vecinos_b) == 2  # A y C
        destinos = {a.destino for a in vecinos_b}
        assert destinos == {"A", "C"}

    def test_tiempo_estimado_automatico(self):
        """Test: Cálculo automático de tiempo según tipo de camino."""
        grafo = GrafoRutas()
        grafo.agregar_camino(
            "A", "B",
            distancia_km=60,
            fiabilidad=0.9,
            tipo_camino=TipoCamino.ASFALTADO
            # No especificamos tiempo_estimado_min
        )
        
        arista = grafo.obtener_vecinos("A")[0]
        # 60 km a 60 km/h = 1 hora = 60 min
        assert arista.tiempo_estimado_min == 60


class TestAlgoritmoFiabilidad:
    """Suite de tests para algoritmo_fiabilidad.py"""
    
    @pytest.fixture
    def grafo_complejo(self):
        """Fixture: Grafo con múltiples rutas."""
        grafo = GrafoRutas()
        
        # Crear red en forma de rombo:
        #     A
        #    / \
        #   B   C
        #    \ /
        #     D
        
        grafo.agregar_camino("A", "B", 10, 0.9, TipoCamino.ASFALTADO, 0.1)
        grafo.agregar_camino("A", "C", 15, 0.95, TipoCamino.ASFALTADO, 0.05)
        grafo.agregar_camino("B", "D", 10, 0.7, TipoCamino.TROCHA, 0.4)
        grafo.agregar_camino("C", "D", 8, 0.85, TipoCamino.AFIRMADO, 0.2)
        
        return grafo

    def test_encontrar_ruta_mas_fiable(self, grafo_complejo):
        """Test: Encontrar ruta más fiable entre dos puntos."""
        algoritmo = AlgoritmoFiabilidad(grafo_complejo)
        ruta = algoritmo.encontrar_ruta_mas_fiable("A", "D")
        
        assert ruta is not None
        assert ruta.nodos[0] == "A"
        assert ruta.nodos[-1] == "D"
        assert len(ruta.nodos) >= 2

    def test_ruta_inexistente(self, grafo_complejo):
        """Test: Ruta entre nodos no conectados."""
        grafo_complejo.agregar_nodo("E")  # Nodo aislado
        algoritmo = AlgoritmoFiabilidad(grafo_complejo)
        
        ruta = algoritmo.encontrar_ruta_mas_fiable("A", "E")
        assert ruta is None

    def test_nodo_invalido(self, grafo_complejo):
        """Test: Buscar ruta con nodo que no existe."""
        algoritmo = AlgoritmoFiabilidad(grafo_complejo)
        
        with pytest.raises(ValueError):
            algoritmo.encontrar_ruta_mas_fiable("A", "Z")

    def test_fiabilidad_acumulada(self, grafo_complejo):
        """Test: Fiabilidad acumulada es producto de fiabilidades."""
        algoritmo = AlgoritmoFiabilidad(grafo_complejo)
        ruta = algoritmo.encontrar_ruta_mas_fiable("A", "D")
        
        # Calcular manualmente
        fiabilidad_manual = 1.0
        for arista in ruta.aristas:
            fiabilidad_manual *= arista.fiabilidad
        
        assert abs(ruta.fiabilidad_acumulada - fiabilidad_manual) < 0.001


class TestMaquinaEstados:
    """Suite de tests para maquina_estados.py"""
    
    def test_transicion_valida_alerta(self):
        """Test: Transición válida en máquina de estados de alerta."""
        from datetime import datetime
        
        alerta = Alerta(
            id="TEST-001",
            tipo="bloqueo",
            ubicacion="Test",
            descripcion="Test",
            emisor="USER-1",
            timestamp_creacion=datetime.now()
        )
        
        fsm = MaquinaEstadosAlerta()
        
        assert alerta.estado == EstadoAlerta.EMITIDA
        
        resultado = fsm.procesar_evento(alerta, EventoAlerta.SOLICITAR_VERIFICACION)
        assert resultado is True
        assert alerta.estado == EstadoAlerta.EN_VERIFICACION

    def test_transicion_invalida_alerta(self):
        """Test: Transición inválida debe retornar False."""
        from datetime import datetime
        
        alerta = Alerta(
            id="TEST-002",
            tipo="emergencia",
            ubicacion="Test",
            descripcion="Test",
            emisor="USER-1",
            timestamp_creacion=datetime.now(),
            estado=EstadoAlerta.RESUELTA  # Estado final
        )
        
        fsm = MaquinaEstadosAlerta()
        
        # Intentar transición desde estado final
        resultado = fsm.procesar_evento(alerta, EventoAlerta.CONFIRMAR)
        assert resultado is False
        assert alerta.estado == EstadoAlerta.RESUELTA

    def test_calculo_confianza(self):
        """Test: Confianza aumenta con confirmaciones."""
        from datetime import datetime
        
        alerta = Alerta(
            id="TEST-003",
            tipo="lluvia",
            ubicacion="Test",
            descripcion="Test",
            emisor="USER-1",
            timestamp_creacion=datetime.now(),
            estado=EstadoAlerta.EN_VERIFICACION
        )
        
        fsm = MaquinaEstadosAlerta()
        confianza_inicial = alerta.nivel_confianza
        
        # Primera confirmación - debería solo agregar a la lista sin cambiar estado
        # Para esto, necesitamos simular confirmaciones múltiples en EN_VERIFICACION
        # Agregamos confirmación manualmente primero
        alerta.confirmaciones.append("USER-2")
        alerta.nivel_confianza = fsm._calcular_confianza(alerta)
        confianza_1 = alerta.nivel_confianza
        
        # Segunda confirmación
        alerta.confirmaciones.append("USER-3")
        alerta.nivel_confianza = fsm._calcular_confianza(alerta)
        confianza_2 = alerta.nivel_confianza
        
        assert confianza_1 > confianza_inicial
        assert confianza_2 > confianza_1
        assert len(alerta.confirmaciones) == 2

    def test_fsm_logistica(self):
        """Test: Máquina de estados logística."""
        lote = LoteCosecha(
            id="LOT-TEST",
            producto="papa",
            cantidad_kg=100,
            agricultor_id="AGR-1"
        )
        
        fsm = MaquinaEstadosLogistica()
        
        assert lote.estado == EstadoLote.REGISTRADO
        
        fsm.procesar_evento(lote, EventoLote.ALMACENAR)
        assert lote.estado == EstadoLote.EN_ALMACEN
        
        fsm.procesar_evento(lote, EventoLote.PREPARAR_ENVIO)
        assert lote.estado == EstadoLote.LISTO_ENVIO


if __name__ == "__main__":
    pytest.main([__file__, "-v"])