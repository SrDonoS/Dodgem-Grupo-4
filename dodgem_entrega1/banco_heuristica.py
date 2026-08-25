# -*- coding: utf-8 -*-
"""Banco de pruebas empirico de la heuristica.

    NO FORMA PARTE DE LA ENTREGA DE LA SEMANA 3.

Es una herramienta de medicion. El Minimax que aparece aqui es
deliberadamente minimo y esta solo para RESPONDER CON DATOS a las tres
preguntas que hara el profesor sobre la heuristica:

    1. "Es correcta?"  -> un agente guiado por ella, gana?
    2. "Sirve de algo el termino de restriccion, o basta la distancia?"
       -> se enfrentan las dos versiones entre si.
    3. "Es barata?"    -> cuantas evaluaciones por segundo se logran.

El Minimax de verdad, con su propia arquitectura y sus pruebas, es el
objetivo de la Fase 2.

Ejecutar con:
    python banco_heuristica.py
    python banco_heuristica.py --n 8 --partidas 20
"""

from __future__ import annotations

import argparse
import math
import random
import time
from typing import Callable, Optional, Tuple

import config
import heuristica
import motor

#: Tope de jugadas por partida. En tableros pares el Dodgem puede no
#: terminar si ambos bandos solo esquivan; sin este tope el banco
#: podria quedarse colgado.
LIMITE_JUGADAS = 400

INFINITO = float("inf")


# =====================================================================
# MINIMAX MINIMO (solo instrumento de medicion)
# =====================================================================


class Contador(object):
    """Lleva la cuenta de nodos evaluados, para medir el coste."""

    def __init__(self):
        self.nodos = 0


def _buscar(estado: motor.Estado, profundidad: int, alfa: float,
            beta: float, jugador_max: str, ply: int,
            contador: Contador,
            funcion_evaluar: Callable) -> Tuple[float, Optional[object]]:
    """Minimax con poda Alfa-Beta.

    El parametro `ply` es la profundidad acumulada desde la raiz, es
    decir g(n): se pasa a la funcion de evaluacion para que prefiera
    las victorias cercanas.
    """
    if profundidad == 0 or motor.es_terminal(estado):
        contador.nodos += 1
        return funcion_evaluar(estado, jugador_max, ply), None

    movimientos = motor.movimientos_legales(estado)
    mejor_movimiento = None

    if estado.turno == jugador_max:
        mejor = -INFINITO
        for movimiento in movimientos:
            valor, _ = _buscar(motor.aplicar(estado, movimiento),
                               profundidad - 1, alfa, beta, jugador_max,
                               ply + 1, contador, funcion_evaluar)
            if valor > mejor:
                mejor, mejor_movimiento = valor, movimiento
            alfa = max(alfa, mejor)
            if alfa >= beta:
                break            # Poda: el rival nunca entrara aqui.
        return mejor, mejor_movimiento

    mejor = INFINITO
    for movimiento in movimientos:
        valor, _ = _buscar(motor.aplicar(estado, movimiento),
                           profundidad - 1, alfa, beta, jugador_max,
                           ply + 1, contador, funcion_evaluar)
        if valor < mejor:
            mejor, mejor_movimiento = valor, movimiento
        beta = min(beta, mejor)
        if alfa >= beta:
            break
    return mejor, mejor_movimiento


def agente(profundidad: int, funcion_evaluar=heuristica.evaluar,
           semilla: int = 0):
    """Construye un jugador que busca con la heuristica indicada.

    DESEMPATE ALEATORIO (detalle metodologico importante). Un agente
    que ante varias jugadas de igual valor elige siempre la primera es
    completamente determinista: enfrentado a otro agente determinista
    produce SIEMPRE la misma partida. Medir "80 partidas" en esas
    condiciones no da 80 datos, da 2 repetidos 40 veces, y cualquier
    porcentaje calculado sobre ellos carece de sentido estadistico.

    Por eso, entre las jugadas empatadas en el mejor valor se elige
    una al azar con una semilla propia de cada partida. Asi cada
    partida explora una linea distinta y la muestra es real.

    Consecuencia: en la raiz NO se poda con alfa. Podar ahi devolveria
    cotas superiores en lugar de valores exactos para las jugadas
    inferiores, y el conjunto de empatados quedaria mal identificado.
    Las ramas internas si podan con normalidad.
    """
    azar = random.Random(semilla)

    def jugar(estado, contador):
        jugador_max = estado.turno
        mejor_valor = -INFINITO
        empatadas = []
        for movimiento in motor.movimientos_legales(estado):
            valor, _ = _buscar(motor.aplicar(estado, movimiento),
                               profundidad - 1, -INFINITO, INFINITO,
                               jugador_max, 1, contador, funcion_evaluar)
            if valor > mejor_valor:
                mejor_valor, empatadas = valor, [movimiento]
            elif valor == mejor_valor:
                empatadas.append(movimiento)
        return azar.choice(empatadas)

    jugar.nombre = "busqueda(prof=%d)" % profundidad
    return jugar


