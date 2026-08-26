# -*- coding: utf-8 -*-
"""Funcion de evaluacion heuristica del Dodgem (Semana 3).

===================================================================
IDEA CENTRAL: EL DODGEM ES UNA CARRERA DE DOS PATHFINDINGS
===================================================================

Cada ficha resuelve, por su cuenta, un problema de busqueda de camino:
partir de su casilla y alcanzar su carril de salida. La partida
completa es la superposicion de dos de esos problemas -uno por
jugador- que compiten por las mismas casillas. Evaluar una posicion es
entonces preguntarse: "de los dos corredores, cual esta mas cerca de
terminar su ruta, y cual esta mas estorbado".

De ahi salen los dos bloques de la formula:

    * PROGRESO   -> distancia que falta (busqueda informada / h(n))
    * RESTRICCION-> cuanto le estorbo al rival (bloqueos y movilidad)


-------------------------------------------------------------------
1. LA DISTANCIA MANHATTAN AL CARRIL DE SALIDA
-------------------------------------------------------------------

El objetivo de una ficha no es UNA casilla, sino un CONJUNTO de
casillas meta: cualquier casilla virtual situada justo despues de su
borde de salida. Para el jugador A (avanza al Este) ese conjunto es
{(f, n) : 0 <= f < n}.

La distancia Manhattan de una ficha a un conjunto es el minimo de las
distancias a sus elementos. Para una ficha de A en (f, c):

    h(f, c) = min  |f - f'| + |n - c|  =  n - c
              f'

porque el minimo se alcanza en f' = f. Es decir: la componente
vertical se anula y la distancia Manhattan al conjunto meta DEGENERA
en la distancia horizontal. Simetricamente, para B en (f, c) resulta
h = f + 1.

Esto NO es una simplificacion arbitraria: es el resultado exacto de
aplicar la definicion de distancia Manhattan a un objetivo que es una
linea completa y no un punto. Conviene tenerlo claro para la defensa,
porque a primera vista parece que "solo se usa una coordenada".

    ADMISIBILIDAD.  Sea el problema relajado en el que se eliminan
    todas las demas fichas. Una ficha a distancia d necesita entonces
    exactamente d movimientos (cada avance descuenta 1). Como los
    obstaculos solo pueden obligar a rodear, nunca a acortar, se
    cumple h(n) <= h*(n): la heuristica NUNCA sobreestima. Es
    admisible, y ademas es el optimo exacto de la relajacion.

    CONSISTENCIA.  Un movimiento legal cambia una sola coordenada en
    una unidad, luego |h(s) - h(s')| <= 1 = coste del movimiento. Se
    cumple h(s) <= c(s, s') + h(s'), la desigualdad triangular que
    exige A*.

    COTA INFERIOR DEL JUGADOR COMPLETO.  Sea D(J) = suma de las
    distancias de todas las fichas de J. Cada turno de J mueve UNA
    ficha UNA casilla: un avance (o salida) baja D en exactamente 1,
    un lateral la deja igual, porque el eje lateral es perpendicular
    al eje de salida. Por lo tanto cada turno reduce D como maximo en
    1, y J necesita AL MENOS D(J) turnos para ganar. D(J) es una cota
    inferior admisible del numero de jugadas que le faltan.

Esa ultima propiedad es la que da sentido a restar las distancias de
los dos jugadores: se comparan dos cotas inferiores de "turnos que me
faltan" contra "turnos que le faltan".


-------------------------------------------------------------------
2. DONDE APARECEN g(n) Y h(n)
-------------------------------------------------------------------

En A* se ordena la frontera por f(n) = g(n) + h(n). En un arbol de
juego con Minimax la analogia es directa pero conviene enunciarla con
precision, porque no son el mismo algoritmo:

    g(n)  ->  la PROFUNDIDAD del nodo: cuantas jugadas se han gastado
              para llegar hasta el. Es coste ya pagado y conocido.

    h(n)  ->  el valor que devuelve esta heuristica en las hojas del
              corte de profundidad: la estimacion de lo que falta,
              construida con las distancias Manhattan de ambos bandos.

    f(n)  ->  la funcion evaluar() de este modulo, que combina ambas:
              un final ganado vale VICTORIA - profundidad, de modo que
              entre dos victorias el agente elige la MAS CORTA, y
              entre dos derrotas la MAS LARGA. Ese descuento por
              profundidad es exactamente el papel de g(n).

Y el orden de exploracion: movimientos_legales() entrega primero las
salidas y los avances (config.ORDEN_TIPOS_MOVIMIENTO), que son las
jugadas que mas reducen h. Explorar primero lo que mas promete es lo
que hace que la poda Alfa-Beta corte antes, igual que en una busqueda
informada.


-------------------------------------------------------------------
3. LOS TRES CRITERIOS DE LA RUBRICA
-------------------------------------------------------------------

CORRECTA para el objetivo
    Es cero en la posicion inicial (simetrica) y crece de forma
    monotona con el progreso real: sacar una ficha, o acercarla a su
    carril, siempre sube el puntaje. Ademas es antisimetrica,
    H(s, A) = -H(s, B), condicion necesaria para usarla en Minimax de
    suma cero. Las pruebas unitarias verifican las tres cosas.

BARATA de calcular
    Un solo recorrido por las fichas de cada bando: O(n) casillas con
    consultas O(1) sobre frozenset. No construye matrices, no copia
    el estado y no explora el tablero completo (que seria O(n^2)).

EXPLICABLE
    Todos los pesos estan en config.py y todos estan expresados en la
    misma unidad: PASOS DE AVANCE. Un +6 significa literalmente "voy
    seis pasos adelante en la carrera". La funcion explicar() imprime
    la contribucion de cada termino para poder defenderla en pantalla.
"""

