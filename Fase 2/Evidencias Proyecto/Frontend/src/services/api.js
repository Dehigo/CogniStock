const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api';

function mensajeDeError(status, datos) {
  if (status === 429) return 'Demasiados intentos. Espera un minuto e inténtalo de nuevo.';
  if (datos?.detail) return datos.detail;
  if (datos && typeof datos === 'object') return Object.values(datos).flat().join(' ');
  return `Error inesperado (${status}).`;
}

async function pedir(ruta, { token, ...opciones } = {}) {
  let respuesta;
  try {
    respuesta = await fetch(`${API_URL}${ruta}`, {
      ...opciones,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Token ${token}` }),
      },
    });
  } catch {
    throw new Error('No se pudo conectar con el servidor.');
  }

  const datos = respuesta.status === 204 ? null : await respuesta.json();
  if (!respuesta.ok) throw new Error(mensajeDeError(respuesta.status, datos));
  return datos;
}

function armarFiltros(filtros) {
  const conValor = Object.entries(filtros).filter(([, valor]) => valor !== '' && valor != null);
  return new URLSearchParams(conValor);
}

export function iniciarSesion(email, password) {
  return pedir('/auth/login/', { method: 'POST', body: JSON.stringify({ email, password }) });
}

export function obtenerUsuario(token) {
  return pedir('/auth/me/', { token });
}

export function cerrarSesion(token) {
  return pedir('/auth/logout/', { method: 'POST', token });
}

export function listarUsuarios(token, filtros = {}) {
  return pedir(`/usuarios/?${armarFiltros(filtros)}`, { token });
}

export function crearUsuario(token, datos) {
  return pedir('/usuarios/', { method: 'POST', token, body: JSON.stringify(datos) });
}

export function editarUsuario(token, id, datos) {
  return pedir(`/usuarios/${id}/`, { method: 'PATCH', token, body: JSON.stringify(datos) });
}

export function desactivarUsuario(token, id) {
  return pedir(`/usuarios/${id}/`, { method: 'DELETE', token });
}

export function listarRoles(token) {
  return pedir('/roles/', { token });
}

export function listarCategorias(token, filtros = {}) {
  return pedir(`/categorias/?${armarFiltros(filtros)}`, { token });
}

export function crearCategoria(token, datos) {
  return pedir('/categorias/', { method: 'POST', token, body: JSON.stringify(datos) });
}

export function editarCategoria(token, id, datos) {
  return pedir(`/categorias/${id}/`, { method: 'PATCH', token, body: JSON.stringify(datos) });
}

export function desactivarCategoria(token, id) {
  return pedir(`/categorias/${id}/`, { method: 'DELETE', token });
}

export function listarProductos(token, filtros = {}) {
  return pedir(`/productos/?${armarFiltros(filtros)}`, { token });
}

export function buscarProductoPorQr(token, codigoQr) {
  return pedir(`/productos/qr/?codigo_qr=${encodeURIComponent(codigoQr)}`, { token });
}

export function registrarSalidaQr(token, datos) {
  return pedir('/salidas/', { method: 'POST', token, body: JSON.stringify(datos) });
}

export function crearProducto(token, datos) {
  return pedir('/productos/', { method: 'POST', token, body: JSON.stringify(datos) });
}

export function editarProducto(token, id, datos) {
  return pedir(`/productos/${id}/`, { method: 'PATCH', token, body: JSON.stringify(datos) });
}

export function desactivarProducto(token, id) {
  return pedir(`/productos/${id}/`, { method: 'DELETE', token });
}

export function listarProveedores(token, filtros = {}) {
  return pedir(`/proveedores/?${armarFiltros(filtros)}`, { token });
}

export function crearProveedor(token, datos) {
  return pedir('/proveedores/', { method: 'POST', token, body: JSON.stringify(datos) });
}

export function editarProveedor(token, id, datos) {
  return pedir(`/proveedores/${id}/`, { method: 'PATCH', token, body: JSON.stringify(datos) });
}

export function desactivarProveedor(token, id) {
  return pedir(`/proveedores/${id}/`, { method: 'DELETE', token });
}

export function listarBitacora(token, filtros = {}) {
  return pedir(`/bitacora/?${armarFiltros(filtros)}`, { token });
}

export function listarParametros(token) {
  return pedir('/parametros/', { token });
}

export function crearParametro(token, datos) {
  return pedir('/parametros/', { method: 'POST', token, body: JSON.stringify(datos) });
}

export function editarParametro(token, id, datos) {
  return pedir(`/parametros/${id}/`, { method: 'PATCH', token, body: JSON.stringify(datos) });
}

export function eliminarParametro(token, id) {
  return pedir(`/parametros/${id}/`, { method: 'DELETE', token });
}

export function listarMonedas(token) {
  return pedir('/monedas/', { token });
}

export function listarCotizaciones(token, filtros = {}) {
  return pedir(`/cotizaciones/?${armarFiltros(filtros)}`, { token });
}

export function crearCotizacion(token, datos) {
  return pedir('/cotizaciones/', { method: 'POST', token, body: JSON.stringify(datos) });
}

export function editarCotizacion(token, id, datos) {
  return pedir(`/cotizaciones/${id}/`, { method: 'PATCH', token, body: JSON.stringify(datos) });
}

export function cambiarEstadoCotizacion(token, id, estado, motivo = '') {
  return pedir(`/cotizaciones/${id}/estado/`, { method: 'POST', token, body: JSON.stringify({ estado, motivo }) });
}

export function listarEntradas(token, filtros = {}) {
  return pedir(`/entradas/?${armarFiltros(filtros)}`, { token });
}

export function registrarEntrada(token, datos) {
  return pedir('/entradas/', { method: 'POST', token, body: JSON.stringify(datos) });
}

export function listarMovimientos(token, filtros = {}) {
  return pedir(`/movimientos/?${armarFiltros(filtros)}`, { token });
}

export function consultarAgente(token, pregunta) {
  return pedir('/agente/consultar/', { method: 'POST', token, body: JSON.stringify({ pregunta }) });
}

export function listarRecomendaciones(token, filtros = {}) {
  return pedir(`/recomendaciones/?${armarFiltros(filtros)}`, { token });
}

export function revisarRecomendacion(token, id, estado) {
  return pedir(`/recomendaciones/${id}/revisar/`, { method: 'POST', token, body: JSON.stringify({ estado }) });
}

export function obtenerTipoCambio(token, desde, hacia) {
  return pedir(`/integraciones/tipo-cambio/?${armarFiltros({ desde, hacia })}`, { token });
}

export function listarFeriados(token, anio) {
  return pedir(`/integraciones/feriados/?${armarFiltros({ anio })}`, { token });
}
