"""
Módulo: nodo.py
Propósito: Define la estructura de un nodo del árbol de derivación sintáctica.

Cada nodo representa una producción aplicada por el parser (ej: "Exp -> Exp | Term")
o un símbolo terminal (ej: "A", "|"). Los hijos del nodo son los componentes
de esa producción, formando así un árbol que documenta paso a paso cómo
la expresión original fue derivada desde el símbolo inicial Exp.
"""


class Nodo:
    """
    Nodo del árbol de derivación sintáctica.

    Attributes:
        valor (str): Etiqueta del nodo. Puede ser:
                     - Una producción: "Exp -> Exp | Term"
                     - Un terminal: "A", "|", "&", "~", "(", ")"
                     - Un identificador de producción hoja: "Factor -> id"
        hijos (list[Nodo]): Lista de sub-nodos que componen esta producción.
                            Vacía si es un nodo hoja (terminal).
    """

    def __init__(self, valor, hijos=None):
        """
        Inicializa un nodo con su etiqueta y lista de hijos.

        Args:
            valor: Etiqueda del nodo (producción o terminal).
            hijos: Lista de nodos hijos. Si no se provee, se asume lista vacía.
        """
        self.valor = valor
        self.hijos = hijos if hijos else []

    def __str__(self, nivel=0):
        """
        Representación textual con indentación para visualizar la jerarquía.

        El prefijo "|- " indica un nodo dentro del árbol.

        Args:
            nivel: Profundidad actual (usada internamente para la recursión).

        Returns:
            str: Ej:
                 |- Exp -> Exp | Term
                   |- Term -> Factor
                     |- Factor -> id
                       |- A
        """
        ret = "  " * nivel + "|- " + self.valor + "\n"
        for hijo in self.hijos:
            ret += hijo.__str__(nivel + 1)
        return ret

    def to_dict(self):
        """
        Convierte el árbol (desde este nodo como raíz) a un diccionario anidado
        para visualización en el frontend.

        La estructura sigue el formato:
        {"name": "...", "children": [...]}

        Returns:
            dict: {"name": "Exp -> Exp | Term", "children": [...]}
        """
        return {
            "name": self.valor,
            "children": [hijo.to_dict() for hijo in self.hijos]
        }
