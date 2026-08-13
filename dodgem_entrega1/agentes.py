# -*- coding: utf-8 -*-
"""Agentes de busqueda no informada para Dodgem.

Este modulo encapsula dos estrategias de recorrido del arbol de juego:

* BFS: explora por capas, priorizando victorias en menor cantidad de
  jugadas.
* DFS: profundiza primero, devolviendo la primera victoria encontrada.

Si no se localiza una victoria dentro de los limites de exploracion,
el agente cae en un criterio local (heuristico) para seleccionar una
jugada razonable y mantener la partida en marcha.
"""

from __future__ import annotations

from collections import deque
from typing import Deque, List, NamedTuple, Optional, Set, Tuple

import config
import motor

ALGORITMO_BFS = "bfs"
ALGORITMO_DFS = "dfs"
ALGORITMO_JUGADOR = "jugador"
ALGORITMOS_DISPONIBLES = (ALGORITMO_JUGADOR, ALGORITMO_BFS, ALGORITMO_DFS)


class NodoBusqueda(NamedTuple):
    """Nodo del arbol de juego para exploracion BFS/DFS."""

    estado: motor.Estado
    primer_movimiento: motor.Movimiento
    profundidad: int


def validar_algoritmo(nombre: str) -> bool:
    """Indica si el identificador de algoritmo esta soportado."""
    return nombre in ALGORITMOS_DISPONIBLES


def elegir_movimiento(
    estado: motor.Estado,
    algoritmo: str,
    max_nodos: int,
    max_profundidad: int,
) -> motor.Movimiento:
    """Elige una jugada para el turno actual con BFS o DFS.

    La busqueda intenta encontrar un estado terminal ganador para el
    jugador en turno. Si no aparece en los limites dados, retorna una
    mejor jugada local segun una heuristica simple y determinista.
    """
    if not validar_algoritmo(algoritmo):
        raise ValueError("Algoritmo desconocido: %s" % algoritmo)
    if algoritmo == ALGORITMO_JUGADOR:
        raise ValueError("El modelo 'jugador' no elige jugadas automaticamente.")

    legales = motor.movimientos_legales(estado)
    if not legales:
        raise ValueError("No hay movimientos legales para el estado actual.")
    if len(legales) == 1:
        return legales[0]

    jugador_objetivo = estado.turno
    frontera, visitados = _inicializar_frontera(estado, legales)

    mejor = _mejor_movimiento_local(estado, legales)
    nodos_explorados = len(frontera)

    while frontera and nodos_explorados <= max_nodos:
        nodo = frontera.popleft() if algoritmo == ALGORITMO_BFS else frontera.pop()
        estado_actual = nodo.estado

        if estado_actual in visitados:
            continue
        visitados.add(estado_actual)

        ganador = motor.ganador(estado_actual)
        if ganador == jugador_objetivo:
            return nodo.primer_movimiento
        if ganador is not None:
            continue
        if nodo.profundidad >= max_profundidad:
            continue

        hijos = _expandir_nodo(estado_actual, nodo.primer_movimiento, nodo.profundidad)
        nodos_explorados += len(hijos)

        if algoritmo == ALGORITMO_BFS:
            frontera.extend(hijos)
        else:
            # En DFS apilamos en orden inverso para respetar el orden
            # natural de movimientos al hacer pop().
            for hijo in reversed(hijos):
                frontera.append(hijo)

    return mejor


def _inicializar_frontera(
    estado: motor.Estado,
    legales: Tuple[motor.Movimiento, ...],
) -> Tuple[Deque[NodoBusqueda], Set[motor.Estado]]:
    """Prepara la frontera inicial aplicando cada jugada legal."""
    frontera: Deque[NodoBusqueda] = deque()
    visitados: Set[motor.Estado] = {estado}
    for movimiento in legales:
        hijo = motor.aplicar(estado, movimiento)
        frontera.append(NodoBusqueda(hijo, movimiento, 1))
    return frontera, visitados


def _expandir_nodo(
    estado: motor.Estado,
    primer_movimiento: motor.Movimiento,
    profundidad: int,
) -> List[NodoBusqueda]:
    """Genera nodos hijos preservando el primer movimiento de la rama."""
    hijos: List[NodoBusqueda] = []
    for movimiento in motor.movimientos_legales(estado):
        estado_hijo = motor.aplicar(estado, movimiento)
        hijos.append(NodoBusqueda(estado_hijo, primer_movimiento, profundidad + 1))
    return hijos


def _mejor_movimiento_local(
    estado: motor.Estado,
    legales: Tuple[motor.Movimiento, ...],
) -> motor.Movimiento:
    """Desempate local cuando BFS/DFS no cierra una victoria."""
    jugador = estado.turno
    rival = motor.oponente(jugador)
    salidas_base = motor.salidas_de(estado, jugador)

    mejor_indice = 0
    mejor_puntaje: Optional[Tuple[int, int, int, int, int]] = None
    for indice, movimiento in enumerate(legales):
        hijo = motor.aplicar(estado, movimiento)
        progreso = motor.salidas_de(hijo, jugador) - salidas_base
        movilidad_rival = len(motor.movimientos_legales(hijo))
        fichas_rival = len(motor.fichas_de(hijo, rival))
        fichas_propias = len(motor.fichas_de(hijo, jugador))
        bono_tipo = 2 if movimiento.tipo == config.TIPO_SALIDA else 1 if movimiento.tipo == config.TIPO_AVANCE else 0

        puntaje = (
            progreso,
            bono_tipo,
            fichas_rival - fichas_propias,
            -movilidad_rival,
            -indice,
        )
        if mejor_puntaje is None or puntaje > mejor_puntaje:
            mejor_puntaje = puntaje
            mejor_indice = indice

    return legales[mejor_indice]