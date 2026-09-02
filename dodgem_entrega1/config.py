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


# ---------------------------------------------------------------------
# 8. PESOS DE LA FUNCION HEURISTICA (Semana 3)
# ---------------------------------------------------------------------
# UNIDAD DE MEDIDA: todos los pesos estan expresados en "pasos de
# avance". Un paso es un movimiento que acerca una ficha una casilla a
# su carril de salida. Fijar W_DISTANCIA = 1.0 define la escala: si la
# heuristica devuelve +6, significa "voy seis pasos adelante en la
# carrera". Esa interpretabilidad es deliberada: la rubrica exige que
# la heuristica sea EXPLICABLE, y una escala arbitraria no lo es.
#
# COMO SE FIJARON ESTOS VALORES. Primero se propuso cada peso con un
# argumento analitico (cuantos pasos cuesta realmente esa situacion).
# Despues se midieron con banco_heuristica.py, enfrentando variantes
# entre si en 120 partidas por combinacion y sobre dos tamanos de
# tablero. Donde el dato contradijo a la estimacion, se conservo el
# dato y se anoto la discrepancia. Los tres pesos marcados abajo como
# "ajustado tras la medicion" son exactamente esos casos.

#: Peso del termino de distancia (Manhattan al carril de salida).
#: Es el ancla de la escala; cambiarlo reescala todo lo demas.
W_DISTANCIA = 1.0

#: Bonificacion extra por cada ficha ya fuera del tablero.
#: Justificacion: el termino de distancia ya cuenta el progreso, pero
#: una ficha fuera es progreso IRREVERSIBLE (no puede volver a ser
#: bloqueada ni estorbar a las propias). Se le concede el valor de dos
#: pasos adicionales como premio a esa seguridad.
W_SALIDA = 2.0

#: Penalizacion por cada ficha propia con su avance tapado por una
#: ficha RIVAL.
#: Cota analitica: una ficha bloqueada de frente necesita al menos un
#: movimiento lateral para esquivar y otro para retomar la linea; son
#: >= 2 pasos perdidos. Ese razonamiento sugeria 3.0.
#: Correccion empirica: el barrido de banco_heuristica.py mostro que
#: 6.0 juega claramente mejor. La interpretacion es que el bloqueo no
#: cuesta solo el rodeo puntual: el rival puede SOSTENERLO, y en un
#: tablero estrecho una ficha frenada estorba ademas a las propias.
#: Se conserva el valor medido, no el estimado.
W_BLOQUEO_RIVAL = 6.0

#: Penalizacion por cada ficha propia tapada por OTRA FICHA PROPIA.
#: Es un atasco autoinfligido: cuesta lo mismo esquivar, pero el rival
#: no lo controla y suele deshacerse solo. Vale menos que el anterior.
W_BLOQUEO_PROPIO = 1.0

#: Penalizacion ADICIONAL por cada ficha propia sin NINGUN movimiento
#: legal. Se suma a la anterior: una ficha inmovilizada por el rival
#: acumula W_BLOQUEO_RIVAL + W_INMOVILIZADA = 10 puntos, de modo que
#: siempre pesa mas que un bloqueo frontal simple aunque el numero de
#: esta linea sea menor.
#: Ajustado de 8.0 a 4.0 tras la medicion: un valor alto empujaba al
#: agente a perseguir bloqueos totales -que son raros- descuidando su
#: propia carrera hacia la salida.
W_INMOVILIZADA = 4.0

#: Peso de la movilidad (numero de jugadas legales disponibles).
#: Actua como desempate y como seguro ante la regla de bloqueo: pocas
#: jugadas legales es una posicion fragil.
#: Ajustado de 0.5 a 0.2 tras la medicion. Con 0.5, conservar jugadas
#: disponibles competia de igual a igual con avanzar (un avance vale
#: 1.0 y una ficha aporta hasta 3 jugadas), y el agente se quedaba
#: dando vueltas en vez de correr hacia su carril.
W_MOVILIDAD = 0.2

#: Valor del turno (tempo). En una carrera, mover primero vale a lo
#: sumo un paso; se usa medio paso para no sobrevalorarlo.
W_TEMPO = 0.5

