# -*- coding: utf-8 -*-
"""Pruebas unitarias de la funcion heuristica.

Ejecutar con:
    python -m unittest pruebas_heuristica -v

Las pruebas estan agrupadas segun los tres criterios de la rubrica:
correcta para el objetivo, barata de calcular y explicable. Varias de
ellas verifican EMPIRICAMENTE las propiedades matematicas que se
afirman en la cabecera de heuristica.py (admisibilidad, consistencia y
la cota inferior del numero de turnos), de modo que la defensa no se
apoye solo en el argumento escrito.
"""

from __future__ import annotations

import random
import unittest
from unittest import mock

import config
import heuristica
import motor


def estados_de_una_partida(n, semilla, maximo=60):
    """Genera posiciones variadas jugando al azar.

    Se usa como banco de posiciones de prueba: cubre situaciones que
    no se pueden anticipar escribiendo tableros a mano.
    """
    azar = random.Random(semilla)
    estado = motor.estado_inicial(n)
    posiciones = [estado]
    while not motor.es_terminal(estado) and len(posiciones) < maximo:
        estado = motor.aplicar(
            estado, azar.choice(motor.movimientos_legales(estado)))
        posiciones.append(estado)
    return posiciones


# =====================================================================
# CRITERIO 1: CORRECTA PARA EL OBJETIVO
# =====================================================================


class PruebasDistanciaManhattan(unittest.TestCase):
    """La distancia debe medir pasos reales hacia el carril correcto."""

    def test_valores_conocidos_del_jugador_a(self):
        # A avanza al Este: la distancia solo depende de la columna.
        n = 6
        self.assertEqual(
            heuristica.distancia_a_la_salida((0, 0), n, config.JUGADOR_A), 6)
        self.assertEqual(
            heuristica.distancia_a_la_salida((3, 0), n, config.JUGADOR_A), 6)
        self.assertEqual(
            heuristica.distancia_a_la_salida((3, 5), n, config.JUGADOR_A), 1)

    def test_valores_conocidos_del_jugador_b(self):
        # B avanza al Norte: la distancia solo depende de la fila.
        n = 6
        self.assertEqual(
            heuristica.distancia_a_la_salida((5, 2), n, config.JUGADOR_B), 6)
        self.assertEqual(
            heuristica.distancia_a_la_salida((0, 2), n, config.JUGADOR_B), 1)

    def test_la_fila_no_afecta_a_a_y_la_columna_no_afecta_a_b(self):
        # Consecuencia de que la meta es una LINEA y no un punto: la
        # componente perpendicular de la distancia Manhattan se anula.
        n = 8
        for fila in range(n):
            self.assertEqual(
                heuristica.distancia_a_la_salida((fila, 3), n,
                                                 config.JUGADOR_A),
                heuristica.distancia_a_la_salida((0, 3), n,
                                                 config.JUGADOR_A))
        for columna in range(n):
            self.assertEqual(
                heuristica.distancia_a_la_salida((3, columna), n,
                                                 config.JUGADOR_B),
                heuristica.distancia_a_la_salida((3, 0), n,
                                                 config.JUGADOR_B))

    def test_es_exacta_en_el_problema_relajado(self):
        """Admisibilidad: h coincide con el optimo del tablero vacio.

        Se calcula por busqueda en anchura, con una implementacion
        independiente de la de heuristica.py, el minimo numero de
        movimientos que necesita una ficha sola para salir. Debe
        coincidir exactamente con la distancia Manhattan; como los
        obstaculos solo pueden alargar el camino, eso demuestra
        h <= h* en el problema real.
        """
        n = 6
        for jugador in config.JUGADORES:
            avance = config.DIRECCION_AVANCE[jugador]
            laterales = config.DIRECCIONES_LATERALES[jugador]
            for fila in range(n):
                for columna in range(n):
                    inicio = (fila, columna)
                    optimo = self._bfs_salida(inicio, n, avance, laterales)
                    estimado = heuristica.distancia_a_la_salida(
                        inicio, n, jugador)
                    self.assertEqual(estimado, optimo,
                                     "ficha %s de %s" % (inicio, jugador))

    @staticmethod
    def _bfs_salida(inicio, n, avance, laterales):
        """Minimo de movimientos para salir de un tablero vacio."""
        frontera = [(inicio, 0)]
        vistos = {inicio}
        while frontera:
            (fila, columna), pasos = frontera.pop(0)
            for vector in (avance,) + tuple(laterales):
                destino = (fila + vector[0], columna + vector[1])
                if not motor.dentro_del_tablero(destino, n):
                    if vector == avance:
                        return pasos + 1   # Movimiento de salida.
                    continue
                if destino not in vistos:
                    vistos.add(destino)
                    frontera.append((destino, pasos + 1))
        raise AssertionError("no hay salida posible")

    def test_cada_turno_reduce_la_distancia_total_a_lo_sumo_en_uno(self):
        """Verifica la cota inferior del numero de turnos.

        Es la propiedad clave del diseno: como un avance descuenta
        exactamente 1 y un lateral descuenta 0, la distancia total es
        una cota inferior admisible de los turnos que faltan.
        """
        for semilla in range(6):
            for estado in estados_de_una_partida(6, semilla):
                if motor.es_terminal(estado):
                    continue
                jugador = estado.turno
                antes = heuristica.distancia_total(estado, jugador)
                for movimiento in motor.movimientos_legales(estado):
                    despues = heuristica.distancia_total(
                        motor.aplicar(estado, movimiento), jugador)
                    esperado = antes - 1 if movimiento.tipo in (
                        config.TIPO_AVANCE, config.TIPO_SALIDA) else antes
                    self.assertEqual(despues, esperado)

    def test_las_fichas_fuera_no_suman_distancia(self):
        n = 6
        estado = motor.Estado(
            n=n, fichas_a=frozenset(), fichas_b=frozenset({(5, 1)}),
            turno=config.JUGADOR_B, salidas_a=5, salidas_b=0,
            sin_progreso=0)
        self.assertEqual(
            heuristica.distancia_total(estado, config.JUGADOR_A), 0)


