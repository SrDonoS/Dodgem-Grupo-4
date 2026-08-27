# 👤 SECCIÓN 3 — VALENTÍN

## El Agente: Minimax con Poda Alfa-Beta

**Tu archivo:** `agente.py` ⚠️ *(singular, no `agentes.py`)*
**Tu tema estrella:** por qué la poda no cambia el resultado, y por qué
el orden de los movimientos lo es todo.

---

## 3.1 🧠 Empecemos por cero: ¿qué es Minimax?

Imagina que juegas al ajedrez y piensas: *"si muevo aquí, él movería
allá, y entonces yo…"*. Eso es Minimax. Formalizado:

- Hay **dos jugadores con intereses opuestos**.
- Tú (**MAX**) quieres el puntaje **más alto** posible.
- Él (**MIN**) quiere el **más bajo**.
- Supones que el rival **juega lo mejor que puede** (pesimismo
  racional: si funciona contra el mejor rival, funciona contra
  cualquiera).

```
                  MAX (mi turno)  → elige el MÁXIMO
                 /       |       \
            MIN        MIN        MIN   → cada uno elige el MÍNIMO
           /  \        /  \       /  \
          3    5      2    9     0    7   ← hojas: la heurística de Carlos
```

- Cada nodo MIN toma el mínimo: 3, 2, 0
- El nodo MAX toma el máximo de esos: **3**

🎯 **Tu frase:** *"Minimax no busca la jugada que más me conviene si el
rival se equivoca. Busca la que **mejor resiste** si el rival juega
perfecto."*

---

## 3.2 ✂️ La poda Alfa-Beta ⭐ TU TEMA ESTRELLA

### El problema

El árbol crece **exponencialmente**. Con ~10 jugadas legales por turno,
mirar 6 jugadas adelante son 10⁶ = **un millón** de posiciones.

### La idea de la poda (explícala con este ejemplo)

```
            MAX
           /    \
      MIN A      MIN B
      /  \       /   \
     3    5     2     ???   ← ¡esta rama NO hace falta mirarla!
```

1. Exploro **A** completo → vale 3 (MIN eligió el mínimo entre 3 y 5).
2. Empiezo **B** y el primer hijo vale **2**.
3. B es un nodo MIN, así que su valor final será **≤ 2**.
4. Pero yo (MAX) ya tengo **3** garantizado con A.
5. **Nunca elegiría B.** ✂️ No hace falta mirar el resto.

### Las dos variables

| Variable | Significado |
|---|---|
| **α (alfa)** | Lo mejor que **MAX** tiene asegurado hasta ahora |
| **β (beta)** | Lo mejor que **MIN** tiene asegurado hasta ahora |

**Condición de corte: `α ≥ β`** → la rama actual ya no puede influir en
la decisión, porque el jugador de arriba ya tiene una opción al menos
igual de buena.

### 🚨 La afirmación clave

> 💬 **"La poda NO cambia el resultado. Solo cambia el trabajo. Devuelve
> exactamente el mismo valor que un Minimax sin poda."**

**Y no lo decimos de palabra: lo demostramos.** `agente.py` incluye
`minimax_sin_poda()`, una implementación de referencia deliberadamente
lenta y **obviamente correcta**:

```python
def minimax_sin_poda(estado, profundidad, jugador_max, ply=0):
    resultado = motor.ganador(estado)
    if resultado is not None or profundidad == 0:
        return heuristica.evaluar(estado, jugador_max, ply, resultado)
    valores = [minimax_sin_poda(motor.aplicar(estado, m, validar=False),
                                profundidad - 1, jugador_max, ply + 1)
               for m in motor.movimientos_legales(estado)]
    return max(valores) if estado.turno == jugador_max else min(valores)
```

Y las pruebas comparan las dos búsquedas sobre **decenas de posiciones
y varias profundidades**. Si alguna vez difirieran, la optimización
estaría mal.

> 🎤 **Si el profesor pregunta "¿cómo sé que su poda es correcta?"**,
> esta es tu respuesta, y es de las mejores del proyecto.

### 📊 Evidencia real (tablero 6×6, posición inicial)

| Profundidad | Sin poda | Con poda | Poda + tabla | Ahorro |
|---|---|---|---|---|
| 3 | 326 | 135 | 135 | 2,4× |
| 4 | 2 702 | 584 | 469 | 5,8× |
| 5 | **24 028** | 2 214 | **1 475** | **16,3×** |

