export function formatearMonto(valor, moneda = 'CLP') {
  return Number(valor ?? 0).toLocaleString('es-CL', {
    style: 'currency',
    currency: moneda,
    maximumFractionDigits: moneda === 'CLP' ? 0 : 2,
  });
}

export function formatearFecha(fecha) {
  // Las fechas sin hora se leen como locales para que no se corran un día.
  const valor = fecha.length === 10 ? `${fecha}T00:00` : fecha;
  return new Date(valor).toLocaleDateString('es-CL');
}
