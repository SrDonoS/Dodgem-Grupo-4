# Dodgem — Entrega 1

Juego de tablero **Dodgem** para dos jugadores humanos, con interfaz
gráfica. Fundamentos de Inteligencia Artificial.

Sin dependencias externas: solo la biblioteca estándar de Python 3.8+
(Tkinter viene incluido).

---

## Cómo ejecutar

```bash
python main.py              # abre la pantalla de configuración
python main.py --n 8        # arranca directamente en un tablero 8 x 8
python main.py --n 10 --diagnostico   # imprime el estado inicial y sale
```

Si Tkinter no está instalado (algunas distribuciones de Linux lo
separan del intérprete):

```bash
sudo apt install python3-tk
```

---

## Estructura del proyecto

| Archivo | Responsabilidad | Contiene lógica de juego |
|---|---|---|
| `config.py` | Todos los parámetros: tamaños, direcciones, reglas, colores. | No |
| `motor.py` | Máquina de estados **pura**: las 6 funciones exigidas. | Sí, toda |
| `gui.py` | Interfaz Tkinter: dibuja y traduce clics. | No |
| `main.py` | Punto de entrada y argumentos de línea de comandos. | No |
| `pruebas_motor.py` | 40 pruebas unitarias del motor. | No |

La regla de oro del diseño: **`gui.py` no sabe jugar al Dodgem.** Si
una jugada aparece resaltada en pantalla es porque
`motor.movimientos_legales()` la devolvió. Esa frontera es lo que
permitirá, en la Fase 2, reemplazar a un humano por un agente Minimax
sin tocar la interfaz.

---

## API del motor

```python
validar_n(n)                -> bool
estado_inicial(n)           -> Estado
movimientos_legales(estado) -> tuple[Movimiento, ...]
aplicar(estado, movimiento) -> Estado      # no muta el original
es_terminal(estado)         -> bool
ganador(estado)             -> "A" | "B" | "EMPATE" | None
```

### Representación del estado

```python
Estado(
    n            = 6,
    fichas_a     = frozenset({(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)}),
    fichas_b     = frozenset({(5, 1), (5, 2), (5, 3), (5, 4), (5, 5)}),
    turno        = "A",
    salidas_a    = 0,
    salidas_b    = 0,
    sin_progreso = 0,
)
```

* `NamedTuple` + `frozenset` ⇒ el estado es **inmutable y hashable**,
  así que sirve directamente como clave de una tabla de
  transposiciones en la Fase 2.
* Conjuntos de coordenadas en vez de matriz `n × n`: comprobar
  "casilla ocupada" cuesta O(1) y generar jugadas cuesta O(fichas), no
  O(n²).
* Coordenadas `(fila, columna)` en base 0, con fila 0 arriba. La
  conversión a la numeración del enunciado (desde 1) ocurre solo en la
  capa de presentación.

---

## Reglas implementadas

* Tablero `n × n` con **n par y n > 4**; `n − 1` fichas por jugador.
* Disposición inicial oficial: A ocupa la columna izquierda completa,
  B la fila inferior completa, y la esquina inferior izquierda queda
  vacía. Al descontar esa esquina compartida, cada jugador queda con
  exactamente `n − 1` fichas.
* **A** avanza a la derecha; puede desplazarse una casilla arriba o
  abajo. Nunca a la izquierda.
* **B** avanza hacia arriba; puede desplazarse una casilla a la
  izquierda o a la derecha. Nunca hacia abajo.
* El destino debe estar vacío. No hay capturas ni saltos.
* **Salidas**: una ficha abandona el tablero solo con un movimiento de
  *avance* cuyo destino cae fuera. Esa única condición implementa a la
  vez que A solo sale por la derecha y B solo por arriba: un intento de
  salir lateralmente usa un vector que no es el de avance y se descarta
  sin necesidad de una regla aparte.
* **Victoria por salida**: gana quien saca todas sus fichas.
* **Bloqueo**: si al inicio de su turno un jugador conserva fichas pero
  no tiene movimientos legales, pierde (no se permite pasar).

> Nota: el Dodgem clásico usa la convención inversa para el bloqueo
> (se penaliza a quien bloquea). Ambas están implementadas; la activa
> se elige con `config.REGLA_BLOQUEO`.

---

## Parámetros modificables en vivo

Todo lo siguiente se cambia editando **solo `config.py`**, sin tocar
`motor.py` ni `gui.py`:

| Quiero cambiar… | Constante |
|---|---|
| El rango de tamaños permitidos | `TAMANO_MINIMO_EXCLUSIVO`, `TAMANO_MAXIMO_TABLERO` |
| Que n pueda ser impar | `RESTO_PARIDAD_REQUERIDO` |
| Cuántas fichas tiene cada jugador | `FICHAS_MENOS_QUE_LADO` |
| La dirección de avance de un jugador | `DIRECCION_AVANCE` (la colocación inicial se reacomoda sola) |
| Los movimientos laterales permitidos | `DIRECCIONES_LATERALES` |
| Que la esquina compartida no quede vacía | `ESQUINA_COMPARTIDA_VACIA` |
| Quién gana al quedar bloqueado | `REGLA_BLOQUEO` |
| Activar tablas por falta de progreso | `TABLAS_HABILITADAS`, `LIMITE_JUGADAS_SIN_PROGRESO` |
| Quién mueve primero | `JUGADOR_INICIAL` |
| Los colores de la interfaz | `PALETA` |

---

## Pruebas

```bash
python -m unittest pruebas_motor -v
```

40 pruebas que cubren: validación de `n`, disposición inicial para
todos los tamaños, prohibición de retroceder, reglas de salida por el
borde correcto, pureza de `aplicar()`, condiciones de victoria y de
bloqueo (con ambas convenciones), tablas, y una simulación de partidas
aleatorias que verifica invariantes jugada a jugada:

* fichas en tablero + fichas fuera = `n − 1`, siempre;
* nunca hay dos fichas en la misma casilla;
* toda ficha en juego está dentro del tablero.

---

## Preparado para la Fase 2 (Minimax + poda Alfa-Beta)

Lo que ya está resuelto para el agente:

1. **Funciones puras**: `aplicar()` devuelve un estado nuevo, así que
   la recursión no necesita deshacer jugadas.
2. **Estados hashables**: tabla de transposiciones sin trabajo extra.
3. **Orden de jugadas**: `movimientos_legales()` entrega primero las
   salidas y los avances (`config.ORDEN_TIPOS_MOVIMIENTO`), que es el
   orden que provoca más cortes en la poda Alfa-Beta.
4. **Corte de profundidad infinita**: el contador `sin_progreso` y la
   regla opcional de tablas evitan ramas que nunca terminan.
5. **Interruptor de rendimiento**:
   `config.VALIDAR_MOVIMIENTOS_AL_APLICAR = False` elimina la
   revalidación dentro de `aplicar()` cuando el buscador ya garantiza
   que el movimiento es legal.

El agente se conectará con una función nueva del tipo
`elegir_movimiento(estado) -> Movimiento`; la interfaz solo tendrá que
llamarla cuando el turno sea del agente y pasar el resultado a
`aplicar()`.