from __future__ import annotations

from typing import Dict, List, NamedTuple, Tuple

import config
import motor


# =====================================================================
# RASGOS DE UN JUGADOR
# =====================================================================


class Rasgos(NamedTuple):
    """Medidas objetivas de la situacion de un jugador.

    Se separan del calculo del puntaje a proposito: los rasgos son
    HECHOS del tablero (cuantos pasos faltan, cuantas fichas estan
    tapadas) y los pesos son OPINIONES sobre su importancia. Poder
    mostrar los rasgos por separado es lo que permite defender la
    formula y ajustarla sin reescribir nada.
    """

    distancia_total: int      # Suma de distancias Manhattan a la meta.
    fichas_fuera: int         # Fichas que ya abandonaron el tablero.
    bloqueadas_por_rival: int  # Avance tapado por una ficha enemiga.
    bloqueadas_por_propias: int  # Avance tapado por una ficha propia.
    inmovilizadas: int        # Sin ningun movimiento legal.
    movilidad: int            # Total de jugadas legales disponibles.


# =====================================================================
# DISTANCIA MANHATTAN AL CARRIL DE SALIDA
# =====================================================================


def _eje_de_salida(jugador: str) -> Tuple[int, int]:
    """Devuelve (indice del eje, sentido) del avance de un jugador.

    El eje es 0 para las filas y 1 para las columnas; el sentido es +1
    o -1. Se deduce de config.DIRECCION_AVANCE en lugar de escribirse
    a mano, de modo que si el profesor invierte la direccion de un
    jugador durante la interrogacion, la heuristica sigue midiendo la
    distancia hacia el carril correcto sin tocar este archivo.
    """
    delta_fila, delta_columna = config.DIRECCION_AVANCE[jugador]
    if delta_columna != 0:
        return 1, delta_columna
    return 0, delta_fila


def distancia_a_la_salida(casilla: motor.Casilla, n: int,
                          jugador: str) -> int:
    """Distancia Manhattan de una ficha a su conjunto de casillas meta.

    Es el numero EXACTO de movimientos de avance que necesitaria la
    ficha si el tablero estuviera vacio (el problema relajado), y por
    lo tanto una cota inferior admisible del numero real.

    Ejemplo con n = 6, jugador A (avanza al Este):
        columna 0 -> 6 pasos   (5 avances hasta la columna 5, + 1 para
                                cruzar el borde y salir)
        columna 5 -> 1 paso
    Una ficha nunca vale 0: mientras siga en el tablero le falta al
    menos el movimiento de salida.
    """
    eje, sentido = _eje_de_salida(jugador)
    coordenada = casilla[eje]
    if sentido > 0:
        # La meta esta pasado el indice n-1: faltan (n-1-coord)
        # avances mas el movimiento que cruza el borde.
        return n - coordenada
    # La meta esta pasado el indice 0.
    return coordenada + 1


