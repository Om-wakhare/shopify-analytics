import { Download } from 'lucide-react'

function toCSV(data, columns) {
  if (!data?.length) return ''
  const header = columns.map((c) => c.label).join(',')
  const rows = data.map((row) =>
    columns.map((c) => {
      const val = c.accessor(row)
      // Wrap in quotes if contains comma or newline
      return typeof val === 'string' && (val.includes(',') || val.includes('\n'))
        ? `"${val}"`
        : val ?? ''
    }).join(',')
  )
  return [header, ...rows].join('\n')
}

function downloadCSV(csv, filename) {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function ExportButton({ data, columns, filename = 'export.csv', label = 'Export CSV' }) {
  const handleExport = () => {
    const csv = toCSV(data, columns)
    if (csv) downloadCSV(csv, filename)
  }

  return (
    <button
      onClick={handleExport}
      disabled={!data?.length}
      className="btn-ghost text-xs gap-1.5 disabled:opacity-40"
    >
      <Download size={13} />
      {label}
    </button>
  )
}
