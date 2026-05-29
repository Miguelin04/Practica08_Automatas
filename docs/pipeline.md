# Pipeline de Validación de Expresiones

## Vista General

```
  Entrada        Tokenización      Análisis Sintáctico        Árbol de          Respuesta
  raw string  →  (Lexer)         →   (Parser)              →  Derivación      →   HTTP JSON
                  regex + Token     Recursive Descent        Nodo + to_dict     FastAPI

                                        ↓
                                   Tabla de Tokens
                                   (Frontend)
```

Cada expresión que ingresa el usuario atraviesa **4 etapas** secuenciales antes de recibir una
respuesta. Este documento detalla qué ocurre en cada una, con ejemplos concretos del código.

---

## Etapa 1 — Tokenización (Lexer)

**Archivo:** `backend/core/analizador.py`, líneas 7–24

### Propósito

Convertir la cadena cruda del usuario en una lista estructurada de **Tokens**, donde cada uno
almacena por separado su **tipo** (para la gramática) y su **valor** (para el árbol de salida).

### Código

```python
cadena_limpia = cadena.replace(" ", "")
raw_tokens = re.findall(r'[a-zA-Z]+|[|&~()]', cadena_limpia)

self.tokens = []
for t in raw_tokens:
    if t.isalpha():
        self.tokens.append(Token("VARIABLE", t))
    elif t == '|':
        self.tokens.append(Token("OPERADOR_OR", t))
    elif t == '&':
        self.tokens.append(Token("OPERADOR_AND", t))
    elif t == '~':
        self.tokens.append(Token("OPERADOR_NOT", t))
    elif t == '(':
        self.tokens.append(Token("PARENTESIS_IZQ", t))
    elif t == ')':
        self.tokens.append(Token("PARENTESIS_DER", t))
```

### Explicación paso a paso

1. **Se eliminan espacios en blanco** — el parser solo trabaja con caracteres significativos.

2. **El regex** `r'[a-zA-Z]+|[|&~()]'` busca dos patrones:
   - `[a-zA-Z]+` — una o más letras (variables como `A`, `id`, `x1`)
   - `[|&~()]` — cualquier operador o paréntesis (un solo caracter)

3. **Cada coincidencia del regex** se convierte en un objeto `Token(tipo, valor)` mediante una
   cadena de `if/elif`. El **tipo** identifica el rol gramatical; el **valor** conserva el texto
   original para mostrarlo en el árbol.

4. El resultado se guarda en `self.tokens` y `self.pos` se inicializa en 0.

### La clase Token

**Archivo:** `backend/models/token.py`

```python
class Token:
    def __init__(self, tipo, valor):
        self.tipo = tipo
        self.valor = valor

    def to_dict(self):
        return {"tipo": self.tipo, "lexema": self.valor}
```

- `to_dict()` serializa el token para enviarlo al frontend como `{"tipo": "VARIABLE", "lexema": "A"}`.

### Tabla de tipos de token

| Lexema (entrada) | Token resultante                   |
| ---------------- | ---------------------------------- |
| `A`, `id`, `abc` | `Token("VARIABLE", "A")`           |
| `\|`              | `Token("OPERADOR_OR", "\|")`        |
| `&`              | `Token("OPERADOR_AND", "&")`       |
| `~`              | `Token("OPERADOR_NOT", "~")`       |
| `(`              | `Token("PARENTESIS_IZQ", "(")`     |
| `)`              | `Token("PARENTESIS_DER", ")")`     |

### Ejemplo concreto: `"A|B&C"`

```
cadena_original = "A|B&C"
cadena_limpia  = "A|B&C"    (no tenía espacios)
raw_tokens     = ['A', '|', 'B', '&', 'C']

# Después del bucle:
self.tokens = [
    Token("VARIABLE",    "A"),
    Token("OPERADOR_OR", "|"),
    Token("VARIABLE",    "B"),
    Token("OPERADOR_AND","&"),
    Token("VARIABLE",    "C"),
]
```

**Qué cambió respecto a la versión anterior:**
- Antes: `['id', '|', 'id', '&', 'id']` — se perdían los nombres `A`, `B`, `C`.
- Ahora: `Token("VARIABLE", "A")`, etc. — el tipo es `VARIABLE` (lo que necesita
  el parser) y el valor `"A"` se conserva para el árbol.

---

## Etapa 2 — Análisis Sintáctico (Parser)

**Archivo:** `backend/core/analizador.py`, líneas 26–88

