import Layout from '../components/layout/Layout.jsx'
import { ChartSkeleton, TableSkeleton } from '../components/ui/Loader.jsx'
import { ErrorBoundary } from '../components/ui/ErrorBoundary.jsx'
import ExportButton from '../components/ui/ExportButton.jsx'
import ProductBarChart from '../components/charts/ProductBarChart.jsx'
import { useProducts } from '../hooks/useKPI.js'
import { fmt } from '../utils/formatters.js'

const PRODUCT_COLUMNS = [
  { label: 'Product',         accessor: (r) => r.product_title },
  { label: 'Vendor',          accessor: (r) => r.vendor },
  { label: 'Type',            accessor: (r) => r.product_type },
  { label: 'Revenue',         accessor: (r) => r.revenue_usd },
  { label: 'Orders',          accessor: (r) => r.order_count },
  { label: 'Units Sold',      accessor: (r) => r.units_sold },
  { label: 'Avg Price',       accessor: (r) => r.avg_unit_price },
  { label: 'Unique Customers',accessor: (r) => r.unique_customers },
]

export default function ProductsPage() {
  const products = useProducts(10)
  const data     = products.data || []
  const totRev   = data.reduce((s, d) => s + +d.revenue_usd, 0)
  const totUnits = data.reduce((s, d) => s + d.units_sold, 0)

  return (
    <Layout title="Products" subtitle="Top product performance by revenue">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Top Product Revenue',     value: fmt.currency(data[0]?.revenue_usd || 0) },
          { label: 'Total Revenue (Top 10)',  value: fmt.currency(totRev, true) },
          { label: 'Total Units Sold',        value: fmt.number(totUnits, true) },
          { label: 'Avg Revenue / Product',   value: fmt.currency(totRev / (data.length || 1), true) },
        ].map((s) => (
          <div key={s.label} className="card">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{s.label}</p>
            <p className="text-xl font-bold text-slate-800 mt-1.5">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="card mb-4">
        <p className="section-title">Top Products by Revenue</p>
        <p className="section-sub mb-4">Paid, non-cancelled orders only</p>
        <ErrorBoundary>
          {products.isLoading ? <ChartSkeleton height={380} /> : <ProductBarChart data={data} />}
        </ErrorBoundary>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <p className="section-title">Product Performance Table</p>
          <ExportButton data={data} columns={PRODUCT_COLUMNS} filename="products.csv" />
        </div>
        {products.isLoading ? <TableSkeleton rows={10} /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  {['#','Product','Vendor','Type','Revenue','Orders','Units Sold','Avg Price','Customers'].map((h) => (
                    <th key={h} className="text-left py-2.5 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((p, i) => (
                  <tr key={p.shopify_product_id} className="border-b border-slate-50 hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-3 text-slate-400 text-xs font-medium">{i + 1}</td>
                    <td className="py-3 px-3 font-medium text-slate-700">{p.product_title}</td>
                    <td className="py-3 px-3 text-slate-500 text-xs">{p.vendor}</td>
                    <td className="py-3 px-3">
                      <span className="badge bg-brand-50 text-brand-600 border border-brand-100">{p.product_type}</span>
                    </td>
                    <td className="py-3 px-3 font-semibold text-slate-800">{fmt.currency(p.revenue_usd)}</td>
                    <td className="py-3 px-3 text-slate-600">{fmt.number(p.order_count)}</td>
                    <td className="py-3 px-3 text-slate-600">{fmt.number(p.units_sold)}</td>
                    <td className="py-3 px-3 text-slate-600">{fmt.currency(p.avg_unit_price)}</td>
                    <td className="py-3 px-3 text-slate-600">{fmt.number(p.unique_customers)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  )
}