def agente_aleatorio(semilla: int):
    """Jugador de referencia: elige una jugada legal al azar."""
    azar = random.Random(semilla)

    def jugar(estado, contador):
        contador.nodos += 1
        return azar.choice(motor.movimientos_legales(estado))

    jugar.nombre = "aleatorio"
    return jugar


# =====================================================================
# HEURISTICA DE CONTRASTE (solo distancia)
# =====================================================================


def evaluar_solo_distancia(estado, jugador_max, profundidad=0):
    """Version reducida: solo el termino de pathfinding.

    Sirve para medir cuanto aporta realmente el bloque de restriccion
    (bloqueos, inmovilidad y movilidad). Si la heuristica completa no
    le ganara a esta, el termino de restriccion no estaria
    justificado.
    """
    resultado = motor.ganador(estado)
    if resultado is not None:
        if resultado == config.EMPATE:
            return config.VALOR_EMPATE
        if resultado == jugador_max:
            return config.VICTORIA - profundidad
        return -config.VICTORIA + profundidad

    rival = motor.oponente(jugador_max)
    return float(heuristica.distancia_total(estado, rival)
                 - heuristica.distancia_total(estado, jugador_max))


# =====================================================================
# PARTIDAS
# =====================================================================


def jugar_partida(n, jugador_de_a, jugador_de_b, contador):
    """Juega una partida completa.

    Devuelve (ganador, motivo), donde el motivo distingue COMO se
    gano: sacando todas las fichas o dejando al rival sin jugadas.
    Saber que proporcion de victorias viene de cada via es lo que
    permite explicar el comportamiento del agente en vez de solo
    contar puntos.
    """
    estado = motor.estado_inicial(n)
    jugadores = {config.JUGADOR_A: jugador_de_a,
                 config.JUGADOR_B: jugador_de_b}
    for _ in range(LIMITE_JUGADAS):
        if motor.es_terminal(estado):
            ganador = motor.ganador(estado)
            if ganador == config.EMPATE:
                return None, "tablas"
            if not motor.fichas_de(estado, ganador):
                return ganador, "salida"
            return ganador, "bloqueo"
        movimiento = jugadores[estado.turno](estado, contador)
        estado = motor.aplicar(estado, movimiento)
    return None, "limite"


def enfrentar(n, constructor_uno, constructor_dos, partidas, etiquetas):
    """Juega un match alternando quien abre, y resume el resultado.

    Alternar el color es imprescindible: en Dodgem mover primero es
    una ventaja, asi que un match a un solo color no mide la calidad
    de la heuristica sino el valor del tempo.
    """
    marcador = {etiquetas[0]: 0, etiquetas[1]: 0, "sin resolver": 0}
    motivos = {"salida": 0, "bloqueo": 0, "tablas": 0, "limite": 0}
    contador = Contador()
    inicio = time.time()

    for numero in range(partidas):
        uno = constructor_uno(numero)
        dos = constructor_dos(numero)
        if numero % 2 == 0:
            ganador, motivo = jugar_partida(n, uno, dos, contador)
            de_a, de_b = etiquetas[0], etiquetas[1]
        else:
            ganador, motivo = jugar_partida(n, dos, uno, contador)
            de_a, de_b = etiquetas[1], etiquetas[0]

        motivos[motivo] += 1
        if ganador == config.JUGADOR_A:
            marcador[de_a] += 1
        elif ganador == config.JUGADOR_B:
            marcador[de_b] += 1
        else:
            marcador["sin resolver"] += 1

    return marcador, time.time() - inicio, contador.nodos, motivos


def intervalo_confianza(victorias, total):
    """Intervalo de confianza del 95% para una proporcion de victorias.

    Aproximacion normal. Sirve para no sacar conclusiones de una
    diferencia que cabe dentro del ruido: con 60 partidas, un 55% de
    victorias todavia es compatible con dos agentes equivalentes.
    """
    if total == 0:
        return 0.0, 0.0
    proporcion = victorias / float(total)
    margen = 1.96 * math.sqrt(proporcion * (1 - proporcion) / total)
    return (max(0.0, proporcion - margen) * 100,
            min(1.0, proporcion + margen) * 100)


# =====================================================================
# MEDICION DE COSTE
# =====================================================================


