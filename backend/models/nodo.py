class Nodo:
    def __init__(self, valor, hijos=None):
        self.valor = valor
        self.hijos = hijos if hijos else []

    def __str__(self, nivel=0):
        # Representación gráfica básica del árbol con tabulaciones
        ret = "  " * nivel + "|- " + self.valor + "\n"
        for hijo in self.hijos:
            ret += hijo.__str__(nivel + 1)
        return ret
