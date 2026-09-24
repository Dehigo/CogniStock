import './App.css'

const stats = [
  { label: 'Productos activos', value: '1,284', change: '+8.2%', tone: 'positive' },
  { label: 'Stock crítico', value: '42', change: '-12%', tone: 'warning' },
  { label: 'Ventas del mes', value: '$48.6K', change: '+15.4%', tone: 'positive' },
  { label: 'Precisión IA', value: '94.7%', change: '+2.1%', tone: 'positive' },
]

const products = [
  { name: 'Laptop Pro 14', sku: 'LP-14', stock: 42, status: 'Disponible', category: 'Tecnología' },
  { name: 'Teclado Mecánico', sku: 'TM-22', stock: 12, status: 'Bajo stock', category: 'Accesorios' },
  { name: 'Monitor 27"', sku: 'M-27', stock: 7, status: 'Crítico', category: 'Tecnología' },
  { name: 'Mouse Inalámbrico', sku: 'MI-05', stock: 58, status: 'Disponible', category: 'Accesorios' },
  { name: 'Impresora Laser', sku: 'IL-09', stock: 16, status: 'Bajo stock', category: 'Oficina' },
]

const insights = [
  'Se recomienda reabastecer 3 productos con demanda creciente en los próximos 7 días.',
  'La categoría de tecnología presenta un aumento del 18% en rotación respecto al mes anterior.',
  'La IA detectó riesgo de faltantes en 2 zonas de almacenamiento durante el fin de semana.',
]

const actions = ['Nuevo ingreso', 'Pedido sugerido', 'Reporte IA', 'Ajuste de stock']

function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">C</div>
          <div>
            <p className="eyebrow">Sistema</p>
            <h2>CogniStock</h2>
          </div>
        </div>

        <nav className="nav">
          <a className="nav-item active" href="#">Dashboard</a>
          <a className="nav-item" href="#">Inventario</a>
          <a className="nav-item" href="#">Proveedores</a>
          <a className="nav-item" href="#">Alertas</a>
          <a className="nav-item" href="#">Agentes IA</a>
        </nav>

        <div className="agent-card">
          <p className="eyebrow">Agente IA</p>
          <h3>ForecastFlow</h3>
          <span className="status-dot">Activo</span>
          <p>Monitorea demanda, stock y oportunidades de compra en tiempo real.</p>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <p className="eyebrow">Panel principal</p>
            <h1>Gestión inteligente de inventario</h1>
          </div>

          <div className="topbar-actions">
            <button className="ghost-btn" type="button">Exportar</button>
            <button className="primary-btn" type="button">+ Nuevo movimiento</button>
          </div>
        </header>

        <section className="stats-grid">
          {stats.map((item) => (
            <article key={item.label} className="stat-card">
              <p>{item.label}</p>
              <div className="stat-row">
                <strong>{item.value}</strong>
                <span className={item.tone}>{item.change}</span>
              </div>
            </article>
          ))}
        </section>

        <section className="content-grid">
          <div className="panel inventory-panel">
            <div className="panel-header">
              <h3>Inventario actual</h3>
              <button type="button" className="link-btn">Ver todo</button>
            </div>

            <table>
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>SKU</th>
                  <th>Stock</th>
                  <th>Categoría</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product) => (
                  <tr key={product.sku}>
                    <td>{product.name}</td>
                    <td>{product.sku}</td>
                    <td>{product.stock}</td>
                    <td>{product.category}</td>
                    <td>
                      <span className={`badge ${product.status.toLowerCase().replace(/\s+/g, '-')}`}>
                        {product.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="panel insights-panel">
            <div className="panel-header">
              <h3>Sugerencias IA</h3>
              <span className="chip">Live</span>
            </div>

            <ul className="insight-list">
              {insights.map((insight) => (
                <li key={insight}>{insight}</li>
              ))}
            </ul>

            <div className="quick-actions">
              {actions.map((action) => (
                <button key={action} type="button" className="action-btn">
                  {action}
                </button>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