#: Puntaje de una victoria. Debe ser ESTRICTAMENTE MAYOR que cualquier
#: valor que pueda devolver la heuristica, para que el agente nunca
#: prefiera una posicion "bonita" antes que un final ganado.
#: heuristica.cota_maxima_heuristica(n) calcula esa cota y las pruebas
#: unitarias verifican que este valor la supera.
VICTORIA = 1_000_000.0

#: Puntaje de unas tablas: ni victoria ni derrota.
VALOR_EMPATE = 0.0

#: Umbral a partir del cual un puntaje se considera "victoria segura"
#: y no una estimacion. La tabla de transposiciones lo necesita para
#: reconocer los puntajes que dependen de la distancia al final y
#: reajustarlos (ver agente.py). Se deja un margen amplio por debajo
#: de VICTORIA para absorber el descuento por profundidad.
UMBRAL_VICTORIA = VICTORIA / 2.0


# ---------------------------------------------------------------------
# 9. AGENTE MINIMAX (Fase 2)
# ---------------------------------------------------------------------

#: Modos de juego disponibles.
MODO_HUMANO_VS_HUMANO = "humano_vs_humano"
MODO_HUMANO_VS_AGENTE = "humano_vs_agente"
MODO_AGENTE_VS_HUMANO = "agente_vs_humano"
MODO_AGENTE_VS_AGENTE = "agente_vs_agente"

#: Que jugador controla cada modo. La interfaz consulta este mapa para
#: saber a quien pedirle la jugada; no lo decide por su cuenta.
CONTROLADOR_POR_MODO = {
    MODO_HUMANO_VS_HUMANO: {JUGADOR_A: "humano", JUGADOR_B: "humano"},
    MODO_HUMANO_VS_AGENTE: {JUGADOR_A: "humano", JUGADOR_B: "agente"},
    MODO_AGENTE_VS_HUMANO: {JUGADOR_A: "agente", JUGADOR_B: "humano"},
    MODO_AGENTE_VS_AGENTE: {JUGADOR_A: "agente", JUGADOR_B: "agente"},
}

#: Nombre legible de cada modo para la pantalla de configuracion.
NOMBRES_MODOS = {
    MODO_HUMANO_VS_HUMANO: "Humano vs Humano",
    MODO_HUMANO_VS_AGENTE: "Humano (A) vs Bot (B)",
    MODO_AGENTE_VS_HUMANO: "Bot (A) vs Humano (B)",
    MODO_AGENTE_VS_AGENTE: "Bot vs Bot (demostracion)",
}

MODO_POR_DEFECTO = MODO_HUMANO_VS_AGENTE

#: Niveles de dificultad.
#: La PROFUNDIDAD es el control principal y es determinista: en el
#: mismo tablero el agente juega siempre igual, cosa que importa para
#: poder reproducir una partida durante la interrogacion.
#: El TOPE DE SEGUNDOS es solo una red de seguridad para tableros
#: grandes: si se agota, la profundizacion iterativa se queda con el
#: mejor resultado de la ultima profundidad COMPLETA (nunca con una a
#: medias, que podria estar sesgada por el orden de exploracion).
NIVELES = {
    "facil": {"profundidad": 2, "segundos": 2.0,
              "descripcion": "Ve tu jugada y su respuesta."},
    "medio": {"profundidad": 4, "segundos": 4.0,
              "descripcion": "Dos jugadas completas por bando."},
    "dificil": {"profundidad": 6, "segundos": 8.0,
                "descripcion": "Tres jugadas por bando. Planifica."},
    "experto": {"profundidad": 8, "segundos": 15.0,
                "descripcion": "Cuatro jugadas por bando. Lento."},
}

#: Orden en que se muestran los niveles en la interfaz.
ORDEN_NIVELES = ("facil", "medio", "dificil", "experto")

NIVEL_POR_DEFECTO = "medio"

#: Tamano maximo de la tabla de transposiciones (numero de entradas).
#: Al superarlo se vacia por completo: es la politica de reemplazo mas
#: simple y basta aqui, porque la tabla se reinicia en cada jugada.
MAXIMO_ENTRADAS_TRANSPOSICION = 400_000

#: Si es True, la tabla de transposiciones se conserva entre jugadas
#: consecutivas. Acelera, pero consume memoria; se limpia al empezar
#: una partida nueva.
REUSAR_TABLA_ENTRE_JUGADAS = True

