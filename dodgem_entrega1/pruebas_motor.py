# -*- coding: utf-8 -*-
"""Pruebas unitarias del motor de Dodgem.

Ejecutar con:
    python -m unittest pruebas_motor -v
    o simplemente:  python pruebas_motor.py

Las pruebas no tocan la interfaz grafica: comprueban unicamente el
contrato de motor.py. Esa es la ventaja practica de haber escrito el
motor como funciones puras, y es tambien lo que permitira, en la Fase
2, validar el Minimax comparando su salida contra estados construidos
a mano.
"""

from __future__ import annotations

import random
import unittest
from unittest import mock

import config
import motor


class PruebasValidarN(unittest.TestCase):
    """Requisito: n par y mayor que 4."""

    def test_rechaza_impares(self):
        for n in (5, 7, 9, 11):
            self.assertFalse(motor.validar_n(n), "n=%d deberia fallar" % n)

    def test_rechaza_pequenos(self):
        for n in (-2, 0, 2, 4):
            self.assertFalse(motor.validar_n(n), "n=%d deberia fallar" % n)

    def test_acepta_pares_mayores_que_cuatro(self):
        for n in (6, 8, 10, 12):
            self.assertTrue(motor.validar_n(n), "n=%d deberia aceptarse" % n)

    def test_rechaza_tipos_no_enteros(self):
        for valor in ("6", 6.0, None, True, [6]):
            self.assertFalse(motor.validar_n(valor))

    def test_motivo_es_none_cuando_es_valido(self):
        self.assertIsNone(motor.motivo_invalidez(6))
        self.assertIsNotNone(motor.motivo_invalidez(5))


class PruebasEstadoInicial(unittest.TestCase):
    """Disposicion oficial: columna izquierda, fila inferior, esquina
    inferior izquierda vacia."""

    def setUp(self):
        self.n = 6
        self.estado = motor.estado_inicial(self.n)

    def test_cantidad_de_fichas(self):
        esperado = self.n - config.FICHAS_MENOS_QUE_LADO
        self.assertEqual(len(self.estado.fichas_a), esperado)
        self.assertEqual(len(self.estado.fichas_b), esperado)

    def test_a_ocupa_la_columna_izquierda(self):
        esperado = {(fila, 0) for fila in range(self.n - 1)}
        self.assertEqual(set(self.estado.fichas_a), esperado)

    def test_b_ocupa_la_fila_inferior(self):
        esperado = {(self.n - 1, columna)
                    for columna in range(1, self.n)}
        self.assertEqual(set(self.estado.fichas_b), esperado)

    def test_esquina_compartida_vacia(self):
        esquina = (self.n - 1, 0)
        self.assertNotIn(esquina, self.estado.fichas_a)
        self.assertNotIn(esquina, self.estado.fichas_b)

    def test_las_fichas_no_se_superponen(self):
        self.assertEqual(self.estado.fichas_a & self.estado.fichas_b,
                         frozenset())

    def test_comienza_el_jugador_a(self):
        self.assertEqual(self.estado.turno, config.JUGADOR_INICIAL)
        self.assertEqual(self.estado.turno, config.JUGADOR_A)

    def test_rechaza_tamano_invalido(self):
        with self.assertRaises(ValueError):
            motor.estado_inicial(5)

    def test_el_estado_es_hashable(self):
        # Requisito para usarlo como clave de una tabla de
        # transposiciones en la Fase 2.
        self.assertIsInstance(hash(self.estado), int)
        self.assertEqual(self.estado, motor.estado_inicial(self.n))

    def test_escala_a_cualquier_n_valido(self):
        for n in motor.tamanos_validos():
            estado = motor.estado_inicial(n)
            self.assertEqual(len(estado.fichas_a), n - 1)
            self.assertEqual(len(estado.fichas_b), n - 1)


