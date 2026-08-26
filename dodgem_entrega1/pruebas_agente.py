# -*- coding: utf-8 -*-
"""Pruebas unitarias del agente Minimax.

Ejecutar con:
    python -m unittest pruebas_agente -v

La prueba central es la de equivalencia: la poda Alfa-Beta y la tabla
de transposiciones son OPTIMIZACIONES, y una optimizacion que cambia
el resultado es un error. Aqui se compara el valor que devuelve la
busqueda optimizada contra el de un Minimax puro escrito de la forma
mas simple posible, sobre decenas de posiciones reales y a varias
profundidades. Si coinciden en todas, la poda esta bien implementada.
"""

from __future__ import annotations

import random
import threading
import unittest

import agente
import config
import heuristica
import motor


def posiciones_de_prueba(n=6, semillas=(0, 1, 2), por_partida=8):
    """Genera posiciones variadas de mitad de partida."""
    posiciones = []
    for semilla in semillas:
        azar = random.Random(semilla)
        estado = motor.estado_inicial(n)
        for _ in range(por_partida):
            if motor.es_terminal(estado):
                break
            posiciones.append(estado)
            estado = motor.aplicar(
                estado, azar.choice(motor.movimientos_legales(estado)))
    return posiciones


# =====================================================================
# EQUIVALENCIA: LA OPTIMIZACION NO CAMBIA EL RESULTADO
# =====================================================================


class PruebasEquivalencia(unittest.TestCase):

    def test_la_poda_no_altera_el_valor(self):
        """Alfa-Beta debe dar el MISMO valor que Minimax sin poda."""
        for estado in posiciones_de_prueba(6, (0, 1, 2, 3)):
            for profundidad in (1, 2, 3):
                referencia = agente.minimax_sin_poda(
                    estado, profundidad, config.JUGADOR_A)
                podado, _ = agente.valor_con_alfa_beta(
                    estado, profundidad, config.JUGADOR_A,
                    usar_tabla=False)
                self.assertAlmostEqual(
                    podado, referencia, places=6,
                    msg="difieren a profundidad %d" % profundidad)

    def test_la_tabla_no_altera_el_valor(self):
        """Anadir transposiciones tampoco puede cambiar el resultado.

        Es la prueba que caza los errores de normalizacion de los
        puntajes de victoria: si al guardar y recuperar no se ajusta
        la distancia al final, los valores se desvian justo en las
        posiciones ganadas, que son las que importan.
        """
        for estado in posiciones_de_prueba(6, (0, 1, 2, 3)):
            for profundidad in (1, 2, 3, 4):
                referencia = agente.minimax_sin_poda(
                    estado, profundidad, config.JUGADOR_A)
                con_tabla, _ = agente.valor_con_alfa_beta(
                    estado, profundidad, config.JUGADOR_A,
                    usar_tabla=True)
                self.assertAlmostEqual(con_tabla, referencia, places=6)

    def test_equivalencia_para_ambos_jugadores(self):
        # El agente puede jugar de A o de B; el signo debe seguir a
        # jugador_max en los dos casos.
        for estado in posiciones_de_prueba(6, (5, 6)):
            for jugador in config.JUGADORES:
                referencia = agente.minimax_sin_poda(estado, 3, jugador)
                podado, _ = agente.valor_con_alfa_beta(estado, 3, jugador)
                self.assertAlmostEqual(podado, referencia, places=6)

    def test_equivalencia_en_tablero_grande(self):
        for estado in posiciones_de_prueba(8, (11,), por_partida=4):
            referencia = agente.minimax_sin_poda(estado, 2,
                                                 config.JUGADOR_A)
            podado, _ = agente.valor_con_alfa_beta(estado, 2,
                                                   config.JUGADOR_A)
            self.assertAlmostEqual(podado, referencia, places=6)


class PruebasNormalizacionDePuntajes(unittest.TestCase):
    """La conversion de puntajes de victoria para la tabla."""

    def test_son_operaciones_inversas(self):
        for ply in range(0, 12):
            for valor in (0.0, 12.5, -7.25, config.VICTORIA - ply,
                          -config.VICTORIA + ply):
                ida = agente._hacia_la_tabla(valor, ply)
                vuelta = agente._desde_la_tabla(ida, ply)
                self.assertAlmostEqual(vuelta, valor, places=6)

    def test_no_toca_los_puntajes_heuristicos(self):
        # Un puntaje normal debe guardarse tal cual: solo los valores
        # de victoria dependen de la profundidad.
        for ply in (0, 3, 9):
            self.assertEqual(agente._hacia_la_tabla(15.0, ply), 15.0)
            self.assertEqual(agente._desde_la_tabla(-15.0, ply), -15.0)

    def test_la_tabla_reutilizada_da_el_mismo_valor(self):
        # Se busca dos veces con el MISMO agente: la segunda encuentra
        # la tabla caliente. El resultado no puede cambiar.
        estado = posiciones_de_prueba(6, (4,))[3]
        jugador = estado.turno
        uno = agente.AgenteMinimax(jugador, profundidad=4, segundos=None)
        primera = uno.elegir(estado)
        segunda = uno.elegir(estado)
        self.assertAlmostEqual(primera.valor, segunda.valor, places=6)
        self.assertEqual(primera.movimiento, segunda.movimiento)