#: Pausa minima (en milisegundos) antes de que el agente mueva. Sin
#: ella, en niveles bajos el bot responde de forma instantanea y la
#: partida se vuelve confusa de seguir.
PAUSA_MINIMA_AGENTE_MS = 350

#: Cada cuantos milisegundos la interfaz consulta si el agente ya
#: termino de pensar. Es un sondeo barato sobre una cola.
INTERVALO_SONDEO_AGENTE_MS = 50

#: Cada cuantos nodos la busqueda comprueba el reloj y la senal de
#: cancelacion. Consultar el reloj en cada nodo seria costoso.
NODOS_ENTRE_COMPROBACIONES = 2048

#: Colores de los elementos propios del agente en la interfaz.
PALETA.update({
    "resalte_jugada_bot": "#F6DDA8",
    "resalte_jugada_bot_borde": "#E2BE72",
    "pensando": "#C9B7E4",
})


# ---------------------------------------------------------------------
# 10. VISUALIZACION DEL RAZONAMIENTO DEL AGENTE
# ---------------------------------------------------------------------
# El objetivo es que se vea COMO decide el agente sin renderizar cada
# nodo del arbol (eso congelaria la ventana y, con cientos de miles de
# nodos, seria ademas ilegible).
#
# La solucion es mostrar solo la RAIZ del arbol: las jugadas que el
# agente tenia disponibles este turno y el puntaje que le dio a cada
# una. Son entre 5 y 45 filas, no cientos de miles, y se dibujan UNA
# vez cuando la busqueda ya termino.

#: Si es True, el agente devuelve el puntaje de CADA jugada legal de la
#: raiz, no solo el de la elegida.
#:
#: CUIDADO, ESTO NO ES GRATIS. Con poda Alfa-Beta, el valor de las
#: jugadas que no son la mejor NO es exacto: la poda corta en cuanto
#: sabe que una jugada es peor que otra ya conocida, y devuelve una
#: COTA en lugar del valor real. Mostrar esas cotas como si fueran
#: puntajes seria enganoso.
#:
#: Por eso, cuando esta opcion esta activa, la busqueda de la raiz
#: renuncia a podar ENTRE HERMANOS: cada jugada de la raiz se explora
#: con la ventana completa (-inf, +inf), que es la condicion que
#: garantiza un valor exacto. Dentro de cada rama la poda sigue
#: funcionando con normalidad.
#:
#: Coste medido en banco_agente.py. Si en la evaluacion se quiere
#: maxima velocidad, basta con poner esto en False.
EXPLICAR_JUGADAS = True

#: Cuantas jugadas se listan en el panel lateral. El resto se resume
#: en una linea final ("y N jugadas mas").
MAXIMO_JUGADAS_EXPLICADAS = 7

#: Si es True, ademas de la lista se marcan en el tablero las jugadas
#: que el agente considero mejores, justo antes de mover.
RESALTAR_JUGADAS_CONSIDERADAS = True

#: Cuantas jugadas se marcan sobre el tablero.
MAXIMO_JUGADAS_RESALTADAS = 4

#: Milisegundos que se muestran esas marcas antes de ejecutar la
#: jugada definitiva. Es la pausa que convierte la busqueda en algo
#: observable: sin ella el bot movería antes de que el ojo lo siga.
MS_RESALTE_CONSIDERACION = 900

#: Prefijo del indicador de "pensando".
#: NOTA: no todos los sistemas renderizan emoji en widgets de Tkinter.
#: En Windows y macOS se ve bien; en algunas distribuciones de Linux
#: sin fuente de emoji instalada aparece un recuadro. Si eso pasa,
#: basta con dejarlo en cadena vacia.
PREFIJO_PENSANDO = "\U0001F916 "        # robot

#: Colores del panel de razonamiento y de las marcas del tablero.
PALETA.update({
    # Escala de calidad: de la mejor jugada a la peor.
    "calidad_alta": "#8FCBA5",
    "calidad_baja": "#D8CEC6",
    "fila_elegida": "#EAF6EF",
    "texto_valor_positivo": "#5C8F73",
    "texto_valor_negativo": "#C08A8A",
})
