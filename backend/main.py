"""
Módulo: main.py
Propósito: Punto de entrada del backend. Servidor FastAPI que expone
el endpoint /api/parse para el análisis de expresiones booleanas.

Flujo de una petición:
    1. Recibe {"expression": "A|B&C"} vía POST.
    2. Crea un AnalizadorSintactico que tokeniza y parsea la expresión.
    3. Retorna:
       - 200 OK con {valid, tokens, tree} si la expresión es válida.
       - 400 Bad Request con {detail} si hay error de sintaxis.

CORS está configurado abierto (allow_origins=["*"]) para desarrollo local.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.analizador import AnalizadorSintactico

# -----------------------------------------------------------------------
# Configuración de la aplicación FastAPI
# -----------------------------------------------------------------------
app = FastAPI(
    title="CFG Parser API",
    description="API para análisis léxico-sintáctico de expresiones booleanas "
                "basado en Gramática Libre de Contexto.",
    version="1.0.0"
)

# -----------------------------------------------------------------------
# Middleware CORS — permite peticiones desde cualquier origen
# (útil para desarrollo con frontend en un puerto diferente)
# -----------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # En producción, restringir a orígenes específicos
    allow_credentials=True,
    allow_methods=["*"],         # Permitir todos los métodos HTTP
    allow_headers=["*"],         # Permitir todos los headers
)


# -----------------------------------------------------------------------
# Modelo de datos para la petición
# -----------------------------------------------------------------------
class ExpressionRequest(BaseModel):
    """
    Schema de la petición POST /api/parse.

    Attributes:
        expression (str): La expresión booleana a analizar.
                          Ej: "A|B&C", "~(A&B)", "id | id & ~id".
    """
    expression: str


# -----------------------------------------------------------------------
# Endpoint principal
# -----------------------------------------------------------------------
@app.post("/api/parse")
def parse_expression(request: ExpressionRequest):
    """
    Analiza una expresión booleana y retorna su tabla de tokens y árbol de derivación.

    Ejemplo de petición:
        POST /api/parse
        {"expression": "A|B&C"}

    Respuesta exitosa (200):
        {
            "valid": true,
            "tokens": [
                {"tipo": "VARIABLE",    "lexema": "A"},
                {"tipo": "OPERADOR_OR", "lexema": "|"},
                {"tipo": "VARIABLE",    "lexema": "B"},
                {"tipo": "OPERADOR_AND","lexema": "&"},
                {"tipo": "VARIABLE",    "lexema": "C"}
            ],
            "derivation": [
                {"paso": 0, "produccion": "-",           "forma": "Exp"},
                {"paso": 1, "produccion": "Exp -> Exp | Term", "forma": "Term | Term"},
                {"paso": 2, "produccion": "Term -> Factor",    "forma": "Factor | Term"},
                ...
            ],
            "tree": {
                "name": "Exp -> Exp | Term",
                "children": [...]
            }
        }

    Respuesta de error (400):
        {"detail": "Error de sintaxis: ..."}

    Args:
        request: Objeto ExpressionRequest con el campo 'expression'.

    Returns:
        dict: Con valid (bool), tokens (list), derivation (list), tree (dict).

    Raises:
        HTTPException 400: Si el análisis sintáctico falla.
    """
    analizador = AnalizadorSintactico(request.expression)

    try:
        arbol_derivacion = analizador.analizar()
        return {
            "valid": True,
            "tokens": analizador.obtener_tokens(),
            "derivation": analizador.obtener_derivacion(arbol_derivacion),
            "tree": arbol_derivacion.to_dict()
        }
    except Exception as e:
        # Cualquier excepción del analizador se traduce a HTTP 400
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------------------------------------------------
# Punto de entrada para ejecución directa
# -----------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",   # Escuchar en todas las interfaces de red
        port=8000,
        reload=True        # Recargar automáticamente al cambiar el código
    )