class PruebasMovimientosLegales(unittest.TestCase):

    def setUp(self):
        self.n = 6
        self.estado = motor.estado_inicial(self.n)

    def test_a_nunca_retrocede(self):
        # Ninguna jugada de A puede disminuir el indice de columna.
        for movimiento in motor.movimientos_legales(self.estado):
            self.assertGreaterEqual(movimiento.destino[1],
                                    movimiento.origen[1])

    def test_b_nunca_retrocede(self):
        estado = self.estado._replace(turno=config.JUGADOR_B)
        for movimiento in motor.movimientos_legales(estado):
            self.assertLessEqual(movimiento.destino[0],
                                 movimiento.origen[0])

    def test_no_se_permite_ocupar_casilla_ocupada(self):
        ocupadas = motor.casillas_ocupadas(self.estado)
        for movimiento in motor.movimientos_legales(self.estado):
            if not movimiento.es_salida:
                self.assertNotIn(movimiento.destino, ocupadas)

    def test_conteo_inicial_de_jugadas_de_a(self):
        # Cada una de las 5 fichas de A avanza a la derecha; ademas la
        # ficha inferior puede bajar a la esquina libre. Las demas
        # tienen sus laterales ocupados por fichas del propio bando.
        movimientos = motor.movimientos_legales(self.estado)
        self.assertEqual(len(movimientos), self.n)

    def test_la_lista_es_determinista(self):
        primera = motor.movimientos_legales(self.estado)
        segunda = motor.movimientos_legales(self.estado)
        self.assertEqual(primera, segunda)

    def test_las_salidas_van_primero(self):
        # Estado artificial: una ficha de A pegada al borde derecho.
        estado = motor.Estado(
            n=self.n,
            fichas_a=frozenset({(2, self.n - 1)}),
            fichas_b=frozenset({(4, 4)}),
            turno=config.JUGADOR_A,
            salidas_a=0, salidas_b=0, sin_progreso=0,
        )
        movimientos = motor.movimientos_legales(estado)
        self.assertTrue(movimientos[0].es_salida)

    def test_hay_movimientos_legales_coincide_con_la_lista(self):
        estado = self.estado
        for _ in range(30):
            movimientos = motor.movimientos_legales(estado)
            self.assertEqual(bool(movimientos),
                             motor.hay_movimientos_legales(estado))
            if not movimientos or motor.es_terminal(estado):
                break
            estado = motor.aplicar(estado, movimientos[0])


class PruebasSalidaDelTablero(unittest.TestCase):
    """A solo sale por la derecha; B solo por arriba."""

    def test_a_sale_por_la_derecha(self):
        n = 6
        estado = motor.Estado(
            n=n, fichas_a=frozenset({(0, n - 1)}),
            fichas_b=frozenset({(n - 1, 1)}),
            turno=config.JUGADOR_A,
            salidas_a=0, salidas_b=0, sin_progreso=0,
        )
        salidas = [m for m in motor.movimientos_legales(estado)
                   if m.es_salida]
        self.assertEqual(len(salidas), 1)
        self.assertEqual(salidas[0].destino, (0, n))

    def test_a_no_sale_por_arriba(self):
        # Ficha de A en la fila superior: su lateral hacia arriba cae
        # fuera del tablero y NO debe generarse como jugada.
        n = 6
        estado = motor.Estado(
            n=n, fichas_a=frozenset({(0, 2)}),
            fichas_b=frozenset({(n - 1, 1)}),
            turno=config.JUGADOR_A,
            salidas_a=0, salidas_b=0, sin_progreso=0,
        )
        destinos = {m.destino for m in motor.movimientos_legales(estado)}
        self.assertNotIn((-1, 2), destinos)
        self.assertEqual(destinos, {(0, 3), (1, 2)})

    def test_b_sale_por_arriba(self):
        n = 6
        estado = motor.Estado(
            n=n, fichas_a=frozenset({(3, 0)}),
            fichas_b=frozenset({(0, 3)}),
            turno=config.JUGADOR_B,
            salidas_a=0, salidas_b=0, sin_progreso=0,
        )
        salidas = [m for m in motor.movimientos_legales(estado)
                   if m.es_salida]
        self.assertEqual(len(salidas), 1)
        self.assertEqual(salidas[0].destino, (-1, 3))

    def test_b_no_sale_por_los_costados(self):
        n = 6
        estado = motor.Estado(
            n=n, fichas_a=frozenset({(3, 3)}),
            fichas_b=frozenset({(2, n - 1)}),
            turno=config.JUGADOR_B,
            salidas_a=0, salidas_b=0, sin_progreso=0,
        )
        destinos = {m.destino for m in motor.movimientos_legales(estado)}
        self.assertNotIn((2, n), destinos)
        self.assertEqual(destinos, {(1, n - 1), (2, n - 2)})


