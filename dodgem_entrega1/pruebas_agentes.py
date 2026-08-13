# -*- coding: utf-8 -*-
"""Pruebas unitarias de agentes BFS/DFS para Dodgem."""

from __future__ import annotations

import unittest

import agentes
import config
import motor


class PruebasAgentes(unittest.TestCase):

    def test_valida_modelo_jugador(self):
        self.assertTrue(agentes.validar_algoritmo(agentes.ALGORITMO_JUGADOR))

    def test_retorna_movimiento_legal_en_estado_inicial(self):
        estado = motor.estado_inicial(6)
        legales = set(motor.movimientos_legales(estado))

        mov_bfs = agentes.elegir_movimiento(
            estado,
            agentes.ALGORITMO_BFS,
            max_nodos=300,
            max_profundidad=4,
        )
        mov_dfs = agentes.elegir_movimiento(
            estado,
            agentes.ALGORITMO_DFS,
            max_nodos=300,
            max_profundidad=4,
        )

        self.assertIn(mov_bfs, legales)
        self.assertIn(mov_dfs, legales)

    def test_rechaza_algoritmo_desconocido(self):
        estado = motor.estado_inicial(6)
        with self.assertRaises(ValueError):
            agentes.elegir_movimiento(
                estado,
                "ucs",
                max_nodos=100,
                max_profundidad=3,
            )

    def test_jugador_no_ejecuta_busqueda_automatica(self):
        estado = motor.estado_inicial(6)
        with self.assertRaises(ValueError):
            agentes.elegir_movimiento(
                estado,
                agentes.ALGORITMO_JUGADOR,
                max_nodos=100,
                max_profundidad=3,
            )

    def test_retorna_jugada_unica_sin_buscar(self):
        n = 6
        estado = motor.Estado(
            n=n,
            fichas_a=frozenset({(0, n - 1)}),
            fichas_b=frozenset({(1, n - 1)}),
            turno=config.JUGADOR_A,
            salidas_a=0,
            salidas_b=0,
            sin_progreso=0,
        )
        legales = motor.movimientos_legales(estado)
        self.assertEqual(len(legales), 1)

        elegido = agentes.elegir_movimiento(
            estado,
            agentes.ALGORITMO_BFS,
            max_nodos=50,
            max_profundidad=2,
        )
        self.assertEqual(elegido, legales[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
