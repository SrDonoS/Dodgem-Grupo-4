# -*- coding: utf-8 -*-
"""Configuracion central del proyecto Dodgem (Entrega 1).

Este modulo es el UNICO lugar donde viven los parametros del juego.
Ni el motor ni la interfaz contienen "numeros magicos": todo valor que
el profesor pueda querer modificar en vivo durante la interrogacion
(tamano del tablero, direcciones de movimiento, regla de bloqueo,
colores) esta declarado aqui con un nombre autoexplicativo.

Por que separar la configuracion:
    En la Fase 2 el algoritmo Minimax explorara miles de estados por
    jugada. Si las reglas estuvieran incrustadas dentro de la logica,
    cambiar un parametro obligaria a tocar el buscador. Al centralizar
    las constantes, el motor queda escrito "en funcion de parametros"
    y el arbol de busqueda se adapta solo.
"""

# ---------------------------------------------------------------------
# 1. IDENTIFICACION DE LOS JUGADORES
# ---------------------------------------------------------------------

#: Identificador interno del jugador que avanza hacia la derecha.
JUGADOR_A = "A"

#: Identificador interno del jugador que avanza hacia arriba.
JUGADOR_B = "B"

#: Tupla con ambos jugadores. Iterar sobre esta tupla evita escribir
#: "A" y "B" a mano en el resto del programa.
JUGADORES = (JUGADOR_A, JUGADOR_B)

#: Jugador que realiza el primer movimiento de la partida.
JUGADOR_INICIAL = JUGADOR_A

#: Valor devuelto por ganador() cuando la partida termina en tablas.
EMPATE = "EMPATE"

#: Nombres legibles usados por la interfaz grafica.
NOMBRES_JUGADORES = {
    JUGADOR_A: "Jugador A",
    JUGADOR_B: "Jugador B",
}

#: Descripcion corta del objetivo de cada jugador (para la interfaz).
OBJETIVOS_JUGADORES = {
    JUGADOR_A: "avanza a la derecha y sale por el borde derecho",
    JUGADOR_B: "avanza hacia arriba y sale por el borde superior",
}


# ---------------------------------------------------------------------
# 2. RESTRICCIONES DEL TAMANO DEL TABLERO
# ---------------------------------------------------------------------
# El enunciado exige: tablero n x n, con n par y n > 4.
# En vez de escribir "if n % 2 == 0 and n > 4" dentro del motor,
# expresamos la regla como constantes editables.

#: Divisor usado para comprobar la paridad de n.
DIVISOR_PARIDAD = 2

#: Resto que debe dejar n al dividirse por DIVISOR_PARIDAD.
#: 0 -> n debe ser par. Cambiar a 1 permitiria tableros impares.
RESTO_PARIDAD_REQUERIDO = 0

#: Valor que n debe superar estrictamente (n > 4 segun el enunciado).
TAMANO_MINIMO_EXCLUSIVO = 4

#: Cota superior practica. No es una regla del juego, sino un limite
#: para que la interfaz siga siendo legible. Subirlo es seguro: el
#: motor no depende de este valor.
TAMANO_MAXIMO_TABLERO = 16

#: Tamano ofrecido por defecto en la pantalla de configuracion.
TAMANO_POR_DEFECTO = 6

#: Cantidad de fichas por jugador = n - FICHAS_MENOS_QUE_LADO.
#: El enunciado pide n - 1 fichas por jugador.
FICHAS_MENOS_QUE_LADO = 1


# ---------------------------------------------------------------------
# 3. GEOMETRIA DEL TABLERO Y DIRECCIONES DE MOVIMIENTO
# ---------------------------------------------------------------------
# Sistema de coordenadas INTERNO: (fila, columna) con indice base 0.
#   - fila 0      -> borde SUPERIOR del tablero
#   - columna 0   -> borde IZQUIERDO del tablero
#   - fila n-1    -> borde INFERIOR
#   - columna n-1 -> borde DERECHO
#
# El enunciado numera desde 1 ("fila 1", "columna n"). La conversion a
# la numeracion humana se hace SOLO en la capa de presentacion, nunca
# dentro del motor. Trabajar en base 0 evita sumar y restar 1 en cada
# calculo del futuro Minimax.

#: Vector (delta_fila, delta_columna) del movimiento de AVANCE.
#: A avanza al Este (columna + 1); B avanza al Norte (fila - 1).
#: Toda la logica de salida del tablero se deduce de este diccionario.
DIRECCION_AVANCE = {
    JUGADOR_A: (0, 1),
    JUGADOR_B: (-1, 0),
}

