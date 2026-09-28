import { AlertTriangle, TrendingDown, ShieldAlert, CheckCircle2 } from 'lucide-react'
import type { FinalVerdict, RiskLevel, SuccessProbability } from '../types/api'
import { riskColor } from './RiskBadge'

interface VerdictCardProps {
  verdict: FinalVerdict
}

function riskLabel(risk: RiskLevel) {
  return { critical: 'Critical Risk', high: 'High Risk', medium: 'Medium Risk', low: 'Low Risk' }[risk]
}

function riskIcon(risk: RiskLevel) {
  const size = 22
  switch (risk) {
    case 'critical': return <ShieldAlert size={size} />
    case 'high':     return <AlertTriangle size={size} />
    case 'medium':   return <TrendingDown size={size} />
    case 'low':      return <CheckCircle2 size={size} />
  }
}

function riskTint(risk: RiskLevel) {
  return { critical: '#FFF0F2', high: '#FFF4EE', medium: '#FFFBEB', low: '#ECFDF5' }[risk]
}

function probabilityLabel(prob: SuccessProbability) {
  return { very_low: 'Very Low', low: 'Low', moderate: 'Moderate' }[prob] + ' Success Probability'
}

export default function VerdictCard({ verdict }: VerdictCardProps) {
  const color = riskColor(verdict.overall_risk)
  const tint = riskTint(verdict.overall_risk)

  return (
    <div className="rounded-2xl overflow-hidden" style={{ border: '1px solid #EBEBEB', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>

      {/* Top band — tinted header */}
      <div
        className="px-8 py-6 flex items-center justify-between"
        style={{ background: tint, borderBottom: '1px solid #EBEBEB' }}
      >
        <div className="flex items-center gap-3" style={{ color }}>
          {riskIcon(verdict.overall_risk)}
          <span
            className="font-display font-black text-2xl italic"
            style={{ color, letterSpacing: '-0.02em' }}
          >
            {riskLabel(verdict.overall_risk)}
          </span>
        </div>

        {/* Success probability pill */}
        <span
          className="text-xs font-semibold px-3 py-1.5 rounded-full"
          style={{ background: '#FFFFFF', color: '#555555', border: '1px solid #EBEBEB' }}
        >
          {probabilityLabel(verdict.success_probability)}
        </span>
      </div>

      {/* Body */}
      <div className="bg-white px-8 py-6 space-y-6">

        {/* Key concerns */}
        {verdict.key_concerns.length > 0 && (
          <div>
            <h4
              className="text-[10px] font-bold tracking-widest uppercase mb-4"
              style={{ color: '#BBBBBB' }}
            >
              Key Concerns
            </h4>
            <ol className="space-y-3">
              {verdict.key_concerns.map((concern, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span
                    className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold mt-0.5"
                    style={{ background: tint, color }}
                  >
                    {i + 1}
                  </span>
                  <p className="text-sm leading-relaxed" style={{ color: '#333333' }}>
                    {concern}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Summary */}
        <div style={{ borderTop: '1px solid #F2F1ED', paddingTop: '1.25rem' }}>
          <h4
            className="text-[10px] font-bold tracking-widest uppercase mb-3"
            style={{ color: '#BBBBBB' }}
          >
            Analysis Summary
          </h4>
          <p className="text-sm leading-relaxed" style={{ color: '#555555' }}>
            {verdict.summary}
          </p>
        </div>
      </div>
    </div>
  )
}