### Propósito

Recorrer la lista de tokens y verificar que siguen la **Gramática Libre de Contexto (CFG)**,
construyendo simultáneamente el **árbol de derivación**.

### La Gramática

```
Exp    -> Term { '|' Term }
Term   -> Factor { '&' Factor }
Factor -> '~' Factor
        | '(' Exp ')'
        | id
```

- `Exp`, `Term`, `Factor` son **no terminales** (variables de la gramática).
- `|`, `&`, `~`, `(`, `)`, `id` son **terminales** (símbolos que aparecen en la entrada).
- La precedencia queda implícita por la jerarquía: **NOT (`~`) > AND (`&`) > OR (`|`)**.

### Implementación: Recursive Descent Parser

Cada no terminal se convierte en un método que:
1. Examina el token actual (`self.obtener_token_actual()`)
2. Decide qué producción aplicar según el tipo del token
3. Consume tokens (`self.avanzar()`) y hace llamadas recursivas
4. Retorna un `Nodo` que representa la subderivación

#### `obtener_token_actual()`, `obtener_tokens()` y `avanzar()`

```python
def obtener_token_actual(self):
    if self.pos < len(self.tokens):
        return self.tokens[self.pos]
    return None

def obtener_tokens(self):
    return [t.to_dict() for t in self.tokens]

def avanzar(self):
    self.pos += 1
```

- `obtener_token_actual()` — cursor que devuelve el token actual (o `None`).
- `obtener_tokens()` — serializa toda la lista de tokens para enviarla al frontend.
- `avanzar()` — mueve el cursor a la siguiente posición.

---

#### `Exp()` — Maneja el operador OR (`|`)

```python
def Exp(self):
    nodo_izq = self.Term()
    token = self.obtener_token_actual()
    while token is not None and token.tipo == 'OPERADOR_OR':
        self.avanzar()
        nodo_der = self.Term()
        nodo_izq = Nodo("Exp -> Exp | Term",
                        [nodo_izq, Nodo(token.valor), nodo_der])
        token = self.obtener_token_actual()
    if not nodo_izq.valor.startswith("Exp ->"):
        return Nodo("Exp -> Term", [nodo_izq])
    return nodo_izq
```

**Regla:** `Exp -> Term { '|' Term }` — cero o más repeticiones de `| Term`.

**Flujo:**
1. Llama a `Term()` para obtener el operando izquierdo.
2. Mientras el token actual sea `OPERADOR_OR`:
   - Consume el `|`.
   - Llama a `Term()` para obtener el operando derecho.
   - Construye un nodo `"Exp -> Exp | Term"` con tres hijos: izquierdo, operador, derecho.
   - El operando izquierdo del siguiente ciclo es todo lo construido hasta ahora (asociatividad
     izquierda).
3. Si nunca hubo `|`, envuelve el resultado en `"Exp -> Term"`.

---

#### `Term()` — Maneja el operador AND (`&`)

```python
def Term(self):
    nodo_izq = self.Factor()
    token = self.obtener_token_actual()
    while token is not None and token.tipo == 'OPERADOR_AND':
        self.avanzar()
        nodo_der = self.Factor()
        nodo_izq = Nodo("Term -> Term & Factor",
                        [nodo_izq, Nodo(token.valor), nodo_der])
        token = self.obtener_token_actual()
    if not nodo_izq.valor.startswith("Term ->"):
        return Nodo("Term -> Factor", [nodo_izq])
    return nodo_izq
```

**Regla:** `Term -> Factor { '&' Factor }` — idéntico a `Exp()` pero con `&`.

---

#### `Factor()` — Maneja NOT, paréntesis y variables

```python
def Factor(self):
    token = self.obtener_token_actual()
    if token is None:
        raise Exception("Error de sintaxis: Se esperaba un token "
                        "pero la expresión está incompleta")
    if token.tipo == 'OPERADOR_NOT':
        self.avanzar()
        return Nodo("Factor -> ~ Factor", [Nodo(token.valor), self.Factor()])

    elif token.tipo == 'PARENTESIS_IZQ':
        self.avanzar()
        nodo_exp = self.Exp()
        token_cierre = self.obtener_token_actual()
        if token_cierre is not None and token_cierre.tipo == 'PARENTESIS_DER':
            self.avanzar()
            return Nodo("Factor -> ( Exp )",
                        [Nodo(token.valor), nodo_exp, Nodo(token_cierre.valor)])
        else:
            raise Exception("Error de sintaxis: Falta paréntesis de cierre ')'")

    elif token.tipo == 'VARIABLE':
        self.avanzar()
        return Nodo("Factor -> id", [Nodo(token.valor)])

    else:
        raise Exception(f"Error de sintaxis: Se esperaba 'id', '~' o '(' "
                        f"pero se encontró '{token.valor}'")
```