Ramificación efectiva tras podar: **4,67** (frente a las jugadas
legales reales).

---

## 3.3 🎯 El orden de los movimientos lo es TODO

**❓ "¿Por qué importa el orden si el resultado es el mismo?"**

Porque **Alfa-Beta poda más cuanto antes aparezca la mejor jugada**.

- 🥇 **Orden perfecto:** el ahorro es máximo (raíz cuadrada del número
  de nodos: pasas de `bᵈ` a `b^(d/2)`, que es como **duplicar la
  profundidad gratis**).
- 🥉 **Orden pésimo** (peor jugada primero): la poda no sirve
  prácticamente de nada.

### Nuestras dos fuentes de orden

**1. El orden natural del motor.** `movimientos_legales()` devuelve
primero las **salidas**, luego los **avances**, luego los
**laterales** — `config.ORDEN_TIPOS_MOVIMIENTO`.

> 💬 *"Las salidas y los avances son justamente las jugadas que más
> reducen h(n), la distancia a la meta. Explorar primero lo que más
> promete es la misma idea que en una búsqueda informada."*

**2. La mejor jugada de la iteración anterior**, guardada en la tabla
de transposiciones. Es la optimización **más rentable de todas**: si la
primera jugada examinada resulta ser la mejor, todas las demás se podan
casi de inmediato.

```python
@staticmethod
def _ordenar(movimientos, sugerido):
    if sugerido is None or sugerido not in movimientos:
        return movimientos
    return [sugerido] + [m for m in movimientos if m != sugerido]
```

---

## 3.4 🗃️ La tabla de transposiciones

### ¿Qué es una "transposición"?

**Distintas secuencias de jugadas que llevan a la misma posición.**
Mover primero la ficha 1 y luego la 2 da el mismo tablero que mover
primero la 2 y luego la 1. Sin tabla, el árbol vuelve a evaluar ese
subárbol entero **cada vez**.

### 🎁 Aquí cobramos una decisión de la Entrega 1

> 💬 *"`Estado` es un `NamedTuple` de `frozenset`, o sea **hashable**, y
> sirve tal cual como clave de un diccionario. No tuvimos que inventar
> ninguna función de hash: el diseño inmutable del motor nos lo dio
> gratis."*

### Qué se guarda

```python
class Entrada(NamedTuple):
    profundidad: int       # profundidad RESTANTE con la que se analizó
    valor: float           # puntaje, ya normalizado
    bandera: str           # EXACTO | COTA_INFERIOR | COTA_SUPERIOR
    mejor: Movimiento      # para ordenar en el futuro
```

**Las tres banderas** (te lo pueden preguntar):

| Bandera | Significado | Cuándo se guarda |
|---|---|---|
| `EXACTO` | El valor guardado es el verdadero | El nodo se exploró completo dentro de la ventana |
| `COTA_INFERIOR` | El verdadero es **≥** al guardado | Hubo corte por beta (fail-high) |
| `COTA_SUPERIOR` | El verdadero es **≤** al guardado | Nunca superó alfa (fail-low) |

**Reemplazo:** si la entrada existente se analizó **más a fondo**, se
conserva. Vale más una respuesta mirando 6 jugadas que una mirando 2.

---

## 3.5 ⚠️ EL DETALLE DELICADO: puntajes de victoria en la tabla

🔴 **Esto es lo más sofisticado del proyecto. Domínalo.**

### El problema

`evaluar()` devuelve `VICTORIA − profundidad` para un final ganado. Ese
valor depende de **DÓNDE está el nodo en el árbol**, no solo de la
posición.

Si lo guardaras tal cual y lo reutilizaras desde **otra** profundidad,
el agente creería tener una victoria más cercana (o más lejana) de lo
que realmente es.

### La solución

```python
def _hacia_la_tabla(valor, ply):      # al GUARDAR
    if valor >= UMBRAL_VICTORIA:  return valor + ply
    if valor <= -UMBRAL_VICTORIA: return valor - ply
    return valor                       # los puntajes normales no se tocan

def _desde_la_tabla(valor, ply):      # al LEER (operación inversa)
    if valor >= UMBRAL_VICTORIA:  return valor - ply
    if valor <= -UMBRAL_VICTORIA: return valor + ply
    return valor
```

