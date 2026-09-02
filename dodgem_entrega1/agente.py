# -*- coding: utf-8 -*-
"""Agente Minimax con poda Alfa-Beta para el Dodgem (Fase 2).

Este modulo es el "cerebro". No dibuja, no lee teclado y no conoce
Tkinter: recibe un estado y devuelve la jugada que considera mejor.
Puede ejecutarse en un hilo aparte porque no toca nada compartido -el
motor es puro y las unicas estructuras mutables (tabla y contadores)
pertenecen a la instancia del agente-.

===================================================================
COMO FUNCIONA
===================================================================

1. MINIMAX
   Dos jugadores con intereses opuestos. En los nodos del agente se
   toma el maximo y en los del rival el minimo, suponiendo que el
   rival juega lo mejor posible. Las hojas se puntuan con
   heuristica.evaluar(), es decir f(n) = g(n) + h(n).

2. PODA ALFA-BETA
   alfa = lo mejor que MAX tiene asegurado hasta ahora.
   beta  = lo mejor que MIN tiene asegurado hasta ahora.
   Cuando alfa >= beta, la rama que se esta explorando ya no puede
   influir en la decision: el jugador de arriba ya tiene una opcion
   al menos igual de buena y nunca elegira esta. Se corta.

   La poda NO cambia el resultado, solo el trabajo: devuelve
   exactamente el mismo valor que un Minimax sin poda. Eso no se
   afirma de palabra, se comprueba en pruebas_agente.py comparando
   ambas busquedas nodo por nodo sobre decenas de posiciones.

3. ORDENAMIENTO DE JUGADAS
   Alfa-Beta poda mas cuanto antes aparezca la mejor jugada. Se usan
   dos fuentes de orden:
     * el orden natural de motor.movimientos_legales(): primero las
       salidas y los avances, que son las jugadas que mas reducen la
       distancia a la meta;
     * la mejor jugada encontrada para esa misma posicion en una
       iteracion anterior, guardada en la tabla de transposiciones.

4. TABLA DE TRANSPOSICIONES
   Distintas secuencias de jugadas llevan a la misma posicion (una
   transposicion). Sin tabla, el arbol vuelve a evaluar ese subarbol
   entero cada vez. Aqui se aprovecha una decision de la Entrega 1:
   Estado es un NamedTuple de frozensets, o sea HASHABLE, y sirve
   directamente como clave de un diccionario.

5. PROFUNDIZACION ITERATIVA
   Se busca a profundidad 1, luego 2, luego 3... hasta la profundidad
   del nivel o hasta agotar el tope de tiempo. Parece un desperdicio
   repetir el trabajo, pero no lo es: cada iteracion deja en la tabla
   la mejor jugada de cada posicion, y esa informacion hace que la
   siguiente iteracion pode muchisimo mas. Ademas siempre hay una
   respuesta lista, que es lo que permite tener un tope de tiempo sin
   arriesgarse a devolver una busqueda a medias.

===================================================================
EL DETALLE DELICADO: PUNTAJES DE VICTORIA EN LA TABLA
===================================================================

evaluar() devuelve VICTORIA - profundidad para un final ganado, de
modo que el agente prefiera ganar cuanto antes. Ese valor depende de
DONDE esta el nodo en el arbol, no solo de la posicion.

Si se guardara tal cual en la tabla y luego se reutilizara desde otra
profundidad, el agente creeria tener una victoria mas cercana (o mas
lejana) de lo que es. Por eso, al guardar se convierte el puntaje a
"distancia desde este nodo" sumando la profundidad, y al leer se
deshace la conversion. Los puntajes heuristicos normales no se tocan.
"""

from __future__ import annotations

import time
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

import config
import heuristica
import motor

#: Banderas de la tabla de transposiciones.
EXACTO = "exacto"            # El valor guardado es el verdadero.
COTA_INFERIOR = "inferior"   # El verdadero es >= al guardado (corte beta).
COTA_SUPERIOR = "superior"   # El verdadero es <= al guardado (corte alfa).

