from core.analizador import AnalizadorSintactico

def main():
    # Ejemplos sacados de la práctica
    expresiones_prueba = [
        "id",
        "id | id",
        "id & ~id",
        "id | id & ~id",
        "~(id & id) | id",
        "id & id |"  # Esta fallará a propósito para probar validación
    ]

    print("=== VALIDADOR DE GRAMÁTICA LIBRE DE CONTEXTO (CFG) ===")
    print("Variables: Exp, Term, Factor")
    print("Terminales: |, &, ~, (, ), id")
    
    for expresion in expresiones_prueba:
        print("-" * 50)
        print(f"\nAnalizando expresión: {expresion}")
        analizador = AnalizadorSintactico(expresion)
        try:
            arbol_derivacion = analizador.analizar()
            print("Resultado: [VÁLIDO] La cadena pertenece al lenguaje.")
            print("Árbol de derivación sintáctica:\n")
            print(arbol_derivacion)
        except Exception as e:
            print(f"Resultado: [INVÁLIDO] La cadena no pertenece al lenguaje.")
            print(str(e))

if __name__ == '__main__':
    main()