def distancia_total(estado: motor.Estado, jugador: str) -> int:
    """Suma de las distancias de todas las fichas vivas del jugador.

    Cota inferior del numero de turnos que le faltan para ganar (ver
    la demostracion en la cabecera del modulo). Las fichas ya salidas
    no aparecen en el conjunto, asi que aportan 0 de forma natural.
    """
    return sum(distancia_a_la_salida(casilla, estado.n, jugador)
               for casilla in motor.fichas_de(estado, jugador))


def distancia_total_inicial(n: int) -> int:
    """Distancia total de un jugador en la posicion de apertura.

    Sirve como escala de referencia: n - 1 fichas, cada una a n pasos
    de su carril. Se usa en explicar() para expresar el progreso como
    porcentaje.
    """
    return motor.fichas_por_jugador(n) * n


# =====================================================================
# BLOQUEOS: EL TERMINO DE RESTRICCION
# =====================================================================


def _clasificar_bloqueo(casilla: motor.Casilla, estado: motor.Estado,
                        jugador: str, propias: frozenset,
                        rivales: frozenset) -> Tuple[int, int, int]:
    """Analiza el estorbo que sufre UNA ficha.

    Devuelve la terna (bloqueada_por_rival, bloqueada_por_propia,
    inmovilizada), con 0 o 1 en cada posicion.

    Criterio: una ficha esta "bloqueada" si la casilla que tiene
    justo delante -en su direccion de avance- esta ocupada. Ese es el
    estorbo que de verdad importa, porque es el unico que retrasa el
    descuento de su distancia Manhattan: los movimientos laterales no
    acercan la ficha a la meta.

    Caso especial: si el avance cae FUERA del tablero, la ficha esta
    en su carril de salida y puede irse siempre. Nunca se cuenta como
    bloqueada ni como inmovilizada, porque ninguna ficha rival puede
    ocupar una casilla que no existe.
    """
    n = estado.n
    avance = config.DIRECCION_AVANCE[jugador]
    frente = (casilla[0] + avance[0], casilla[1] + avance[1])

    if not motor.dentro_del_tablero(frente, n):
        return 0, 0, 0

    por_rival = 1 if frente in rivales else 0
    por_propia = 1 if frente in propias else 0
    if not (por_rival or por_propia):
        return 0, 0, 0

    # El frente esta tapado: solo queda esquivar de lado. Si tampoco
    # hay lateral libre, la ficha esta completamente inmovilizada.
    ocupadas = propias | rivales
    for lateral in config.DIRECCIONES_LATERALES[jugador]:
        destino = (casilla[0] + lateral[0], casilla[1] + lateral[1])
        if motor.dentro_del_tablero(destino, n) and destino not in ocupadas:
            return por_rival, por_propia, 0

    return por_rival, por_propia, 1


# =====================================================================
# EXTRACCION DE RASGOS
# =====================================================================


def extraer_rasgos(estado: motor.Estado, jugador: str) -> Rasgos:
    """Calcula de una sola pasada todas las medidas de un jugador.

    Coste: un recorrido sobre las n-1 fichas del bando, con tres
    consultas O(1) por ficha. No se construye ninguna matriz n x n.
    """
    propias = motor.fichas_de(estado, jugador)
    rivales = motor.fichas_de(estado, motor.oponente(jugador))

    distancia = 0
    bloqueadas_rival = 0
    bloqueadas_propias = 0
    inmovilizadas = 0

    for casilla in propias:
        distancia += distancia_a_la_salida(casilla, estado.n, jugador)
        por_rival, por_propia, inmovil = _clasificar_bloqueo(
            casilla, estado, jugador, propias, rivales)
        bloqueadas_rival += por_rival
        bloqueadas_propias += por_propia
        inmovilizadas += inmovil

    return Rasgos(
        distancia_total=distancia,
        fichas_fuera=motor.salidas_de(estado, jugador),
        bloqueadas_por_rival=bloqueadas_rival,
        bloqueadas_por_propias=bloqueadas_propias,
        inmovilizadas=inmovilizadas,
        movilidad=_contar_movilidad(estado, jugador),
    )