class PruebasSignoYSimetria(unittest.TestCase):
    """El puntaje debe ser positivo para quien va ganando."""

    def test_es_antisimetrica(self):
        # Condicion necesaria para un Minimax de suma cero: lo que
        # gana uno lo pierde exactamente el otro.
        for semilla in range(8):
            for estado in estados_de_una_partida(6, semilla):
                desde_a = heuristica.heuristica_dodgem(
                    estado, config.JUGADOR_A)
                desde_b = heuristica.heuristica_dodgem(
                    estado, config.JUGADOR_B)
                self.assertAlmostEqual(desde_a, -desde_b, places=9)

    def test_la_posicion_inicial_solo_difiere_en_el_tempo(self):
        # La apertura del Dodgem es simetrica: misma distancia total,
        # mismas fichas, misma movilidad. La unica ventaja de A es
        # tener el turno, asi que el puntaje debe ser exactamente el
        # peso del tempo.
        for n in (6, 8, 10):
            estado = motor.estado_inicial(n)
            self.assertAlmostEqual(
                heuristica.heuristica_dodgem(estado, config.JUGADOR_A),
                config.W_TEMPO, places=9)

    def test_es_cero_en_la_apertura_si_se_ignora_el_tempo(self):
        with mock.patch.object(config, "W_TEMPO", 0.0):
            for n in (6, 8, 10, 12):
                estado = motor.estado_inicial(n)
                self.assertAlmostEqual(
                    heuristica.heuristica_dodgem(estado, config.JUGADOR_A),
                    0.0, places=9)

    def test_avanzar_mejora_el_puntaje(self):
        # Dos posiciones identicas salvo por una ficha de A que esta
        # una columna mas adelante. Mismo turno en ambas, para que el
        # termino de tempo no interfiera (en Minimax los hermanos
        # siempre comparten el jugador que mueve).
        n = 6
        base = dict(n=n, fichas_b=frozenset({(5, 3)}),
                    turno=config.JUGADOR_A, salidas_a=0, salidas_b=0,
                    sin_progreso=0)
        atras = motor.Estado(fichas_a=frozenset({(1, 1)}), **base)
        adelante = motor.Estado(fichas_a=frozenset({(1, 2)}), **base)
        self.assertGreater(
            heuristica.heuristica_dodgem(adelante, config.JUGADOR_A),
            heuristica.heuristica_dodgem(atras, config.JUGADOR_A))

    def test_sacar_una_ficha_mejora_el_puntaje(self):
        n = 6
        antes = motor.Estado(
            n=n, fichas_a=frozenset({(1, n - 1)}),
            fichas_b=frozenset({(5, 3)}), turno=config.JUGADOR_A,
            salidas_a=0, salidas_b=0, sin_progreso=0)
        salida = [m for m in motor.movimientos_legales(antes)
                  if m.es_salida][0]
        despues = motor.aplicar(antes, salida)
        # Se compara con el tempo neutralizado, porque al aplicar la
        # jugada el turno pasa al rival.
        with mock.patch.object(config, "W_TEMPO", 0.0):
            self.assertGreater(
                heuristica.heuristica_dodgem(despues, config.JUGADOR_A),
                heuristica.heuristica_dodgem(antes, config.JUGADOR_A))

    def test_favorece_a_quien_tiene_mas_fichas_fuera(self):
        n = 6
        estado = motor.Estado(
            n=n, fichas_a=frozenset({(2, 2)}), fichas_b=frozenset({(2, 4)}),
            turno=config.JUGADOR_A, salidas_a=3, salidas_b=0,
            sin_progreso=0)
        self.assertGreater(
            heuristica.heuristica_dodgem(estado, config.JUGADOR_A), 0)


