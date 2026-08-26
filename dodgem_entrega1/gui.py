# -*- coding: utf-8 -*-
"""Interfaz grafica del Dodgem construida con Tkinter.

Esta capa es puramente de PRESENTACION. Su unica manera de conocer o
alterar la partida es a traves de las funciones publicas de motor.py:
no reimplementa ninguna regla, no sabe en que direccion avanza cada
jugador y no decide quien gana. Si una jugada aparece resaltada en
pantalla es porque motor.movimientos_legales() la devolvio.

Esa separacion estricta es la que permitira, en la Fase 2, sustituir a
un jugador humano por un agente Minimax sin tocar una sola linea de
este archivo: bastara con que, cuando le toque al agente, alguien
llame a aplicar() con el movimiento que el buscador eligio.

Tkinter forma parte de la biblioteca estandar de Python, de modo que
el proyecto no depende de ningun paquete externo.
"""

from __future__ import annotations

import math
import queue
import threading
import tkinter as tk
from tkinter import font as tkfont
from typing import Dict, List, Optional, Tuple

import agente
import config
import motor


# =====================================================================
# COMPONENTES VISUALES REUTILIZABLES
# =====================================================================


def _familia_tipografica(raiz: tk.Misc) -> str:
    """Elige la primera fuente disponible de la lista de preferencias.

    Se evita depender de una fuente concreta: en Linux, Windows y macOS
    el conjunto instalado es distinto y una familia inexistente produce
    una sustitucion arbitraria y fea.
    """
    disponibles = set(tkfont.families(raiz))
    for familia in config.FAMILIAS_TIPOGRAFICAS:
        if familia in disponibles:
            return familia
    return tkfont.nametofont("TkDefaultFont").actual("family")


class BotonPastel(tk.Frame):
    """Boton dibujado a mano con la paleta del proyecto.

    No se usa tk.Button porque en macOS ignora el color de fondo y en
    Windows dibuja un relieve gris que rompe el estilo pastel. Un Frame
    con un Label dentro y los eventos enlazados a mano se ve identico
    en los tres sistemas operativos.
    """

    def __init__(self, maestro, texto, comando, familia,
                 variante="normal", tamano_fuente=11, **kwargs):
        self._variante = variante
        self._comando = comando
        self._activo = True
        self._marcado = False

        fondo, color_texto = self._colores()
        super().__init__(maestro, bg=fondo, highlightthickness=0, bd=0,
                         **kwargs)

        self._etiqueta = tk.Label(
            self, text=texto, bg=fondo, fg=color_texto,
            font=(familia, tamano_fuente, "bold"),
            padx=14, pady=8, cursor="hand2",
        )
        self._etiqueta.pack(fill=tk.BOTH, expand=True)

        for widget in (self, self._etiqueta):
            widget.bind("<Button-1>", self._al_presionar)
            widget.bind("<Enter>", self._al_entrar)
            widget.bind("<Leave>", self._al_salir)

    # -- estilo ------------------------------------------------------

    def _colores(self, resaltado: bool = False) -> Tuple[str, str]:
        """Devuelve (color de fondo, color de texto) segun el estado."""
        paleta = config.PALETA
        if not self._activo:
            return (paleta["boton_desactivado"],
                    paleta["boton_texto_desactivado"])
        if self._variante == "primario":
            clave = "boton_primario_hover" if resaltado else "boton_primario"
            return paleta[clave], paleta["boton_primario_texto"]
        if self._variante == "chip" and self._marcado:
            return paleta["boton_primario"], paleta["boton_primario_texto"]
        clave = "boton_fondo_hover" if resaltado else "boton_fondo"
        return paleta[clave], paleta["boton_texto"]

    def _repintar(self, resaltado: bool = False) -> None:
        fondo, color_texto = self._colores(resaltado)
        self.configure(bg=fondo)
        self._etiqueta.configure(bg=fondo, fg=color_texto)

    # -- eventos -----------------------------------------------------

    def _al_presionar(self, _evento) -> None:
        if self._activo and self._comando is not None:
            self._comando()

    def _al_entrar(self, _evento) -> None:
        self._repintar(resaltado=True)

    def _al_salir(self, _evento) -> None:
        self._repintar(resaltado=False)

    # -- API publica -------------------------------------------------

    def habilitar(self, activo: bool) -> None:
        """Activa o desactiva el boton (afecta color y cursor)."""
        self._activo = activo
        self._etiqueta.configure(cursor="hand2" if activo else "arrow")
        self._repintar()

    def marcar(self, marcado: bool) -> None:
        """Marca un chip como seleccionado."""
        self._marcado = marcado
        self._repintar()


def _crear_tarjeta(maestro: tk.Misc) -> tk.Frame:
    """Crea un contenedor con fondo de tarjeta y borde suave."""
    return tk.Frame(
        maestro,
        bg=config.PALETA["fondo_tarjeta"],
        highlightbackground=config.PALETA["borde_suave"],
        highlightthickness=1, bd=0,
    )


def _rectangulo_redondeado(lienzo: tk.Canvas, x1, y1, x2, y2, radio,
                           **kwargs) -> int:
    """Dibuja un rectangulo de esquinas redondeadas en un Canvas.

    Tkinter no ofrece esta primitiva. El truco estandar es crear un
    poligono con los vertices duplicados en las esquinas y activar
    smooth=True, que aplica una curva de Bezier sobre esos puntos.
    """
    radio = max(0.0, min(radio, (x2 - x1) / 2.0, (y2 - y1) / 2.0))
    puntos = [
        x1 + radio, y1, x2 - radio, y1, x2, y1,
        x2, y1 + radio, x2, y2 - radio, x2, y2,
        x2 - radio, y2, x1 + radio, y2, x1, y2,
        x1, y2 - radio, x1, y1 + radio, x1, y1,
    ]
    return lienzo.create_polygon(puntos, smooth=True, **kwargs)


# =====================================================================
# PANTALLA 1: CONFIGURACION DE LA PARTIDA
# =====================================================================