def _contar_movilidad(estado: motor.Estado, jugador: str) -> int:
    """Numero de jugadas legales que tendria el jugador si moviera.

    Se delega en motor.contar_movimientos_legales() en vez de
    reimplementar la regla aqui: la legalidad tiene UNA sola
    definicion, y vive en el motor.

    Se usa la version que CUENTA en lugar de len(movimientos_legales)
    porque esta ultima construye una tupla de objetos Movimiento y la
    ordena; en una funcion que el arbol de busqueda llama en cada
    hoja, ese trabajo desperdiciado domina el tiempo total. Medido en
    banco_heuristica.py, el cambio triplica las evaluaciones por
    segundo sin alterar ni un punto del resultado (lo verifica una
    prueba unitaria de equivalencia).
    """
    return motor.contar_movimientos_legales(estado, jugador)


# =====================================================================
# LA FUNCION HEURISTICA
# =====================================================================


def _signo_del_termino_de_inmovilidad() -> float:
    """Ajusta el termino de inmovilidad a la regla de bloqueo activa.

    Detalle facil de pasar por alto y que cambia el signo del
    resultado: con config.BLOQUEADO_PIERDE (regla del enunciado),
    dejar al rival sin jugadas es GANAR, asi que inmovilizarlo suma.
    Con la regla clasica config.BLOQUEADO_GANA ocurre lo contrario:
    quien bloquea es penalizado, de modo que inmovilizar al rival
    RESTA. Una heuristica que no siga a la regla activa empujaria al
    agente justo hacia la derrota.
    """
    if config.REGLA_BLOQUEO == config.BLOQUEADO_PIERDE:
        return 1.0
    return -1.0


def heuristica_dodgem(estado: motor.Estado, jugador_max: str) -> float:
    """Evalua una posicion desde el punto de vista de jugador_max.

    Signo: POSITIVO si la posicion favorece a jugador_max, NEGATIVO si
    favorece a su rival, y 0 si esta equilibrada. Como todos los
    terminos son diferencias entre los dos bandos, la funcion es
    antisimetrica por construccion:

        heuristica_dodgem(s, A) == -heuristica_dodgem(s, B)

    Escala: 1 punto = 1 paso de avance (config.W_DISTANCIA = 1.0).

    FORMULA COMPLETA

        H = W_DISTANCIA      * (D_min  - D_max)
          + W_SALIDA         * (F_max  - F_min)
          + W_BLOQUEO_RIVAL  * (BR_min - BR_max)
          + W_BLOQUEO_PROPIO * (BP_min - BP_max)
          + s * W_INMOVILIZADA * (I_min - I_max)
          + W_MOVILIDAD      * (M_max  - M_min)
          + W_TEMPO          * (+1 si mueve max, -1 si mueve min)

    donde D = distancia total, F = fichas fuera, BR = fichas tapadas
    por el rival, BP = fichas tapadas por companeras, I = fichas
    inmovilizadas, M = movilidad, y s es el signo que impone la regla
    de bloqueo activa.

    Notese que la distancia entra INVERTIDA (D_min - D_max): en un
    problema de pathfinding menos distancia es mejor, mientras que en
    una funcion de evaluacion mas puntaje es mejor. Restar al reves es
    el error de signo mas facil de cometer aqui.
    """
    jugador_min = motor.oponente(jugador_max)
    yo = extraer_rasgos(estado, jugador_max)
    rival = extraer_rasgos(estado, jugador_min)

    # --- Bloque PROGRESO: la carrera hacia el carril de salida ------
    # Cuanto menos me falta a mi frente a lo que le falta a el.
    progreso = config.W_DISTANCIA * (rival.distancia_total
                                     - yo.distancia_total)
    # Premio adicional por el progreso ya consolidado e irreversible.
    progreso += config.W_SALIDA * (yo.fichas_fuera - rival.fichas_fuera)

    # --- Bloque RESTRICCION: cuanto nos estorbamos -------------------
    # Sus fichas tapadas suman; las mias tapadas restan.
    restriccion = config.W_BLOQUEO_RIVAL * (rival.bloqueadas_por_rival
                                            - yo.bloqueadas_por_rival)
    restriccion += config.W_BLOQUEO_PROPIO * (rival.bloqueadas_por_propias
                                              - yo.bloqueadas_por_propias)
    restriccion += (_signo_del_termino_de_inmovilidad()
                    * config.W_INMOVILIZADA
                    * (rival.inmovilizadas - yo.inmovilizadas))
    restriccion += config.W_MOVILIDAD * (yo.movilidad - rival.movilidad)

    # --- Tempo: en una carrera, tener el turno vale medio paso -------
    tempo = config.W_TEMPO * (1.0 if estado.turno == jugador_max else -1.0)

    return progreso + restriccion + tempo