class PruebasTerminoDeRestriccion(unittest.TestCase):
    """Deteccion de bloqueos: el segundo bloque de la formula."""

    def test_detecta_bloqueo_frontal_del_rival(self):
        # Ficha de A en (2,2) con una ficha de B justo delante, en
        # (2,3), y una lateral libre: bloqueada pero no inmovilizada.
        n = 6
        estado = motor.Estado(
            n=n, fichas_a=frozenset({(2, 2)}), fichas_b=frozenset({(2, 3)}),
            turno=config.JUGADOR_A, salidas_a=0, salidas_b=0,
            sin_progreso=0)
        rasgos = heuristica.extraer_rasgos(estado, config.JUGADOR_A)
        self.assertEqual(rasgos.bloqueadas_por_rival, 1)
        self.assertEqual(rasgos.bloqueadas_por_propias, 0)
        self.assertEqual(rasgos.inmovilizadas, 0)

    def test_distingue_el_atasco_propio(self):
        n = 6
        estado = motor.Estado(
            n=n, fichas_a=frozenset({(2, 2), (2, 3)}),
            fichas_b=frozenset({(5, 1)}), turno=config.JUGADOR_A,
            salidas_a=0, salidas_b=0, sin_progreso=0)
        rasgos = heuristica.extraer_rasgos(estado, config.JUGADOR_A)
        self.assertEqual(rasgos.bloqueadas_por_propias, 1)
        self.assertEqual(rasgos.bloqueadas_por_rival, 0)

    def test_detecta_ficha_inmovilizada(self):
        # A en la esquina superior izquierda con el frente y el unico
        # lateral disponible tapados: no tiene ninguna jugada.
        n = 6
        estado = motor.Estado(
            n=n, fichas_a=frozenset({(0, 0)}),
            fichas_b=frozenset({(0, 1), (1, 0)}), turno=config.JUGADOR_A,
            salidas_a=0, salidas_b=0, sin_progreso=0)
        rasgos = heuristica.extraer_rasgos(estado, config.JUGADOR_A)
        self.assertEqual(rasgos.inmovilizadas, 1)
        self.assertEqual(rasgos.movilidad, 0)
        # Las penalizaciones son ACUMULATIVAS: una ficha inmovilizada
        # tambien cuenta como bloqueada de frente, asi que siempre
        # pesa mas que un bloqueo simple.
        self.assertEqual(rasgos.bloqueadas_por_rival, 1)

    def test_una_ficha_en_el_carril_nunca_esta_bloqueada(self):
        # Su avance sale del tablero: ninguna ficha puede taparlo.
        n = 6
        estado = motor.Estado(
            n=n, fichas_a=frozenset({(2, n - 1)}),
            fichas_b=frozenset({(1, n - 1), (3, n - 1)}),
            turno=config.JUGADOR_A, salidas_a=0, salidas_b=0,
            sin_progreso=0)
        rasgos = heuristica.extraer_rasgos(estado, config.JUGADOR_A)
        self.assertEqual(rasgos.bloqueadas_por_rival, 0)
        self.assertEqual(rasgos.inmovilizadas, 0)

    def test_bloquear_al_rival_sube_el_puntaje(self):
        n = 6
        libre = motor.Estado(
            n=n, fichas_a=frozenset({(4, 4)}), fichas_b=frozenset({(2, 2)}),
            turno=config.JUGADOR_A, salidas_a=0, salidas_b=0,
            sin_progreso=0)
        # Misma distancia para ambos, pero ahora A tapa el avance de B.
        bloqueando = motor.Estado(
            n=n, fichas_a=frozenset({(1, 2)}), fichas_b=frozenset({(2, 2)}),
            turno=config.JUGADOR_A, salidas_a=0, salidas_b=0,
            sin_progreso=0)
        self.assertGreater(
            heuristica.heuristica_dodgem(bloqueando, config.JUGADOR_A),
            heuristica.heuristica_dodgem(libre, config.JUGADOR_A))

    def test_el_signo_sigue_a_la_regla_de_bloqueo_activa(self):
        """Con la regla clasica, inmovilizar al rival debe RESTAR.

        Es el detalle que mas facilmente produce un agente que juega a
        perder: si la regla premia al bloqueado, una heuristica que
        siga premiando el bloqueo empuja al agente hacia la derrota.
        """
        # B en (3,0): su avance (2,0) esta tapado, su lateral derecho
        # (3,1) tambien, y el izquierdo cae fuera del tablero (salir de
        # lado no es legal). Queda sin ninguna jugada.
        n = 6
        estado = motor.Estado(
            n=n, fichas_a=frozenset({(2, 0), (3, 1), (4, 4)}),
            fichas_b=frozenset({(3, 0)}), turno=config.JUGADOR_B,
            salidas_a=0, salidas_b=0, sin_progreso=0)
        rasgos_b = heuristica.extraer_rasgos(estado, config.JUGADOR_B)
        self.assertEqual(rasgos_b.inmovilizadas, 1)
        self.assertEqual(rasgos_b.movilidad, 0)

        with mock.patch.object(config, "REGLA_BLOQUEO",
                               config.BLOQUEADO_PIERDE):
            con_regla_del_enunciado = heuristica.heuristica_dodgem(
                estado, config.JUGADOR_A)
        with mock.patch.object(config, "REGLA_BLOQUEO",
                               config.BLOQUEADO_GANA):
            con_regla_clasica = heuristica.heuristica_dodgem(
                estado, config.JUGADOR_A)

        diferencia = 2 * config.W_INMOVILIZADA * rasgos_b.inmovilizadas
        self.assertAlmostEqual(
            con_regla_del_enunciado - con_regla_clasica, diferencia,
            places=9)