Se convierte el puntaje a **"distancia desde este nodo"**. Así el valor
guardado dice *"desde aquí se gana en d jugadas"*, que **sí** es una
propiedad de la posición y no del sitio donde la encontramos.

> 🎤 **Frase para la defensa:** *"Es el error clásico de un Minimax con
> transposiciones, y es exactamente lo que caza nuestra prueba
> `test_la_tabla_no_altera_el_valor`: compara la búsqueda con tabla
> contra el Minimax puro. Si la normalización estuviera mal, los
> valores se desviarían justo en las posiciones ganadas, que son las
> que importan."*

---

## 3.6 🔁 Profundización iterativa y búsqueda "anytime"

### Qué es

En vez de buscar directamente a profundidad 6, se busca a **1, luego 2,
luego 3…** hasta la profundidad objetivo o hasta agotar el tiempo.

### ❓ "¿No es un desperdicio repetir el trabajo?"

**No, y hay dos razones:**

**1. Cada iteración deja en la tabla la mejor jugada de cada posición.**
La iteración siguiente empieza examinando esa jugada primero y **poda
muchísimo más**. El trabajo "repetido" es una inversión en ordenamiento.

📐 *Dato numérico:* el árbol crece exponencialmente, así que las
iteraciones 1..d−1 juntas cuestan mucho menos que la iteración d. El
sobrecoste teórico es de apenas ~b/(b−1), y el mejor ordenamiento
**compensa de sobra**.

**2. Siempre hay una respuesta lista.** Eso es la propiedad
**ANYTIME**: si te interrumpen en cualquier momento, tienes una jugada
válida disponible.

### 🎯 La sutileza que debes mencionar tú mismo

> 💬 *"Si el tope de tiempo salta a media iteración, devolvemos el
> resultado de la **última profundidad COMPLETA**, nunca el de una
> iteración a medias. Como la raíz se explora en orden, una iteración
> incompleta solo ha visto las primeras jugadas y su 'mejor' estaría
> **sesgada por ese orden**."*

⭐ Esa observación demuestra que entendiste el algoritmo de verdad.

### El corte temprano

```python
if abs(valor) >= config.UMBRAL_VICTORIA:
    break   # ya demostró victoria o derrota forzada
```

Si ya sabes que ganas, mirar más hondo no aporta nada.

---

## 3.7 ⚖️ g(n) vs h(n) — la pregunta que SEGURO te hacen

### En A\* (búsqueda informada clásica)

```
f(n) = g(n) + h(n)
       ↑      ↑
       │      └── coste ESTIMADO de aquí al final
       └───────── coste REAL ya pagado desde el inicio
```

### En nuestro árbol de juego

| Concepto | Dónde está en nuestro código |
|---|---|
| **g(n)** | La **PROFUNDIDAD** del nodo (`ply`): cuántas jugadas se gastaron para llegar. Es coste ya pagado y **conocido**. |
| **h(n)** | Lo que devuelve `heuristica_dodgem()` en las hojas del corte de profundidad. Es la estimación de lo que **falta**. |
| **f(n)** | La función `evaluar()`, que combina ambas: un final ganado vale `VICTORIA − profundidad`. |

### 🚨 Sé honesto con el matiz (esto te da credibilidad)

> 💬 *"Conviene enunciarlo con precisión, porque **no son el mismo
> algoritmo**. En A\* ordenas la frontera por f = g + h. En Minimax no
> hay frontera ordenada: hay un árbol con dos jugadores. La analogía es
> **real pero no literal**: g(n) aparece como el descuento por
> profundidad, que hace que entre dos victorias el agente elija la más
> corta y entre dos derrotas la más larga. Y h(n) es literalmente la
> heurística en las hojas."*

⚠️ Si dices "esto es A\*" sin más, un profesor atento te corrige. Si tú
mismo señalas el matiz, ganas puntos.

---

## 3.8 🔍 Función por función