class PruebasAplicar(unittest.TestCase):
    """aplicar() debe ser una funcion pura."""

    def setUp(self):
        self.estado = motor.estado_inicial(6)

    def test_no_muta_el_estado_original(self):
        copia = motor.Estado(*self.estado)
        movimiento = motor.movimientos_legales(self.estado)[0]
        motor.aplicar(self.estado, movimiento)
        self.assertEqual(self.estado, copia)
        self.assertEqual(self.estado.fichas_a, copia.fichas_a)
        self.assertEqual(self.estado.fichas_b, copia.fichas_b)

    def test_devuelve_un_objeto_distinto(self):
        movimiento = motor.movimientos_legales(self.estado)[0]
        nuevo = motor.aplicar(self.estado, movimiento)
        self.assertIsNot(nuevo, self.estado)
        self.assertNotEqual(nuevo, self.estado)

    def test_alterna_el_turno(self):
        movimiento = motor.movimientos_legales(self.estado)[0]
        nuevo = motor.aplicar(self.estado, movimiento)
        self.assertEqual(nuevo.turno, config.JUGADOR_B)
        siguiente = motor.aplicar(nuevo, motor.movimientos_legales(nuevo)[0])
        self.assertEqual(siguiente.turno, config.JUGADOR_A)

    def test_la_ficha_cambia_de_casilla(self):
        movimiento = motor.movimientos_legales(self.estado)[0]
        nuevo = motor.aplicar(self.estado, movimiento)
        self.assertNotIn(movimiento.origen, nuevo.fichas_a)
        self.assertIn(movimiento.destino, nuevo.fichas_a)

    def test_la_salida_retira_la_ficha_y_suma_al_contador(self):
        n = 6
        estado = motor.Estado(
            n=n, fichas_a=frozenset({(0, n - 1)}),
            fichas_b=frozenset({(n - 1, 1), (n - 1, 2)}),
            turno=config.JUGADOR_A,
            salidas_a=2, salidas_b=0, sin_progreso=7,
        )
        salida = [m for m in motor.movimientos_legales(estado)
                  if m.es_salida][0]
        nuevo = motor.aplicar(estado, salida)
        self.assertEqual(len(nuevo.fichas_a), 0)
        self.assertEqual(nuevo.salidas_a, 3)
        self.assertEqual(nuevo.sin_progreso, 0)

    def test_rechaza_movimiento_ilegal(self):
        ilegal = motor.Movimiento((0, 0), (0, -1), config.TIPO_LATERAL)
        with self.assertRaises(ValueError):
            motor.aplicar(self.estado, ilegal)


class PruebasCondicionesDeTermino(unittest.TestCase):

    def test_partida_recien_iniciada_no_es_terminal(self):
        estado = motor.estado_inicial(6)
        self.assertFalse(motor.es_terminal(estado))
        self.assertIsNone(motor.ganador(estado))

    def test_gana_quien_saca_todas_sus_fichas(self):
        n = 6
        estado = motor.Estado(
            n=n, fichas_a=frozenset(),
            fichas_b=frozenset({(n - 1, 1)}),
            turno=config.JUGADOR_B,
            salidas_a=n - 1, salidas_b=0, sin_progreso=0,
        )
        self.assertTrue(motor.es_terminal(estado))
        self.assertEqual(motor.ganador(estado), config.JUGADOR_A)

    def _estado_con_a_bloqueado(self):
        # A en la esquina superior izquierda, con el avance y el unico
        # lateral disponible tapados por fichas de B.
        n = 6
        return motor.Estado(
            n=n, fichas_a=frozenset({(0, 0)}),
            fichas_b=frozenset({(0, 1), (1, 0)}),
            turno=config.JUGADOR_A,
            salidas_a=0, salidas_b=0, sin_progreso=0,
        )

    def test_el_bloqueado_pierde_con_la_regla_del_enunciado(self):
        estado = self._estado_con_a_bloqueado()
        self.assertEqual(motor.movimientos_legales(estado), ())
        with mock.patch.object(config, "REGLA_BLOQUEO",
                               config.BLOQUEADO_PIERDE):
            self.assertTrue(motor.es_terminal(estado))
            self.assertEqual(motor.ganador(estado), config.JUGADOR_B)

    def test_la_regla_de_bloqueo_es_parametrizable(self):
        estado = self._estado_con_a_bloqueado()
        with mock.patch.object(config, "REGLA_BLOQUEO",
                               config.BLOQUEADO_GANA):
            self.assertEqual(motor.ganador(estado), config.JUGADOR_A)

    def test_tablas_por_falta_de_progreso(self):
        estado = motor.estado_inicial(6)._replace(sin_progreso=100)
        with mock.patch.object(config, "TABLAS_HABILITADAS", True):
            with mock.patch.object(config, "LIMITE_JUGADAS_SIN_PROGRESO",
                                   100):
                self.assertEqual(motor.ganador(estado), config.EMPATE)
        # Con la regla desactivada (valor por defecto) la partida sigue.
        self.assertIsNone(motor.ganador(estado))