# =====================================================================
# PUENTE CON EL ARBOL:  f(n) = g(n) + h(n)
# =====================================================================


class PruebasEvaluar(unittest.TestCase):

    def _estado_ganado_por_a(self, n=6):
        return motor.Estado(
            n=n, fichas_a=frozenset(), fichas_b=frozenset({(5, 1)}),
            turno=config.JUGADOR_B, salidas_a=n - 1, salidas_b=0,
            sin_progreso=0)

    def test_la_victoria_supera_a_cualquier_heuristica(self):
        for n in motor.tamanos_validos():
            cota = heuristica.cota_maxima_heuristica(n)
            self.assertGreater(config.VICTORIA, cota,
                               "VICTORIA no domina la heuristica en n=%d" % n)

    def test_la_heuristica_nunca_excede_su_cota(self):
        for n in (6, 8, 10):
            cota = heuristica.cota_maxima_heuristica(n)
            for semilla in range(4):
                for estado in estados_de_una_partida(n, semilla):
                    valor = heuristica.heuristica_dodgem(
                        estado, config.JUGADOR_A)
                    self.assertLessEqual(abs(valor), cota)

    def test_prefiere_la_victoria_mas_rapida(self):
        # Es el papel de g(n): descontar el coste ya pagado.
        estado = self._estado_ganado_por_a()
        rapida = heuristica.evaluar(estado, config.JUGADOR_A, profundidad=2)
        lenta = heuristica.evaluar(estado, config.JUGADOR_A, profundidad=8)
        self.assertGreater(rapida, lenta)

    def test_prefiere_la_derrota_mas_lejana(self):
        estado = self._estado_ganado_por_a()
        pronta = heuristica.evaluar(estado, config.JUGADOR_B, profundidad=2)
        tardia = heuristica.evaluar(estado, config.JUGADOR_B, profundidad=8)
        self.assertLess(pronta, tardia)

    def test_los_terminales_tienen_el_signo_correcto(self):
        estado = self._estado_ganado_por_a()
        self.assertGreater(
            heuristica.evaluar(estado, config.JUGADOR_A), 0)
        self.assertLess(
            heuristica.evaluar(estado, config.JUGADOR_B), 0)

    def test_en_nodo_no_terminal_devuelve_la_heuristica(self):
        estado = motor.estado_inicial(6)
        self.assertAlmostEqual(
            heuristica.evaluar(estado, config.JUGADOR_A, profundidad=3),
            heuristica.heuristica_dodgem(estado, config.JUGADOR_A),
            places=9)

    def test_las_tablas_valen_cero(self):
        estado = motor.estado_inicial(6)._replace(sin_progreso=100)
        with mock.patch.object(config, "TABLAS_HABILITADAS", True):
            with mock.patch.object(config, "LIMITE_JUGADAS_SIN_PROGRESO",
                                   100):
                self.assertEqual(
                    heuristica.evaluar(estado, config.JUGADOR_A),
                    config.VALOR_EMPATE)