INFINITO = float("inf")


class _BusquedaInterrumpida(Exception):
    """Se agoto el tiempo o el usuario cancelo la busqueda."""


class Entrada(NamedTuple):
    """Una posicion ya analizada, guardada en la tabla."""

    profundidad: int          # Profundidad RESTANTE con la que se analizo.
    valor: float              # Puntaje, ya normalizado (ver cabecera).
    bandera: str              # EXACTO, COTA_INFERIOR o COTA_SUPERIOR.
    mejor: Optional[motor.Movimiento]   # Para ordenar en el futuro.


class JugadaEvaluada(NamedTuple):
    """El veredicto del agente sobre UNA jugada de la raiz.

    Es la unidad de informacion que hace visible el razonamiento: por
    cada jugada que el agente podia hacer este turno, que puntaje le
    dio y como se compara con las demas.

    Atributos:
        movimiento: la jugada.
        valor:      su puntaje Minimax EXACTO, en la misma escala que
                    la heuristica (1 punto = 1 paso de avance).
        elegida:    True solo en la jugada que finalmente se juega.
        calidad:    posicion relativa dentro de este turno, de 0.0 (la
                    peor de las disponibles) a 1.0 (la mejor). Si todas
                    empatan, vale 1.0 para todas.

                    Se calcula AQUI y no en la interfaz a proposito:
                    decidir que jugada es "buena" es un juicio sobre el
                    juego, no una decision de presentacion. La interfaz
                    solo traduce ese numero a un color.
        etiqueta:   notacion breve lista para mostrar ("f1c1 -> f1c2").
    """

    movimiento: motor.Movimiento
    valor: float
    elegida: bool
    calidad: float
    etiqueta: str

    def texto(self) -> str:
        """Fila completa tal como se lee en el panel."""
        if abs(self.valor) >= config.UMBRAL_VICTORIA:
            puntaje = "GANA" if self.valor > 0 else "PIERDE"
        else:
            puntaje = "%+.1f pts" % self.valor
        marca = "  (Elegida)" if self.elegida else ""
        return "%s: %s%s" % (self.etiqueta, puntaje, marca)


class Resultado(NamedTuple):
    """Lo que devuelve el agente: la jugada y como llego a ella."""

    movimiento: motor.Movimiento
    valor: float
    profundidad: int          # Profundidad completada de verdad.
    nodos: int
    podas: int
    aciertos_tabla: int
    segundos: float
    completa: bool            # False si el tope de tiempo la corto.
    #: Todas las jugadas de la raiz con su puntaje, ordenadas de mejor
    #: a peor desde el punto de vista del agente. Vacia si el agente
    #: se creo con explicar=False.
    evaluaciones: Tuple[JugadaEvaluada, ...] = ()

    def resumen(self) -> str:
        """Linea legible para mostrar en la interfaz."""
        if abs(self.valor) >= config.UMBRAL_VICTORIA:
            veredicto = ("victoria forzada" if self.valor > 0
                         else "derrota forzada")
        else:
            veredicto = "%+.1f" % self.valor
        return ("prof %d%s  |  %s  |  %d nodos  |  %d podas  |  %.2f s"
                % (self.profundidad, "" if self.completa else "*",
                   veredicto, self.nodos, self.podas, self.segundos))


# =====================================================================
# NORMALIZACION DE PUNTAJES PARA LA TABLA
# =====================================================================


def _hacia_la_tabla(valor: float, ply: int) -> float:
    """Convierte un puntaje absoluto en distancia desde este nodo."""
    if valor >= config.UMBRAL_VICTORIA:
        return valor + ply
    if valor <= -config.UMBRAL_VICTORIA:
        return valor - ply
    return valor


def _desde_la_tabla(valor: float, ply: int) -> float:
    """Operacion inversa de _hacia_la_tabla()."""
    if valor >= config.UMBRAL_VICTORIA:
        return valor - ply
    if valor <= -config.UMBRAL_VICTORIA:
        return valor + ply
    return valor