def medir_coste(n, repeticiones=20000):
    """Evaluaciones por segundo de heuristica_dodgem()."""
    azar = random.Random(7)
    estados = []
    estado = motor.estado_inicial(n)
    while len(estados) < 40 and not motor.es_terminal(estado):
        estados.append(estado)
        estado = motor.aplicar(
            estado, azar.choice(motor.movimientos_legales(estado)))

    inicio = time.time()
    for indice in range(repeticiones):
        heuristica.heuristica_dodgem(estados[indice % len(estados)],
                                     config.JUGADOR_A)
    transcurrido = time.time() - inicio
    return repeticiones / transcurrido, transcurrido / repeticiones * 1e6


# =====================================================================
# INFORME
# =====================================================================


def main(argumentos=None):
    analizador = argparse.ArgumentParser(
        description="Banco de pruebas de la heuristica del Dodgem.")
    analizador.add_argument("--n", type=int, default=6)
    analizador.add_argument("--partidas", type=int, default=30)
    opciones = analizador.parse_args(argumentos)
    n = opciones.n
    partidas = opciones.partidas

    # Dentro del banco la busqueda solo aplica movimientos que ella
    # misma genero, asi que revalidarlos en aplicar() es trabajo
    # perdido. Es el interruptor documentado en config.py.
    config.VALIDAR_MOVIMIENTOS_AL_APLICAR = False

    print("=" * 66)
    print("BANCO DE PRUEBAS DE LA HEURISTICA  -  tablero %d x %d" % (n, n))
    print("=" * 66)

    print("\n1. COSTE DE UNA EVALUACION")
    print("-" * 66)
    for tamano in (n, 10, 16):
        por_segundo, microsegundos = medir_coste(tamano, 20000)
        print("   n = %-3d %10.0f evaluaciones/s   (%.1f us cada una)"
              % (tamano, por_segundo, microsegundos))

    print("\n2. LA HEURISTICA CONTRA UN JUGADOR ALEATORIO")
    print("-" * 66)
    print("   %d partidas por profundidad, alternando quien abre." % partidas)
    for profundidad in (1, 2, 3):
        marcador, segundos, nodos, motivos = enfrentar(
            n,
            lambda semilla, p=profundidad: agente(p, semilla=semilla),
            lambda semilla: agente_aleatorio(1000 + semilla),
            partidas, ("heuristica", "aleatorio"))
        victorias = marcador["heuristica"]
        bajo, alto = intervalo_confianza(victorias, partidas)
        print("   profundidad %d:  %2d-%2d   %3.0f%% "
              "[IC95: %.0f-%.0f%%]   %5.1f s, %d nodos"
              % (profundidad, victorias, marcador["aleatorio"],
                 100.0 * victorias / partidas, bajo, alto, segundos, nodos))
        print("                   fin por salida: %d, por bloqueo: %d"
              % (motivos["salida"], motivos["bloqueo"]))

    print("\n3. APORTE DEL TERMINO DE RESTRICCION")
    print("-" * 66)
    print("   Heuristica completa contra la version de SOLO DISTANCIA.")
    print("   A profundidad 1 no hay busqueda que compense: el")
    print("   resultado mide la evaluacion, no el arbol.")
    for profundidad in (1, 2):
        marcador, segundos, _, motivos = enfrentar(
            n,
            lambda semilla, p=profundidad: agente(
                p, heuristica.evaluar, semilla),
            lambda semilla, p=profundidad: agente(
                p, evaluar_solo_distancia, 500 + semilla),
            partidas * 2, ("completa", "solo distancia"))
        decididas = marcador["completa"] + marcador["solo distancia"]
        bajo, alto = intervalo_confianza(marcador["completa"], decididas)
        print("   profundidad %d:  completa %2d  -  solo distancia %2d"
              % (profundidad, marcador["completa"],
                 marcador["solo distancia"]))
        print("                   %.0f%% [IC95: %.0f-%.0f%%]   "
              "fin por salida: %d, por bloqueo: %d   (%.1f s)"
              % (100.0 * marcador["completa"] / max(1, decididas),
                 bajo, alto, motivos["salida"], motivos["bloqueo"],
                 segundos))
    print("   Si el intervalo contiene el 50%, la diferencia NO es")
    print("   estadisticamente significativa con esta muestra.")

    print("\n4. DESGLOSE DE UNA POSICION")
    print("-" * 66)
    azar = random.Random(3)
    estado = motor.estado_inicial(n)
    for _ in range(9):
        estado = motor.aplicar(
            estado, azar.choice(motor.movimientos_legales(estado)))
    print(motor.tablero_ascii(estado))
    print()
    print(heuristica.explicar(estado, config.JUGADOR_A))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