# =====================================================================
# CRITERIO 2 Y 3: BARATA Y EXPLICABLE
# =====================================================================


class PruebasCosteYExplicabilidad(unittest.TestCase):

    def test_no_muta_el_estado(self):
        # La heuristica cambia el turno internamente para medir la
        # movilidad del rival; debe hacerlo sobre una copia.
        estado = motor.estado_inicial(8)
        copia = motor.Estado(*estado)
        heuristica.heuristica_dodgem(estado, config.JUGADOR_A)
        self.assertEqual(estado, copia)

    def test_el_contador_rapido_coincide_con_la_lista(self):
        # La movilidad se mide con motor.contar_movimientos_legales(),
        # que evita construir y ordenar la lista. Esta prueba garantiza
        # que la version rapida no se desvia de la version canonica.
        for n in (6, 8):
            for semilla in range(5):
                for estado in estados_de_una_partida(n, semilla):
                    for jugador in config.JUGADORES:
                        con_turno = estado._replace(turno=jugador)
                        self.assertEqual(
                            motor.contar_movimientos_legales(estado, jugador),
                            len(motor.movimientos_legales(con_turno)))

    def test_es_determinista(self):
        estado = motor.estado_inicial(8)
        valores = {heuristica.heuristica_dodgem(estado, config.JUGADOR_A)
                   for _ in range(5)}
        self.assertEqual(len(valores), 1)

    def test_el_desglose_suma_el_total(self):
        # Requisito de explicabilidad: la tabla que se muestra en la
        # defensa tiene que cuadrar con el numero final.
        for semilla in range(5):
            for estado in estados_de_una_partida(6, semilla):
                total = sum(aporte for _, aporte, _ in
                            heuristica.desglosar(estado, config.JUGADOR_A))
                self.assertAlmostEqual(
                    total,
                    heuristica.heuristica_dodgem(estado, config.JUGADOR_A),
                    places=9)

    def test_explicar_produce_texto(self):
        texto = heuristica.explicar(motor.estado_inicial(6),
                                    config.JUGADOR_A)
        self.assertIn("TOTAL", texto)
        self.assertIn("Distancia a la salida", texto)

    def test_los_pesos_son_configurables(self):
        # Sin peso de distancia y sin tempo, dos posiciones que solo
        # difieren en el avance deben puntuar igual.
        n = 6
        base = dict(n=n, fichas_b=frozenset({(5, 3)}),
                    turno=config.JUGADOR_A, salidas_a=0, salidas_b=0,
                    sin_progreso=0)
        atras = motor.Estado(fichas_a=frozenset({(1, 1)}), **base)
        adelante = motor.Estado(fichas_a=frozenset({(1, 2)}), **base)
        with mock.patch.object(config, "W_DISTANCIA", 0.0):
            self.assertAlmostEqual(
                heuristica.heuristica_dodgem(atras, config.JUGADOR_A),
                heuristica.heuristica_dodgem(adelante, config.JUGADOR_A),
                places=9)


if __name__ == "__main__":
    unittest.main(verbosity=2)