# =====================================================================
# EL BUSCADOR
# =====================================================================


class _Buscador(object):
    """Una busqueda concreta: un estado raiz y un presupuesto.

    Se separa del agente porque el agente vive toda la partida
    (conserva la tabla) mientras que el buscador vive una sola jugada
    (conserva los contadores y el reloj).
    """

    def __init__(self, jugador_max, tabla, limite_tiempo=None,
                 cancelar=None, usar_tabla=True, usar_poda=True,
                 cortes_solo_exactos=False):
        self.jugador_max = jugador_max
        self.tabla = tabla
        self.limite_tiempo = limite_tiempo
        self.cancelar = cancelar
        self.usar_tabla = usar_tabla
        self.usar_poda = usar_poda
        # Cuando se necesitan puntajes EXACTOS para mostrarlos, la
        # tabla solo puede usarse para cortar si su entrada es EXACTA.
        # Una entrada de tipo COTA dice "el valor real es >= x" o
        # "<= x", y reutilizarla estrecharia la ventana de busqueda:
        # el valor que saldria seria una cota valida, pero no el
        # numero que queremos ensenar en pantalla. Las entradas de
        # cota se siguen usando para ORDENAR, que es gratis y seguro.
        self.cortes_solo_exactos = cortes_solo_exactos

        self.nodos = 0
        self.podas = 0
        self.aciertos_tabla = 0
        self._cuenta_atras = config.NODOS_ENTRE_COMPROBACIONES

    # -- control de tiempo y cancelacion -----------------------------

    def _comprobar_limites(self) -> None:
        """Revisa el reloj y la senal de cancelacion cada N nodos.

        Consultar el reloj en cada nodo costaria mas que evaluar la
        posicion. Se hace cada config.NODOS_ENTRE_COMPROBACIONES.
        """
        self._cuenta_atras -= 1
        if self._cuenta_atras > 0:
            return
        self._cuenta_atras = config.NODOS_ENTRE_COMPROBACIONES
        if self.cancelar is not None and self.cancelar.is_set():
            raise _BusquedaInterrumpida()
        if (self.limite_tiempo is not None
                and time.monotonic() >= self.limite_tiempo):
            raise _BusquedaInterrumpida()

    # -- ordenamiento -------------------------------------------------

    @staticmethod
    def _ordenar(movimientos: Sequence[motor.Movimiento],
                 sugerido: Optional[motor.Movimiento]):
        """Pone delante la mejor jugada conocida de esta posicion.

        Es la optimizacion mas rentable de todas: si la primera jugada
        examinada resulta ser la mejor, todas las demas se podan casi
        de inmediato.
        """
        if sugerido is None or sugerido not in movimientos:
            return movimientos
        resto = [m for m in movimientos if m != sugerido]
        return [sugerido] + resto

    # -- nucleo -------------------------------------------------------

    def _alfa_beta(self, estado: motor.Estado, restante: int,
                   alfa: float, beta: float, ply: int) -> float:
        """Valor Minimax del estado, con poda Alfa-Beta.

        Argumentos:
            restante: profundidad que aun se puede explorar.
            alfa/beta: ventana de busqueda heredada del padre.
            ply: profundidad desde la raiz, o sea g(n).
        """
        self.nodos += 1
        self._comprobar_limites()

        alfa_original = alfa
        beta_original = beta
        sugerido = None

        # --- consulta a la tabla de transposiciones ------------------
        if self.usar_tabla:
            entrada = self.tabla.get(estado)
            if entrada is not None:
                sugerido = entrada.mejor
                # Solo sirve si se analizo al menos tan a fondo como
                # necesitamos ahora; si no, se aprovecha unicamente
                # como pista de ordenamiento.
                if entrada.profundidad >= restante:
                    valor = _desde_la_tabla(entrada.valor, ply)
                    if entrada.bandera == EXACTO:
                        self.aciertos_tabla += 1
                        return valor
                    if not self.cortes_solo_exactos:
                        if entrada.bandera == COTA_INFERIOR:
                            alfa = max(alfa, valor)
                        else:
                            beta = min(beta, valor)
                        if alfa >= beta:
                            self.aciertos_tabla += 1
                            return valor

        # --- hoja: terminal o corte de profundidad -------------------
        # ganador() se calcula UNA vez y se le pasa a evaluar(), que si
        # no lo recalcularia en cada hoja del arbol.
        resultado = motor.ganador(estado)
        if resultado is not None or restante == 0:
            return heuristica.evaluar(estado, self.jugador_max, ply,
                                      resultado)

        movimientos = self._ordenar(motor.movimientos_legales(estado),
                                    sugerido)
        maximizando = estado.turno == self.jugador_max
        mejor_movimiento = None

        if maximizando:
            mejor = -INFINITO
            for movimiento in movimientos:
                hijo = motor.aplicar(estado, movimiento, validar=False)
                valor = self._alfa_beta(hijo, restante - 1, alfa, beta,
                                        ply + 1)
                if valor > mejor:
                    mejor, mejor_movimiento = valor, movimiento
                if mejor > alfa:
                    alfa = mejor
                if self.usar_poda and alfa >= beta:
                    # MIN ya tiene arriba una opcion de valor <= beta;
                    # nunca permitira llegar hasta aqui.
                    self.podas += 1
                    break
        else:
            mejor = INFINITO
            for movimiento in movimientos:
                hijo = motor.aplicar(estado, movimiento, validar=False)
                valor = self._alfa_beta(hijo, restante - 1, alfa, beta,
                                        ply + 1)
                if valor < mejor:
                    mejor, mejor_movimiento = valor, movimiento
                if mejor < beta:
                    beta = mejor
                if self.usar_poda and alfa >= beta:
                    self.podas += 1
                    break

        # --- guardado en la tabla ------------------------------------
        if self.usar_tabla:
            if mejor <= alfa_original:
                bandera = COTA_SUPERIOR   # Nunca supero alfa: es un techo.
            elif mejor >= beta_original:
                bandera = COTA_INFERIOR   # Corto por beta: es un piso.
            else:
                bandera = EXACTO
            self._guardar(estado, restante,
                          _hacia_la_tabla(mejor, ply), bandera,
                          mejor_movimiento)
        return mejor

    def _guardar(self, estado, profundidad, valor, bandera, mejor):
        """Escribe en la tabla, con reemplazo por profundidad.

        Si la entrada existente se analizo MAS a fondo que la nueva,
        se conserva: vale mas una respuesta mirando seis jugadas que
        una mirando dos. Al llenarse, la tabla se vacia entera; es la
        politica mas simple y basta porque se reinicia por partida.
        """
        anterior = self.tabla.get(estado)
        if anterior is not None and anterior.profundidad > profundidad:
            return
        if len(self.tabla) >= config.MAXIMO_ENTRADAS_TRANSPOSICION:
            self.tabla.clear()
        self.tabla[estado] = Entrada(profundidad, valor, bandera, mejor)

    # -- raiz ---------------------------------------------------------

    def buscar_raiz(self, estado: motor.Estado, profundidad: int,
                    preferido: Optional[motor.Movimiento] = None,
                    explicar: bool = False):
        """Explora la raiz. Devuelve (valor, mejor jugada, puntajes).

        La raiz se trata aparte por dos motivos. El primero es obvio:
        aqui si importa CUAL es la mejor jugada, no solo su valor. El
        segundo tiene que ver con poder ensenar el razonamiento.

        POR QUE `explicar` CAMBIA LA BUSQUEDA
        -------------------------------------
        En Alfa-Beta normal, la ventana de cada hermano se estrecha con
        lo que ya se sabe: si la jugada 1 vale 4, la jugada 2 se busca
        con alfa = 4, y en cuanto se demuestra que no llega a 4, se
        corta. Eso es exactamente lo que hace rapida a la poda... pero
        significa que el numero que devuelve la jugada 2 NO es su
        puntaje: es solo "algo <= 4". Publicar esa cifra en pantalla
        como "el puntaje de la jugada 2" seria mentir.

        Con explicar=True cada jugada de la raiz se busca con la
        ventana COMPLETA (-inf, +inf). Un nodo explorado con ventana
        completa no puede fallar ni por arriba ni por abajo, asi que su
        valor es el verdadero valor Minimax. Se pierde el ahorro de
        podar ENTRE hermanos -solo ahi, la poda dentro de cada rama
        sigue intacta- y a cambio la tabla que ve el usuario es cierta.

        La lista devuelta viene ordenada de mejor a peor DESDE EL PUNTO
        DE VISTA DEL AGENTE, que no es lo mismo que de mayor a menor
        valor: si el agente juega de MIN en este nodo, su mejor jugada
        es la de menor puntaje.
        """
        movimientos = self._ordenar(motor.movimientos_legales(estado),
                                    preferido)
        maximizando = estado.turno == self.jugador_max
        alfa, beta = -INFINITO, INFINITO
        mejor_valor = -INFINITO if maximizando else INFINITO
        mejor_movimiento = movimientos[0]
        puntajes: List[Tuple[motor.Movimiento, float]] = []

        for movimiento in movimientos:
            hijo = motor.aplicar(estado, movimiento, validar=False)
            if explicar:
                valor = self._alfa_beta(hijo, profundidad - 1,
                                        -INFINITO, INFINITO, 1)
                puntajes.append((movimiento, valor))
            else:
                valor = self._alfa_beta(hijo, profundidad - 1,
                                        alfa, beta, 1)
            if maximizando:
                if valor > mejor_valor:
                    mejor_valor, mejor_movimiento = valor, movimiento
                    alfa = max(alfa, valor)
            else:
                if valor < mejor_valor:
                    mejor_valor, mejor_movimiento = valor, movimiento
                    beta = min(beta, valor)

        if self.usar_tabla:
            self._guardar(estado, profundidad,
                          _hacia_la_tabla(mejor_valor, 0), EXACTO,
                          mejor_movimiento)

        evaluaciones = _construir_evaluaciones(puntajes, mejor_movimiento,
                                               maximizando)
        return mejor_valor, mejor_movimiento, evaluaciones


