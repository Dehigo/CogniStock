// Mismos nombres que Rol en el backend. El menú solo refleja los permisos; la API es la que los aplica.
export const ROL_ADMINISTRADOR = 'Administrador';
export const ROL_ENCARGADO = 'Encargado de inventario';

const GESTIONAN_INVENTARIO = [ROL_ADMINISTRADOR, ROL_ENCARGADO];

export const SECCIONES = [
  {
    id: 'productos',
    grupo: 'Inventario',
    titulo: 'Productos',
  },
  {
    id: 'categorias',
    grupo: 'Inventario',
    titulo: 'Categorías',
  },
  {
    id: 'proveedores',
    grupo: 'Inventario',
    titulo: 'Proveedores',
  },
  {
    id: 'cotizaciones',
    grupo: 'Inventario',
    titulo: 'Cotizaciones',
    roles: GESTIONAN_INVENTARIO,
  },
  {
    id: 'entradas',
    grupo: 'Inventario',
    titulo: 'Entradas',
    roles: GESTIONAN_INVENTARIO,
  },
  {
    id: 'movimientos',
    grupo: 'Inventario',
    titulo: 'Movimientos',
  },
  {
    id: 'salidas',
    grupo: 'Inventario',
    titulo: 'Salidas (QR)',
    roles: GESTIONAN_INVENTARIO,
    descripcion: 'Validación rápida de stock por QR para registrar salidas del inventario.',
    requisito: 'RF-08',
  },
  {
    id: 'alertas',
    grupo: 'Inventario',
    titulo: 'Alertas de stock',
  },
  {
    id: 'usuarios',
    grupo: 'Administración',
    titulo: 'Usuarios',
    roles: [ROL_ADMINISTRADOR],
  },
  {
    id: 'bitacora',
    grupo: 'Administración',
    titulo: 'Bitácora',
    roles: [ROL_ADMINISTRADOR],
  },
  {
    id: 'parametros',
    grupo: 'Administración',
    titulo: 'Parámetros',
    roles: [ROL_ADMINISTRADOR],
  },
];

export const SECCION_INICIAL = 'usuarios';

export function seccionesDelRol(rol) {
  return SECCIONES.filter((seccion) => !seccion.roles || seccion.roles.includes(rol));
}
