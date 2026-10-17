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

export function iniciarSesion(email, password) {
  return pedir('/auth/login/', { method: 'POST', body: JSON.stringify({ email, password }) });
}

export function obtenerUsuario(token) {
  return pedir('/auth/me/', { token });
}

export function cerrarSesion(token) {
  return pedir('/auth/logout/', { method: 'POST', token });
}
