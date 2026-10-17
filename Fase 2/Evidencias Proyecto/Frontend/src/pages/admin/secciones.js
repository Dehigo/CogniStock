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
    descripcion: 'Revisión y aprobación de cotizaciones. Solo una cotización aprobada permite registrar entradas.',
    requisito: 'RF-05',
  },
  {
    id: 'movimientos',
    grupo: 'Inventario',
    titulo: 'Movimientos',
    descripcion: 'Historial de entradas y salidas con producto, cantidad, fecha y usuario responsable.',
    requisito: 'RF-09',
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
  },
  {
    id: 'bitacora',
    grupo: 'Administración',
    titulo: 'Bitácora',
  },
  {
    id: 'parametros',
    grupo: 'Administración',
    titulo: 'Parámetros',
  },
];

export const SECCION_INICIAL = 'usuarios';