#: Vectores de los movimientos LATERALES permitidos a cada jugador.
#: A puede desplazarse verticalmente; B, horizontalmente. Ningun
#: jugador puede retroceder, por lo que el vector opuesto al avance
#: no aparece en ninguna lista.
DIRECCIONES_LATERALES = {
    JUGADOR_A: ((-1, 0), (1, 0)),
    JUGADOR_B: ((0, -1), (0, 1)),
}

#: Si es True, la casilla comun a las dos lineas de salida (la esquina
#: inferior izquierda en la configuracion clasica) queda vacia. Esta es
#: la disposicion oficial del Dodgem y la que produce exactamente
#: n - 1 fichas por jugador.
ESQUINA_COMPARTIDA_VACIA = True


# ---------------------------------------------------------------------
# 4. TIPOS DE MOVIMIENTO
# ---------------------------------------------------------------------

#: Movimiento en la direccion de avance, con destino dentro del tablero.
TIPO_AVANCE = "avance"

#: Movimiento lateral (esquiva), siempre dentro del tablero.
TIPO_LATERAL = "lateral"

#: Movimiento de avance cuyo destino cae fuera del tablero: la ficha
#: abandona la partida. Solo es legal en la direccion de avance, lo que
#: implementa automaticamente la prohibicion de salir por los bordes
#: equivocados.
TIPO_SALIDA = "salida"

#: Orden en que movimientos_legales() agrupa las jugadas. Colocar
#: primero las salidas y los avances mejora la poda Alfa-Beta de la
#: Fase 2, porque las jugadas mas prometedoras se evaluan antes.
ORDEN_TIPOS_MOVIMIENTO = (TIPO_SALIDA, TIPO_AVANCE, TIPO_LATERAL)


# ---------------------------------------------------------------------
# 5. REGLAS DE TERMINO DE LA PARTIDA
# ---------------------------------------------------------------------

#: Constantes para la regla de bloqueo.
BLOQUEADO_PIERDE = "bloqueado_pierde"
BLOQUEADO_GANA = "bloqueado_gana"

#: Regla activa. El enunciado de la asignatura pide BLOQUEADO_PIERDE:
#: si al inicio de su turno un jugador conserva fichas pero no tiene
#: movimientos legales, pierde de inmediato (no se permite pasar).
#: El Dodgem clasico usa la convencion inversa (BLOQUEADO_GANA, porque
#: se penaliza al rival que bloquea). Cambiar esta unica linea alterna
#: entre ambas reglas sin tocar el motor.
REGLA_BLOQUEO = BLOQUEADO_PIERDE

#: Tablas por falta de progreso. En tableros pares el juego puede
#: alargarse indefinidamente si ambos jugadores solo esquivan; este
#: limite evita partidas infinitas y, en la Fase 2, arboles de busqueda
#: sin condicion de corte natural.
#: Se considera "progreso" unicamente la salida de una ficha.
TABLAS_HABILITADAS = False

#: Numero de jugadas consecutivas sin que salga ninguna ficha tras el
#: cual se declara empate (solo si TABLAS_HABILITADAS es True).
LIMITE_JUGADAS_SIN_PROGRESO = 100


# ---------------------------------------------------------------------
# 6. RENDIMIENTO (relevante para la Fase 2)
# ---------------------------------------------------------------------

#: Si es True, aplicar() verifica que el movimiento recibido sea legal
#: antes de construir el nuevo estado. Es lo correcto mientras juegan
#: humanos. Al inyectar Minimax puede desactivarse: el buscador solo
#: aplica movimientos que el mismo obtuvo de movimientos_legales(),
#: y ahorrar esa validacion en miles de nodos es significativo.
VALIDAR_MOVIMIENTOS_AL_APLICAR = True

#: Limite de nodos explorados por turno para agentes BFS/DFS.
BUSQUEDA_MAX_NODOS = 12000

#: Profundidad maxima explorada por turno para agentes BFS/DFS.
BUSQUEDA_MAX_PROFUNDIDAD = 18

#: Retardo visual (ms) entre jugadas en modo computadora vs computadora.
RETARDO_TURNO_AUTOMATICO_MS = 260

#: Minimo de segundos permitido en el deslizador de velocidad.
RETARDO_MINIMO_SEGUNDOS = 0.01

#: Maximo de segundos permitido en el deslizador de velocidad.
RETARDO_MAXIMO_SEGUNDOS = 1

#: Paso de ajuste en segundos del deslizador.
RETARDO_PASO_SEGUNDOS = 0.05


# ---------------------------------------------------------------------
# 7. PARAMETROS DE LA INTERFAZ GRAFICA
# ---------------------------------------------------------------------
# Nada de lo que sigue afecta a las reglas del juego. El motor no
# importa ninguna de estas constantes.