# =====================================================================
# PUENTE CON EL ARBOL DE BUSQUEDA:  f(n) = g(n) + h(n)
# =====================================================================


def cota_maxima_heuristica(n: int) -> float:
    """Cota superior (holgada) de |heuristica_dodgem| en un tablero n.

    Se obtiene sumando el maximo teorico de cada termino por separado.
    Es holgada a proposito -esos maximos no pueden darse todos a la
    vez- porque su unico uso es garantizar que config.VICTORIA queda
    por encima de cualquier puntaje heuristico posible. Sin esa
    garantia, Minimax podria preferir una posicion "bonita" antes que
    un final ganado.
    """
    fichas = motor.fichas_por_jugador(n)
    movimientos_por_ficha = 1 + len(
        config.DIRECCIONES_LATERALES[config.JUGADOR_A])
    return (
        config.W_DISTANCIA * fichas * n
        + config.W_SALIDA * fichas
        + config.W_BLOQUEO_RIVAL * fichas
        + config.W_BLOQUEO_PROPIO * fichas
        + config.W_INMOVILIZADA * fichas
        + config.W_MOVILIDAD * fichas * movimientos_por_ficha
        + config.W_TEMPO
    )


#: Centinela para distinguir "no me pasaron el resultado" de "el
#: resultado es None", que significa partida en curso.
SIN_CALCULAR = object()


def evaluar(estado: motor.Estado, jugador_max: str,
            profundidad: int = 0, resultado=SIN_CALCULAR) -> float:
    """Valor de un nodo del arbol: f(n) = g(n) + h(n).

    Es la funcion que llamara Minimax. Distingue dos situaciones:

    * NODO TERMINAL. El resultado ya no es una estimacion, es un
      hecho. Se devuelve +-VICTORIA corregida por la profundidad:

          ganar en la jugada 3  ->  VICTORIA - 3
          ganar en la jugada 7  ->  VICTORIA - 7   (menor: peor)

      Ese descuento es el termino g(n): entre dos victorias el agente
      escoge la mas rapida, y entre dos derrotas la mas lenta (que da
      mas oportunidades de que el rival se equivoque). Sin el, todas
      las victorias valdrian igual y el agente podria dar rodeos
      absurdos teniendo el remate disponible.

    * NODO DE CORTE. Se agoto la profundidad permitida y hay que
      estimar: se devuelve h(n) = heuristica_dodgem().

    Argumentos:
        estado:      posicion a evaluar.
        jugador_max: jugador cuyo punto de vista se adopta. Debe ser
                     SIEMPRE el mismo en toda la busqueda (el agente),
                     no el jugador que mueve en este nodo.
        profundidad: numero de jugadas desde la raiz, es decir g(n).
        resultado:   salida de motor.ganador(estado), si el llamador
                     ya la calculo. El buscador necesita conocer el
                     ganador ANTES de decidir si el nodo es hoja, y
                     volver a calcularlo aqui duplicaria el trabajo en
                     todas las hojas del arbol. Si no se pasa, se
                     calcula igual que siempre.
    """
    if resultado is SIN_CALCULAR:
        resultado = motor.ganador(estado)

    if resultado is None:
        return heuristica_dodgem(estado, jugador_max)
    if resultado == config.EMPATE:
        return config.VALOR_EMPATE
    if resultado == jugador_max:
        return config.VICTORIA - profundidad
    return -config.VICTORIA + profundidad


