import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { fmt } from '../../utils/formatters.js'

export default function CohortHeatmap({ data = [] }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!data.length || !ref.current) return

    // ── Derive cohort months & max offset from data ─────────────────
    const cohortMonths = [...new Set(data.map((d) => d.cohort_month))].sort()
    const maxOffset    = Math.max(...data.map((d) => +d.month_offset))

    // Build lookup: cohort_month + offset → row
    const lookup = new Map(data.map((d) => [`${d.cohort_month}|${d.month_offset}`, d]))

    // ── Layout ────────────────────────────────────────────────────────
    const container = ref.current
    const totalW  = container.clientWidth || 800
    const margin  = { top: 20, right: 24, bottom: 36, left: 88 }
    const cols    = maxOffset + 1
    const rows    = cohortMonths.length
    const cellW   = Math.floor((totalW - margin.left - margin.right) / cols)
    const cellH   = Math.max(30, Math.min(40, Math.floor(320 / rows)))
    const W       = margin.left + cellW * cols + margin.right
    const H       = margin.top  + cellH * rows + margin.bottom

    d3.select(container).select('svg').remove()

    const svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('viewBox', `0 0 ${W} ${H}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

    // ── Color scale ───────────────────────────────────────────────────
    const color = d3.scaleSequential()
      .domain([0, 100])
      .interpolator(d3.interpolateRgb('#f5f3ff', '#6d28d9'))

    // ── Tooltip ───────────────────────────────────────────────────────
    const tooltip = d3.select(container)
      .append('div')
      .style('position', 'absolute')
      .style('background', 'white')
      .style('border', '1px solid #e2e8f0')
      .style('border-radius', '10px')
      .style('padding', '8px 12px')
      .style('font-size', '12px')
      .style('font-family', 'Inter, sans-serif')
      .style('box-shadow', '0 4px 16px rgba(0,0,0,.10)')
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .style('z-index', 50)

    // ── Cells ─────────────────────────────────────────────────────────
    cohortMonths.forEach((cohort, row) => {
      for (let col = 0; col <= maxOffset; col++) {
        const d   = lookup.get(`${cohort}|${col}`)
        const pct = d ? +d.retention_rate_pct : null
        const x   = col * cellW
        const y   = row * cellH

        const cell = g.append('rect')
          .attr('x', x + 1).attr('y', y + 1)
          .attr('width', cellW - 2).attr('height', cellH - 2)
          .attr('rx', 4)
          .attr('fill', pct !== null ? color(pct) : '#f8fafc')
          .attr('cursor', pct !== null ? 'pointer' : 'default')

        if (pct !== null) {
          // Label inside cell
          const textColor = pct > 55 ? 'white' : '#4c1d95'
          g.append('text')
            .attr('x', x + cellW / 2).attr('y', y + cellH / 2 + 4)
            .attr('text-anchor', 'middle')
            .attr('font-size', Math.min(cellW / 5, 11))
            .attr('font-family', 'Inter, sans-serif')
            .attr('font-weight', 600)
            .attr('fill', textColor)
            .attr('pointer-events', 'none')
            .text(`${pct.toFixed(0)}%`)

          cell
            .on('mouseover', function (event) {
              d3.select(this).attr('stroke', '#7c3aed').attr('stroke-width', 1.5)
              tooltip
                .html(`
                  <div style="font-weight:600;color:#1e293b;margin-bottom:4px">${fmt.monthFull(cohort)}</div>
                  <div style="color:#64748b">Month <strong style="color:#1e293b">${col}</strong></div>
                  <div style="color:#64748b">Retention <strong style="color:#7c3aed">${pct.toFixed(1)}%</strong></div>
                  <div style="color:#64748b">${fmt.number(d.active_customers)} / ${fmt.number(d.cohort_size)} customers</div>
                `)
                .style('opacity', 1)
                .style('left', `${event.offsetX + 12}px`)
                .style('top',  `${event.offsetY - 60}px`)
            })
            .on('mousemove', function (event) {
              tooltip
                .style('left', `${event.offsetX + 12}px`)
                .style('top',  `${event.offsetY - 60}px`)
            })
            .on('mouseout', function () {
              d3.select(this).attr('stroke', 'none')
              tooltip.style('opacity', 0)
            })
        }
      }
    })

    // ── Y axis: cohort labels ─────────────────────────────────────────
    cohortMonths.forEach((cohort, row) => {
      g.append('text')
        .attr('x', -8).attr('y', row * cellH + cellH / 2 + 4)
        .attr('text-anchor', 'end')
        .attr('font-size', 11)
        .attr('font-family', 'Inter, sans-serif')
        .attr('fill', '#94a3b8')
        .text(fmt.month(cohort))
    })

    // ── X axis: month offset labels ───────────────────────────────────
    for (let col = 0; col <= maxOffset; col++) {
      g.append('text')
        .attr('x', col * cellW + cellW / 2)
        .attr('y', rows * cellH + 20)
        .attr('text-anchor', 'middle')
        .attr('font-size', 10)
        .attr('font-family', 'Inter, sans-serif')
        .attr('fill', '#94a3b8')
        .text(`M${col}`)
    }

    // ── Color legend ──────────────────────────────────────────────────
    const legendW = 120, legendH = 8
    const legendX = W - margin.right - legendW
    const legendY = H - margin.bottom + 20

    const defs = svg.append('defs')
    const grad = defs.append('linearGradient').attr('id', 'cohort-legend-grad')
    grad.append('stop').attr('offset', '0%').attr('stop-color', '#f5f3ff')
    grad.append('stop').attr('offset', '100%').attr('stop-color', '#6d28d9')

    svg.append('rect')
      .attr('x', legendX).attr('y', legendY)
      .attr('width', legendW).attr('height', legendH)
      .attr('rx', 4)
      .attr('fill', 'url(#cohort-legend-grad)')

    svg.append('text').attr('x', legendX).attr('y', legendY - 3)
      .attr('font-size', 9).attr('fill', '#94a3b8').attr('font-family', 'Inter').text('0%')
    svg.append('text').attr('x', legendX + legendW).attr('y', legendY - 3)
      .attr('text-anchor', 'end').attr('font-size', 9).attr('fill', '#94a3b8').attr('font-family', 'Inter').text('100%')

    return () => { tooltip.remove() }
  }, [data])

  return (
    <div ref={ref} className="relative w-full overflow-x-auto" />
  )
}
