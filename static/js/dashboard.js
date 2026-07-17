// dashboard.js
// Logica del dashboard: actualizacion periodica de tarjetas/tabla/alertas,
// grafica de tendencia con Chart.js, y el boton "Simular Falla".

const INTERVALO_ACTUALIZACION_MS = 4000; // cada 4 segundos
const TOTAL_NODOS = 5;

let nodoSeleccionado = 1; // nodo que se muestra en la grafica (por defecto, Nodo 1)
let grafica = null;

// --- Utilidad: color de fondo del punto de estado ---
function claseEstado(estado) {
    if (estado === "Falla") return "falla";
    if (estado === "Advertencia") return "advertencia";
    return "activo";
}

// --- Actualiza las 5 tarjetas con los datos recibidos de /api/nodos ---
function actualizarTarjetas(nodos) {
    nodos.forEach((nodo) => {
        const id = nodo.id;

        const punto = document.getElementById(`punto-${id}`);
        const temp = document.getElementById(`temp-${id}`);
        const cpu = document.getElementById(`cpu-${id}`);
        const usuarios = document.getElementById(`usuarios-${id}`);

        if (!punto) return; // por si hay mas/menos nodos de los esperados

        punto.className = `estado-punto ${claseEstado(nodo.estado)}`;
        temp.textContent = nodo.temperatura;
        cpu.textContent = nodo.cpu;
        usuarios.textContent = nodo.usuarios_conectados;
    });
}

// --- Actualiza la tabla resumen con todos los nodos ---
function actualizarTabla(nodos) {
    const cuerpo = document.getElementById("tabla-nodos-cuerpo");
    cuerpo.innerHTML = "";

    nodos.forEach((nodo) => {
        const fila = document.createElement("tr");
        fila.innerHTML = `
            <td>${nodo.nombre}</td>
            <td>${nodo.estado}</td>
            <td>${nodo.temperatura} &deg;C</td>
            <td>${nodo.latencia} ms</td>
            <td>${nodo.cpu} %</td>
            <td>${nodo.memoria} %</td>
            <td>${nodo.usuarios_conectados}</td>
            <td>${nodo.ultima_actualizacion}</td>
        `;
        cuerpo.appendChild(fila);
    });
}

// --- Actualiza el panel de alertas (solo Advertencia / Falla) ---
function actualizarAlertas(alertas) {
    const lista = document.getElementById("lista-alertas");
    lista.innerHTML = "";

    if (alertas.length === 0) {
        lista.innerHTML = '<li class="sin-alertas">Sin alertas por el momento.</li>';
        return;
    }

    alertas.forEach((nodo) => {
        const item = document.createElement("li");
        const tipo = nodo.estado === "Falla" ? "alerta-falla" : "alerta-advertencia";
        item.className = tipo;
        item.textContent = `${nodo.nombre}: ${nodo.estado} - Temperatura ${nodo.temperatura} °C`;
        lista.appendChild(item);
    });
}

// --- Actualiza la hora de "ultima actualizacion" en el encabezado ---
function actualizarHora() {
    const ahora = new Date();
    document.getElementById("hora-actualizacion").textContent = ahora.toLocaleTimeString();
}

// --- Crea o actualiza la grafica de Chart.js con el historial del nodo seleccionado ---
function actualizarGrafica(historial) {
    const etiquetas = historial.map((lectura) => lectura.timestamp.split("T")[1] || lectura.timestamp);
    const temperaturas = historial.map((lectura) => lectura.temperatura);
    const cpus = historial.map((lectura) => lectura.cpu);

    if (grafica === null) {
        const ctx = document.getElementById("grafica-nodo").getContext("2d");
        grafica = new Chart(ctx, {
            type: "line",
            data: {
                labels: etiquetas,
                datasets: [
                    {
                        label: "Temperatura (°C)",
                        data: temperaturas,
                        borderColor: "#d0342c",
                        backgroundColor: "rgba(208, 52, 44, 0.1)",
                        tension: 0.3,
                    },
                    {
                        label: "CPU (%)",
                        data: cpus,
                        borderColor: "#1a3c6e",
                        backgroundColor: "rgba(26, 60, 110, 0.1)",
                        tension: 0.3,
                    },
                ],
            },
            options: {
                responsive: true,
                animation: false,
                scales: {
                    y: { beginAtZero: true },
                },
            },
        });
    } else {
        grafica.data.labels = etiquetas;
        grafica.data.datasets[0].data = temperaturas;
        grafica.data.datasets[1].data = cpus;
        grafica.update();
    }
}

// --- Trae el historial del nodo seleccionado y refresca la grafica ---
async function refrescarGrafica() {
    try {
        const respuesta = await fetch(`/api/historial/${nodoSeleccionado}`);
        const historial = await respuesta.json();
        actualizarGrafica(historial);
    } catch (error) {
        console.error("Error al obtener el historial:", error);
    }
}

// --- Trae los nodos y refresca tarjetas + tabla ---
async function refrescarNodos() {
    try {
        const respuesta = await fetch("/api/nodos");
        const nodos = await respuesta.json();
        actualizarTarjetas(nodos);
        actualizarTabla(nodos);
        actualizarHora();
    } catch (error) {
        console.error("Error al obtener los nodos:", error);
    }
}

// --- Trae las alertas activas ---
async function refrescarAlertas() {
    try {
        const respuesta = await fetch("/api/alertas");
        const alertas = await respuesta.json();
        actualizarAlertas(alertas);
    } catch (error) {
        console.error("Error al obtener las alertas:", error);
    }
}

// --- Refresca todo de una vez (usado por el intervalo periodico) ---
async function refrescarTodo() {
    await refrescarNodos();
    await refrescarAlertas();
    await refrescarGrafica();
}

// --- Boton "Simular Falla": envia el POST y refresca de inmediato ---
function configurarBotonesFalla() {
    const botones = document.querySelectorAll(".btn-falla");

    botones.forEach((boton) => {
        boton.addEventListener("click", async () => {
            const id = boton.dataset.id;

            try {
                const respuesta = await fetch(`/api/simular_falla/${id}`, { method: "POST" });
                const resultado = await respuesta.json();
                console.log(`Falla forzada en Nodo ${id}:`, resultado.mensaje);

                // Selecciona automaticamente ese nodo para mostrar el salto en la grafica
                nodoSeleccionado = parseInt(id, 10);
                document.getElementById("nodo-seleccionado-nombre").textContent = `Nodo ${id}`;

                await refrescarTodo();
            } catch (error) {
                console.error("Error al forzar la falla:", error);
            }
        });
    });
}

// --- Permite hacer clic en una tarjeta para cambiar el nodo de la grafica ---
function configurarSeleccionDeNodo() {
    for (let id = 1; id <= TOTAL_NODOS; id++) {
        const tarjeta = document.getElementById(`tarjeta-${id}`);
        if (!tarjeta) continue;

        tarjeta.addEventListener("click", async (evento) => {
            // Si el clic vino del boton "Simular Falla", no cambiar la seleccion (el boton ya maneja su propio flujo)
            if (evento.target.classList.contains("btn-falla")) return;

            nodoSeleccionado = id;
            document.getElementById("nodo-seleccionado-nombre").textContent = `Nodo ${id}`;
            await refrescarGrafica();
        });
    }
}

// --- Inicializacion ---
document.addEventListener("DOMContentLoaded", () => {
    configurarBotonesFalla();
    configurarSeleccionDeNodo();

    refrescarTodo(); // primera carga inmediata

    setInterval(refrescarTodo, INTERVALO_ACTUALIZACION_MS);
});