**Regla:** `Factor -> '~' Factor | '(' Exp ')' | id`

**Tres caminos:**

| Token actual           | Acción                                      |
| ---------------------- | ------------------------------------------- |
| `OPERADOR_NOT` (`~`)   | Consume `~`, llama `Factor()` recursivo, construye `"Factor -> ~ Factor"` |
| `PARENTESIS_IZQ` (`(`) | Consume `(`, llama `Exp()`, espera `)`, construye `"Factor -> ( Exp )"`   |
| `VARIABLE` (`A`)       | Consume el token, construye `"Factor -> id"` con el **valor original** como hijo |
| cualquier otro / `None`| Lanza excepción                              |

**Importante:** Cuando el token es `VARIABLE`, el nodo hoja se crea con
`Nodo(token.valor)` — esto hace que el árbol muestre `A` en vez del `id` genérico.

---

### Precedencia de operadores

La jerarquía de métodos en el parser (Exp → Term → Factor) establece la precedencia:

```
 Mayor precedencia       ~  (NOT)
                         &  (AND)
 Menor precedencia       |  (OR)
```

`Exp()` llama a `Term()`, que llama a `Factor()`. Esto significa que en `A|B&C`:

- `Exp()` ve el `|` y divide la expresión en `A` (izquierda) y `B&C` (derecha).
- Para evaluar la derecha, `Exp()` llama a `Term()`.
- `Term()` ve el `&` y divide en `B` y `C`.

Resultado: `A | (B & C)` — el AND se agrupa antes que el OR.

---

## Etapa 3 — Construcción del Árbol de Derivación

**Archivo:** `backend/models/nodo.py`

### La clase Nodo

```python
class Nodo:
    def __init__(self, valor, hijos=None):
        self.valor = valor
        self.hijos = hijos if hijos else []

    def to_dict(self):
        return {
            "name": self.valor,
            "children": [hijo.to_dict() for hijo in self.hijos]
        }
```

Cada nodo guarda:
- **`valor`**: una etiqueta que describe la producción aplicada (p. ej. `"Exp -> Exp | Term"`)
  o un terminal (p. ej. `"A"`, `"|"`).
- **`hijos`**: lista de subnodos que representan los componentes de la producción.

### Serialización a JSON

`to_dict()` convierte el árbol en un diccionario recursivo:

```python
# Ejemplo para un nodo hoja "A"
{"name": "A", "children": []}

# Ejemplo para "Factor -> id" con hijo "A"
{
    "name": "Factor -> id",
    "children": [{"name": "A", "children": []}]
}
```

Este formato es directamente compatible con `d3.hierarchy()` en el frontend.

---

## Etapa 4 — Respuesta HTTP

**Archivo:** `backend/main.py`

### Endpoint

```python
@app.post("/api/parse")
def parse_expression(request: ExpressionRequest):
    analizador = AnalizadorSintactico(request.expression)
    try:
        arbol_derivacion = analizador.analizar()
        return {
            "valid": True,
            "tokens": analizador.obtener_tokens(),
            "tree": arbol_derivacion.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

1. Recibe `{"expression": "A|B"}` como JSON.
2. Crea un `AnalizadorSintactico` con la cadena.
3. Llama a `analizar()`, que ejecuta todo el pipeline (tokenizar + parsear).
4. Si es exitoso: responde `200 OK` con `{valid: true, tokens: [...], tree: {...}}`.
5. Si falla: responde `400 Bad Request` con `{detail: "mensaje de error"}`.

### Formato de la respuesta exitosa

```json
{
  "valid": true,
  "tokens": [
    {"tipo": "VARIABLE",    "lexema": "A"},
    {"tipo": "OPERADOR_OR", "lexema": "|"},
    {"tipo": "VARIABLE",    "lexema": "B"},
    {"tipo": "OPERADOR_AND","lexema": "&"},
    {"tipo": "VARIABLE",    "lexema": "C"}
  ],
  "tree": { "name": "Exp -> Exp | Term", "children": [...] }
}
```

---

## Etapa 5 — Visualización en el Frontend

**Archivos:** `frontend/index.html`, `frontend/script.js`, `frontend/style.css`

### Tabla de Tokens

El frontend recibe `data.tokens` y lo renderiza en una tabla HTML:

```html
<section id="token-section" class="glass-panel">
    <h2>Tabla de Tokens</h2>
    <div class="token-table-wrapper">
        <table id="token-table">
            <thead>
                <tr><th>Token</th><th>Lexema</th></tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>