| Función | Qué hace | Por qué existe |
|---|---|---|
| `_Buscador.__init__` | Guarda jugador, tabla, reloj, contadores | Se separa del agente porque el **agente** vive toda la partida (conserva la tabla) y el **buscador** vive una sola jugada (contadores y reloj) |
| `_comprobar_limites()` | Revisa reloj y cancelación | Solo cada **2048 nodos**: consultar el reloj en cada nodo costaría más que evaluar la posición |
| `_ordenar()` | Pone delante la mejor jugada conocida | La optimización más rentable |
| `_alfa_beta()` | El núcleo recursivo | Es el algoritmo |
| `_guardar()` | Escribe en la tabla con reemplazo por profundidad | Al llenarse, la tabla se vacía entera (política simple, se reinicia por partida) |
| `buscar_raiz()` | Explora la raíz y devuelve **(valor, jugada)** | La raíz se trata aparte porque aquí sí importa **cuál** es la mejor jugada, no solo su valor |
| `AgenteMinimax.elegir()` | Profundización iterativa + estadísticas | Es la API pública |
| `AgenteMinimax.reiniciar()` | Vacía la tabla | Al empezar partida nueva |
| `elegir_movimiento()` | API mínima: estado → jugada | Es la firma que prometimos al cerrar la Entrega 1 |
| `minimax_sin_poda()` | Referencia lenta y correcta | **Para demostrar que la poda no altera el resultado** |
| `valor_con_alfa_beta()` | Valor + nodos visitados | Permite medir cuánto ahorra cada optimización activándolas y desactivándolas |

### `Resultado` — lo que ve el usuario

```python
class Resultado(NamedTuple):
    movimiento, valor, profundidad, nodos, podas,
    aciertos_tabla, segundos, completa
```

El panel lateral muestra esto en vivo durante la partida.

> 💬 *"Esos números no son decoración: son **la evidencia de que la
> poda funciona**. En la interrogación permiten comparar nodos
> visitados y podas entre un nivel y otro sin salir del juego."*

---

## 3.9 🔥 CAMBIOS EN VIVO — Tu guion paso a paso

### 🎚️ Cambio 1: "Cambie la profundidad / añada un nivel"

**Archivo:** `config.py`, sección 9.

```python
NIVELES = {
    "facil":   {"profundidad": 2, "segundos": 2.0,  "descripcion": "..."},
    "medio":   {"profundidad": 4, "segundos": 4.0,  "descripcion": "..."},
    "dificil": {"profundidad": 6, "segundos": 8.0,  "descripcion": "..."},
    "experto": {"profundidad": 8, "segundos": 15.0, "descripcion": "..."},
    # ← AÑADE AQUÍ
    "brutal":  {"profundidad": 10, "segundos": 30.0,
                "descripcion": "Cinco jugadas por bando."},
}
ORDEN_NIVELES = ("facil", "medio", "dificil", "experto", "brutal")
```

> 🎤 *"La interfaz genera los botones a partir de `ORDEN_NIVELES`, así
> que el nivel nuevo **aparece solo** sin tocar `gui.py`."*

### 🎲 Cambio 2: "Hágalo estocástico (que elija al azar entre empates)"

⭐ **Esta es tu pregunta trampa. Prepárala bien.**

**Estado actual: DETERMINISTA.** En `buscar_raiz`, entre jugadas de
igual valor se queda con la **primera** (`if valor > mejor_valor`, con
`>` estricto).

**Cómo hacerlo estocástico** — en `agente.py`, `buscar_raiz`:

```python
import random   # ← añadir arriba del archivo

# ANTES
for movimiento in movimientos:
    hijo = motor.aplicar(estado, movimiento, validar=False)
    valor = self._alfa_beta(hijo, profundidad - 1, alfa, beta, 1)
    if maximizando:
        if valor > mejor_valor:
            mejor_valor, mejor_movimiento = valor, movimiento
            alfa = max(alfa, valor)

# DESPUÉS: se recogen TODAS las empatadas y se elige una al azar
empatadas = []
for movimiento in movimientos:
    hijo = motor.aplicar(estado, movimiento, validar=False)
    valor = self._alfa_beta(hijo, profundidad - 1, -INFINITO, INFINITO, 1)
    if valor > mejor_valor:
        mejor_valor, empatadas = valor, [movimiento]
    elif valor == mejor_valor:
        empatadas.append(movimiento)
mejor_movimiento = random.choice(empatadas)
```

🚨 **El detalle CRÍTICO que debes mencionar** (y que casi nadie ve):

> 💬 *"Fíjese que al hacerlo estocástico **hay que dejar de podar con
> alfa en la raíz**: le paso `-INFINITO, INFINITO` a cada hijo. Si
> podara, las jugadas inferiores devolverían **cotas** en lugar de
> valores exactos, y el conjunto de 'empatadas' quedaría mal
> identificado. Se pierde algo de velocidad en la raíz —solo ahí, las
> ramas internas siguen podando— a cambio de que el desempate sea
> correcto."*

