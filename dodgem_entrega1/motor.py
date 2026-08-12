# -*- coding: utf-8 -*-
"""Motor del juego Dodgem: maquina de estados PURA.

Este modulo no imprime nada, no lee teclado, no dibuja y no guarda
estado global. Expone unicamente funciones que reciben un estado y
devuelven un valor nuevo. Esa disciplina es lo que permitira, en la
Fase 2, que Minimax con poda Alfa-Beta simule miles de partidas
hipoteticas sin corromper la partida real.

API exigida por el enunciado:
    validar_n(n)                -> bool
    estado_inicial(n)           -> Estado
    movimientos_legales(estado) -> tuple[Movimiento, ...]
    aplicar(estado, movimiento) -> Estado   (no muta el original)
    es_terminal(estado)         -> bool
    ganador(estado)             -> str | None

Decisiones de diseno relevantes para Minimax:

1. `Estado` es un NamedTuple de campos inmutables y `fichas_a` /
   `fichas_b` son frozenset. En consecuencia el estado completo es
   HASHABLE: puede usarse directamente como clave de un diccionario.
   Eso habilita gratis una tabla de transposiciones (memoizacion de
   posiciones ya evaluadas), que es la optimizacion que mas reduce el
   arbol de busqueda despues de la poda Alfa-Beta.

2. La inmutabilidad hace innecesario el patron "aplicar / deshacer"
   que obliga a restaurar el tablero al retroceder en la recursion.
   Minimax simplemente pasara el estado hijo a la llamada recursiva y
   el padre seguira intacto: cero errores por mutacion accidental.

3. Los conjuntos de fichas se guardan como frozenset de coordenadas y
   no como matriz n x n. La comprobacion "casilla ocupada" es O(1) y
   generar los movimientos cuesta O(fichas propias), no O(n^2). Con
   n - 1 fichas por bando esto importa cuando el buscador expande
   cientos de miles de nodos.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, List, NamedTuple, Optional, Set, Tuple

import config

# Alias de tipo: una casilla es un par (fila, columna) en base 0.
Casilla = Tuple[int, int]


# =====================================================================
# ESTRUCTURAS DE DATOS
# =====================================================================


class Movimiento(NamedTuple):
    """Una jugada individual, completamente descrita e inmutable.

    Atributos:
        origen:  casilla de partida, siempre dentro del tablero.
        destino: casilla de llegada. Si el tipo es TIPO_SALIDA, este
                 par cae deliberadamente FUERA del tablero (por ejemplo
                 (fila, n) para el jugador A). Conservar la coordenada
                 virtual permite que la interfaz dibuje la ficha
                 saliendo por el carril correcto y que el historial sea
                 reconstruible.
        tipo:    TIPO_AVANCE, TIPO_LATERAL o TIPO_SALIDA.
    """

    origen: Casilla
    destino: Casilla
    tipo: str

    @property
    def es_salida(self) -> bool:
        """Indica si la jugada retira la ficha de la partida."""
        return self.tipo == config.TIPO_SALIDA


class Estado(NamedTuple):
    """Fotografia completa e inmutable de una partida.

    Contiene todo lo necesario para decidir la siguiente jugada y nada
    mas. No guarda historial: el historial es responsabilidad de la
    interfaz, porque Minimax no lo necesita y arrastrarlo multiplicaria
    la memoria del arbol de busqueda.

    Atributos:
        n:            lado del tablero.
        fichas_a:     posiciones de las fichas del jugador A.
        fichas_b:     posiciones de las fichas del jugador B.
        turno:        jugador al que le toca mover.
        salidas_a:    fichas de A que ya abandonaron el tablero.
        salidas_b:    fichas de B que ya abandonaron el tablero.
        sin_progreso: jugadas consecutivas sin que salga ninguna ficha
                      (contador usado por la regla opcional de tablas).
    """

    n: int
    fichas_a: FrozenSet[Casilla]
    fichas_b: FrozenSet[Casilla]
    turno: str
    salidas_a: int
    salidas_b: int
    sin_progreso: int


# =====================================================================
# UTILIDADES INTERNAS
# =====================================================================


def oponente(jugador: str) -> str:
    """Devuelve el identificador del rival del jugador indicado."""
    if jugador == config.JUGADOR_A:
        return config.JUGADOR_B
    return config.JUGADOR_A


def fichas_de(estado: Estado, jugador: str) -> FrozenSet[Casilla]:
    """Devuelve el conjunto de fichas del jugador pedido."""
    if jugador == config.JUGADOR_A:
        return estado.fichas_a
    return estado.fichas_b


def salidas_de(estado: Estado, jugador: str) -> int:
    """Devuelve cuantas fichas del jugador ya salieron del tablero."""
    if jugador == config.JUGADOR_A:
        return estado.salidas_a
    return estado.salidas_b


def casillas_ocupadas(estado: Estado) -> FrozenSet[Casilla]:
    """Union de las fichas de ambos jugadores.

    Se calcula al inicio de movimientos_legales() una sola vez, en vez
    de consultar dos conjuntos por cada casilla candidata.
    """
    return estado.fichas_a | estado.fichas_b


def dentro_del_tablero(casilla: Casilla, n: int) -> bool:
    """Indica si la casilla pertenece al tablero n x n."""
    fila, columna = casilla
    return 0 <= fila < n and 0 <= columna < n


def fichas_por_jugador(n: int) -> int:
    """Cantidad de fichas con que arranca cada jugador (n - 1)."""
    return n - config.FICHAS_MENOS_QUE_LADO


def _linea_de_partida(n: int,
                      direccion_avance: Tuple[int, int]) -> List[Casilla]:
    """Calcula el borde donde se despliegan las fichas de un jugador.

    En Dodgem cada bando arranca pegado al borde OPUESTO a su direccion
    de avance, de modo que tenga el tablero completo por delante. En vez
    de escribir "A empieza en la columna 0" a mano, ese borde se DEDUCE
    del vector de avance declarado en config.DIRECCION_AVANCE.

    Consecuencia practica: si durante la interrogacion el profesor pide
    invertir el sentido de avance de un jugador, basta con cambiar el
    vector en config.py; la colocacion inicial se reacomoda sola y
    ninguna otra funcion necesita ser editada.
    """
    delta_fila, delta_columna = direccion_avance
    if delta_columna != 0:
        # Avance horizontal: la linea de partida es una COLUMNA entera.
        columna = 0 if delta_columna > 0 else n - 1
        return [(fila, columna) for fila in range(n)]
    # Avance vertical: la linea de partida es una FILA entera.
    fila = 0 if delta_fila > 0 else n - 1
    return [(fila, columna) for columna in range(n)]


def _clave_de_orden(movimiento: Movimiento) -> Tuple[int, int, int, int, int]:
    """Clave de ordenamiento estable para la lista de jugadas.

    Se ordena primero por tipo (segun config.ORDEN_TIPOS_MOVIMIENTO) y
    luego por coordenadas. Dos motivos:

    * Determinismo: la misma posicion produce siempre la misma lista,
      requisito para que las pruebas y la futura busqueda sean
      reproducibles.
    * Poda Alfa-Beta: examinar primero las salidas y los avances (las
      jugadas que mas suelen mejorar la posicion) provoca cortes mas
      tempranos, que es de donde viene casi toda la ganancia de la poda.
    """
    prioridad = config.ORDEN_TIPOS_MOVIMIENTO.index(movimiento.tipo)
    return (
        prioridad,
        movimiento.origen[0],
        movimiento.origen[1],
        movimiento.destino[0],
        movimiento.destino[1],
    )


# =====================================================================
# 1. VALIDACION DEL TAMANO DEL TABLERO
# =====================================================================


def validar_n(n: int) -> bool:
    """Indica si n es un tamano de tablero permitido.

    Reglas (todas parametrizadas en config.py):
        * n debe ser un entero.
        * n debe ser par              -> DIVISOR_PARIDAD / RESTO_PARIDAD
        * n debe ser mayor que 4      -> TAMANO_MINIMO_EXCLUSIVO
        * n no debe exceder el limite -> TAMANO_MAXIMO_TABLERO

    El cuarto criterio es una cota practica de la interfaz, no una regla
    del Dodgem; se puede elevar en config.py sin tocar este archivo.
    """
    if isinstance(n, bool) or not isinstance(n, int):
        return False
    if n % config.DIVISOR_PARIDAD != config.RESTO_PARIDAD_REQUERIDO:
        return False
    if n <= config.TAMANO_MINIMO_EXCLUSIVO:
        return False
    return n <= config.TAMANO_MAXIMO_TABLERO


def motivo_invalidez(n: object) -> Optional[str]:
    """Explica en castellano por que un tamano fue rechazado.

    Funcion auxiliar pensada para la interfaz: validar_n() responde
    solo True/False (contrato limpio para el motor), mientras que aqui
    se construye el mensaje que lee el usuario. Asi la logica de
    validacion no se duplica ni se contamina con texto.
    """
    if isinstance(n, bool) or not isinstance(n, int):
        return "El tamano debe ser un numero entero."
    if n % config.DIVISOR_PARIDAD != config.RESTO_PARIDAD_REQUERIDO:
        return "El tamano debe ser un numero par."
    if n <= config.TAMANO_MINIMO_EXCLUSIVO:
        return ("El tamano debe ser mayor que %d."
                % config.TAMANO_MINIMO_EXCLUSIVO)
    if n > config.TAMANO_MAXIMO_TABLERO:
        return ("El tamano maximo soportado es %d."
                % config.TAMANO_MAXIMO_TABLERO)
    return None


def tamanos_validos() -> Tuple[int, ...]:
    """Lista todos los tamanos aceptados, para poblar la interfaz."""
    limite = config.TAMANO_MAXIMO_TABLERO + 1
    return tuple(n for n in range(limite) if validar_n(n))


# =====================================================================
# 2. ESTADO INICIAL
# =====================================================================


def estado_inicial(n: int) -> Estado:
    """Construye la posicion de apertura de un tablero n x n.

    Disposicion oficial del Dodgem:
        * El jugador A ocupa la columna izquierda completa.
        * El jugador B ocupa la fila inferior completa.
        * La casilla comun a ambas lineas (la esquina inferior
          izquierda) queda VACIA.

    Al descontar esa esquina compartida, cada jugador queda
    automaticamente con n - 1 fichas, sin necesidad de contar a mano.

    Lanza:
        ValueError: si n no supera validar_n().
    """
    if not validar_n(n):
        raise ValueError(motivo_invalidez(n) or "Tamano de tablero invalido.")

    linea_a = _linea_de_partida(n, config.DIRECCION_AVANCE[config.JUGADOR_A])
    linea_b = _linea_de_partida(n, config.DIRECCION_AVANCE[config.JUGADOR_B])

    # La interseccion de ambas lineas es exactamente una casilla: la
    # esquina donde se cruzan los dos bordes de partida.
    esquina_compartida: Set[Casilla] = set(linea_a) & set(linea_b)
    if not config.ESQUINA_COMPARTIDA_VACIA:
        esquina_compartida = set()

    fichas_a = frozenset(linea_a) - esquina_compartida
    fichas_b = frozenset(linea_b) - esquina_compartida

    return Estado(
        n=n,
        fichas_a=fichas_a,
        fichas_b=fichas_b,
        turno=config.JUGADOR_INICIAL,
        salidas_a=0,
        salidas_b=0,
        sin_progreso=0,
    )


# =====================================================================
# 3. GENERACION DE MOVIMIENTOS LEGALES
# =====================================================================


def movimientos_legales(estado: Estado) -> Tuple[Movimiento, ...]:
    """Devuelve todas las jugadas legales del jugador en turno.

    Para cada ficha propia se prueban tres vectores: el de avance y los
    dos laterales. Un destino es aceptado si:

        a) cae dentro del tablero y la casilla esta vacia
           -> movimiento normal (no hay capturas ni saltos), o
        b) cae fuera del tablero PERO el vector usado era el de avance
           -> la ficha sale de la partida.

    La condicion (b) implementa por si sola las dos restricciones de
    salida del enunciado: A solo puede salir por el borde derecho y B
    solo por el borde superior. Un intento de salir lateralmente cae
    fuera del tablero con un vector que no es el de avance, y por lo
    tanto se descarta sin necesidad de escribir una regla aparte.

    Devuelve una tupla (inmutable) para que ninguna capa superior pueda
    alterar por accidente la lista de jugadas de un nodo del arbol.
    """
    jugador = estado.turno
    propias = fichas_de(estado, jugador)
    ocupadas = casillas_ocupadas(estado)

    avance = config.DIRECCION_AVANCE[jugador]
    laterales = config.DIRECCIONES_LATERALES[jugador]
    vectores: Tuple[Tuple[int, int], ...] = (avance,) + tuple(laterales)

    movimientos: List[Movimiento] = []
    for origen in propias:
        fila, columna = origen
        for vector in vectores:
            destino = (fila + vector[0], columna + vector[1])
            es_avance = vector == avance

            if not dentro_del_tablero(destino, estado.n):
                # Fuera del tablero: legal solo como salida frontal.
                if es_avance:
                    movimientos.append(
                        Movimiento(origen, destino, config.TIPO_SALIDA)
                    )
                continue

            if destino in ocupadas:
                # Sin capturas ni saltos: la casilla debe estar vacia.
                continue

            tipo = config.TIPO_AVANCE if es_avance else config.TIPO_LATERAL
            movimientos.append(Movimiento(origen, destino, tipo))

    movimientos.sort(key=_clave_de_orden)
    return tuple(movimientos)


def hay_movimientos_legales(estado: Estado) -> bool:
    """Version corto-circuitada de movimientos_legales().

    Para detectar un bloqueo basta con encontrar UNA jugada; construir
    y ordenar la lista completa es trabajo desperdiciado. En la Fase 2
    esta comprobacion se ejecuta en cada nodo del arbol, asi que la
    diferencia se acumula.
    """
    jugador = estado.turno
    ocupadas = casillas_ocupadas(estado)
    avance = config.DIRECCION_AVANCE[jugador]
    vectores = (avance,) + tuple(config.DIRECCIONES_LATERALES[jugador])

    for fila, columna in fichas_de(estado, jugador):
        for vector in vectores:
            destino = (fila + vector[0], columna + vector[1])
            if not dentro_del_tablero(destino, estado.n):
                if vector == avance:
                    return True
                continue
            if destino not in ocupadas:
                return True
    return False


# =====================================================================
# 4. APLICACION DE UNA JUGADA (funcion pura)
# =====================================================================


def aplicar(estado: Estado, movimiento: Movimiento) -> Estado:
    """Devuelve un estado NUEVO con la jugada aplicada.

    El estado recibido no se modifica en absoluto: se construyen
    conjuntos nuevos y se retorna una instancia distinta de Estado.
    Esta garantia es la que permitira a Minimax explorar ramas
    hipoteticas sin necesidad de deshacer jugadas al retroceder.

    Efectos de la jugada:
        * La ficha desaparece de su casilla de origen.
        * Si el movimiento es una salida, no reaparece y se incrementa
          el contador de salidas; en caso contrario ocupa el destino.
        * El turno pasa al rival (no se permite pasar el turno).
        * Se actualiza el contador de jugadas sin progreso.

    Lanza:
        ValueError: si el movimiento no es legal y la validacion esta
                    activada en config.VALIDAR_MOVIMIENTOS_AL_APLICAR.
    """
    if config.VALIDAR_MOVIMIENTOS_AL_APLICAR:
        if movimiento not in movimientos_legales(estado):
            raise ValueError(
                "Movimiento ilegal para el estado actual: %r" % (movimiento,)
            )

    jugador = estado.turno
    nuevas_fichas: Set[Casilla] = set(fichas_de(estado, jugador))
    nuevas_fichas.discard(movimiento.origen)

    salidas = salidas_de(estado, jugador)
    if movimiento.es_salida:
        salidas += 1
        sin_progreso = 0  # Sacar una ficha SI es progreso: se reinicia.
    else:
        nuevas_fichas.add(movimiento.destino)
        sin_progreso = estado.sin_progreso + 1

    campos: Dict[str, object] = {
        "turno": oponente(jugador),
        "sin_progreso": sin_progreso,
    }
    if jugador == config.JUGADOR_A:
        campos["fichas_a"] = frozenset(nuevas_fichas)
        campos["salidas_a"] = salidas
    else:
        campos["fichas_b"] = frozenset(nuevas_fichas)
        campos["salidas_b"] = salidas

    # _replace() es la API oficial de NamedTuple: NO muta, devuelve una
    # tupla nueva con los campos indicados reemplazados.
    return estado._replace(**campos)


# =====================================================================
# 5 y 6. CONDICIONES DE TERMINO
# =====================================================================


def ganador(estado: Estado) -> Optional[str]:
    """Devuelve el ganador, EMPATE, o None si la partida sigue.

    Orden de evaluacion (importa, porque las condiciones se solapan):

    1. Victoria por salida: un jugador sin fichas en el tablero saco
       todas las suyas y gana. Se comprueba primero porque es la
       condicion mas barata y la de mayor prioridad.
    2. Tablas por falta de progreso, si la regla esta habilitada.
    3. Bloqueo: si el jugador en turno conserva fichas pero no tiene
       ninguna jugada legal, se resuelve segun config.REGLA_BLOQUEO.
       Se evalua al ultimo porque es la comprobacion mas costosa.
    """
    if not estado.fichas_a:
        return config.JUGADOR_A
    if not estado.fichas_b:
        return config.JUGADOR_B

    if config.TABLAS_HABILITADAS:
        if estado.sin_progreso >= config.LIMITE_JUGADAS_SIN_PROGRESO:
            return config.EMPATE

    if not hay_movimientos_legales(estado):
        if config.REGLA_BLOQUEO == config.BLOQUEADO_PIERDE:
            return oponente(estado.turno)
        return estado.turno

    return None


def es_terminal(estado: Estado) -> bool:
    """Indica si la partida ha terminado.

    Se define como la negacion de "ganador() es None" para que ambas
    funciones no puedan desincronizarse: existe una sola definicion de
    fin de partida y vive en ganador().
    """
    return ganador(estado) is not None


def motivo_de_termino(estado: Estado) -> Optional[str]:
    """Describe en castellano por que termino la partida.

    Auxiliar de presentacion; el motor no la necesita.
    """
    resultado = ganador(estado)
    if resultado is None:
        return None
    if resultado == config.EMPATE:
        return "Tablas: se alcanzo el limite de jugadas sin progreso."
    if not fichas_de(estado, resultado):
        return "%s saco todas sus fichas del tablero." % (
            config.NOMBRES_JUGADORES[resultado]
        )
    bloqueado = oponente(resultado)
    if config.REGLA_BLOQUEO == config.BLOQUEADO_PIERDE:
        return "%s quedo sin movimientos legales y pierde." % (
            config.NOMBRES_JUGADORES[bloqueado]
        )
    return "%s quedo bloqueado y gana por la regla clasica." % (
        config.NOMBRES_JUGADORES[resultado]
    )


# =====================================================================
# UTILIDADES DE PRESENTACION Y DIAGNOSTICO
# =====================================================================


def a_coordenada_humana(casilla: Casilla) -> str:
    """Convierte (fila, columna) base 0 a la notacion del enunciado.

    El enunciado numera filas y columnas desde 1 (fila 1 = superior,
    columna n = derecha). La conversion vive aqui, en el borde del
    motor, para que el nucleo trabaje siempre en base 0.
    """
    fila, columna = casilla
    return "f%dc%d" % (fila + 1, columna + 1)


def describir_movimiento(movimiento: Movimiento, jugador: str) -> str:
    """Texto de una jugada para el historial de la interfaz."""
    etiqueta = config.NOMBRES_JUGADORES[jugador]
    if movimiento.es_salida:
        return "%s  %s  ->  SALE" % (
            etiqueta,
            a_coordenada_humana(movimiento.origen),
        )
    return "%s  %s  ->  %s  (%s)" % (
        etiqueta,
        a_coordenada_humana(movimiento.origen),
        a_coordenada_humana(movimiento.destino),
        movimiento.tipo,
    )


def tablero_ascii(estado: Estado) -> str:
    """Representacion en texto del tablero, util para depurar.

    No se usa para jugar (la partida corre en la interfaz grafica),
    pero permite verificar el estado por consola durante el desarrollo
    y sera practica para depurar el arbol de Minimax en la Fase 2.
    """
    simbolo_vacio = "."
    lineas: List[str] = []
    encabezado = "    " + " ".join(
        "%2d" % (columna + 1) for columna in range(estado.n)
    )
    lineas.append(encabezado)
    for fila in range(estado.n):
        celdas: List[str] = []
        for columna in range(estado.n):
            casilla = (fila, columna)
            if casilla in estado.fichas_a:
                celdas.append(config.JUGADOR_A)
            elif casilla in estado.fichas_b:
                celdas.append(config.JUGADOR_B)
            else:
                celdas.append(simbolo_vacio)
        lineas.append("%2d  " % (fila + 1) + "  ".join(celdas))
    lineas.append("")
    lineas.append(
        "Turno: %s | Fuera -> A: %d, B: %d"
        % (config.NOMBRES_JUGADORES[estado.turno],
           estado.salidas_a, estado.salidas_b)
    )
    return "\n".join(lineas)
