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
    descripcion: 'Productos bajo el stock mínimo o agotados, y recomendaciones de reposición del agente de IA.',
    requisito: 'RF-07 / RF-11',
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
    descripcion: 'Configuración general del sistema, como umbrales de alerta y días de cobertura.',
    requisito: 'RF-02',
  },
];

export const SECCION_INICIAL = 'usuarios';