**Ventajas de cada opción:**

| Determinista ✅ | Estocástico ✅ |
|---|---|
| Reproducible: misma partida siempre | Menos predecible para el humano |
| Se puede depurar | Más natural de jugar |
| **Se puede reproducir en la evaluación** | Necesario para **medir** (si no, 20 partidas son 1 repetida 20 veces) |

> 🎤 *"De hecho, en nuestro **banco de medición** el agente **sí** es
> estocástico, justamente porque enfrentando dos agentes deterministas
> las 20 partidas serían la misma repetida. En el juego lo dejamos
> determinista para que usted pueda reproducir una partida."*

⭐⭐ Esa respuesta es de sobresaliente: muestra que entiendes que la
misma decisión de diseño tiene respuestas distintas según el contexto.

### ⏱️ Cambio 3: "Quite el límite de tiempo" / "Póngalo en 1 segundo"

```python
NIVELES["dificil"]["segundos"] = 1.0     # o 0 para desactivarlo
```

**Cómo explicar el diseño:**

> *"La **profundidad manda** y el tiempo es solo una red de seguridad.
> Lo elegimos así porque el bot debe ser **reproducible**: si la
> dificultad dependiera del reloj, jugaría distinto en cada computador
> y usted no podría reproducir una partida. El tope solo se activa en
> tableros grandes."*

📊 **Datos que respaldan la decisión:**

| Nivel | n=6 | n=10 | n=16 |
|---|---|---|---|
| fácil (prof. 2) | 0,00 s | 0,00 s | 0,01 s |
| medio (prof. 4) | 0,01 s | 0,03 s | 0,25 s |
| difícil (prof. 6) | 0,09 s | 0,78 s | **8,02 s\*** |
| experto (prof. 8) | 0,50 s | 5,67 s | **15,04 s\*** |

`*` = actuó el tope de seguridad.

### 🔬 Cambio 4: "Demuéstreme que la poda sirve"

```bash
python banco_agente.py
```

O en vivo:

```python
python3 -c "
import agente, config, motor
e = motor.estado_inicial(6)
for usar in (False, True):
    v, n = agente.valor_con_alfa_beta(e, 5, 'A', usar_tabla=False, usar_poda=usar)
    print('poda=%-5s  valor=%.1f  nodos=%d' % (usar, v, n))"
```

> 🎤 *"Fíjese que el **valor es idéntico** en las dos líneas. Solo
> cambian los nodos: de 24 028 a 2 214."*

---

## 3.10 🎯 Preguntas trampa para Valentín

| ❓ Pregunta | ✅ Respuesta |
|---|---|
| *"¿Alfa-Beta encuentra siempre la misma jugada que Minimax puro?"* | *"Siempre el mismo **valor**. La **jugada** puede diferir si hay empates, porque depende del orden de exploración. Ambas son óptimas."* ⭐ |
| *"¿Qué pasa si la heurística de Carlos es mala?"* | *"El agente juega mal, pero **la búsqueda sigue siendo correcta**. Son responsabilidades separadas: yo garantizo que encuentro el óptimo **según la función de evaluación**; Carlos garantiza que esa función mide lo correcto."* |
| *"¿Por qué su agente juega en otro hilo?"* | *"Porque si Minimax corriera en el hilo de Tkinter, la ventana dejaría de repintarse y el sistema la marcaría como 'no responde'."* |
| *"¿Y si el usuario reinicia mientras piensa?"* | *"Hay un contador de **generación**: el resultado que llega tarde trae una generación antigua y se descarta. Además un `threading.Event` cancela la búsqueda."* |
| *"¿Su agente es óptimo?"* | *"Es óptimo **hasta la profundidad de búsqueda**. Más allá confía en la heurística. Solo con profundidad infinita sería juego perfecto."* |
| *"¿Cuántos nodos por segundo?"* | *"Depende de la posición. La heurística cuesta ~15,7 µs, así que el techo son ~64 000 evaluaciones/s. A profundidad 5 visitamos 1 475 nodos con tabla."* |
| *"¿Por qué guarda la tabla entre jugadas?"* | *"Porque las posiciones ya analizadas siguen siendo válidas. `config.REUSAR_TABLA_ENTRE_JUGADAS` lo controla; se limpia al empezar partida nueva."* |
| *"¿Qué pasa si dos posiciones distintas tienen el mismo hash?"* | *"No usamos hash truncado: la clave es el `Estado` completo, así que Python compara por igualdad real. No hay colisiones falsas. En motores serios se usa Zobrist de 64 bits y sí puede haber colisiones."* ⭐ |

