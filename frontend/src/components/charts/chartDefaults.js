export const PALETTE = {
  brand:   ['#7c3aed','#a78bfa','#c4b5fd'],
  teal:    ['#0891b2','#06b6d4','#67e8f9'],
  emerald: ['#059669','#10b981','#6ee7b7'],
  amber:   ['#d97706','#f59e0b','#fcd34d'],
  rose:    ['#e11d48','#f43f5e','#fda4af'],
  mixed:   ['#7c3aed','#06b6d4','#10b981','#f59e0b','#f43f5e'],
}

export const BASE = {
  fontFamily: 'Inter, system-ui, sans-serif',
  foreColor:  '#94a3b8',
  toolbar:    { show: false },
  zoom:       { enabled: false },
  animations: { enabled: true, easing: 'easeinout', speed: 700, dynamicAnimation: { enabled: true, speed: 400 } },
  dropShadow: { enabled: false },
}

export const TOOLTIP = {
  theme: 'light',
  style: { fontFamily: 'Inter, system-ui, sans-serif', fontSize: '12px' },
  x:     { show: true },
  marker: { show: true },
}

export const GRID = {
  borderColor:    '#f1f5f9',
  strokeDashArray: 3,
  padding:        { top: -10 },
  xaxis: { lines: { show: false } },
  yaxis: { lines: { show: true  } },
}

export const AXIS = {
  axisBorder: { show: false },
  axisTicks:  { show: false },
  labels: {
    style: {
      fontSize:   '11px',
      fontFamily: 'Inter, system-ui, sans-serif',
      fontWeight: 500,
      colors:     '#94a3b8',
    },
  },
}