def _construir_evaluaciones(puntajes, elegida, maximizando):
    """Ordena los puntajes de la raiz y les asigna una calidad.

    `calidad` normaliza el puntaje al intervalo [0, 1] dentro de este
    turno: 1.0 es la mejor jugada disponible y 0.0 la peor. Sirve para
    que la interfaz pueda colorear sin tener que saber nada del juego
    -solo mapea un numero a un color-.

    Se normaliza por turno y no en una escala absoluta porque lo que
    interesa mostrar es la comparacion entre las opciones de AHORA. En
    una posicion donde todas las jugadas son malas, la "menos mala"
    sigue siendo la que el agente elige y merece destacarse.
    """
    if not puntajes:
        return ()

    valores = [valor for _, valor in puntajes]
    mejor = max(valores) if maximizando else min(valores)
    peor = min(valores) if maximizando else max(valores)
    rango = abs(mejor - peor)

    evaluadas = []
    for movimiento, valor in puntajes:
        if rango < 1e-9:
            calidad = 1.0          # Todas empatan.
        else:
            calidad = abs(valor - peor) / rango
        evaluadas.append(JugadaEvaluada(
            movimiento=movimiento,
            valor=valor,
            elegida=movimiento == elegida,
            calidad=calidad,
            etiqueta=motor.etiqueta_corta_de_movimiento(movimiento),
        ))

    # De mejor a peor para el agente. Los desempates, en orden:
    #   1. la jugada elegida va primera entre las que empatan, porque
    #      es confuso leer una lista donde la marcada "(Elegida)" no
    #      encabeza el grupo de las mejores;
    #   2. luego por etiqueta, para que el orden sea estable y la
    #      misma posicion produzca siempre la misma tabla.
    evaluadas.sort(key=lambda e: (-e.calidad, not e.elegida, e.etiqueta))
    return tuple(evaluadas)