</section>
```

### Lógica en JavaScript

```javascript
function drawTokenTable(tokens) {
    const tbody = document.querySelector('#token-table tbody');
    tbody.innerHTML = '';
    tokens.forEach(t => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${t.tipo}</td><td>${t.lexema}</td>`;
        tbody.appendChild(tr);
    });
    tokenSection.style.display = 'block';
}
```

Cada fila de la tabla muestra el **tipo** de token (coloreado en azul) y su **lexema** original.

### Ejemplo visual

```
┌──────────────────────────────────┐
│  Tabla de Tokens                 │
│                                  │
│  TOKEN              LEXEMA       │
│  ───────────────    ───────      │
│  VARIABLE           A            │
│  OPERADOR_OR        |            │
│  VARIABLE           B            │
│  OPERADOR_AND       &            │
│  VARIABLE           C            │
└──────────────────────────────────┘
```

### Árbol de Derivación (D3.js)

El árbol se dibuja con D3.js, usando `d3.hierarchy()` y `d3.tree()`. Cada nodo muestra
la producción aplicada (`"Factor -> id"`, `"Exp -> Exp | Term"`, etc.) y las hojas
muestran el nombre original de la variable (`A`, `B`, `C`).

---

## Ejemplo Completo: `A|B&C`

### Paso 1 — Tokenización

```
cadena_limpia = "A|B&C"
raw_tokens    = ['A', '|', 'B', '&', 'C']

self.tokens = [
    Token("VARIABLE",    "A"),
    Token("OPERADOR_OR", "|"),
    Token("VARIABLE",    "B"),
    Token("OPERADOR_AND","&"),
    Token("VARIABLE",    "C"),
]
```

### Paso 2 — Recorrido del Parser

```
Exp() llama:
  ├─ Term() llama:
  │    ├─ Factor() → token = VARIABLE("A") → consume, retorna Nodo("Factor -> id", ["A"])
  │    └─ token = OPERADOR_AND("&") → NO es el caso (es '|')
  │    → retorna Nodo("Term -> Factor", [Nodo("Factor -> id", ["A"])])
  │
  ├─ token = OPERADOR_OR("|") → SÍ, consume
  │
  ├─ Term() llama:
  │    ├─ Factor() → token = VARIABLE("B") → consume, retorna Nodo("Factor -> id", ["B"])
  │    ├─ token = OPERADOR_AND("&") → SÍ, consume
  │    ├─ Factor() → token = VARIABLE("C") → consume, retorna Nodo("Factor -> id", ["C"])
  │    └─ retorna Nodo("Term -> Term & Factor", [Nodo("Factor->id",["B"]), "&", Nodo("Factor->id",["C"])])
  │
  └─ retorna Nodo("Exp -> Exp | Term",
       [Nodo("Exp->Term", [Nodo("Factor->id",["A"])]), "|",
        Nodo("Term->Term&Factor", [Nodo("Factor->id",["B"]), "&", Nodo("Factor->id",["C"])])])
```

### Paso 3 — Árbol resultante

```
Exp -> Exp | Term
├── Exp -> Term
│   └── Factor -> id
│       └── A
├── |
└── Term -> Term & Factor
    ├── Factor -> id
    │   └── B
    ├── &
    └── Factor -> id
        └── C
```

### Paso 4 — JSON enviado al frontend

```json
{
  "valid": true,
  "tokens": [
    {"tipo": "VARIABLE",    "lexema": "A"},
    {"tipo": "OPERADOR_OR", "lexema": "|"},
    {"tipo": "VARIABLE",    "lexema": "B"},
    {"tipo": "OPERADOR_AND","lexema": "&"},
    {"tipo": "VARIABLE",    "lexema": "C"}
  ],
  "tree": {
    "name": "Exp -> Exp | Term",
    "children": [
      {
        "name": "Term -> Factor",
        "children": [{
          "name": "Factor -> id",
          "children": [{"name": "A", "children": []}]
        }]
      },
      {"name": "|", "children": []},
      {
        "name": "Term -> Term & Factor",
        "children": [
          {
            "name": "Factor -> id",
            "children": [{"name": "B", "children": []}]
          },
          {"name": "&", "children": []},
          {
            "name": "Factor -> id",
            "children": [{"name": "C", "children": []}]
          }
        ]
      }
    ]
  }
}
```

### Paso 5 — Tabla renderizada en el frontend

```
┌──────────────────────────────────┐
│  Tabla de Tokens                 │
│                                  │
│  TOKEN              LEXEMA       │
│  ───────────────    ───────      │
│  VARIABLE           A            │
│  OPERADOR_OR        |            │
│  VARIABLE           B            │
│  OPERADOR_AND       &            │
│  VARIABLE           C            │
└──────────────────────────────────┘
```

---

## Ejemplo con NOT y Paréntesis: `~(A|B)&C`

### Tokenización

```
cadena_limpia = "~(A|B)&C"
raw_tokens    = ['~', '(', 'A', '|', 'B', ')', '&', 'C']

self.tokens = [
    Token("OPERADOR_NOT",   "~"),
    Token("PARENTESIS_IZQ", "("),
    Token("VARIABLE",       "A"),
    Token("OPERADOR_OR",    "|"),
    Token("VARIABLE",       "B"),
    Token("PARENTESIS_DER", ")"),
    Token("OPERADOR_AND",   "&"),
    Token("VARIABLE",       "C"),
]
```

### Árbol resultante

```
Exp -> Term
└── Term -> Term & Factor
    ├── Factor -> ~ Factor
    │   ├── ~
    │   └── Factor -> ( Exp )
    │       ├── (
    │       ├── Exp -> Exp | Term
    │       │   ├── Term -> Factor
    │       │   │   └── Factor -> id
    │       │   │       └── A
    │       │   ├── |
    │       │   └── Term -> Factor
    │       │       └── Factor -> id
    │       │           └── B
    │       └── )
    ├── &
    └── Factor -> id
        └── C
```

---

## Manejo de Errores

| Expresión  | Error                                    | Causa                                        |
| ---------- | ---------------------------------------- | -------------------------------------------- |
| `A\|`       | `Se esperaba un token...`                | `Factor()` recibe `None` después del `\|`     |
| `(A\|B`     | `Falta paréntesis de cierre ')'`         | Se abre `(` pero no hay `)` antes del final  |
| `A\|B)`     | `Símbolos inesperados al final -> [')']` | Sobran tokens después de haber completado `Exp()` |
| `&B`        | `Se esperaba 'id', '~' o '('...`         | `&` no es válido como inicio de `Factor()`   |
| `~`         | `Se esperaba un token...`                | `~` requiere un `Factor()` a la derecha      |
| `A%%B`      | `Símbolos inesperados al final -> ['B']` | `%%` no son tokens válidos, se ignoran; `A` se parsea y `B` sobra |

---

## Diagrama de flujo resumido

```
┌─────────────────────────────────────────────────────────────────────┐
│                     POST /api/parse                                 │
│              {"expression": "A|B&C"}                                │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  AnalizadorSintactico.__init__("A|B&C")                            │
│                                                                     │
│  1. Limpiar espacios                                                │
│  2. regex → ['A', '|', 'B', '&', 'C']                              │
│  3. Mapear a Token[]                                                │
│     [VAR("A"), OR("|"), VAR("B"), AND("&"), VAR("C")]              │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  analizar()                                                         │
│                                                                     │
│  Exp() → recorre tokens con cursor                                  │
│    ├─ llama Term() → Factor()                                       │
│    ├─ detecta OR → consume, llama Term()                            │
│    │  └─ detecta AND → consume, llama Factor()                      │
│    └─ construye Nodos en cada paso                                  │
│                                                                     │
│  Resultado: árbol de derivación (raíz Nodo)                         │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  arbol.to_dict() + analizador.obtener_tokens()                     │
│                                                                     │
│  → tokens: [{"tipo":"VARIABLE","lexema":"A"}, ...]                  │
│  → tree: {"name":"Exp -> Exp | Term", "children":[...]}             │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Response: 200 OK                                                   │
│  {"valid":true, "tokens":[...], "tree":{...}}                       │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Frontend:                                                          │
│  1. Dibuja tabla de Tokens (Token | Lexema)                        │
│  2. Dibuja árbol de derivación con D3.js                           │
└─────────────────────────────────────────────────────────────────────┘
```
