/**
 * script.js — Lógica principal del frontend.
 *
 * Funcionalidad:
 * 1. Escucha el evento 'submit' del formulario de análisis.
 * 2. Envía la expresión al backend (POST /api/parse) mediante fetch().
 * 3. Si la respuesta es exitosa (200):
 *    - Muestra un mensaje de éxito.
 *    - Renderiza la tabla de tokens (drawTokenTable).
 *    - Dibuja el árbol de derivación con D3.js (drawTree).
 * 4. Si la respuesta es error (400):
 *    - Muestra el mensaje de error del backend.
 *    - Limpia la tabla y el árbol.
 * 5. Si hay error de conexión:
 *    - Muestra mensaje de error de red.
 *    - Limpia la tabla y el árbol.
 */

document.addEventListener('DOMContentLoaded', () => {

    // ------------------------------------------------------------------
    // Referencias a elementos del DOM (se obtienen una vez al inicio)
    // ------------------------------------------------------------------
    const form = document.getElementById('parse-form');           // Formulario de entrada
    const input = document.getElementById('expression-input');    // Input de texto
    const statusMsg = document.getElementById('status-message');   // Mensaje de éxito/error
    const emptyState = document.getElementById('empty-state');     // Estado vacío del árbol
    const treeContainer = document.getElementById('tree-container'); // Contenedor SVG del árbol
    const tokenSection = document.getElementById('token-section'); // Sección de la tabla de tokens

    // ------------------------------------------------------------------
    // Evento principal: Envío del formulario
    // ------------------------------------------------------------------
    form.addEventListener('submit', async (e) => {
        e.preventDefault(); // Evitar recarga de página

        const expression = input.value.trim();
        if (!expression) return; // No hacer nada si está vacío

        // --- Limpiar estado anterior ---
        statusMsg.className = 'status-message hidden';
        statusMsg.innerHTML = '';

        try {
            // --- Petición al backend ---
            const response = await fetch('http://localhost:8000/api/parse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ expression })
            });

            const data = await response.json();

            if (response.ok) {
                // ------------------------------------------------------
                // Éxito (200): La expresión es sintácticamente válida
                // ------------------------------------------------------
                showStatus('Éxito: La cadena pertenece al lenguaje.', 'success');

                // Renderizar tabla de tokens con los datos del backend
                drawTokenTable(data.tokens);

                // Dibujar árbol de derivación con D3.js
                drawTree(data.tree);

            } else {
                // ------------------------------------------------------
                // Error (400): La expresión tiene errores de sintaxis
                // ------------------------------------------------------
                showStatus(`Error: ${data.detail}`, 'error');
                clearTokenTable();
                clearTree();
            }

        } catch (error) {
            // ------------------------------------------------------
            // Error de red: El backend no está disponible
            // ------------------------------------------------------
            showStatus('Error de conexión con el servidor. ¿Está corriendo el backend?', 'error');
            clearTokenTable();
            clearTree();
        }
    });

    // ------------------------------------------------------------------
    // showStatus: Muestra un mensaje de estado con estilo (éxito/error)
    // ------------------------------------------------------------------
    /**
     * @param {string} text  - Texto del mensaje a mostrar.
     * @param {string} type  - Tipo: 'success' (verde) o 'error' (rojo).
     */
    function showStatus(text, type) {
        statusMsg.innerHTML = text;
        statusMsg.className = `status-message status-${type} show`;
    }

    // ------------------------------------------------------------------
    // drawTokenTable: Renderiza la tabla de tokens en el DOM
    // ------------------------------------------------------------------
    /**
     * Construye las filas del <tbody> de la tabla de tokens.
     * Cada fila contiene dos celdas: el tipo del token y su lexema original.
     *
     * @param {Array<{tipo: string, lexema: string}>} tokens -
     *        Lista de tokens proveniente de la respuesta del backend.
     */
    function drawTokenTable(tokens) {
        const tbody = document.querySelector('#token-table tbody');
        tbody.innerHTML = ''; // Limpiar filas anteriores

        tokens.forEach(t => {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${t.tipo}</td><td>${t.lexema}</td>`;
            tbody.appendChild(tr);
        });

        tokenSection.style.display = 'block';
    }

    // ------------------------------------------------------------------
    // clearTokenTable: Oculta y limpia la tabla de tokens
    // ------------------------------------------------------------------
    function clearTokenTable() {
        const tbody = document.querySelector('#token-table tbody');
        tbody.innerHTML = '';
        tokenSection.style.display = 'none';
    }

    // ------------------------------------------------------------------
    // clearTree: Elimina el SVG del árbol y muestra el estado vacío
    // ------------------------------------------------------------------
    function clearTree() {
        const svg = d3.select("#tree-container svg");
        if (!svg.empty()) svg.remove();
        emptyState.style.display = 'block';
    }

    // ------------------------------------------------------------------
    // drawTree: Dibuja el árbol de derivación con D3.js
    // ------------------------------------------------------------------
    /**
     * Genera un diagrama jerárquico vertical usando D3.js.
     * Los datos (treeData) siguen el formato:
     *   {"name": "...", "children": [{"name": "...", "children": [...]}]}
     *
     * Características del árbol:
     *   - Layout: d3.tree() con distribución radial desde la raíz.
     *   - Nodos: Círculos con etiquetas de texto (producción gramatical).
     *   - Enlaces: Líneas curvas (bezier) entre padre e hijo.
     *   - Zoom: Interactivo con scroll (d3.zoom).
     *
     * @param {Object} treeData - Datos jerárquicos del árbol de derivación.
     */
    function drawTree(treeData) {
        // Limpiar el SVG anterior si existe
        clearTree();
        emptyState.style.display = 'none';

        // --- Dimensiones del contenedor ---
        const width = treeContainer.clientWidth;
        const height = treeContainer.clientHeight;
        const margin = { top: 50, right: 90, bottom: 50, left: 90 };

        // --- Crear SVG con zoom habilitado ---
        const svg = d3.select("#tree-container").append("svg")
            .attr("width", width)
            .attr("height", height)
            .call(d3.zoom().on("zoom", (event) => {
                svgGroup.attr("transform", event.transform);
            }))
            .append("g")
            .attr("transform", `translate(${width / 2}, ${margin.top})`);

        const svgGroup = svg; // Grupo raíz para aplicar zoom

        // --- Layout del árbol ---
        const treemap = d3.tree().size([
            width - margin.left - margin.right,
            height - margin.top - margin.bottom
        ]);

        // Convertir datos planos a jerarquía D3
        let nodes = d3.hierarchy(treeData, d => d.children);
        nodes = treemap(nodes); // Calcular posiciones (x, y)

        // --- Dibujar enlaces (líneas curvas entre padre e hijo) ---
        const link = svgGroup.selectAll(".link")
            .data(nodes.descendants().slice(1)) // Todos excepto la raíz
            .enter().append("path")
            .attr("class", "link")
            .attr("d", d => {
                // Curva bezier cúbica: suave y elegante
                return "M" + d.x + "," + d.y
                    + "C" + d.x + "," + (d.y + d.parent.y) / 2
                    + " " + d.parent.x + "," + (d.y + d.parent.y) / 2
                    + " " + d.parent.x + "," + d.parent.y;
            });

        // --- Dibujar nodos (círculos + texto) ---
        const node = svgGroup.selectAll(".node")
            .data(nodes.descendants())
            .enter().append("g")
            .attr("class", "node")
            .attr("transform", d => `translate(${d.x}, ${d.y})`);

        // Círculo del nodo (con hover effect en CSS)
        node.append("circle").attr("r", 10);

        // Etiqueta de texto:
        //   - Si tiene hijos: arriba del círculo (dy = -20)
        //   - Si es hoja: abajo del círculo (dy = 25)
        node.append("text")
            .attr("dy", d => d.children ? -20 : 25)
            .style("text-anchor", "middle")
            .text(d => d.data.name);

        // --- Ajustar zoom inicial para centrar el árbol ---
        const zoom = d3.zoom().on("zoom", (event) => {
            svgGroup.attr("transform", event.transform);
        });
        d3.select("#tree-container svg").call(
            zoom.transform,
            d3.zoomIdentity.translate(width / 2, margin.top).scale(1)
        );
    }

    // ------------------------------------------------------------------
    // Redibujar al redimensionar la ventana
    // ------------------------------------------------------------------
    /**
     * Cuando la ventana cambia de tamaño, actualiza las dimensiones
     * del SVG para que el árbol se ajuste al nuevo contenedor.
     */
    window.addEventListener('resize', () => {
        const svg = d3.select("#tree-container svg");
        if (!svg.empty()) {
            svg.attr("width", treeContainer.clientWidth)
               .attr("height", treeContainer.clientHeight);
        }
    });

    // ------------------------------------------------------------------
    // Botones de ejemplo: Cargar expresión y enviar automáticamente
    // ------------------------------------------------------------------
    /**
     * Cada botón de ejemplo tiene un texto como "A | B".
     * Al hacer clic, se copia ese texto al input y se dispara el submit
     * del formulario para analizarlo inmediatamente.
     */
    const exampleBtns = document.querySelectorAll('.example-btn');
    exampleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            input.value = btn.textContent;
            form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        });
    });

});
