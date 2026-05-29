# Analizador de Expresiones Booleanas y Árbol de Derivación (CFG) 🌳

Un analizador sintáctico web moderno para evaluar expresiones booleanas basadas en una Gramática Libre de Contexto (CFG). Esta herramienta valida si una cadena pertenece al lenguaje definido y dibuja dinámicamente el **Árbol de Derivación Sintáctica** correspondiente en una interfaz visual muy atractiva.

![Vista de la Interfaz Web](https://img.shields.io/badge/UI-Glassmorphism-blue?style=for-the-badge) ![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi) ![Frontend](https://img.shields.io/badge/Frontend-D3.js-F9A03C?style=for-the-badge&logo=d3.js)

## ✨ Características

* **Análisis Sintáctico:** Analiza y valida expresiones booleanas en tiempo real.
* **Gramática Libre de Contexto (CFG):** Respeta reglas de precedencia para los operadores lógicos OR (`|`), AND (`&`), NOT (`~`) y paréntesis `()`.
* **Visualización Dinámica:** Renderiza el árbol de derivación utilizando la potente librería `D3.js` con soporte para arrastrar y hacer zoom.
* **Diseño Premium:** Interfaz de usuario moderna estilo *Glassmorphism*, modo oscuro inmersivo, y animaciones de fondo.
* **Ejemplos Rápidos:** Botones interactivos para evaluar cadenas predefinidas rápidamente.

## 📐 Gramática Implementada

El analizador utiliza las siguientes producciones para armar el árbol garantizando la correcta precedencia (NOT > AND > OR):

```text
Exp    -> Term { '|' Term }
Term   -> Factor { '&' Factor }
Factor -> '~' Factor 
        | '(' Exp ')' 
        | 'id'
```

*Los terminales son:* `id`, `|`, `&`, `~`, `(`, `)`.

---

## 🚀 Guía de Instalación y Ejecución

El proyecto está dividido en dos partes principales: un backend en **Python (FastAPI)** y un frontend estático en **HTML/CSS/JS**.

### 1. Levantar el Backend (API)

Abre una terminal y navega a la carpeta del proyecto.

```bash
cd backend

# (Opcional pero recomendado) Crea y activa un entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Linux/Mac
# venv\Scripts\activate   # En Windows

# Instala las dependencias necesarias
pip install -r requirements.txt

# Ejecuta el servidor FastAPI
python main.py
```
*El backend estará disponible en `http://localhost:8000`*

### 2. Levantar el Frontend (Interfaz Visual)

Abre **otra** pestaña de la terminal y navega a la carpeta del frontend:

```bash
cd frontend

# Inicia un servidor estático de Python
python3 -m http.server 3000
```
*El frontend estará disponible en `http://localhost:3000`*

---

## 🎮 Cómo Usarlo

1. Abre tu navegador y dirígete a [http://localhost:3000](http://localhost:3000).
2. En la barra de búsqueda, ingresa una expresión booleana válida. Por ejemplo: `id | id & ~id`.
3. Presiona el botón **Analizar**.
4. ¡Observa cómo el árbol de derivación se dibuja automáticamente en el panel inferior!
5. **Tip:** Puedes usar la rueda del ratón para hacer *zoom* y hacer clic y arrastrar para moverte por el lienzo si el árbol es muy grande. También puedes usar los botones de "Ejemplos" para cargar expresiones al instante.

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python 3, FastAPI, Uvicorn, Pydantic.
* **Frontend:** HTML5, CSS3 (Vanilla), JavaScript (Vanilla).
* **Visualización de Datos:** D3.js (v7).
* **Estilos:** Glassmorphism, Google Fonts (Outfit).