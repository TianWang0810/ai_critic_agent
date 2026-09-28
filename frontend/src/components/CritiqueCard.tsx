import type { Critique } from '../types/api'
import RiskBadge, { riskColor } from './RiskBadge'

interface CritiqueCardProps {
  critique: Critique
  index: number
}

export default function CritiqueCard({ critique, index }: CritiqueCardProps) {
  const color = riskColor(critique.risk_level)

  return (
    <div
      className="bg-white rounded-2xl p-6 transition-all duration-300"
      style={{
        border: '1px solid #EBEBEB',
        borderLeft: `3px solid ${color}`,
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
        animationDelay: `${index * 80}ms`,
        animationFillMode: 'both',
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.boxShadow = '0 4px 20px rgba(0,0,0,0.08)'
        ;(e.currentTarget as HTMLDivElement).style.transform = 'translateY(-1px)'
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.boxShadow = '0 1px 3px rgba(0,0,0,0.05)'
        ;(e.currentTarget as HTMLDivElement).style.transform = 'none'
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span
          className="text-[10px] font-bold tracking-widest uppercase"
          style={{ color: '#BBBBBB' }}
        >
          Assumption {index + 1}
        </span>
        <RiskBadge risk={critique.risk_level} size="sm" />
      </div>

      {/* Assumption text */}
      <p
        className="font-display font-bold text-base leading-snug mb-3 italic"
        style={{ color: '#111111', letterSpacing: '-0.01em' }}
      >
        "{critique.assumption_text}"
      </p>

      {/* Counterargument */}
      <p className="text-sm leading-relaxed mb-5" style={{ color: '#555555' }}>
        {critique.counterargument}
      </p>

      {/* Evidence */}
      {critique.evidence_used.length > 0 && (
        <div
          className="rounded-xl px-4 py-3 space-y-1.5"
          style={{ background: '#FAFAF8', border: '1px solid #EBEBEB' }}
        >
          <span
            className="text-[10px] font-bold tracking-widest uppercase block mb-2"
            style={{ color: '#BBBBBB' }}
          >
            Evidence
          </span>
          {critique.evidence_used.map((ev, i) => (
            <p key={i} className="text-xs leading-relaxed font-mono" style={{ color: '#888888' }}>
              <span style={{ color }}> → </span>
              {ev}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}
