// =====================================================================
// URL DEL BACKEND: es el ÚNICO lugar donde se configura.
// - Si la página corre en tu compu (localhost / 127.0.0.1), usa el backend local.
// - En cualquier otro lado (Netlify), usa el backend desplegado en Render.
// =====================================================================
const API_PRODUCCION = "https://proyecto-promedio.onrender.com";
const API_LOCAL = "http://localhost:8000";

const esLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const API_URL = esLocal ? API_LOCAL : API_PRODUCCION;