# =====================================================================
# EL AGENTE
# =====================================================================


class AgenteMinimax(object):
    """Jugador automatico. Conserva su tabla durante la partida."""

    def __init__(self, jugador: str, nivel: Optional[str] = None,
                 profundidad: Optional[int] = None,
                 segundos: Optional[float] = None,
                 explicar: Optional[bool] = None):
        """Configura el agente.

        Argumentos:
            jugador:     a quien controla; es su jugador_max y no debe
                         cambiar, porque la tabla guarda valores desde
                         ese punto de vista.
            nivel:       clave de config.NIVELES.
            profundidad: sobrescribe la del nivel.
            segundos:    sobrescribe el tope del nivel. None = sin tope.
            explicar:    si es True, el Resultado incluye el puntaje
                         exacto de TODAS las jugadas de la raiz, a
                         cambio de renunciar a la poda entre hermanos
                         de la raiz. None = usar config.EXPLICAR_JUGADAS.
        """
        ajustes = config.NIVELES[nivel or config.NIVEL_POR_DEFECTO]
        self.jugador = jugador
        self.nivel = nivel or config.NIVEL_POR_DEFECTO
        self.profundidad = profundidad or ajustes["profundidad"]
        self.segundos = ajustes["segundos"] if segundos is None else segundos
        self.explicar = (config.EXPLICAR_JUGADAS if explicar is None
                         else explicar)
        self.tabla: Dict[motor.Estado, Entrada] = {}
        self.ultimo_resultado: Optional[Resultado] = None

    def reiniciar(self) -> None:
        """Olvida lo aprendido. Se llama al empezar una partida nueva."""
        self.tabla.clear()
        self.ultimo_resultado = None

    def elegir(self, estado: motor.Estado, cancelar=None) -> Resultado:
        """Devuelve la jugada elegida y las estadisticas de la busqueda.

        Usa profundizacion iterativa: 1, 2, 3... hasta la profundidad
        del nivel. Si el tope de tiempo salta a media iteracion, se
        devuelve el resultado de la ULTIMA PROFUNDIDAD COMPLETA. Nunca
        el de una iteracion a medias: como la raiz se explora en orden,
        una iteracion incompleta solo ha visto las primeras jugadas y
        su "mejor" estaria sesgada por ese orden.

        Argumentos:
            cancelar: threading.Event opcional. Si se activa, la
                      busqueda aborta y se devuelve lo mejor que se
                      tenia hasta ese momento.

        Lanza:
            ValueError: si el estado ya es terminal.
        """
        if motor.es_terminal(estado):
            raise ValueError("La partida ya termino: no hay jugada.")

        if not config.REUSAR_TABLA_ENTRE_JUGADAS:
            self.tabla.clear()

        comienzo = time.monotonic()
        limite = None if not self.segundos else comienzo + self.segundos

        # Con explicar activo, la tabla solo puede cortar con entradas
        # EXACTAS (ver _Buscador). No es solo una precaucion: como cada
        # jugada de la raiz se busca con ventana completa, esas
        # busquedas GENERAN entradas exactas, que las iteraciones
        # siguientes si pueden reutilizar. La restriccion se paga sola.
        buscador = _Buscador(self.jugador, self.tabla, limite, cancelar,
                             cortes_solo_exactos=self.explicar)
        movimientos = motor.movimientos_legales(estado)

        mejor_movimiento = movimientos[0]
        mejor_valor = 0.0
        profundidad_lograda = 0
        completa = True
        evaluaciones: Tuple[JugadaEvaluada, ...] = ()

        for profundidad in range(1, self.profundidad + 1):
            try:
                valor, movimiento, puntajes = buscador.buscar_raiz(
                    estado, profundidad, mejor_movimiento, self.explicar)
            except _BusquedaInterrumpida:
                completa = False
                break

            mejor_valor, mejor_movimiento = valor, movimiento
            profundidad_lograda = profundidad
            # Se conservan los puntajes de la ULTIMA iteracion completa.
            # Los de una iteracion interrumpida solo cubririan las
            # primeras jugadas y darian una tabla enganosa.
            evaluaciones = puntajes

            # Si ya se demostro una victoria o una derrota forzada, no
            # hay nada que ganar mirando mas hondo.
            if abs(valor) >= config.UMBRAL_VICTORIA:
                break

        # NOTA SOBRE UNA OPTIMIZACION QUE NO FUNCIONO.
        # Parece mas barato buscar normal en todas las iteraciones y
        # hacer UNA sola pasada explicativa al final, con la tabla ya
        # caliente. Se probo y sale entre un 8% y un 11% PEOR. El
        # motivo: las iteraciones rapidas llenan la tabla de entradas
        # de tipo COTA, que la pasada exacta tiene que rechazar, asi
        # que se queda sin tabla util justo cuando mas la necesita.
        # Explicar desde el principio la llena de entradas EXACTAS.

        self.ultimo_resultado = Resultado(
            movimiento=mejor_movimiento,
            valor=mejor_valor,
            profundidad=profundidad_lograda,
            nodos=buscador.nodos,
            podas=buscador.podas,
            aciertos_tabla=buscador.aciertos_tabla,
            segundos=time.monotonic() - comienzo,
            completa=completa,
            evaluaciones=evaluaciones,
        )
        return self.ultimo_resultado


