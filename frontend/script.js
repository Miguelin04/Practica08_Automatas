document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('parse-form');
    const input = document.getElementById('expression-input');
    const statusMsg = document.getElementById('status-message');
    const emptyState = document.getElementById('empty-state');
    const treeContainer = document.getElementById('tree-container');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const expression = input.value.trim();
        
        if (!expression) return;

        // Limpiar el estado anterior
        statusMsg.className = 'status-message hidden';
        statusMsg.innerHTML = '';
        
        // Poner estado de carga visual si lo deseamos (opcional)
        
        try {
            const response = await fetch('http://localhost:8000/api/parse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ expression })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showStatus('Éxito: La cadena pertenece al lenguaje. ✔️', 'success');
                drawTree(data.tree);
            } else {
                showStatus(`Error: ${data.detail} ❌`, 'error');
                clearTree();
            }
        } catch (error) {
            showStatus('Error de conexión con el servidor. ¿Está corriendo el backend? 🔌', 'error');
            clearTree();
        }
    });

    function showStatus(text, type) {
        statusMsg.innerHTML = text;
        statusMsg.className = `status-message status-${type} show`;
    }

    function clearTree() {
        // Limpiar svg actual
        const svg = d3.select("#tree-container svg");
        if (!svg.empty()) svg.remove();
        emptyState.style.display = 'block';
    }

    function drawTree(treeData) {
        // Limpiar contenedor
        clearTree();
        emptyState.style.display = 'none';

        // Dimensiones
        const width = treeContainer.clientWidth;
        const height = treeContainer.clientHeight;
        const margin = {top: 50, right: 90, bottom: 50, left: 90};
        
        // Crear SVG
        const svg = d3.select("#tree-container").append("svg")
            .attr("width", width)
            .attr("height", height)
            .call(d3.zoom().on("zoom", (event) => {
                svgGroup.attr("transform", event.transform);
            }))
            .append("g")
            .attr("transform", `translate(${width/2},${margin.top})`); // Centrado arriba
            
        const svgGroup = svg; // El grupo que será zoomeado

        // Declarar el layout de árbol de D3
        // Usamos tree para distribución más bonita
        const treemap = d3.tree().size([width - margin.left - margin.right, height - margin.top - margin.bottom]);

        // Asignar los datos a la jerarquía
        let nodes = d3.hierarchy(treeData, d => d.children);
        
        // Mapear los nodos al layout
        nodes = treemap(nodes);

        // -- LINKS (Las líneas) --
        const link = svgGroup.selectAll(".link")
            .data(nodes.descendants().slice(1))
            .enter().append("path")
            .attr("class", "link")
            .attr("d", d => {
                return "M" + d.x + "," + d.y
                    + "C" + d.x + "," + (d.y + d.parent.y) / 2
                    + " " + d.parent.x + "," +  (d.y + d.parent.y) / 2
                    + " " + d.parent.x + "," + d.parent.y;
            });

        // -- NODOS --
        const node = svgGroup.selectAll(".node")
            .data(nodes.descendants())
            .enter().append("g")
            .attr("class", "node")
            .attr("transform", d => `translate(${d.x},${d.y})`);

        // Círculos de los nodos
        node.append("circle")
            .attr("r", 10);

        // Textos de los nodos
        node.append("text")
            .attr("dy", d => d.children ? -20 : 25)
            .style("text-anchor", "middle")
            .text(d => d.data.name);
            
        // Ajuste inicial de zoom y posición
        const zoom = d3.zoom().on("zoom", (event) => {
            svgGroup.attr("transform", event.transform);
        });
        
        d3.select("#tree-container svg").call(zoom.transform, d3.zoomIdentity.translate(width/2, margin.top).scale(1));
    }
    
    // Redibujar al cambiar tamaño de ventana
    window.addEventListener('resize', () => {
        const svg = d3.select("#tree-container svg");
        if (!svg.empty()) {
            svg.attr("width", treeContainer.clientWidth)
               .attr("height", treeContainer.clientHeight);
        }
    });

    // Event listeners para botones de ejemplos
    const exampleBtns = document.querySelectorAll('.example-btn');
    exampleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            input.value = btn.textContent;
            // Disparar evento de submit automáticamente
            form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
        });
    });
});
