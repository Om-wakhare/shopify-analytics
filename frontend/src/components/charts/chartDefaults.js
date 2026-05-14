export const PALETTE = {
  primary:  ['#7c3aed', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444'],
  brand:    ['#7c3aed', '#a78bfa', '#c4b5fd'],
  emerald:  ['#059669', '#10b981', '#6ee7b7'],
  sky:      ['#0284c7', '#0ea5e9', '#67e8f9'],
  amber:    ['#d97706', '#f59e0b', '#fcd34d'],
  rose:     ['#e11d48', '#f43f5e', '#fda4af'],
}

export const BASE = {
  fontFamily:  'Inter, system-ui, sans-serif',
  foreColor:   '#94a3b8',
  toolbar:     { show: false },
  zoom:        { enabled: false },
  sparkline:   { enabled: false },
  background:  'transparent',
  animations:  {
    enabled:          true,
    easing:           'easeinout',
    speed:            700,
    dynamicAnimation: { enabled: true, speed: 400 },
  },
}

export const TOOLTIP = {
  theme: 'light',
  style: { fontFamily: 'Inter, system-ui, sans-serif', fontSize: '12px' },
  x:     { show: true },
  marker:{ show: true },
}

export const GRID = {
  borderColor:     '#f1f5f9',
  strokeDashArray: 3,
  padding:         { top: -10, right: 0, left: 0 },
  xaxis:           { lines: { show: false } },
  yaxis:           { lines: { show: true  } },
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
