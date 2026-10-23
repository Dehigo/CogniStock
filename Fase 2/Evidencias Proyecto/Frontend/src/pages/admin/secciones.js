// Mismos nombres que Rol en el backend. El menú solo refleja los permisos; la API es la que los aplica.
export const ROL_ADMINISTRADOR = 'Administrador';
export const ROL_ENCARGADO = 'Encargado de inventario';
export const ROL_OPERATIVO = 'Usuario operativo';

const TODOS = [ROL_ADMINISTRADOR, ROL_ENCARGADO, ROL_OPERATIVO];
const GESTIONAN_INVENTARIO = [ROL_ADMINISTRADOR, ROL_ENCARGADO];
const SOLO_ADMINISTRADOR = [ROL_ADMINISTRADOR];

// Quién ve cada sección del menú.
export const SECCIONES = [
  { id: 'productos', grupo: 'Inventario', titulo: 'Productos', roles: TODOS },
  { id: 'categorias', grupo: 'Inventario', titulo: 'Categorías', roles: GESTIONAN_INVENTARIO },
  { id: 'proveedores', grupo: 'Inventario', titulo: 'Proveedores', roles: GESTIONAN_INVENTARIO },
  { id: 'cotizaciones', grupo: 'Inventario', titulo: 'Cotizaciones', roles: GESTIONAN_INVENTARIO },
  { id: 'entradas', grupo: 'Inventario', titulo: 'Entradas', roles: GESTIONAN_INVENTARIO },
  { id: 'salidas', grupo: 'Inventario', titulo: 'Salidas (QR)', roles: TODOS },
  { id: 'movimientos', grupo: 'Inventario', titulo: 'Movimientos', roles: GESTIONAN_INVENTARIO },
  { id: 'alertas', grupo: 'Inventario', titulo: 'Alertas de stock', roles: GESTIONAN_INVENTARIO },
  { id: 'agente', grupo: 'Inventario', titulo: 'Asistente IA', roles: TODOS },
  { id: 'usuarios', grupo: 'Administración', titulo: 'Usuarios', roles: SOLO_ADMINISTRADOR },
  { id: 'bitacora', grupo: 'Administración', titulo: 'Bitácora', roles: SOLO_ADMINISTRADOR },
  { id: 'parametros', grupo: 'Administración', titulo: 'Parámetros', roles: SOLO_ADMINISTRADOR },
];

// La primera pantalla que ve cada rol al entrar.
const INICIO = { [ROL_ADMINISTRADOR]: 'usuarios', [ROL_ENCARGADO]: 'productos', [ROL_OPERATIVO]: 'salidas' };

export function seccionInicial(rol) {
  return INICIO[rol] ?? 'productos';
}

export function seccionesDelRol(rol) {
  return SECCIONES.filter((seccion) => seccion.roles.includes(rol));
}

export function gestionaInventario(rol) {
  return GESTIONAN_INVENTARIO.includes(rol);
}