# =====================================================================
# EXPLICABILIDAD: DESGLOSE PARA LA DEFENSA
# =====================================================================


def desglosar(estado: motor.Estado,
              jugador_max: str) -> List[Tuple[str, float, str]]:
    """Descompone el puntaje en (nombre, aporte, detalle) por termino.

    Permite mostrar en la interrogacion de donde sale cada punto, en
    vez de exhibir un numero magico.
    """
    jugador_min = motor.oponente(jugador_max)
    yo = extraer_rasgos(estado, jugador_max)
    rival = extraer_rasgos(estado, jugador_min)
    signo = _signo_del_termino_de_inmovilidad()

    filas = [
        ("Distancia a la salida",
         config.W_DISTANCIA * (rival.distancia_total - yo.distancia_total),
         "me faltan %d pasos, a el %d"
         % (yo.distancia_total, rival.distancia_total)),
        ("Fichas ya fuera",
         config.W_SALIDA * (yo.fichas_fuera - rival.fichas_fuera),
         "%d contra %d" % (yo.fichas_fuera, rival.fichas_fuera)),
        ("Tapadas por el rival",
         config.W_BLOQUEO_RIVAL * (rival.bloqueadas_por_rival
                                   - yo.bloqueadas_por_rival),
         "mias %d, suyas %d" % (yo.bloqueadas_por_rival,
                                rival.bloqueadas_por_rival)),
        ("Atascos propios",
         config.W_BLOQUEO_PROPIO * (rival.bloqueadas_por_propias
                                    - yo.bloqueadas_por_propias),
         "mios %d, suyos %d" % (yo.bloqueadas_por_propias,
                                rival.bloqueadas_por_propias)),
        ("Fichas inmovilizadas",
         signo * config.W_INMOVILIZADA * (rival.inmovilizadas
                                          - yo.inmovilizadas),
         "mias %d, suyas %d" % (yo.inmovilizadas, rival.inmovilizadas)),
        ("Movilidad",
         config.W_MOVILIDAD * (yo.movilidad - rival.movilidad),
         "%d jugadas contra %d" % (yo.movilidad, rival.movilidad)),
        ("Tempo",
         config.W_TEMPO * (1.0 if estado.turno == jugador_max else -1.0),
         "mueve %s" % config.NOMBRES_JUGADORES[estado.turno]),
    ]
    return filas


def explicar(estado: motor.Estado, jugador_max: str) -> str:
    """Tabla en texto con el desglose del puntaje.

    Pensada para acompanar la defensa oral: se ejecuta sobre una
    posicion cualquiera y muestra por que la heuristica opina lo que
    opina.
    """
    lineas = [
        "Evaluacion desde el punto de vista de %s"
        % config.NOMBRES_JUGADORES[jugador_max],
        "-" * 62,
        "%-24s %9s   %s" % ("TERMINO", "APORTE", "DETALLE"),
    ]
    for nombre, aporte, detalle in desglosar(estado, jugador_max):
        lineas.append("%-24s %+9.1f   %s" % (nombre, aporte, detalle))
    lineas.append("-" * 62)
    lineas.append("%-24s %+9.1f   (1 punto = 1 paso de avance)"
                  % ("TOTAL", heuristica_dodgem(estado, jugador_max)))

    resultado = motor.ganador(estado)
    if resultado is not None:
        lineas.append("")
        lineas.append("Posicion TERMINAL: evaluar() devolveria %+.1f"
                      % evaluar(estado, jugador_max))
    return "\n".join(lineas)