TITULO_VENTANA = "Dodgem"
SUBTITULO_VENTANA = "Fundamentos de Inteligencia Artificial - Entrega 1"

#: Tamano inicial de la ventana en pixeles (ancho, alto).
TAMANO_VENTANA_INICIAL = (1040, 720)

#: Tamano minimo de la ventana en pixeles (ancho, alto).
TAMANO_VENTANA_MINIMO = (860, 600)

#: Ancho fijo del panel lateral de informacion, en pixeles.
ANCHO_PANEL_LATERAL = 300

#: Margen exterior del lienzo del tablero, en pixeles.
MARGEN_LIENZO = 28

#: Radio de las esquinas redondeadas de las celdas, como fraccion del
#: lado de la celda.
FRACCION_RADIO_CELDA = 0.22

#: Diametro de las fichas como fraccion del lado de la celda.
FRACCION_DIAMETRO_FICHA = 0.68

#: Diametro de los marcadores de destino legal, como fraccion del lado.
FRACCION_DIAMETRO_MARCADOR = 0.30

#: Separacion entre celdas (padding interno), como fraccion del lado.
FRACCION_SEPARACION_CELDA = 0.06

#: Ancho del margen donde se rotulan filas y columnas, como fraccion
#: del lado de la celda.
FRACCION_GUTTER_COORDENADAS = 0.62

#: Lado minimo de celda en pixeles: por debajo de esto la ventana deja
#: de encoger el tablero.
LADO_MINIMO_CELDA = 22

#: Familias tipograficas candidatas, en orden de preferencia. La
#: interfaz elige la primera disponible en el sistema.
FAMILIAS_TIPOGRAFICAS = (
    "Quicksand", "Nunito", "Avenir Next", "Segoe UI",
    "Helvetica Neue", "Helvetica", "DejaVu Sans",
)

#: Paleta pastel. Las claves son nombres semanticos, no colores, para
#: poder cambiar el tema completo editando solo este diccionario.
PALETA = {
    # Superficies
    "fondo_ventana": "#FAF6F2",
    "fondo_panel": "#FFFFFF",
    "fondo_tarjeta": "#FBF6F1",
    "borde_suave": "#EDE2D9",
    # Texto
    "texto_principal": "#5B4F47",
    "texto_secundario": "#A2938A",
    "texto_sobre_color": "#FFFFFF",
    # Celdas del tablero
    "celda_clara": "#FDFAF7",
    "celda_oscura": "#F4ECE4",
    "celda_esquina_libre": "#EFE4DA",
    "sombra_celda": "#E9DED5",
    # Carriles de salida
    "carril_a": "#FCEFF1",
    "carril_b": "#EAF2FA",
    "flecha_carril": "#CDBDB2",
    # Fichas del jugador A (rosa pastel)
    "ficha_a": "#F2A7AF",
    "ficha_a_borde": "#DD8A93",
    "ficha_a_brillo": "#FBD5D9",
    # Fichas del jugador B (azul pastel)
    "ficha_b": "#9FC4E8",
    "ficha_b_borde": "#7FA6CF",
    "ficha_b_brillo": "#D2E4F6",
    # Estados de interaccion
    "seleccion": "#FFE2A6",
    "seleccion_borde": "#EFC66E",
    "destino_normal": "#B4E1C4",
    "destino_normal_borde": "#8FCBA5",
    "destino_salida": "#D8C3EC",
    "destino_salida_borde": "#B99FD4",
    # Botones
    "boton_fondo": "#F1E6DC",
    "boton_fondo_hover": "#E7D8CB",
    "boton_texto": "#6B5C52",
    "boton_primario": "#A8D5C2",
    "boton_primario_hover": "#93C9B3",
    "boton_primario_texto": "#33574A",
    "boton_desactivado": "#F5EFE9",
    "boton_texto_desactivado": "#C7BAB0",
    # Mensajes
    "aviso_error": "#D98C8C",
    "aviso_ok": "#7FB79A",
}

#: Color de relleno de cada jugador, agrupado para acceso directo.
COLORES_JUGADOR = {
    JUGADOR_A: {
        "relleno": PALETA["ficha_a"],
        "borde": PALETA["ficha_a_borde"],
        "brillo": PALETA["ficha_a_brillo"],
        "carril": PALETA["carril_a"],
    },
    JUGADOR_B: {
        "relleno": PALETA["ficha_b"],
        "borde": PALETA["ficha_b_borde"],
        "brillo": PALETA["ficha_b_brillo"],
        "carril": PALETA["carril_b"],
    },
}

#: Cantidad maxima de jugadas mostradas en el historial lateral.
MAXIMO_JUGADAS_EN_HISTORIAL = 200
