# -*- coding: utf-8 -*-
"""Banco de medicion del agente Minimax.

    NO FORMA PARTE DE LA ENTREGA. Es una herramienta de medicion.

Responde con numeros a lo que preguntara el profesor sobre la Fase 2:

    1. "Cuanto ahorra realmente la poda Alfa-Beta?"
    2. "Y la tabla de transposiciones, aporta algo encima de la poda?"
    3. "Cuanto tarda por jugada? Se congelaria la interfaz?"
    4. "Un nivel alto le gana de verdad a uno bajo?"

Ejecutar con:
    python banco_agente.py
    python banco_agente.py --n 8 --partidas 12
"""

from __future__ import annotations

import argparse
import math
import random
import time

import agente
import config
import motor

LIMITE_JUGADAS = 400


def formatear(numero):
    """Separa los miles con espacios finos, mas legible en consola."""
    return "{:,}".format(int(numero)).replace(",", " ")


def intervalo_confianza(victorias, total):
    if total == 0:
        return 0.0, 0.0
    proporcion = victorias / float(total)
    margen = 1.96 * math.sqrt(proporcion * (1 - proporcion) / total)
    return (max(0.0, proporcion - margen) * 100,
            min(1.0, proporcion + margen) * 100)


# =====================================================================
# 1 y 2. CUANTO AHORRA CADA OPTIMIZACION
# =====================================================================


def medir_optimizaciones(n, profundidad_maxima):
    """Cuenta nodos con y sin cada optimizacion, sobre la apertura."""
    estado = motor.estado_inicial(n)
    print("   %-5s %14s %14s %14s %9s" %
          ("prof", "sin poda", "con poda", "poda+tabla", "ahorro"))
    print("   " + "-" * 60)

    for profundidad in range(1, profundidad_maxima + 1):
        crudo, nodos_crudo = agente.valor_con_alfa_beta(
            estado, profundidad, config.JUGADOR_A,
            usar_tabla=False, usar_poda=False)
        podado, nodos_poda = agente.valor_con_alfa_beta(
            estado, profundidad, config.JUGADOR_A,
            usar_tabla=False, usar_poda=True)
        con_tabla, nodos_tabla = agente.valor_con_alfa_beta(
            estado, profundidad, config.JUGADOR_A,
            usar_tabla=True, usar_poda=True)

        # Comprobacion en caliente: las tres busquedas deben coincidir.
        # Si alguna vez no coincidieran, la optimizacion estaria mal y
        # el numero de nodos no significaria nada.
        assert abs(crudo - podado) < 1e-6, "la poda altero el resultado"
        assert abs(crudo - con_tabla) < 1e-6, "la tabla altero el resultado"

        print("   %-5d %14s %14s %14s %8.1fx"
              % (profundidad, formatear(nodos_crudo), formatear(nodos_poda),
                 formatear(nodos_tabla),
                 nodos_crudo / float(max(1, nodos_tabla))))


def medir_factor_de_ramificacion(n):
    """Ramificacion media real frente a la efectiva tras podar.

    La ramificacion efectiva es la medida clasica de cuanto sirve la
    poda: es el numero de hijos que TENDRIA que tener un arbol sin
    poda para visitar los mismos nodos.
    """
    estado = motor.estado_inicial(n)
    ramificacion = len(motor.movimientos_legales(estado))
    profundidad = 5
    _, nodos = agente.valor_con_alfa_beta(
        estado, profundidad, config.JUGADOR_A, usar_tabla=False)
    efectiva = nodos ** (1.0 / profundidad)
    print("   Jugadas legales en la apertura: %d" % ramificacion)
    print("   Ramificacion efectiva tras podar (prof %d): %.2f"
          % (profundidad, efectiva))


# =====================================================================
# 3. TIEMPO POR JUGADA
# =====================================================================


def medir_tiempos():
    """Segundos por jugada en cada nivel y tamano de tablero.

    Es lo que justifica el tope de tiempo de seguridad: la profundidad
    manda, pero en tableros grandes una profundidad alta se dispara y
    sin tope el usuario veria la ventana congelada.
    """
    print("   %-10s %10s %10s %10s" % ("nivel", "n=6", "n=10", "n=16"))
    print("   " + "-" * 44)
    for nivel in config.ORDEN_NIVELES:
        columnas = []
        for n in (6, 10, 16):
            estado = motor.estado_inicial(n)
            # Se avanzan unas jugadas: la apertura es atipicamente
            # pobre en opciones y daria tiempos optimistas.
            azar = random.Random(5)
            for _ in range(6):
                estado = motor.aplicar(
                    estado, azar.choice(motor.movimientos_legales(estado)))
            cerebro = agente.AgenteMinimax(estado.turno, nivel)
            comienzo = time.time()
            resultado = cerebro.elegir(estado)
            transcurrido = time.time() - comienzo
            marca = "" if resultado.completa else "*"
            columnas.append("%.2fs%s" % (transcurrido, marca))
        print("   %-10s %10s %10s %10s"
              % (nivel, columnas[0], columnas[1], columnas[2]))
    print("   (*) el tope de tiempo corto la profundizacion iterativa.")


