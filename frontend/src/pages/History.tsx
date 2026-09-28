import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { AlertCircle, PlusCircle, Clock } from 'lucide-react'
import { listEvaluations } from '../api/client'
import RiskBadge from '../components/RiskBadge'
import { riskColor } from '../components/RiskBadge'
import type { RiskLevel } from '../types/api'

type Filter = 'all' | RiskLevel

const FILTERS: { label: string; value: Filter }[] = [
  { label: 'All', value: 'all' },
  { label: 'Critical', value: 'critical' },
  { label: 'High', value: 'high' },
  { label: 'Medium', value: 'medium' },
  { label: 'Low', value: 'low' },
]

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export default function History() {
  const navigate = useNavigate()
  const [activeFilter, setActiveFilter] = useState<Filter>('all')

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['evaluations', activeFilter],
    queryFn: () => listEvaluations({ limit: 50, risk_filter: activeFilter === 'all' ? undefined : activeFilter }),
  })

  return (
    <div style={{ background: '#FAFAF8', minHeight: 'calc(100vh - 57px)' }}>
      {/* Red header */}
      <div style={{ background: '#E8143A' }} className="px-6 pt-8 pb-10">
        <div className="max-w-4xl mx-auto">
          <h1 className="font-display font-black text-3xl italic text-white mb-1" style={{ letterSpacing: '-0.02em' }}>
            History
          </h1>
          <p className="text-sm" style={{ color: 'rgba(255,255,255,0.6)' }}>
            {isLoading ? 'Loading...' : data ? `${data.length} evaluation${data.length !== 1 ? 's' : ''} recorded` : ''}
          </p>
        </div>
      </div>

      <main className="max-w-4xl mx-auto px-6 -mt-4">
        {/* Filter pills — float over the red/white boundary */}
        <div className="flex items-center gap-2 mb-6 flex-wrap">
          {FILTERS.map((f) => {
            const isActive = activeFilter === f.value
            const activeColor = f.value === 'all' ? '#E8143A' : riskColor(f.value as RiskLevel)
            return (
              <button
                key={f.value}
                onClick={() => setActiveFilter(f.value)}
                className="px-4 py-1.5 rounded-full text-sm font-semibold transition-all duration-200"
                style={
                  isActive
                    ? { background: '#111111', color: '#FFFFFF', border: '1px solid #111111' }
                    : { background: '#FFFFFF', color: '#888888', border: '1px solid #EBEBEB' }
                }
                onMouseEnter={(e) => {
                  if (!isActive) (e.currentTarget as HTMLButtonElement).style.borderColor = activeColor
                }}
                onMouseLeave={(e) => {
                  if (!isActive) (e.currentTarget as HTMLButtonElement).style.borderColor = '#EBEBEB'
                }}
              >
                {f.label}
              </button>
            )
          })}
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((n) => (
              <div key={n} className="flex items-center justify-between px-5 py-4 rounded-2xl bg-white" style={{ border: '1px solid #EBEBEB' }}>
                <div className="flex-1 mr-4">
                  <div className="h-4 w-2/3 rounded mb-2 shimmer-bg" />
                  <div className="h-3 w-1/2 rounded shimmer-bg" />
                </div>
                <div className="flex items-center gap-3">
                  <div className="h-5 w-16 rounded-full shimmer-bg" />
                  <div className="h-3 w-12 rounded shimmer-bg" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error */}
        {isError && (
          <div className="flex flex-col items-center gap-4 py-20 text-center">
            <AlertCircle size={40} style={{ color: '#E8143A' }} />
            <h2 className="text-xl font-bold" style={{ color: '#111111' }}>Failed to load history</h2>
            <p className="text-sm" style={{ color: '#888888' }}>
              {error instanceof Error ? error.message : 'An unexpected error occurred.'}
            </p>
            <button onClick={() => refetch()} className="mt-2 px-6 py-2 rounded-xl text-sm font-semibold text-white" style={{ background: '#E8143A' }}>
              Try Again
            </button>
          </div>
        )}

        {/* Empty */}
        {!isLoading && !isError && data && data.length === 0 && (
          <div className="flex flex-col items-center gap-4 py-24 text-center">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center" style={{ background: '#F2F1ED' }}>
              <Clock size={24} style={{ color: '#CCCCCC' }} />
            </div>
            <h2 className="text-xl font-bold" style={{ color: '#111111' }}>
              {activeFilter === 'all' ? 'No evaluations yet' : `No ${activeFilter} risk evaluations`}
            </h2>
            <p className="text-sm max-w-xs" style={{ color: '#888888' }}>
              {activeFilter === 'all'
                ? 'Start by analyzing a startup idea. Results will appear here.'
                : 'Switch to "All" to see evaluations across all risk levels.'}
            </p>
            <button
              onClick={() => activeFilter === 'all' ? navigate('/') : setActiveFilter('all')}
              className="mt-2 flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white"
              style={{ background: '#E8143A' }}
            >
              <PlusCircle size={15} />
              {activeFilter === 'all' ? 'Analyze an Idea' : 'Show All'}
            </button>
          </div>
        )}

        {/* List */}
        {!isLoading && !isError && data && data.length > 0 && (
          <div className="space-y-2 pb-12">
            {data.map((ev, i) => (
              <div
                key={ev.evaluation_id}
                onClick={() => navigate(`/result/${ev.evaluation_id}`)}
                className="flex items-center justify-between px-5 py-4 rounded-2xl bg-white cursor-pointer transition-all duration-200"
                style={{ border: '1px solid #EBEBEB', animationDelay: `${i * 40}ms` }}
                onMouseEnter={(e) => {
                  const el = e.currentTarget as HTMLDivElement
                  el.style.boxShadow = '0 4px 16px rgba(0,0,0,0.08)'
                  el.style.borderLeftColor = '#E8143A'
                  el.style.borderLeftWidth = '3px'
                  el.style.transform = 'translateX(2px)'
                }}
                onMouseLeave={(e) => {
                  const el = e.currentTarget as HTMLDivElement
                  el.style.boxShadow = 'none'
                  el.style.borderLeftColor = '#EBEBEB'
                  el.style.borderLeftWidth = '1px'
                  el.style.transform = 'none'
                }}
              >
                <div className="flex-1 min-w-0 mr-4">
                  <p className="text-sm font-semibold truncate mb-0.5" style={{ color: '#111111' }}>
                    {ev.idea.length > 90 ? ev.idea.slice(0, 90) + '…' : ev.idea}
                  </p>
                  <p className="text-xs truncate" style={{ color: '#AAAAAA' }}>
                    {ev.idea_summary}
                  </p>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <RiskBadge risk={ev.overall_risk} size="sm" />
                  <span className="text-xs" style={{ color: '#CCCCCC' }}>
                    {formatDate(ev.created_at)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