# =====================================================================
# API SIMPLE
# =====================================================================


def elegir_movimiento(estado: motor.Estado,
                      nivel: Optional[str] = None,
                      profundidad: Optional[int] = None,
                      segundos: Optional[float] = None
                      ) -> motor.Movimiento:
    """Punto de enganche minimo: estado -> jugada.

    Crea un agente de un solo uso para el jugador que este en turno.
    Es la firma que se anuncio al cerrar la Entrega 1. Para jugar una
    partida completa conviene usar AgenteMinimax, que conserva la
    tabla de transposiciones entre jugadas.
    """
    agente = AgenteMinimax(estado.turno, nivel, profundidad, segundos)
    return agente.elegir(estado).movimiento


# =====================================================================
# REFERENCIA PARA LAS PRUEBAS
# =====================================================================


def minimax_sin_poda(estado: motor.Estado, profundidad: int,
                     jugador_max: str, ply: int = 0) -> float:
    """Minimax puro, sin poda ni tabla. Implementacion de referencia.

    Existe unicamente para demostrar en pruebas_agente.py que la poda
    Alfa-Beta no altera el resultado: se comparan los dos valores en
    muchas posiciones y deben coincidir exactamente. Es el argumento
    solido de que la optimizacion es correcta, y no solo mas rapida.

    Deliberadamente escrita de la forma mas simple posible, aunque sea
    lenta: una referencia solo sirve si es obviamente correcta.
    """
    resultado = motor.ganador(estado)
    if resultado is not None or profundidad == 0:
        return heuristica.evaluar(estado, jugador_max, ply, resultado)

    valores = [
        minimax_sin_poda(motor.aplicar(estado, movimiento, validar=False),
                         profundidad - 1, jugador_max, ply + 1)
        for movimiento in motor.movimientos_legales(estado)
    ]
    if estado.turno == jugador_max:
        return max(valores)
    return min(valores)


def valor_con_alfa_beta(estado: motor.Estado, profundidad: int,
                        jugador_max: str, usar_tabla: bool = True,
                        usar_poda: bool = True) -> Tuple[float, int]:
    """Valor Minimax con poda, mas el numero de nodos visitados.

    Auxiliar de las pruebas y del banco: permite medir cuanto trabajo
    ahorra cada optimizacion activandolas y desactivandolas.
    """
    buscador = _Buscador(jugador_max, {}, None, None, usar_tabla,
                         usar_poda)
    valor = buscador._alfa_beta(estado, profundidad, -INFINITO, INFINITO, 0)
    return valor, buscador.nodos