class PantallaConfiguracion(tk.Frame):
    """Pide el tamano del tablero antes de empezar.

    Todo lo que se ofrece aqui proviene de motor.tamanos_validos() y de
    motor.validar_n(): la interfaz no sabe que n debe ser par ni mayor
    que 4, solo pregunta.
    """

    def __init__(self, maestro, aplicacion, familia):
        super().__init__(maestro, bg=config.PALETA["fondo_ventana"])
        self._aplicacion = aplicacion
        self._familia = familia
        self._n_elegido = config.TAMANO_POR_DEFECTO
        self._modo_elegido = config.MODO_POR_DEFECTO
        self._nivel_elegido = config.NIVEL_POR_DEFECTO
        self._chips: Dict[int, BotonPastel] = {}
        self._chips_modo: Dict[str, BotonPastel] = {}
        self._chips_nivel: Dict[str, BotonPastel] = {}

        self._construir()

    # -- construccion ------------------------------------------------

    def _construir(self) -> None:
        paleta = config.PALETA
        centro = tk.Frame(self, bg=paleta["fondo_ventana"])
        centro.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(
            centro, text=config.TITULO_VENTANA.upper(),
            bg=paleta["fondo_ventana"], fg=paleta["texto_principal"],
            font=(self._familia, 40, "bold"),
        ).pack()

        tk.Label(
            centro, text=config.SUBTITULO_VENTANA,
            bg=paleta["fondo_ventana"], fg=paleta["texto_secundario"],
            font=(self._familia, 11),
        ).pack(pady=(2, 22))

        # Dos columnas: los ajustes a la izquierda y el recordatorio de
        # reglas a la derecha. Apilarlo todo en vertical desbordaria la
        # ventana en pantallas de portatil.
        columnas = tk.Frame(centro, bg=paleta["fondo_ventana"])
        columnas.pack()

        izquierda = tk.Frame(columnas, bg=paleta["fondo_ventana"])
        izquierda.pack(side=tk.LEFT, anchor=tk.N, padx=(0, 14))
        derecha = tk.Frame(columnas, bg=paleta["fondo_ventana"])
        derecha.pack(side=tk.LEFT, anchor=tk.N)

        self._construir_tarjeta_tamano(izquierda)
        self._construir_tarjeta_oponente(izquierda)
        self._construir_tarjeta_reglas(derecha)

        BotonPastel(
            centro, "Comenzar partida", self._comenzar, self._familia,
            variante="primario", tamano_fuente=13,
        ).pack(pady=(20, 0), ipadx=10)

    def _construir_tarjeta_oponente(self, maestro: tk.Misc) -> None:
        """Eleccion del modo de juego y del nivel del agente.

        Los modos y los niveles se leen de config.py, de modo que
        anadir un nivel nuevo (o cambiar su profundidad) durante la
        interrogacion no requiere tocar la interfaz.
        """
        paleta = config.PALETA
        tarjeta = _crear_tarjeta(maestro)
        tarjeta.pack(fill=tk.X)

        tk.Label(
            tarjeta, text="Oponente",
            bg=paleta["fondo_tarjeta"], fg=paleta["texto_principal"],
            font=(self._familia, 12, "bold"),
        ).pack(anchor=tk.W, padx=22, pady=(16, 6))

        for modo in (config.MODO_HUMANO_VS_HUMANO,
                     config.MODO_HUMANO_VS_AGENTE,
                     config.MODO_AGENTE_VS_HUMANO,
                     config.MODO_AGENTE_VS_AGENTE):
            chip = BotonPastel(
                tarjeta, config.NOMBRES_MODOS[modo],
                lambda valor=modo: self._elegir_modo(valor), self._familia,
                variante="chip", tamano_fuente=10)
            chip.pack(fill=tk.X, padx=22, pady=2)
            self._chips_modo[modo] = chip

        self._etiqueta_nivel = tk.Label(
            tarjeta, text="Nivel del bot",
            bg=paleta["fondo_tarjeta"], fg=paleta["texto_principal"],
            font=(self._familia, 12, "bold"))
        self._etiqueta_nivel.pack(anchor=tk.W, padx=22, pady=(14, 6))

        self._fila_niveles = tk.Frame(tarjeta, bg=paleta["fondo_tarjeta"])
        self._fila_niveles.pack(anchor=tk.W, padx=22)

        for nivel in config.ORDEN_NIVELES:
            chip = BotonPastel(
                self._fila_niveles, nivel.capitalize(),
                lambda valor=nivel: self._elegir_nivel(valor),
                self._familia, variante="chip", tamano_fuente=10)
            chip.pack(side=tk.LEFT, padx=(0, 4))
            self._chips_nivel[nivel] = chip

        self._descripcion_nivel = tk.Label(
            tarjeta, text="", bg=paleta["fondo_tarjeta"],
            fg=paleta["texto_secundario"], font=(self._familia, 9),
            justify=tk.LEFT, wraplength=300)
        self._descripcion_nivel.pack(anchor=tk.W, padx=22, pady=(8, 16))

        self._elegir_modo(self._modo_elegido)
        self._elegir_nivel(self._nivel_elegido)

    def _construir_tarjeta_tamano(self, maestro: tk.Misc) -> None:
        paleta = config.PALETA
        tarjeta = _crear_tarjeta(maestro)
        tarjeta.pack(fill=tk.X, pady=(0, 14))

        tk.Label(
            tarjeta, text="Tamano del tablero  (n x n)",
            bg=paleta["fondo_tarjeta"], fg=paleta["texto_principal"],
            font=(self._familia, 12, "bold"),
        ).pack(anchor=tk.W, padx=22, pady=(16, 2))

        tk.Label(
            tarjeta,
            text="n debe ser par y mayor que %d."
                 % config.TAMANO_MINIMO_EXCLUSIVO,
            bg=paleta["fondo_tarjeta"], fg=paleta["texto_secundario"],
            font=(self._familia, 10),
        ).pack(anchor=tk.W, padx=22)

        fila_chips = tk.Frame(tarjeta, bg=paleta["fondo_tarjeta"])
        fila_chips.pack(padx=22, pady=(12, 4))

        # Los chips se generan a partir del motor: si en config.py se
        # amplia TAMANO_MAXIMO_TABLERO, aparecen solos.
        for n in motor.tamanos_validos():
            chip = BotonPastel(
                fila_chips, str(n),
                lambda valor=n: self._elegir(valor), self._familia,
                variante="chip", tamano_fuente=11,
            )
            chip.pack(side=tk.LEFT, padx=4)
            self._chips[n] = chip

        fila_manual = tk.Frame(tarjeta, bg=paleta["fondo_tarjeta"])
        fila_manual.pack(anchor=tk.W, padx=22, pady=(8, 4))

        tk.Label(
            fila_manual, text="Otro valor:", bg=paleta["fondo_tarjeta"],
            fg=paleta["texto_secundario"], font=(self._familia, 10),
        ).pack(side=tk.LEFT)

        self._entrada = tk.Entry(
            fila_manual, width=6, justify=tk.CENTER,
            bg=paleta["fondo_panel"], fg=paleta["texto_principal"],
            relief=tk.FLAT, highlightthickness=1,
            highlightbackground=paleta["borde_suave"],
            highlightcolor=paleta["boton_primario"],
            font=(self._familia, 11),
        )
        self._entrada.pack(side=tk.LEFT, padx=8, ipady=4)
        self._entrada.bind("<Return>", lambda _e: self._aplicar_entrada())

        BotonPastel(
            fila_manual, "Usar", self._aplicar_entrada, self._familia,
            tamano_fuente=10,
        ).pack(side=tk.LEFT)

        self._mensaje = tk.Label(
            tarjeta, text="", bg=paleta["fondo_tarjeta"],
            fg=paleta["aviso_error"], font=(self._familia, 10),
        )
        self._mensaje.pack(anchor=tk.W, padx=22, pady=(0, 14))

        self._elegir(self._n_elegido)

    def _construir_tarjeta_reglas(self, maestro: tk.Misc) -> None:
        paleta = config.PALETA
        tarjeta = _crear_tarjeta(maestro)
        tarjeta.pack(fill=tk.X)

        tk.Label(
            tarjeta, text="Reglas activas",
            bg=paleta["fondo_tarjeta"], fg=paleta["texto_principal"],
            font=(self._familia, 12, "bold"),
        ).pack(anchor=tk.W, padx=22, pady=(16, 6))

        # El texto se arma leyendo config.py, de modo que si el profesor
        # cambia una regla durante la interrogacion, la pantalla lo
        # refleja sin que haya que editar este archivo.
        if config.REGLA_BLOQUEO == config.BLOQUEADO_PIERDE:
            texto_bloqueo = ("Sin movimientos legales al inicio del turno: "
                             "ese jugador PIERDE.")
        else:
            texto_bloqueo = ("Sin movimientos legales al inicio del turno: "
                             "ese jugador GANA (regla clasica).")

        lineas = [
            "Fichas por jugador: n - %d." % config.FICHAS_MENOS_QUE_LADO,
            "%s %s." % (config.NOMBRES_JUGADORES[config.JUGADOR_A],
                        config.OBJETIVOS_JUGADORES[config.JUGADOR_A]),
            "%s %s." % (config.NOMBRES_JUGADORES[config.JUGADOR_B],
                        config.OBJETIVOS_JUGADORES[config.JUGADOR_B]),
            "Destino siempre vacio: no hay capturas ni saltos.",
            "Gana quien saca todas sus fichas del tablero.",
            texto_bloqueo,
            "Comienza: %s." % config.NOMBRES_JUGADORES[config.JUGADOR_INICIAL],
        ]
        for linea in lineas:
            tk.Label(
                tarjeta, text="•  " + linea, justify=tk.LEFT,
                bg=paleta["fondo_tarjeta"], fg=paleta["texto_secundario"],
                font=(self._familia, 10),
            ).pack(anchor=tk.W, padx=26)

        tk.Frame(tarjeta, bg=paleta["fondo_tarjeta"], height=14).pack()

    # -- interaccion -------------------------------------------------

    def _elegir(self, n: int) -> None:
        """Selecciona un tamano ofrecido como chip."""
        self._n_elegido = n
        self._mensaje.configure(text="")
        for valor, chip in self._chips.items():
            chip.marcar(valor == n)

    def _aplicar_entrada(self) -> None:
        """Valida el tamano escrito a mano usando el motor."""
        texto = self._entrada.get().strip()
        try:
            valor = int(texto)
        except ValueError:
            self._mensaje.configure(
                text="Escribe un numero entero.",
                fg=config.PALETA["aviso_error"])
            return

        if not motor.validar_n(valor):
            self._mensaje.configure(
                text=motor.motivo_invalidez(valor) or "Tamano invalido.",
                fg=config.PALETA["aviso_error"])
            return

        self._elegir(valor)
        self._mensaje.configure(
            text="Tablero de %d x %d listo." % (valor, valor),
            fg=config.PALETA["aviso_ok"])

    def _elegir_modo(self, modo: str) -> None:
        """Fija el modo y muestra u oculta la eleccion de nivel."""
        self._modo_elegido = modo
        for valor, chip in self._chips_modo.items():
            chip.marcar(valor == modo)

        # El nivel solo tiene sentido si juega al menos un bot.
        hay_agente = "agente" in config.CONTROLADOR_POR_MODO[modo].values()
        for chip in self._chips_nivel.values():
            chip.habilitar(hay_agente)
        color = (config.PALETA["texto_principal"] if hay_agente
                 else config.PALETA["texto_secundario"])
        self._etiqueta_nivel.configure(fg=color)
        if not hay_agente:
            self._descripcion_nivel.configure(
                text="Sin bot: los dos jugadores son humanos.")
        else:
            self._elegir_nivel(self._nivel_elegido)

    def _elegir_nivel(self, nivel: str) -> None:
        """Fija el nivel y explica que implica en jugadas de anticipacion."""
        self._nivel_elegido = nivel
        for valor, chip in self._chips_nivel.items():
            chip.marcar(valor == nivel)
        ajustes = config.NIVELES[nivel]
        self._descripcion_nivel.configure(
            text="Profundidad %d  (%s)  ·  tope de %.0f s"
                 % (ajustes["profundidad"], ajustes["descripcion"],
                    ajustes["segundos"]))

    def _comenzar(self) -> None:
        self._aplicacion.iniciar_partida(
            self._n_elegido, self._modo_elegido, self._nivel_elegido)


