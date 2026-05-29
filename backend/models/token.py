"""
Módulo: token.py
Propósito: Define la estructura de un token léxico.

Un token representa la unidad mínima con significado dentro de la expresión.
Separa el concepto de "tipo" (rol gramatical, ej: VARIABLE, OPERADOR_OR)
del "valor" (texto original, ej: "A", "|").

Esto permite que el parser valide contra tipos abstractos
mientras que el árbol de derivación preserva los nombres reales.
"""


class Token:
    """
    Representa un token resultado del análisis léxico (tokenización).

    Atributos:
        tipo (str): Categoría gramatical del token.
                    Valores posibles: VARIABLE, OPERADOR_OR, OPERADOR_AND,
                    OPERADOR_NOT, PARENTESIS_IZQ, PARENTESIS_DER.
        valor (str): Texto original del lexema tal cual apareció en la entrada.
                     Ej: "A", "|", "&", "~", "(", ")".
    """

    def __init__(self, tipo, valor):
        """
        Inicializa un token con su tipo y valor léxico.

        Args:
            tipo: Categoría gramatical (ej: "VARIABLE", "OPERADOR_OR").
            valor: Texto original del lexema (ej: "A", "|").
        """
        self.tipo = tipo
        self.valor = valor

    def to_dict(self):
        """
        Serializa el token a un diccionario para la respuesta JSON.

        El campo 'tipo' se envía como "tipo" y el 'valor' como "lexema"
        para que sea claro en el frontend qué representa cada campo.

        Returns:
            dict: {"tipo": "VARIABLE", "lexema": "A"}
        """
        return {"tipo": self.tipo, "lexema": self.valor}

    def __repr__(self):
        """
        Representación legible del token para depuración en consola.

        Returns:
            str: Ej: Token(VARIABLE, 'A')
        """
        return f"Token({self.tipo}, '{self.valor}')"
