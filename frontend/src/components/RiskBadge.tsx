import type { RiskLevel } from '../types/api'

interface RiskBadgeProps {
  risk: RiskLevel
  size?: 'sm' | 'md'
}

export function riskColor(risk: RiskLevel): string {
  switch (risk) {
    case 'critical': return '#E8143A'
    case 'high':     return '#EA580C'
    case 'medium':   return '#D97706'
    case 'low':      return '#059669'
  }
}

function riskLabel(risk: RiskLevel): string {
  return risk.charAt(0).toUpperCase() + risk.slice(1)
}

function riskStyle(risk: RiskLevel): React.CSSProperties {
  switch (risk) {
    case 'critical': return { background: '#FFF0F2', color: '#E8143A', border: '1px solid #FECDD3' }
    case 'high':     return { background: '#FFF4EE', color: '#EA580C', border: '1px solid #FED7AA' }
    case 'medium':   return { background: '#FFFBEB', color: '#D97706', border: '1px solid #FDE68A' }
    case 'low':      return { background: '#ECFDF5', color: '#059669', border: '1px solid #A7F3D0' }
  }
}

export default function RiskBadge({ risk, size = 'md' }: RiskBadgeProps) {
  const sizeClass = size === 'sm'
    ? 'px-2 py-0.5 text-[10px]'
    : 'px-3 py-1 text-xs'

  return (
    <span
      className={`inline-flex items-center rounded-full font-bold tracking-wider ${sizeClass}`}
      style={riskStyle(risk)}
    >
      {riskLabel(risk)}
    </span>
  )
}
