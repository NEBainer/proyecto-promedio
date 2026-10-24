// =====================================================================
// Frontend de "Promedio de cursada" (HTML + JS plano, sin frameworks).
// Toda la comunicación con el backend pasa por la función api().
// =====================================================================

const $ = (id) => document.getElementById(id);

// --- Llamada genérica a la API ---------------------------------------
// Si la respuesta no es 2xx, lanza un error con el código y el detalle,
// así cada pantalla lo puede mostrar.
async function api(ruta, opciones = {}) {
  let respuesta;
  try {
    respuesta = await fetch(API_URL + ruta, {
      headers: { "Content-Type": "application/json" },
      ...opciones,
    });
  } catch (e) {
    // fetch solo falla así si no hubo respuesta legible: servidor caído,
    // sin internet, o un problema de CORS.
    const err = new Error("No se pudo conectar con el backend (¿servidor dormido o CORS?).");
    err.status = 0;
    throw err;
  }

  if (respuesta.status === 204) return null;

  let cuerpo = null;
  try { cuerpo = await respuesta.json(); } catch { /* respuesta sin JSON */ }

  if (!respuesta.ok) {
    let detalle = cuerpo && cuerpo.detail ? cuerpo.detail : respuesta.statusText;
    // Los 422 de FastAPI traen una lista de errores de validación.
    if (Array.isArray(detalle)) detalle = detalle.map((d) => d.msg).join("; ");
    const err = new Error(detalle);
    err.status = respuesta.status;
    throw err;
  }
  return cuerpo;
}

// --- Mostrar errores bien visibles (clave para el demo) ---------------
function mostrarError(err, contexto) {
  const titulo = err.status ? `Error ${err.status}` : "Sin conexión";
  $("error-titulo").textContent = `${titulo} — ${contexto}:`;
  $("error-detalle").textContent = " " + err.message;
  $("error").hidden = false;
  console.error(contexto, err);
}
$("error-cerrar").addEventListener("click", () => ($("error").hidden = true));

// Formato argentino: coma decimal (7,50).
const formatear = (n) =>
  n === null || n === undefined
    ? "Sin notas"
    : n.toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

// Clase según la nota: menos de 6 va en rojo, como corrección de profe.
const claseNota = (n) => (n === null || n === undefined ? "sin-notas" : n < 6 ? "baja" : "");

// --- Lista de materias con su promedio --------------------------------
async function cargarMaterias() {
  let materias;
  try {
    materias = await api("/materias");
  } catch (err) {
    mostrarError(err, "cargar materias");
    return;
  }

  const tbody = $("tabla-materias");
  const select = $("materia-select");
  tbody.innerHTML = "";
  select.innerHTML = '<option value="">Elegí una materia</option>';
  $("vacio").hidden = materias.length > 0;

  for (const m of materias) {
    const fila = document.createElement("tr");

    const tdNombre = document.createElement("td");
    tdNombre.textContent = m.nombre; // textContent: evita inyectar HTML
    const tdPromedio = document.createElement("td");
    tdPromedio.textContent = "…";
    tdPromedio.className = "num";
    const tdAcciones = document.createElement("td");
    const borrar = document.createElement("button");
    borrar.textContent = "Borrar";
    borrar.className = "secundario chico";
    borrar.addEventListener("click", () => borrarMateria(m));
    tdAcciones.appendChild(borrar);

    fila.append(tdNombre, tdPromedio, tdAcciones);
    tbody.appendChild(fila);

    const opcion = document.createElement("option");
    opcion.value = m.id;
    opcion.textContent = m.nombre;
    select.appendChild(opcion);

    // Cada materia pide su promedio por separado: si una falla (bug de
    // la materia sin notas), las demás se siguen viendo bien.
    api(`/materias/${m.id}/promedio`)
      .then((r) => {
        tdPromedio.textContent = formatear(r.promedio);
        tdPromedio.className = `num ${claseNota(r.promedio)}`.trim();
      })
      .catch((err) => {
        tdPromedio.textContent = `⚠ Error ${err.status || ""}`.trim();
        tdPromedio.className = "num celda-error";
        mostrarError(err, `promedio de "${m.nombre}"`);
      });
  }
}

// --- Crear materia -------------------------------------------------------
$("form-materia").addEventListener("submit", async (e) => {
  e.preventDefault();
  const nombre = $("nombre").value.trim();
  if (!nombre) return;
  try {
    await api("/materias", { method: "POST", body: JSON.stringify({ nombre }) });
    $("nombre").value = "";
    await cargarMaterias();
  } catch (err) {
    mostrarError(err, "crear materia");
  }
});

// --- Cargar nota -----------------------------------------------------------
$("form-nota").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = $("materia-select").value;
  const valor = parseFloat($("valor").value);
  if (!id) return;
  try {
    await api(`/materias/${id}/notas`, { method: "POST", body: JSON.stringify({ valor }) });
    $("valor").value = "";
    await cargarMaterias();
    $("materia-select").value = id; // deja elegida la misma materia
  } catch (err) {
    mostrarError(err, "cargar nota");
  }
});

// --- Borrar materia ------------------------------------------------------
async function borrarMateria(m) {
  if (!confirm(`¿Borrar "${m.nombre}" y todas sus notas?`)) return;
  try {
    await api(`/materias/${m.id}`, { method: "DELETE" });
    await cargarMaterias();
  } catch (err) {
    mostrarError(err, "borrar materia");
  }
}

// --- Promedio general ----------------------------------------------------
$("ver-general").addEventListener("click", async () => {
  $("promedio-general").textContent = "…";
  try {
    const r = await api("/promedio");
    $("promedio-general").textContent = formatear(r.promedio);
    $("promedio-general").className = `nota-grande ${claseNota(r.promedio)}`.trim();
  } catch (err) {
    $("promedio-general").textContent = "⚠";
    $("promedio-general").className = "nota-grande baja";
    mostrarError(err, "promedio general");
  }
});

$("recargar").addEventListener("click", cargarMaterias);

// --- Al abrir la página ----------------------------------------------------
// Render free "duerme" el servicio tras un rato sin uso: la primera
// llamada puede tardar ~1 minuto. Lo avisamos para que no parezca roto.
async function iniciar() {
  $("api-url").textContent = API_URL;
  const aviso = setTimeout(() => {
    $("estado").textContent = "Despertando el servidor (puede tardar un minuto)";
  }, 3000);
  try {
    await api("/health");
    $("estado").textContent = "Conectado";
    $("estado").className = "ok";
  } catch (err) {
    $("estado").textContent = "Sin conexión";
    $("estado").className = "mal";
    mostrarError(err, "health check");
  } finally {
    clearTimeout(aviso);
  }
  await cargarMaterias();
}

iniciar();