# =====================================================================
# LA OPTIMIZACION SIRVE
# =====================================================================


class PruebasRendimiento(unittest.TestCase):

    def test_la_poda_visita_menos_nodos(self):
        estado = motor.estado_inicial(6)
        _, sin_poda = agente.valor_con_alfa_beta(
            estado, 4, config.JUGADOR_A, usar_tabla=False, usar_poda=False)
        _, con_poda = agente.valor_con_alfa_beta(
            estado, 4, config.JUGADOR_A, usar_tabla=False, usar_poda=True)
        self.assertLess(con_poda, sin_poda)

    def test_la_tabla_visita_menos_nodos_que_solo_la_poda(self):
        estado = motor.estado_inicial(6)
        _, solo_poda = agente.valor_con_alfa_beta(
            estado, 5, config.JUGADOR_A, usar_tabla=False, usar_poda=True)
        _, con_tabla = agente.valor_con_alfa_beta(
            estado, 5, config.JUGADOR_A, usar_tabla=True, usar_poda=True)
        self.assertLess(con_tabla, solo_poda)


# =====================================================================
# CALIDAD DE JUEGO
# =====================================================================


class PruebasDecisiones(unittest.TestCase):

    def test_remata_cuando_puede_ganar_de_inmediato(self):
        # A tiene una sola ficha, ya en el carril de salida: sacarla
        # gana la partida en el acto.
        n = 6
        estado = motor.Estado(
            n=n, fichas_a=frozenset({(2, n - 1)}),
            fichas_b=frozenset({(4, 1), (4, 2)}),
            turno=config.JUGADOR_A, salidas_a=n - 2, salidas_b=0,
            sin_progreso=0)
        cerebro = agente.AgenteMinimax(config.JUGADOR_A, profundidad=4,
                                       segundos=None)
        resultado = cerebro.elegir(estado)
        self.assertTrue(resultado.movimiento.es_salida)
        self.assertGreaterEqual(resultado.valor, config.UMBRAL_VICTORIA)

    def test_detecta_que_la_victoria_esta_a_un_paso(self):
        # El valor devuelto debe ser VICTORIA - 1: ganar en una jugada.
        n = 6
        estado = motor.Estado(
            n=n, fichas_a=frozenset({(2, n - 1)}),
            fichas_b=frozenset({(4, 1), (4, 2)}),
            turno=config.JUGADOR_A, salidas_a=n - 2, salidas_b=0,
            sin_progreso=0)
        cerebro = agente.AgenteMinimax(config.JUGADOR_A, profundidad=3,
                                       segundos=None)
        self.assertAlmostEqual(cerebro.elegir(estado).valor,
                               config.VICTORIA - 1, places=6)

    def test_evita_dejarse_bloquear_pudiendo_evitarlo(self):
        # Con la regla del enunciado, quedarse sin jugadas es perder.
        # Un agente que mire dos jugadas debe esquivar la trampa.
        n = 6
        estado = motor.Estado(
            n=n, fichas_a=frozenset({(0, 0)}),
            fichas_b=frozenset({(1, 1), (2, 0)}),
            turno=config.JUGADOR_A, salidas_a=n - 2, salidas_b=n - 3,
            sin_progreso=0)
        cerebro = agente.AgenteMinimax(config.JUGADOR_A, profundidad=4,
                                       segundos=None)
        resultado = cerebro.elegir(estado)
        siguiente = motor.aplicar(estado, resultado.movimiento)
        self.assertFalse(
            motor.ganador(siguiente) == config.JUGADOR_B,
            "el agente se metio en una derrota inmediata evitable")

    def test_mas_profundidad_no_juega_peor(self):
        # Un agente profundo debe ganarle (o al menos no perder) a uno
        # somero en un enfrentamiento directo.
        victorias_profundo = 0
        decididas = 0
        for partida in range(6):
            estado = motor.estado_inicial(6)
            profundo = agente.AgenteMinimax(
                config.JUGADOR_A if partida % 2 == 0 else config.JUGADOR_B,
                profundidad=4, segundos=None)
            somero = agente.AgenteMinimax(
                config.JUGADOR_B if partida % 2 == 0 else config.JUGADOR_A,
                profundidad=1, segundos=None)
            cerebros = {profundo.jugador: profundo, somero.jugador: somero}
            for _ in range(300):
                if motor.es_terminal(estado):
                    break
                movimiento = cerebros[estado.turno].elegir(estado).movimiento
                estado = motor.aplicar(estado, movimiento)
            ganador = motor.ganador(estado)
            if ganador in config.JUGADORES:
                decididas += 1
                if ganador == profundo.jugador:
                    victorias_profundo += 1
        self.assertGreaterEqual(victorias_profundo, decididas / 2.0)


