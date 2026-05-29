"""
Módulo: analizador.py
Propósito: Implementa el analizador léxico y sintáctico para expresiones booleanas.

El análisis se divide en dos fases:
    1. LÉXICA: Convierte la cadena de entrada en una lista de objetos Token,
       cada uno con un tipo (rol gramatical) y un valor (texto original).
    2. SINTÁCTICA: Recorre los tokens con un parser recursivo descendente
       y construye el árbol de derivación.

Tipos de token:
    - VARIABLE       → cualquier secuencia de letras [a-zA-Z]+
    - OPERADOR_OR    → el caracter '|'
    - OPERADOR_AND   → el caracter '&'
    - OPERADOR_NOT   → el caracter '~'
    - PARENTESIS_IZQ → el caracter '('
    - PARENTESIS_DER → el caracter ')'
"""

import re
from models.nodo import Nodo
from models.token import Token


class AnalizadorSintactico:
    """
    Analizador léxico-sintáctico para expresiones booleanas con |, &, ~, ().

    Mantiene un cursor (self.pos) que avanza a través de la lista de tokens
    mientras los métodos recursivos Exp(), Term() y Factor() consumen tokens
    y construyen nodos del árbol de derivación.

    Atributos:
        cadena_original (str): La expresión ingresada por el usuario sin modificar.
        tokens (list[Token]): Lista de tokens producida por el lexer.
        pos (int): Posición actual del cursor en la lista de tokens.
    """

    def __init__(self, cadena):
        """
        Inicializa el analizador: tokeniza la cadena de entrada.

        PASO 1 - ANÁLISIS LÉXICO:
        1. Limpia espacios en blanco.
        2. Aplica el regex r'[a-zA-Z]+|[|&~()]' para extraer lexemas.
        3. Clasifica cada lexema en su tipo de token correspondiente.

        Args:
            cadena: Expresión cruda del usuario (ej: "A | B & C").
        """
        self.cadena_original = cadena

        # Eliminar espacios: el parser solo trabaja con caracteres significativos
        cadena_limpia = cadena.replace(" ", "")

        # Extraer lexemas: el regex busca dos patrones:
        #   [a-zA-Z]+   → una o más letras (variables)
        #   [|&~()]     → operadores y paréntesis (un caracter cada uno)
        raw_tokens = re.findall(r'[a-zA-Z]+|[|&~()]', cadena_limpia)

        # Clasificar cada lexema en su tipo de Token correspondiente
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

        # Inicializar el cursor del parser al inicio de la lista
        self.pos = 0

    def obtener_token_actual(self):
        """
        Retorna el token en la posición actual del cursor sin consumirlo.

        Si el cursor superó el final de la lista, retorna None señalando
        que no hay más tokens disponibles.

        Returns:
            Token | None: Token actual o None si se alcanzó el final.
        """
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def obtener_tokens(self):
        """
        Serializa todos los tokens a una lista de diccionarios para la respuesta JSON.

        Se usa en el endpoint /api/parse para enviar la tabla de tokens al frontend.

        Returns:
            list[dict]: Lista de {"tipo": ..., "lexema": ...}
        """
        return [t.to_dict() for t in self.tokens]

    def avanzar(self):
        """
        Consume el token actual moviendo el cursor a la siguiente posición.
        """
        self.pos += 1

    def analizar(self):
        """
        Ejecuta el análisis sintáctico completo sobre los tokens tokenizados.

        PASO 2 - ANÁLISIS SINTÁCTICO:
        Invoca Exp() que inicia la cadena de llamadas recursivas
        (Exp → Term → Factor) construyendo todo el árbol de derivación.

        Después de que Exp() retorna, verifica que no hayan sobrado tokens
        sin consumir (lo que indicaría un error de sintaxis).

        Returns:
            Nodo: Raíz del árbol de derivación.

        Raises:
            Exception: Si quedan tokens sin procesar después del análisis.
        """
        arbol = self.Exp()

        # Verificar que se consumieron todos los tokens
        if self.pos < len(self.tokens):
            resto = [t.valor for t in self.tokens[self.pos:]]
            raise Exception(
                f"Error de sintaxis: Símbolos inesperados al final -> {resto}"
            )

        return arbol

    def Exp(self):
        """
        Analiza una expresión con operador OR: Exp -> Term { '|' Term }.

        Construye un nodo "Exp -> Exp | Term" por cada operador '|' encontrado.
        Si no hay '|', retorna un nodo "Exp -> Term" con un solo hijo.

        Asociatividad izquierda: en "A|B|C" se agrupa como "(A|B)|C".

        Returns:
            Nodo: "Exp -> Exp | Term" o "Exp -> Term".
        """
        nodo_izq = self.Term()
        token = self.obtener_token_actual()

        # Mientras haya operadores OR, consumirlos y construir la jerarquía
        while token is not None and token.tipo == 'OPERADOR_OR':
            self.avanzar()  # Consumir el '|'
            nodo_der = self.Term()
            # El operador izquierdo del siguiente ciclo es la expresión completa
            nodo_izq = Nodo(
                "Exp -> Exp | Term",
                [nodo_izq, Nodo(token.valor), nodo_der]
            )
            token = self.obtener_token_actual()

        # Si nunca entró al while, envolver en "Exp -> Term"
        if not nodo_izq.valor.startswith("Exp ->"):
            return Nodo("Exp -> Term", [nodo_izq])
        return nodo_izq

    def Term(self):
        """
        Analiza una expresión con operador AND: Term -> Factor { '&' Factor }.

        Construye un nodo "Term -> Term & Factor" por cada operador '&'.
        Si no hay '&', retorna "Term -> Factor".

        Asociatividad izquierda: en "A&B&C" se agrupa como "(A&B)&C".

        Returns:
            Nodo: "Term -> Term & Factor" o "Term -> Factor".
        """
        nodo_izq = self.Factor()
        token = self.obtener_token_actual()

        # Mientras haya operadores AND, consumirlos y construir la jerarquía
        while token is not None and token.tipo == 'OPERADOR_AND':
            self.avanzar()  # Consumir el '&'
            nodo_der = self.Factor()
            nodo_izq = Nodo(
                "Term -> Term & Factor",
                [nodo_izq, Nodo(token.valor), nodo_der]
            )
            token = self.obtener_token_actual()

        # Si nunca entró al while, envolver en "Term -> Factor"
        if not nodo_izq.valor.startswith("Term ->"):
            return Nodo("Term -> Factor", [nodo_izq])
        return nodo_izq

    def Factor(self):
        """
        Analiza un factor: NOT, paréntesis, o variable.

        Tres casos posibles según el token actual:
        1. OPERADOR_NOT (~) :
            Consume '~' y llama Factor() recursivamente.
            Retorna "Factor -> ~ Factor" con dos hijos: '~' y el sub-factor.
        2. PARENTESIS_IZQ ( ( ) :
            Consume '(', llama Exp() para analizar el contenido,
            espera encontrar PARENTESIS_DER ( ')' ).
            Retorna "Factor -> ( Exp )" con tres hijos: '(', sub-árbol, ')'.
        3. VARIABLE (A, B, id, etc.):
            Consume el token.
            Retorna "Factor -> id" con un hijo: el nombre original de la variable.
        4. Cualquier otro token o None:
            Lanza excepción de sintaxis.

        Returns:
            Nodo: Según el caso, uno de los tres tipos de Factor.

        Raises:
            Exception: Si el token no es válido como inicio de Factor,
                       o si falta paréntesis de cierre.
        """
        token = self.obtener_token_actual()

        # Caso 1: No hay token (expresión incompleta, ej: "A|")
        if token is None:
            raise Exception(
                "Error de sintaxis: Se esperaba un token "
                "pero la expresión está incompleta"
            )

        # Caso 2: Operador NOT '~' (unario, mayor precedencia)
        if token.tipo == 'OPERADOR_NOT':
            self.avanzar()
            return Nodo(
                "Factor -> ~ Factor",
                [Nodo(token.valor), self.Factor()]
            )

        # Caso 3: Paréntesis de apertura '('
        elif token.tipo == 'PARENTESIS_IZQ':
            self.avanzar()
            nodo_exp = self.Exp()
            token_cierre = self.obtener_token_actual()

            # Verificar que exista el paréntesis de cierre
            if token_cierre is not None and token_cierre.tipo == 'PARENTESIS_DER':
                self.avanzar()
                return Nodo(
                    "Factor -> ( Exp )",
                    [Nodo(token.valor), nodo_exp, Nodo(token_cierre.valor)]
                )
            else:
                raise Exception(
                    "Error de sintaxis: Falta paréntesis de cierre ')'"
                )

        # Caso 4: Variable (identificador)
        elif token.tipo == 'VARIABLE':
            self.avanzar()
            # Usar token.valor para preservar el nombre original de la variable
            # en el árbol (ej: "A" en vez de "id" genérico)
            return Nodo("Factor -> id", [Nodo(token.valor)])

        # Caso 5: Token inesperado (ej: "&B" donde '&' no puede iniciar Factor)
        else:
            raise Exception(
                f"Error de sintaxis: Se esperaba 'id', '~' o '(' "
                f"pero se encontró '{token.valor}'"
            )
