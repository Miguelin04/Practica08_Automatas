from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.analizador import AnalizadorSintactico

app = FastAPI(title="CFG Parser API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExpressionRequest(BaseModel):
    expression: str

@app.post("/api/parse")
def parse_expression(request: ExpressionRequest):
    analizador = AnalizadorSintactico(request.expression)
    try:
        arbol_derivacion = analizador.analizar()
        return {
            "valid": True,
            "tree": arbol_derivacion.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