# =====================================================================
# CONTRATO Y ROBUSTEZ
# =====================================================================


class PruebasContrato(unittest.TestCase):

    def test_siempre_devuelve_una_jugada_legal(self):
        for estado in posiciones_de_prueba(6, (7, 8)):
            cerebro = agente.AgenteMinimax(estado.turno, profundidad=3,
                                           segundos=None)
            movimiento = cerebro.elegir(estado).movimiento
            self.assertIn(movimiento, motor.movimientos_legales(estado))

    def test_no_muta_el_estado_recibido(self):
        estado = motor.estado_inicial(6)
        copia = motor.Estado(*estado)
        agente.AgenteMinimax(config.JUGADOR_A, profundidad=4,
                             segundos=None).elegir(estado)
        self.assertEqual(estado, copia)

    def test_rechaza_una_partida_terminada(self):
        estado = motor.Estado(
            n=6, fichas_a=frozenset(), fichas_b=frozenset({(5, 1)}),
            turno=config.JUGADOR_B, salidas_a=5, salidas_b=0,
            sin_progreso=0)
        cerebro = agente.AgenteMinimax(config.JUGADOR_B)
        with self.assertRaises(ValueError):
            cerebro.elegir(estado)

    def test_respeta_la_cancelacion(self):
        # Con la senal ya activada la busqueda aborta enseguida, pero
        # igual debe entregar una jugada legal: la interfaz no puede
        # quedarse sin respuesta.
        estado = motor.estado_inicial(8)
        cancelar = threading.Event()
        cancelar.set()
        cerebro = agente.AgenteMinimax(config.JUGADOR_A, profundidad=8,
                                       segundos=None)
        resultado = cerebro.elegir(estado, cancelar=cancelar)
        self.assertIn(resultado.movimiento, motor.movimientos_legales(estado))

    def test_respeta_el_tope_de_tiempo(self):
        estado = motor.estado_inicial(8)
        cerebro = agente.AgenteMinimax(config.JUGADOR_A, profundidad=12,
                                       segundos=0.25)
        resultado = cerebro.elegir(estado)
        self.assertIn(resultado.movimiento,
                      motor.movimientos_legales(estado))
        # Margen generoso: la comprobacion del reloj es cada N nodos.
        self.assertLess(resultado.segundos, 3.0)
        self.assertGreaterEqual(resultado.profundidad, 1)

    def test_devuelve_una_profundidad_completa(self):
        estado = motor.estado_inicial(6)
        cerebro = agente.AgenteMinimax(config.JUGADOR_A, profundidad=4,
                                       segundos=None)
        resultado = cerebro.elegir(estado)
        self.assertEqual(resultado.profundidad, 4)
        self.assertTrue(resultado.completa)

    def test_es_determinista(self):
        estado = posiciones_de_prueba(6, (9,))[4]
        elecciones = set()
        for _ in range(3):
            cerebro = agente.AgenteMinimax(estado.turno, profundidad=4,
                                           segundos=None)
            elecciones.add(cerebro.elegir(estado).movimiento)
        self.assertEqual(len(elecciones), 1)

    def test_la_api_simple_funciona(self):
        estado = motor.estado_inicial(6)
        movimiento = agente.elegir_movimiento(estado, nivel="facil")
        self.assertIn(movimiento, motor.movimientos_legales(estado))

    def test_reiniciar_vacia_la_tabla(self):
        estado = motor.estado_inicial(6)
        cerebro = agente.AgenteMinimax(config.JUGADOR_A, profundidad=3,
                                       segundos=None)
        cerebro.elegir(estado)
        self.assertGreater(len(cerebro.tabla), 0)
        cerebro.reiniciar()
        self.assertEqual(len(cerebro.tabla), 0)
        self.assertIsNone(cerebro.ultimo_resultado)

    def test_todos_los_niveles_configurados_funcionan(self):
        estado = motor.estado_inicial(6)
        for nivel in config.ORDEN_NIVELES:
            cerebro = agente.AgenteMinimax(config.JUGADOR_A, nivel=nivel)
            resultado = cerebro.elegir(estado)
            self.assertIn(resultado.movimiento,
                          motor.movimientos_legales(estado))
            self.assertTrue(resultado.resumen())


if __name__ == "__main__":
    unittest.main(verbosity=2)