class PruebasPartidaCompleta(unittest.TestCase):
    """Simulacion aleatoria: verifica invariantes a lo largo de una
    partida entera. Es el antecedente directo del bucle que en la Fase
    2 recorrera el arbol de Minimax."""

    def _jugar_al_azar(self, n, semilla, limite=4000):
        azar = random.Random(semilla)
        estado = motor.estado_inicial(n)
        total = motor.fichas_por_jugador(n)
        jugadas = 0

        while not motor.es_terminal(estado) and jugadas < limite:
            legales = motor.movimientos_legales(estado)
            self.assertTrue(legales, "estado sin jugadas no es terminal")
            estado = motor.aplicar(estado, azar.choice(legales))
            jugadas += 1

            # Invariante 1: fichas en tablero + fichas fuera = n - 1.
            self.assertEqual(len(estado.fichas_a) + estado.salidas_a, total)
            self.assertEqual(len(estado.fichas_b) + estado.salidas_b, total)
            # Invariante 2: nunca hay dos fichas en la misma casilla.
            self.assertEqual(estado.fichas_a & estado.fichas_b, frozenset())
            # Invariante 3: todas las fichas estan dentro del tablero.
            for casilla in estado.fichas_a | estado.fichas_b:
                self.assertTrue(motor.dentro_del_tablero(casilla, n))

        return estado, jugadas

    def test_las_partidas_aleatorias_terminan_con_ganador(self):
        for semilla in range(15):
            estado, jugadas = self._jugar_al_azar(6, semilla)
            self.assertTrue(
                motor.es_terminal(estado),
                "la partida %d no termino en %d jugadas" % (semilla, jugadas))
            self.assertIn(motor.ganador(estado), config.JUGADORES)

    def test_invariantes_en_tableros_grandes(self):
        for n in (8, 10):
            estado, _ = self._jugar_al_azar(n, semilla=n)
            self.assertTrue(motor.es_terminal(estado))


class PruebasParametrizacion(unittest.TestCase):
    """El motor debe obedecer a config.py, sin numeros magicos."""

    def test_la_colocacion_sigue_a_la_direccion_de_avance(self):
        # Se invierte el avance de A (ahora va hacia la izquierda):
        # sus fichas deben aparecer solas en la columna derecha.
        direcciones = dict(config.DIRECCION_AVANCE)
        direcciones[config.JUGADOR_A] = (0, -1)
        with mock.patch.object(config, "DIRECCION_AVANCE", direcciones):
            estado = motor.estado_inicial(6)
            columnas = {columna for _, columna in estado.fichas_a}
            self.assertEqual(columnas, {5})

    def test_los_limites_de_tamano_son_configurables(self):
        with mock.patch.object(config, "TAMANO_MINIMO_EXCLUSIVO", 2):
            self.assertTrue(motor.validar_n(4))
        self.assertFalse(motor.validar_n(4))


if __name__ == "__main__":
    unittest.main(verbosity=2)