---

# 🚨 ANEXO: Cosas que TODOS deben saber

## ⚠️ Limitaciones honestas (mejor decirlas ustedes que descubrirlas)

**1. Muchas partidas bot-contra-bot no terminan.** 8 de cada 20 llegan
al tope de 400 jugadas.

> *"Es una propiedad conocida del Dodgem en tableros pares: con juego
> defensivo por ambos lados la partida puede no acabar. Está
> documentado para 4×4 y 5×5. Por eso implementamos tablas opcionales
> con `TABLAS_HABILITADAS`."*

💡 **Si van a demostrar bot vs bot mañana, actívenlo antes.**

**2. Los pesos están ajustados sobre 6×6 y 8×8 a profundidad 1–2.**

> *"El siguiente paso sería re-tunearlos contra el agente final, no
> contra el baseline de solo distancia."*

**3. Si se invierte el avance de un jugador a un eje distinto**, hay
que cambiar también sus `DIRECCIONES_LATERALES` para que sean
perpendiculares.

## 🧪 El as bajo la manga: las pruebas

```bash
python -m unittest pruebas_motor pruebas_heuristica pruebas_agente -v
```

**98 pruebas.** Si el profesor duda de una afirmación, hay una prueba
que la respalda:

| Afirmación | Prueba que la demuestra |
|---|---|
| "`aplicar` no muta" | `test_no_muta_el_estado_original` |
| "La distancia es admisible" | `test_es_exacta_en_el_problema_relajado` (BFS independiente) |
| "Cada turno reduce D en ≤1" | `test_cada_turno_reduce_la_distancia_total_a_lo_sumo_en_uno` |
| "La poda no cambia el valor" | `test_la_poda_no_altera_el_valor` |
| "La tabla no cambia el valor" | `test_la_tabla_no_altera_el_valor` |
| "n impar funciona" | `test_acepta_tableros_impares_si_se_cambia_la_paridad` |
| "Nunca hay fichas encimadas" | `test_nunca_hay_fichas_encimadas_en_la_apertura` |

> 🎤 **Frase de cierre potentísima:** *"Cada afirmación de diseño que
> acabamos de hacer tiene una prueba unitaria que la respalda. Puede
> ejecutarlas ahora mismo."*

## 💬 Las 5 frases que deben salir en la defensa

1. 🏛️ *"La interfaz no sabe jugar al Dodgem. Si una jugada se resalta
   es porque el motor la devolvió."*
2. 🧊 *"El estado es inmutable y hashable, y eso nos dio la tabla de
   transposiciones gratis."*
3. 🎯 *"Un destino fuera del tablero es legal solo si el vector era el
   de avance. Esa única condición implementa las dos reglas de salida."*
4. 📐 *"La distancia Manhattan degenera en una coordenada porque la meta
   es una línea, no un punto. Es el resultado exacto de la definición."*
5. ✂️ *"La poda no cambia el resultado, solo el trabajo. Y lo
   demostramos comparando contra un Minimax sin poda."*

## ✅ Checklist para esta noche

- [ ] Cada uno **abre su archivo** y lee las funciones de su sección
- [ ] Donovan ejecuta los 6 cambios en vivo y los deshace
- [ ] Carlos ejecuta `explicar()` antes y después de cambiar un peso
- [ ] Valentín ejecuta el comparador de nodos con y sin poda
- [ ] Los tres corren `python -m unittest ... -v` y ven los 98 OK
- [ ] Los tres juegan **una partida completa** contra el bot
- [ ] Los tres se saben las 5 frases
- [ ] Decidir **quién responde qué** si la pregunta es ambigua
- [ ] Dejar el proyecto abierto en el editor, con `config.py` a mano

---

**¡Mucha suerte mañana! 🍀**

*Recuerden: el profesor no busca que reciten. Busca que entiendan.
Cuando expliquen **por qué** tomaron una decisión, no solo **qué**
hace el código, ahí es donde se gana la defensa.* 💪
