import re
from models.nodo import Nodo

class AnalizadorSintactico:
    def __init__(self, cadena):
        self.cadena_original = cadena
        # Limpiamos espacios y tokenizamos
        cadena_limpia = cadena.replace(" ", "")
        # Buscamos 'id' o caracteres especiales
        self.tokens = re.findall(r'id|[a-zA-Z]+|[|&~()]', cadena_limpia)
        # Convertimos cualquier letra suelta en 'id' para facilitar pruebas (ej. 'a' -> 'id')
        self.tokens = ['id' if t.isalpha() and t != 'id' else t for t in self.tokens]
        self.pos = 0

    def obtener_token_actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def avanzar(self):
        self.pos += 1

    def analizar(self):
        arbol = self.Exp()
        
        # Si terminamos de armar el árbol pero sobraron tokens, hay un error de sintaxis
        if self.pos < len(self.tokens):
            raise Exception(f"Error de sintaxis: Símbolos inesperados al final -> {self.tokens[self.pos:]}")
        
        return arbol

    # Reglas para 'Exp' (Maneja el operador OR '|')
    def Exp(self):
        # Exp -> Term { '|' Term }
        nodo_izq = self.Term()
        
        while self.obtener_token_actual() == '|':
            self.avanzar() # Consumimos '|'
            nodo_der = self.Term()
            # Creamos un nuevo nodo uniendo la izquierda y derecha
            nodo_izq = Nodo("Exp -> Exp | Term", [nodo_izq, Nodo("|"), nodo_der])
            
        # Si no hubo '|', simplemente bajamos al siguiente nivel
        if not nodo_izq.valor.startswith("Exp ->"):
            return Nodo("Exp -> Term", [nodo_izq])
        return nodo_izq

    # Reglas para 'Term' (Maneja el operador AND '&')
    def Term(self):
        # Term -> Factor { '&' Factor }
        nodo_izq = self.Factor()
        
        while self.obtener_token_actual() == '&':
            self.avanzar() # Consumimos '&'
            nodo_der = self.Factor()
            nodo_izq = Nodo("Term -> Term & Factor", [nodo_izq, Nodo("&"), nodo_der])
            
        if not nodo_izq.valor.startswith("Term ->"):
            return Nodo("Term -> Factor", [nodo_izq])
        return nodo_izq

    # Reglas para 'Factor' (Maneja NOT '~', Paréntesis e 'id')
    def Factor(self):
        token = self.obtener_token_actual()
        
        if token == '~':
            self.avanzar()
            return Nodo("Factor -> ~ Factor", [Nodo("~"), self.Factor()])
            
        elif token == '(':
            self.avanzar()
            nodo_exp = self.Exp()
            if self.obtener_token_actual() == ')':
                self.avanzar()
                return Nodo("Factor -> ( Exp )", [Nodo("("), nodo_exp, Nodo(")")])
            else:
                raise Exception("Error de sintaxis: Falta paréntesis de cierre ')'")
                
        elif token == 'id':
            self.avanzar()
            return Nodo("Factor -> id", [Nodo("id")])
            
        else:
            raise Exception(f"Error de sintaxis: Se esperaba 'id', '~' o '(' pero se encontró '{token}'")
