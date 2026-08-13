# -*- coding: utf-8 -*-
"""Punto de entrada del proyecto Dodgem (Entrega 1).

Uso tipico:
    python main.py                  # abre la pantalla de configuracion
    python main.py --n 8            # arranca directamente en 8 x 8
    python main.py --n 10 --diagnostico
                                    # imprime el estado inicial y sale

El parametro --n permite fijar el tamano del tablero "como entrada en
la ejecucion", tal como exige el enunciado, sin renunciar a poder
elegirlo tambien desde la interfaz grafica.
"""

from __future__ import annotations

import argparse
import sys

import config
import dodgem_entrega1.motor as motor


def construir_analizador() -> argparse.ArgumentParser:
    """Define los argumentos aceptados por linea de comandos."""
    analizador = argparse.ArgumentParser(
        prog="dodgem",
        description="Dodgem para dos jugadores humanos (Entrega 1).",
    )
    analizador.add_argument(
        "--n", type=int, default=None, metavar="TAMANO",
        help=("Lado del tablero. Debe ser par y mayor que %d "
              "(maximo %d). Si se omite, se elige en la interfaz."
              % (config.TAMANO_MINIMO_EXCLUSIVO,
                 config.TAMANO_MAXIMO_TABLERO)),
    )
    analizador.add_argument(
        "--diagnostico", action="store_true",
        help=("Imprime en consola el estado inicial y sus movimientos "
              "legales, sin abrir la interfaz. Util para depurar."),
    )
    return analizador


def imprimir_diagnostico(n: int) -> None:
    """Vuelca el estado inicial en texto plano.

    Sirve para comprobar rapidamente la disposicion de las fichas al
    cambiar parametros en config.py, y sera util para inspeccionar
    nodos del arbol de busqueda en la Fase 2.
    """
    estado = motor.estado_inicial(n)
    print("Tablero %d x %d  |  %d fichas por jugador"
          % (n, n, motor.fichas_por_jugador(n)))
    print()
    print(motor.tablero_ascii(estado))
    print()
    movimientos = motor.movimientos_legales(estado)
    print("Movimientos legales del turno inicial: %d" % len(movimientos))
    for movimiento in movimientos:
        print("   " + motor.describir_movimiento(movimiento, estado.turno))
    print()
    print("es_terminal:", motor.es_terminal(estado))
    print("ganador:", motor.ganador(estado))


def main(argumentos=None) -> int:
    """Rutina principal. Devuelve el codigo de salida del proceso."""
    opciones = construir_analizador().parse_args(argumentos)

    # Validacion temprana: si el usuario paso un n invalido, se avisa
    # con el mismo criterio que usa el motor.
    if opciones.n is not None and not motor.validar_n(opciones.n):
        print("Tamano invalido: %s" % motor.motivo_invalidez(opciones.n),
              file=sys.stderr)
        return 2

    if opciones.diagnostico:
        imprimir_diagnostico(opciones.n or config.TAMANO_POR_DEFECTO)
        return 0

    # La interfaz se importa aqui, y no arriba, para que --diagnostico
    # siga funcionando en equipos donde falte el modulo tkinter.
    try:
        import dodgem_entrega1.gui as gui
    except ImportError:
        print(
            "No se pudo cargar tkinter (interfaz grafica).\n"
            "En Debian/Ubuntu se instala con:  sudo apt install python3-tk\n"
            "Mientras tanto puedes usar:  python main.py --diagnostico",
            file=sys.stderr,
        )
        return 1

    gui.lanzar(opciones.n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