# =====================================================================
# PANTALLA 2: LA PARTIDA
# =====================================================================


class PantallaJuego(tk.Frame):
    """Tablero interactivo y panel de informacion.

    Mantiene una PILA de estados (self._estados). Como el motor nunca
    muta un estado, guardar la referencia anterior basta para deshacer:
    no hay que reconstruir nada ni invertir la jugada.
    """

    def __init__(self, maestro, aplicacion, familia, n: int,
                 modo: str = config.MODO_HUMANO_VS_HUMANO,
                 nivel: str = config.NIVEL_POR_DEFECTO):
        super().__init__(maestro, bg=config.PALETA["fondo_ventana"])
        self._aplicacion = aplicacion
        self._familia = familia
        self._n = n
        self._modo = modo
        self._nivel = nivel
        self._controlador = config.CONTROLADOR_POR_MODO[modo]

        # Un agente por jugador controlado por la maquina. Cada uno
        # conserva SU tabla de transposiciones durante toda la partida:
        # las posiciones ya analizadas siguen siendo validas jugada a
        # jugada, asi que reaprovecharlas es puro beneficio.
        self._agentes: Dict[str, agente.AgenteMinimax] = {
            jugador: agente.AgenteMinimax(jugador, nivel)
            for jugador, quien in self._controlador.items()
            if quien == "agente"
        }

        # Historial de la partida (responsabilidad de la interfaz, no
        # del motor: Minimax no necesita arrastrar el pasado).
        self._estados: List[motor.Estado] = [motor.estado_inicial(n)]
        self._jugadas: List[str] = []

        # Estado de interaccion del raton.
        self._seleccion: Optional[motor.Casilla] = None
        self._destinos: Dict[motor.Casilla, motor.Movimiento] = {}

        # --- coordinacion con el hilo del agente ---------------------
        # La busqueda NO puede correr en el hilo de Tkinter: mientras
        # calcula, la ventana dejaria de repintarse y de responder al
        # raton, y el sistema la marcaria como "no responde". Se lanza
        # en un hilo aparte que deja el resultado en una cola, y el
        # hilo de la interfaz la consulta periodicamente con after().
        # Regla de oro: SOLO el hilo de Tkinter toca widgets.
        self._cola_agente: "queue.Queue" = queue.Queue()
        self._cancelar_agente: Optional[threading.Event] = None
        self._pensando = False
        self._fase_animacion = 0
        # Identifica la partida en curso. Si el usuario reinicia
        # mientras el bot piensa, el resultado que llegue tarde traera
        # una generacion antigua y se descarta.
        self._generacion = 0
        self._ultimo_resultado_agente: Optional[agente.Resultado] = None
        self._ultima_jugada_agente: Optional[motor.Movimiento] = None

        # Geometria del lienzo, recalculada en cada redibujo.
        self._lado = 0.0
        self._origen_x = 0.0
        self._origen_y = 0.0

        self._construir()
        self._refrescar()

    # -- acceso al estado actual -------------------------------------

    @property
    def _estado(self) -> motor.Estado:
        return self._estados[-1]

    # -- construccion de la interfaz ---------------------------------

    def _construir(self) -> None:
        paleta = config.PALETA

        self._lienzo = tk.Canvas(
            self, bg=paleta["fondo_ventana"], highlightthickness=0, bd=0,
        )
        self._lienzo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._lienzo.bind("<Configure>", lambda _e: self._dibujar())
        self._lienzo.bind("<Button-1>", self._al_hacer_clic)
        self._lienzo.bind("<Motion>", self._al_mover_raton)

        panel = tk.Frame(self, bg=paleta["fondo_panel"],
                         width=config.ANCHO_PANEL_LATERAL)
        panel.pack(side=tk.RIGHT, fill=tk.Y)
        panel.pack_propagate(False)
        self._construir_panel(panel)

    def _construir_panel(self, panel: tk.Frame) -> None:
        paleta = config.PALETA

        tk.Label(
            panel, text=config.TITULO_VENTANA.upper(),
            bg=paleta["fondo_panel"], fg=paleta["texto_principal"],
            font=(self._familia, 22, "bold"),
        ).pack(anchor=tk.W, padx=22, pady=(20, 0))

        tk.Label(
            panel, text="Tablero %d x %d" % (self._n, self._n),
            bg=paleta["fondo_panel"], fg=paleta["texto_secundario"],
            font=(self._familia, 10),
        ).pack(anchor=tk.W, padx=22, pady=(0, 14))

        # --- tarjeta de turno ---
        tarjeta_turno = _crear_tarjeta(panel)
        tarjeta_turno.pack(fill=tk.X, padx=18, pady=(0, 12))

        fila = tk.Frame(tarjeta_turno, bg=paleta["fondo_tarjeta"])
        fila.pack(fill=tk.X, padx=16, pady=14)

        self._punto_turno = tk.Canvas(
            fila, width=18, height=18, bg=paleta["fondo_tarjeta"],
            highlightthickness=0,
        )
        self._punto_turno.pack(side=tk.LEFT)

        columna_texto = tk.Frame(fila, bg=paleta["fondo_tarjeta"])
        columna_texto.pack(side=tk.LEFT, padx=10)

        self._etiqueta_turno = tk.Label(
            columna_texto, text="", bg=paleta["fondo_tarjeta"],
            fg=paleta["texto_principal"], font=(self._familia, 13, "bold"),
        )
        self._etiqueta_turno.pack(anchor=tk.W)

        self._etiqueta_objetivo = tk.Label(
            columna_texto, text="", bg=paleta["fondo_tarjeta"],
            fg=paleta["texto_secundario"], font=(self._familia, 9),
            justify=tk.LEFT, wraplength=190,
        )
        self._etiqueta_objetivo.pack(anchor=tk.W)

        # --- marcadores de cada jugador ---
        self._marcadores: Dict[str, Dict[str, tk.Widget]] = {}
        for jugador in config.JUGADORES:
            self._marcadores[jugador] = self._construir_marcador(
                panel, jugador)

        # --- tarjeta del agente (solo si hay bot en la partida) ---
        self._tarjeta_agente = None
        if self._agentes:
            self._construir_tarjeta_agente(panel)

        # --- historial ---
        tk.Label(
            panel, text="Historial", bg=paleta["fondo_panel"],
            fg=paleta["texto_principal"], font=(self._familia, 11, "bold"),
        ).pack(anchor=tk.W, padx=22, pady=(8, 4))

        contenedor_historial = tk.Frame(panel, bg=paleta["fondo_panel"])
        contenedor_historial.pack(fill=tk.BOTH, expand=True,
                                  padx=18, pady=(0, 8))

        barra = tk.Scrollbar(contenedor_historial, orient=tk.VERTICAL,
                             relief=tk.FLAT, bd=0,
                             troughcolor=paleta["fondo_panel"])
        barra.pack(side=tk.RIGHT, fill=tk.Y)

        self._lista_historial = tk.Listbox(
            contenedor_historial, bg=paleta["fondo_tarjeta"],
            fg=paleta["texto_secundario"], font=(self._familia, 9),
            relief=tk.FLAT, highlightthickness=1, bd=0,
            highlightbackground=paleta["borde_suave"],
            selectbackground=paleta["seleccion"],
            selectforeground=paleta["texto_principal"],
            activestyle="none", yscrollcommand=barra.set,
        )
        self._lista_historial.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barra.configure(command=self._lista_historial.yview)

        # --- mensaje de estado ---
        self._etiqueta_mensaje = tk.Label(
            panel, text="", bg=paleta["fondo_panel"],
            fg=paleta["texto_secundario"], font=(self._familia, 10),
            wraplength=config.ANCHO_PANEL_LATERAL - 44, justify=tk.LEFT,
        )
        self._etiqueta_mensaje.pack(anchor=tk.W, padx=22, pady=(0, 10))

        # --- botones ---
        botonera = tk.Frame(panel, bg=paleta["fondo_panel"])
        botonera.pack(fill=tk.X, padx=18, pady=(0, 18))

        self._boton_deshacer = BotonPastel(
            botonera, "Deshacer", self._deshacer, self._familia,
            tamano_fuente=10)
        self._boton_deshacer.pack(side=tk.LEFT, expand=True, fill=tk.X,
                                  padx=(0, 4))

        BotonPastel(botonera, "Reiniciar", self._reiniciar, self._familia,
                    tamano_fuente=10).pack(side=tk.LEFT, expand=True,
                                           fill=tk.X, padx=4)

        BotonPastel(botonera, "Nuevo tablero", self._nuevo_tablero,
                    self._familia, tamano_fuente=10).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=(4, 0))

    def _construir_tarjeta_agente(self, panel: tk.Frame) -> None:
        """Tarjeta con el pensamiento del bot y sus estadisticas."""
        paleta = config.PALETA
        tarjeta = _crear_tarjeta(panel)
        tarjeta.pack(fill=tk.X, padx=18, pady=(4, 8))
        self._tarjeta_agente = tarjeta

        self._titulo_agente = tk.Label(
            tarjeta, text="", bg=paleta["fondo_tarjeta"],
            fg=paleta["texto_principal"], font=(self._familia, 11, "bold"),
            justify=tk.LEFT)
        self._titulo_agente.pack(anchor=tk.W, padx=16, pady=(12, 2))

        self._detalle_agente = tk.Label(
            tarjeta, text="", bg=paleta["fondo_tarjeta"],
            fg=paleta["texto_secundario"], font=(self._familia, 9),
            justify=tk.LEFT, wraplength=config.ANCHO_PANEL_LATERAL - 70)
        self._detalle_agente.pack(anchor=tk.W, padx=16, pady=(0, 12))

    def _construir_marcador(self, panel: tk.Frame,
                            jugador: str) -> Dict[str, tk.Widget]:
        """Tarjeta con las fichas en tablero y fuera de un jugador."""
        paleta = config.PALETA
        colores = config.COLORES_JUGADOR[jugador]

        tarjeta = _crear_tarjeta(panel)
        tarjeta.pack(fill=tk.X, padx=18, pady=(0, 8))

        cabecera = tk.Frame(tarjeta, bg=paleta["fondo_tarjeta"])
        cabecera.pack(fill=tk.X, padx=16, pady=(12, 4))

        punto = tk.Canvas(cabecera, width=14, height=14,
                          bg=paleta["fondo_tarjeta"], highlightthickness=0)
        punto.create_oval(1, 1, 13, 13, fill=colores["relleno"],
                          outline=colores["borde"])
        punto.pack(side=tk.LEFT)

        tk.Label(
            cabecera, text=config.NOMBRES_JUGADORES[jugador],
            bg=paleta["fondo_tarjeta"], fg=paleta["texto_principal"],
            font=(self._familia, 11, "bold"),
        ).pack(side=tk.LEFT, padx=8)

        etiqueta_cuenta = tk.Label(
            cabecera, text="", bg=paleta["fondo_tarjeta"],
            fg=paleta["texto_secundario"], font=(self._familia, 9),
        )
        etiqueta_cuenta.pack(side=tk.RIGHT)

        barra = tk.Canvas(tarjeta, height=8, bg=paleta["fondo_tarjeta"],
                          highlightthickness=0)
        barra.pack(fill=tk.X, padx=16, pady=(2, 14))

        return {"barra": barra, "cuenta": etiqueta_cuenta}

    # =================================================================
    # GEOMETRIA DEL TABLERO
    # =================================================================
    # El lienzo dibuja una rejilla logica mas ancha que el tablero:
    #
    #   fila  -1        -> carril de salida del jugador B (arriba)
    #   filas 0 .. n-1  -> tablero
    #   columnas 0..n-1 -> tablero
    #   columna n       -> carril de salida del jugador A (derecha)
    #
    # Gracias a esto, la coordenada "virtual" que devuelve un
    # movimiento de salida -por ejemplo (fila, n) para A- cae
    # exactamente sobre el carril correspondiente: no hace falta
    # ningun caso especial para dibujar o para detectar el clic.

    def _recalcular_geometria(self) -> None:
        ancho = self._lienzo.winfo_width()
        alto = self._lienzo.winfo_height()
        gutter = config.FRACCION_GUTTER_COORDENADAS

        # Columnas dibujadas: rotulo + tablero + carril de A.
        celdas_x = self._n + 1 + gutter
        # Filas dibujadas: carril de B + tablero + rotulo.
        celdas_y = self._n + 1 + gutter

        disponible_x = max(1, ancho - 2 * config.MARGEN_LIENZO)
        disponible_y = max(1, alto - 2 * config.MARGEN_LIENZO)

        self._lado = max(
            config.LADO_MINIMO_CELDA,
            min(disponible_x / celdas_x, disponible_y / celdas_y),
        )
        self._origen_x = (ancho - self._lado * celdas_x) / 2.0
        self._origen_y = (alto - self._lado * celdas_y) / 2.0

    def _esquina(self, fila: int, columna: int) -> Tuple[float, float]:
        """Pixel superior izquierdo de una celda logica."""
        gutter = config.FRACCION_GUTTER_COORDENADAS
        x = self._origen_x + (columna + gutter) * self._lado
        y = self._origen_y + (fila + 1) * self._lado
        return x, y

    def _centro(self, fila: int, columna: int) -> Tuple[float, float]:
        x, y = self._esquina(fila, columna)
        return x + self._lado / 2.0, y + self._lado / 2.0

    def _casilla_desde_pixel(self, px: float,
                             py: float) -> motor.Casilla:
        """Traduce un clic a coordenadas logicas (puede caer fuera)."""
        gutter = config.FRACCION_GUTTER_COORDENADAS
        columna = math.floor((px - self._origen_x) / self._lado - gutter)
        fila = math.floor((py - self._origen_y) / self._lado) - 1
        return int(fila), int(columna)

    # =================================================================
    # DIBUJO
    # =================================================================

    def _dibujar(self) -> None:
        """Redibuja el tablero completo desde cero.

        Reconstruir todo en cada cambio es mas simple y menos propenso
        a errores que actualizar objetos individuales, y con tableros
        de a lo mas 16 x 16 el costo es irrelevante.
        """
        if self._lienzo.winfo_width() <= 1:
            return  # La ventana aun no tiene tamano real.

        self._recalcular_geometria()
        self._lienzo.delete(tk.ALL)

        self._dibujar_carriles()
        self._dibujar_celdas()
        self._dibujar_rotulos()
        self._dibujar_ultima_jugada_del_bot()
        self._dibujar_marcadores_de_destino()
        self._dibujar_fichas()

        if motor.es_terminal(self._estado):
            self._dibujar_cartel_final()

    def _dibujar_carriles(self) -> None:
        """Zonas de salida: franja superior (B) y derecha (A)."""
        paleta = config.PALETA
        lado = self._lado
        radio = lado * config.FRACCION_RADIO_CELDA

        # Carril del jugador B: encima de la fila 0.
        x1, y1 = self._esquina(-1, 0)
        x2, y2 = self._esquina(-1, self._n - 1)
        _rectangulo_redondeado(
            self._lienzo, x1 + 2, y1 + 2, x2 + lado - 2, y2 + lado - 2,
            radio, fill=config.COLORES_JUGADOR[config.JUGADOR_B]["carril"],
            outline="")
        for columna in range(self._n):
            cx, cy = self._centro(-1, columna)
            self._dibujar_flecha(cx, cy, config.DIRECCION_AVANCE[
                config.JUGADOR_B])

        # Carril del jugador A: a la derecha de la columna n-1.
        x1, y1 = self._esquina(0, self._n)
        x2, y2 = self._esquina(self._n - 1, self._n)
        _rectangulo_redondeado(
            self._lienzo, x1 + 2, y1 + 2, x2 + lado - 2, y2 + lado - 2,
            radio, fill=config.COLORES_JUGADOR[config.JUGADOR_A]["carril"],
            outline="")
        for fila in range(self._n):
            cx, cy = self._centro(fila, self._n)
            self._dibujar_flecha(cx, cy, config.DIRECCION_AVANCE[
                config.JUGADOR_A])

    def _dibujar_flecha(self, cx: float, cy: float,
                        direccion: Tuple[int, int]) -> None:
        """Dibuja una flecha apuntando en la direccion indicada.

        La forma se deduce del vector de avance: si en config.py se
        cambia el sentido de un jugador, las flechas se reorientan
        solas.
        """
        tamano = self._lado * 0.18
        delta_fila, delta_columna = direccion
        punta = (cx + delta_columna * tamano, cy + delta_fila * tamano)
        # Vector perpendicular al de avance, para la base del triangulo.
        perp = (-delta_columna, delta_fila)
        base_x = cx - delta_columna * tamano * 0.6
        base_y = cy - delta_fila * tamano * 0.6
        izquierda = (base_x + perp[1] * tamano * 0.8,
                     base_y + perp[0] * tamano * 0.8)
        derecha = (base_x - perp[1] * tamano * 0.8,
                   base_y - perp[0] * tamano * 0.8)
        self._lienzo.create_polygon(
            punta[0], punta[1], izquierda[0], izquierda[1],
            derecha[0], derecha[1],
            fill=config.PALETA["flecha_carril"], outline="")

    def _dibujar_celdas(self) -> None:
        paleta = config.PALETA
        lado = self._lado
        separacion = lado * config.FRACCION_SEPARACION_CELDA
        radio = lado * config.FRACCION_RADIO_CELDA

        for fila in range(self._n):
            for columna in range(self._n):
                x, y = self._esquina(fila, columna)
                claro = (fila + columna) % 2 == 0
                color = paleta["celda_clara"] if claro else paleta[
                    "celda_oscura"]
                _rectangulo_redondeado(
                    self._lienzo,
                    x + separacion, y + separacion,
                    x + lado - separacion, y + lado - separacion,
                    radio, fill=color, outline=paleta["sombra_celda"],
                    width=1)

    def _dibujar_rotulos(self) -> None:
        """Numeracion de filas y columnas en la notacion del enunciado.

        Se muestran desde 1 (fila 1 = superior), aunque internamente el
        motor trabaje en base 0.
        """
        paleta = config.PALETA
        fuente = (self._familia, max(7, int(self._lado * 0.24)))

        for fila in range(self._n):
            x, _ = self._esquina(fila, 0)
            _, cy = self._centro(fila, 0)
            self._lienzo.create_text(
                x - self._lado * config.FRACCION_GUTTER_COORDENADAS / 2.0,
                cy, text=str(fila + 1), fill=paleta["texto_secundario"],
                font=fuente)

        base_y = self._esquina(self._n - 1, 0)[1] + self._lado
        for columna in range(self._n):
            cx, _ = self._centro(self._n - 1, columna)
            self._lienzo.create_text(
                cx,
                base_y + self._lado
                * config.FRACCION_GUTTER_COORDENADAS / 2.0,
                text=str(columna + 1), fill=paleta["texto_secundario"],
                font=fuente)

    def _dibujar_ultima_jugada_del_bot(self) -> None:
        """Marca de donde a donde movio el bot en su ultimo turno.

        Sin esta pista, contra un bot rapido cuesta darse cuenta de que
        ficha se movio: el tablero simplemente aparece distinto.
        """
        movimiento = self._ultima_jugada_agente
        if movimiento is None:
            return
        paleta = config.PALETA
        lado = self._lado
        separacion = lado * config.FRACCION_SEPARACION_CELDA
        radio = lado * config.FRACCION_RADIO_CELDA

        for casilla in (movimiento.origen, movimiento.destino):
            x, y = self._esquina(casilla[0], casilla[1])
            _rectangulo_redondeado(
                self._lienzo, x + separacion, y + separacion,
                x + lado - separacion, y + lado - separacion,
                radio, fill=paleta["resalte_jugada_bot"],
                outline=paleta["resalte_jugada_bot_borde"], width=2)

    def _dibujar_marcadores_de_destino(self) -> None:
        """Resalta las casillas legales de la ficha seleccionada."""
        if self._seleccion is None:
            return
        paleta = config.PALETA
        lado = self._lado
        separacion = lado * config.FRACCION_SEPARACION_CELDA
        radio_celda = lado * config.FRACCION_RADIO_CELDA
        radio_marcador = lado * config.FRACCION_DIAMETRO_MARCADOR / 2.0

        for casilla, movimiento in self._destinos.items():
            es_salida = movimiento.es_salida
            relleno = paleta["destino_salida" if es_salida
                             else "destino_normal"]
            borde = paleta["destino_salida_borde" if es_salida
                           else "destino_normal_borde"]
            x, y = self._esquina(casilla[0], casilla[1])
            _rectangulo_redondeado(
                self._lienzo, x + separacion, y + separacion,
                x + lado - separacion, y + lado - separacion,
                radio_celda, fill="", outline=borde, width=2)
            cx, cy = self._centro(casilla[0], casilla[1])
            self._lienzo.create_oval(
                cx - radio_marcador, cy - radio_marcador,
                cx + radio_marcador, cy + radio_marcador,
                fill=relleno, outline="")

        # Halo sobre la ficha seleccionada.
        x, y = self._esquina(self._seleccion[0], self._seleccion[1])
        _rectangulo_redondeado(
            self._lienzo, x + separacion, y + separacion,
            x + lado - separacion, y + lado - separacion,
            radio_celda, fill=paleta["seleccion"],
            outline=paleta["seleccion_borde"], width=2)

    def _dibujar_fichas(self) -> None:
        for jugador in config.JUGADORES:
            colores = config.COLORES_JUGADOR[jugador]
            for casilla in sorted(motor.fichas_de(self._estado, jugador)):
                self._dibujar_ficha(casilla, colores)

    def _dibujar_ficha(self, casilla: motor.Casilla,
                       colores: Dict[str, str]) -> None:
        lado = self._lado
        radio = lado * config.FRACCION_DIAMETRO_FICHA / 2.0
        cx, cy = self._centro(casilla[0], casilla[1])

        # Sombra suave, para dar sensacion de relieve.
        desplazamiento = lado * 0.045
        self._lienzo.create_oval(
            cx - radio, cy - radio + desplazamiento,
            cx + radio, cy + radio + desplazamiento,
            fill=config.PALETA["sombra_celda"], outline="")

        self._lienzo.create_oval(
            cx - radio, cy - radio, cx + radio, cy + radio,
            fill=colores["relleno"], outline=colores["borde"], width=2)

        # Brillo superior izquierdo.
        radio_brillo = radio * 0.34
        self._lienzo.create_oval(
            cx - radio * 0.42 - radio_brillo,
            cy - radio * 0.42 - radio_brillo,
            cx - radio * 0.42 + radio_brillo,
            cy - radio * 0.42 + radio_brillo,
            fill=colores["brillo"], outline="")

    def _dibujar_cartel_final(self) -> None:
        """Tarjeta central con el resultado de la partida."""
        paleta = config.PALETA
        resultado = motor.ganador(self._estado)
        ancho = self._lienzo.winfo_width()
        alto = self._lienzo.winfo_height()

        if resultado == config.EMPATE:
            titulo = "Tablas"
            color = paleta["texto_principal"]
        else:
            titulo = "Gana %s" % config.NOMBRES_JUGADORES[resultado]
            color = config.COLORES_JUGADOR[resultado]["borde"]

        ancho_tarjeta = min(ancho * 0.7, 420)
        alto_tarjeta = 132
        x1 = (ancho - ancho_tarjeta) / 2.0
        y1 = (alto - alto_tarjeta) / 2.0

        _rectangulo_redondeado(
            self._lienzo, x1, y1, x1 + ancho_tarjeta, y1 + alto_tarjeta,
            22, fill=paleta["fondo_panel"], outline=paleta["borde_suave"],
            width=2)
        self._lienzo.create_text(
            ancho / 2.0, y1 + 46, text=titulo, fill=color,
            font=(self._familia, 22, "bold"))
        self._lienzo.create_text(
            ancho / 2.0, y1 + 84,
            text=motor.motivo_de_termino(self._estado) or "",
            fill=paleta["texto_secundario"], font=(self._familia, 10),
            width=ancho_tarjeta - 40)

    # =================================================================
    # INTERACCION
    # =================================================================

    def _turno_es_humano(self) -> bool:
        """Indica si la jugada actual le corresponde a una persona."""
        return self._controlador[self._estado.turno] == "humano"

    def _al_hacer_clic(self, evento) -> None:
        """Selecciona una ficha propia o ejecuta un destino resaltado."""
        if motor.es_terminal(self._estado):
            return
        # Mientras piensa el bot el tablero queda en solo lectura: dejar
        # mover al humano en el turno del rival corromperia la partida
        # que el agente esta analizando en el otro hilo.
        if not self._turno_es_humano():
            return

        casilla = self._casilla_desde_pixel(evento.x, evento.y)

        # 1) Clic sobre un destino resaltado -> se juega el movimiento.
        if casilla in self._destinos:
            self._jugar(self._destinos[casilla])
            return

        # 2) Clic sobre una ficha propia -> se selecciona.
        if casilla in motor.fichas_de(self._estado, self._estado.turno):
            self._seleccionar(casilla)
            return

        # 3) Cualquier otro clic -> se deselecciona.
        self._seleccionar(None)

    def _al_mover_raton(self, evento) -> None:
        """Cambia el cursor cuando el raton esta sobre algo accionable."""
        if motor.es_terminal(self._estado) or not self._turno_es_humano():
            self._lienzo.configure(cursor="")
            return
        casilla = self._casilla_desde_pixel(evento.x, evento.y)
        accionable = (
            casilla in self._destinos
            or casilla in motor.fichas_de(self._estado, self._estado.turno)
        )
        self._lienzo.configure(cursor="hand2" if accionable else "")

    def _seleccionar(self, casilla: Optional[motor.Casilla]) -> None:
        """Fija la ficha activa y recalcula sus destinos legales.

        Los destinos NO se calculan aqui: se filtran de la lista que
        devuelve el motor. La interfaz nunca decide que es legal.
        """
        self._seleccion = casilla
        self._destinos = {}
        if casilla is not None:
            for movimiento in motor.movimientos_legales(self._estado):
                if movimiento.origen == casilla:
                    self._destinos[movimiento.destino] = movimiento
        self._dibujar()

    def _jugar(self, movimiento: motor.Movimiento) -> None:
        """Aplica un movimiento y apila el nuevo estado."""
        estado_previo = self._estado
        nuevo_estado = motor.aplicar(estado_previo, movimiento)

        self._estados.append(nuevo_estado)
        self._jugadas.append(
            motor.describir_movimiento(movimiento, estado_previo.turno))

        self._seleccion = None
        self._destinos = {}
        self._refrescar()

    # =================================================================
    # TURNO DEL AGENTE (en un hilo aparte)
    # =================================================================

    def _lanzar_turno_del_agente(self) -> None:
        """Pone a pensar al agente si le toca mover.

        Se llama al final de cada refresco. Comprueba tres cosas antes
        de arrancar: que la partida siga viva, que el turno sea de un
        jugador controlado por la maquina, y que no haya ya una
        busqueda en marcha.
        """
        if self._pensando or motor.es_terminal(self._estado):
            return
        cerebro = self._agentes.get(self._estado.turno)
        if cerebro is None:
            return

        self._pensando = True
        self._fase_animacion = 0
        self._cancelar_agente = threading.Event()

        hilo = threading.Thread(
            target=self._pensar_en_segundo_plano,
            args=(self._estado, cerebro, self._cancelar_agente,
                  self._generacion),
            daemon=True,   # No debe impedir que la ventana se cierre.
        )
        hilo.start()
        self.after(config.PAUSA_MINIMA_AGENTE_MS, self._sondear_agente)
        self._refrescar_panel_agente()

    def _pensar_en_segundo_plano(self, estado, cerebro, cancelar,
                                 generacion) -> None:
        """Cuerpo del hilo trabajador.

        IMPORTANTE: aqui no se toca ni un solo widget. Tkinter no es
        seguro para multiples hilos; hacerlo produce cierres
        inesperados dificiles de reproducir. La unica comunicacion con
        la interfaz es depositar una tupla en la cola.

        Trabajar sobre `estado` es seguro sin copiarlo ni bloquear
        nada porque el motor es puro: el hilo no puede modificarlo.
        """
        try:
            resultado = cerebro.elegir(estado, cancelar=cancelar)
            self._cola_agente.put((generacion, resultado, None))
        except Exception as error:            # noqa: BLE001
            # Cualquier fallo viaja a la interfaz para mostrarse ahi;
            # una excepcion perdida en un hilo daemon dejaria la
            # partida colgada en "pensando" sin explicacion.
            self._cola_agente.put((generacion, None, error))

    def _sondear_agente(self) -> None:
        """Consulta la cola desde el hilo de Tkinter."""
        if not self._pensando:
            return
        try:
            generacion, resultado, error = self._cola_agente.get_nowait()
        except queue.Empty:
            # Todavia piensa: se anima el indicador y se vuelve a mirar.
            self._fase_animacion += 1
            self._actualizar_indicador_pensando()
            self.after(config.INTERVALO_SONDEO_AGENTE_MS,
                       self._sondear_agente)
            return

        self._pensando = False

        # Resultado de una partida anterior (el usuario reinicio o
        # deshizo mientras el bot pensaba): se descarta.
        if generacion != self._generacion:
            return

        if error is not None:
            self._etiqueta_mensaje.configure(
                text="El agente fallo: %s" % error,
                fg=config.PALETA["aviso_error"])
            return

        self._ultimo_resultado_agente = resultado
        self._ultima_jugada_agente = resultado.movimiento
        self._jugar(resultado.movimiento)

    def _detener_agente(self) -> None:
        """Cancela la busqueda en curso e invalida su resultado.

        Se llama antes de reiniciar, deshacer o cambiar de pantalla.
        Subir la generacion basta para ignorar lo que llegue tarde; la
        senal de cancelacion, ademas, hace que el hilo termine pronto
        en vez de seguir gastando CPU.
        """
        self._generacion += 1
        if self._cancelar_agente is not None:
            self._cancelar_agente.set()
        self._pensando = False
        self._ultima_jugada_agente = None

    # -- botones -----------------------------------------------------

    def _deshacer(self) -> None:
        """Retrocede hasta la ultima decision de una persona.

        Basta con descartar estados: como aplicar() nunca muto el
        anterior, cada estado previo sigue intacto en la pila.

        Contra un bot no se retrocede UNA jugada sino todas las que
        haga falta hasta que vuelva a tocarle al humano. Deshacer solo
        una devolveria el turno al agente, que repetiria su jugada al
        instante (es determinista) y el boton pareceria no funcionar.
        """
        if len(self._estados) <= 1:
            return
        self._detener_agente()

        self._estados.pop()
        if self._jugadas:
            self._jugadas.pop()

        # Si hay agentes en juego, seguir retrocediendo mientras el
        # turno no sea de una persona.
        if self._agentes:
            while len(self._estados) > 1 and not self._turno_es_humano():
                self._estados.pop()
                if self._jugadas:
                    self._jugadas.pop()

        self._seleccion = None
        self._destinos = {}
        self._refrescar()

    def _reiniciar(self) -> None:
        self._detener_agente()
        for cerebro in self._agentes.values():
            cerebro.reiniciar()
        self._estados = self._estados[:1]
        self._jugadas = []
        self._seleccion = None
        self._destinos = {}
        self._ultimo_resultado_agente = None
        self._refrescar()

    def _nuevo_tablero(self) -> None:
        self._detener_agente()
        self._aplicacion.mostrar_configuracion()

    # =================================================================
    # ACTUALIZACION DEL PANEL
    # =================================================================

    def _refrescar(self) -> None:
        """Sincroniza todos los widgets con el estado actual."""
        estado = self._estado
        paleta = config.PALETA
        terminada = motor.es_terminal(estado)

        # Turno.
        colores_turno = config.COLORES_JUGADOR[estado.turno]
        self._punto_turno.delete(tk.ALL)
        self._punto_turno.create_oval(
            2, 2, 16, 16, fill=colores_turno["relleno"],
            outline=colores_turno["borde"], width=2)

        if terminada:
            self._etiqueta_turno.configure(text="Partida terminada")
            self._etiqueta_objetivo.configure(
                text=motor.motivo_de_termino(estado) or "")
        else:
            quien = self._controlador[estado.turno]
            sufijo = "" if quien == "humano" else "  (bot)"
            self._etiqueta_turno.configure(
                text="Turno de %s%s"
                     % (config.NOMBRES_JUGADORES[estado.turno], sufijo))
            self._etiqueta_objetivo.configure(
                text=config.OBJETIVOS_JUGADORES[estado.turno].capitalize())

        # Marcadores por jugador.
        total = motor.fichas_por_jugador(self._n)
        for jugador in config.JUGADORES:
            en_tablero = len(motor.fichas_de(estado, jugador))
            fuera = motor.salidas_de(estado, jugador)
            widgets = self._marcadores[jugador]
            widgets["cuenta"].configure(
                text="%d en tablero  |  %d fuera" % (en_tablero, fuera))
            self._dibujar_barra_progreso(widgets["barra"], jugador,
                                         fuera, total)

        # Historial.
        self._lista_historial.delete(0, tk.END)
        maximo = config.MAXIMO_JUGADAS_EN_HISTORIAL
        inicio = max(0, len(self._jugadas) - maximo)
        for numero, texto in enumerate(self._jugadas[inicio:],
                                       start=inicio + 1):
            self._lista_historial.insert(
                tk.END, "%3d.  %s" % (numero, texto))
        self._lista_historial.yview_moveto(1.0)

        # Mensaje inferior.
        if terminada:
            self._etiqueta_mensaje.configure(
                text=motor.motivo_de_termino(estado) or "",
                fg=paleta["texto_principal"])
        elif not self._turno_es_humano():
            self._etiqueta_mensaje.configure(
                text="El bot esta analizando la posicion...",
                fg=paleta["texto_secundario"])
        else:
            cantidad = len(motor.movimientos_legales(estado))
            self._etiqueta_mensaje.configure(
                text="Haz clic en una ficha de %s para ver sus %d jugadas "
                     "legales." % (config.NOMBRES_JUGADORES[estado.turno],
                                   cantidad),
                fg=paleta["texto_secundario"])

        self._boton_deshacer.habilitar(len(self._estados) > 1)
        self._refrescar_panel_agente()
        self._dibujar()

        # Ultimo paso: si le toca a un bot, se pone a pensar. Va aqui,
        # despues de dibujar, para que el usuario vea el tablero
        # actualizado antes de que empiece la busqueda.
        self._lanzar_turno_del_agente()

    # =================================================================
    # PANEL DEL AGENTE
    # =================================================================

    def _refrescar_panel_agente(self) -> None:
        """Muestra el estado y las estadisticas de la ultima busqueda.

        Estos numeros no son decoracion: son la evidencia de que la
        poda funciona. En la interrogacion permiten comparar nodos
        visitados y podas entre un nivel y otro sin salir del juego.
        """
        if self._tarjeta_agente is None:
            return

        if self._pensando:
            self._actualizar_indicador_pensando()
            return

        resultado = self._ultimo_resultado_agente
        if resultado is None:
            self._titulo_agente.configure(
                text="Bot (%s)" % self._nivel.capitalize())
            self._detalle_agente.configure(text="Aun no ha jugado.")
            return

        # El puntaje se muestra siempre desde el punto de vista DEL BOT,
        # que es su jugador_max. Decirlo evita la confusion de leer un
        # numero negativo y creer que va perdiendo el humano.
        if abs(resultado.valor) >= config.UMBRAL_VICTORIA:
            veredicto = ("Ve una victoria forzada suya."
                         if resultado.valor > 0
                         else "Se ve perdido con juego perfecto.")
        else:
            veredicto = "Se evalua a si mismo en %+.1f pasos." % (
                resultado.valor,)

        self._titulo_agente.configure(
            text="Bot (%s)  ·  %.2f s" % (self._nivel.capitalize(),
                                          resultado.segundos))
        self._detalle_agente.configure(
            text="%s\nProfundidad %d%s  ·  %s nodos  ·  %s podas\n"
                 "%s aciertos de tabla"
                 % (veredicto, resultado.profundidad,
                    "" if resultado.completa else " (cortado por tiempo)",
                    "{:,}".format(resultado.nodos).replace(",", " "),
                    "{:,}".format(resultado.podas).replace(",", " "),
                    "{:,}".format(resultado.aciertos_tabla).replace(",",
                                                                    " ")))

    def _actualizar_indicador_pensando(self) -> None:
        """Anima los puntos suspensivos mientras el agente calcula."""
        if self._tarjeta_agente is None:
            return
        puntos = "." * (1 + self._fase_animacion // 4 % 3)
        self._titulo_agente.configure(
            text="Bot (%s) pensando%s" % (self._nivel.capitalize(), puntos))
        self._detalle_agente.configure(
            text="Profundidad objetivo %d, tope de %.0f s."
                 % (config.NIVELES[self._nivel]["profundidad"],
                    config.NIVELES[self._nivel]["segundos"]))

    def _dibujar_barra_progreso(self, barra: tk.Canvas, jugador: str,
                                fuera: int, total: int) -> None:
        """Barra que muestra cuantas fichas ya salieron del tablero."""
        barra.delete(tk.ALL)
        ancho = barra.winfo_width()
        if ancho <= 1:
            # Aun sin geometria: se reintenta cuando Tk la calcule.
            barra.after(50, lambda: self._dibujar_barra_progreso(
                barra, jugador, fuera, total))
            return
        alto = int(barra["height"])
        colores = config.COLORES_JUGADOR[jugador]

        _rectangulo_redondeado(barra, 0, 0, ancho, alto, alto / 2.0,
                               fill=config.PALETA["celda_oscura"],
                               outline="")
        if total > 0 and fuera > 0:
            avance = max(alto, ancho * fuera / float(total))
            _rectangulo_redondeado(barra, 0, 0, avance, alto, alto / 2.0,
                                   fill=colores["relleno"], outline="")


# =====================================================================
# APLICACION
# =====================================================================


class AplicacionDodgem(tk.Tk):
    """Ventana principal: alterna entre configuracion y partida."""

    def __init__(self, n_inicial: Optional[int] = None,
                 modo: Optional[str] = None,
                 nivel: Optional[str] = None):
        super().__init__()
        self.title("%s - %s" % (config.TITULO_VENTANA,
                                config.SUBTITULO_VENTANA))
        self.configure(bg=config.PALETA["fondo_ventana"])
        self.geometry("%dx%d" % config.TAMANO_VENTANA_INICIAL)
        self.minsize(*config.TAMANO_VENTANA_MINIMO)

        self._familia = _familia_tipografica(self)
        self._pantalla: Optional[tk.Frame] = None

        self._modo = modo or config.MODO_POR_DEFECTO
        self._nivel = nivel or config.NIVEL_POR_DEFECTO

        # Cerrar la ventana debe cancelar cualquier busqueda en curso.
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

        if n_inicial is not None and motor.validar_n(n_inicial):
            self.iniciar_partida(n_inicial, self._modo, self._nivel)
        else:
            self.mostrar_configuracion()

    def _cambiar_pantalla(self, pantalla: tk.Frame) -> None:
        if self._pantalla is not None:
            detener = getattr(self._pantalla, "_detener_agente", None)
            if detener is not None:
                detener()
            self._pantalla.destroy()
        self._pantalla = pantalla
        pantalla.pack(fill=tk.BOTH, expand=True)

    def mostrar_configuracion(self) -> None:
        self._cambiar_pantalla(
            PantallaConfiguracion(self, self, self._familia))

    def iniciar_partida(self, n: int, modo: Optional[str] = None,
                        nivel: Optional[str] = None) -> None:
        self._modo = modo or self._modo
        self._nivel = nivel or self._nivel
        self._cambiar_pantalla(
            PantallaJuego(self, self, self._familia, n,
                          self._modo, self._nivel))

    def _al_cerrar(self) -> None:
        """Cancela la busqueda antes de destruir la ventana.

        El hilo del agente es daemon, asi que no impediria salir, pero
        avisarle evita que siga consumiendo CPU durante el cierre.
        """
        if self._pantalla is not None:
            detener = getattr(self._pantalla, "_detener_agente", None)
            if detener is not None:
                detener()
        self.destroy()


def lanzar(n_inicial: Optional[int] = None, modo: Optional[str] = None,
           nivel: Optional[str] = None) -> None:
    """Punto de entrada de la interfaz grafica."""
    aplicacion = AplicacionDodgem(n_inicial, modo, nivel)
    aplicacion.mainloop()