# =====================================================================
# 4. CALIDAD DE JUEGO
# =====================================================================


#: Jugadas al azar con que arranca cada partida del banco.
#: Los agentes son DETERMINISTAS: enfrentados desde la posicion
#: inicial producirian siempre la misma partida, y jugar diez seria
#: repetir una diez veces. Sembrar una apertura aleatoria distinta en
#: cada partida es lo que convierte el marcador en una muestra real.
JUGADAS_DE_APERTURA = 4


def jugar_partida(n, cerebros, aleatorio_para=None, semilla=0,
                  apertura=JUGADAS_DE_APERTURA):
    """Juega una partida entre agentes o contra un jugador aleatorio."""
    azar = random.Random(semilla)
    estado = motor.estado_inicial(n)

    # Apertura sembrada al azar (identica para los dos bandos, porque
    # se juega antes de que ninguno de los dos decida nada).
    for _ in range(apertura):
        if motor.es_terminal(estado):
            return motor.ganador(estado)
        estado = motor.aplicar(
            estado, azar.choice(motor.movimientos_legales(estado)),
            validar=False)

    for _ in range(LIMITE_JUGADAS):
        if motor.es_terminal(estado):
            return motor.ganador(estado)
        if estado.turno == aleatorio_para:
            movimiento = azar.choice(motor.movimientos_legales(estado))
        else:
            movimiento = cerebros[estado.turno].elegir(estado).movimiento
        estado = motor.aplicar(estado, movimiento, validar=False)
    return None


def enfrentar_niveles(n, nivel_uno, nivel_dos, partidas):
    """Match entre dos niveles, alternando quien abre."""
    marcador = {nivel_uno: 0, nivel_dos: 0, "sin resolver": 0}
    for numero in range(partidas):
        if numero % 2 == 0:
            asignacion = {config.JUGADOR_A: nivel_uno,
                          config.JUGADOR_B: nivel_dos}
        else:
            asignacion = {config.JUGADOR_A: nivel_dos,
                          config.JUGADOR_B: nivel_uno}
        cerebros = {jugador: agente.AgenteMinimax(jugador, nivel)
                    for jugador, nivel in asignacion.items()}
        ganador = jugar_partida(n, cerebros, semilla=numero)
        if ganador in config.JUGADORES:
            marcador[asignacion[ganador]] += 1
        else:
            marcador["sin resolver"] += 1
    return marcador


def enfrentar_aleatorio(n, nivel, partidas):
    victorias = 0
    decididas = 0
    for numero in range(partidas):
        agente_juega = (config.JUGADOR_A if numero % 2 == 0
                        else config.JUGADOR_B)
        rival = motor.oponente(agente_juega)
        cerebros = {agente_juega: agente.AgenteMinimax(agente_juega, nivel)}
        ganador = jugar_partida(n, cerebros, aleatorio_para=rival,
                                semilla=100 + numero)
        if ganador in config.JUGADORES:
            decididas += 1
            if ganador == agente_juega:
                victorias += 1
    return victorias, decididas


# =====================================================================
# INFORME
# =====================================================================


def main(argumentos=None):
    analizador = argparse.ArgumentParser(
        description="Banco de medicion del agente Minimax.")
    analizador.add_argument("--n", type=int, default=6)
    analizador.add_argument("--partidas", type=int, default=10)
    opciones = analizador.parse_args(argumentos)
    n = opciones.n

    print("=" * 66)
    print("BANCO DEL AGENTE MINIMAX  -  tablero %d x %d" % (n, n))
    print("=" * 66)

    print("\n1. NODOS VISITADOS SEGUN LA OPTIMIZACION")
    print("-" * 66)
    print("   Posicion inicial. Las tres columnas devuelven EL MISMO")
    print("   valor (se comprueba con assert); solo cambia el trabajo.")
    medir_optimizaciones(n, 5)

    print("\n2. RAMIFICACION")
    print("-" * 66)
    medir_factor_de_ramificacion(n)

    print("\n3. TIEMPO POR JUGADA")
    print("-" * 66)
    medir_tiempos()

    print("\n4. CALIDAD DE JUEGO")
    print("-" * 66)
    print("   Cada partida arranca con %d jugadas al azar: los agentes"
          % JUGADAS_DE_APERTURA)
    print("   son deterministas y sin eso se repetiria la misma partida.")
    for nivel in ("facil", "medio", "dificil"):
        victorias, decididas = enfrentar_aleatorio(n, nivel,
                                                   opciones.partidas)
        bajo, alto = intervalo_confianza(victorias, decididas)
        print("   %-8s contra aleatorio: %2d/%2d  [IC95: %.0f-%.0f%%]"
              % (nivel, victorias, decididas, bajo, alto))

    for uno, dos in (("medio", "facil"), ("dificil", "medio")):
        marcador = enfrentar_niveles(n, uno, dos, opciones.partidas)
        print("   %-8s contra %-8s: %2d - %2d  (sin resolver: %d)"
              % (uno, dos, marcador[uno], marcador[dos],
                 marcador["sin resolver"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
