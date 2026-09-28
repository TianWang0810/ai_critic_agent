import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Download, FileText, AlertCircle } from 'lucide-react'
import { getEvaluation } from '../api/client'
import VerdictCard from '../components/VerdictCard'
import CritiqueCard from '../components/CritiqueCard'
import RiskBadge from '../components/RiskBadge'
import type { EvaluationDetail } from '../types/api'

function SkeletonCard() {
  return (
    <div className="rounded-2xl p-6 bg-white" style={{ border: '1px solid #EBEBEB' }}>
      <div className="flex items-center justify-between mb-4">
        <div className="h-3 w-24 rounded shimmer-bg" />
        <div className="h-5 w-16 rounded-full shimmer-bg" />
      </div>
      <div className="h-4 w-full rounded mb-2 shimmer-bg" />
      <div className="h-4 w-3/4 rounded mb-4 shimmer-bg" />
      <div className="h-3 w-full rounded mb-1.5 shimmer-bg" />
      <div className="h-3 w-5/6 rounded shimmer-bg" />
    </div>
  )
}

function exportJSON(data: EvaluationDetail) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `critique-${data.evaluation_id}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function exportMarkdown(data: EvaluationDetail) {
  const { critique, idea, evaluation_id } = data
  const { verdict, critiques, idea_summary } = critique
  const md = [
    `# Startup Critique Report`,
    `**Evaluation ID:** ${evaluation_id}`,
    `**Date:** ${new Date(data.created_at).toLocaleDateString()}`,
    ``,
    `## Idea`,
    `> ${idea}`,
    ``,
    `**Summary:** ${idea_summary}`,
    ``,
    `---`,
    ``,
    `## Verdict`,
    `**Overall Risk:** ${verdict.overall_risk.toUpperCase()}`,
    `**Success Probability:** ${verdict.success_probability.replace('_', ' ')}`,
    ``,
    `### Key Concerns`,
    ...verdict.key_concerns.map((c, i) => `${i + 1}. ${c}`),
    ``,
    `### Summary`,
    verdict.summary,
    ``,
    `---`,
    ``,
    `## Assumption Analysis`,
    ``,
    ...critiques.flatMap((c, i) => [
      `### Assumption ${i + 1} — ${c.risk_level.toUpperCase()} RISK`,
      `**${c.assumption_text}**`,
      ``,
      c.counterargument,
      ``,
      `**Evidence:**`,
      ...c.evidence_used.map((e) => `- ${e}`),
      ``,
    ]),
  ].join('\n')
  const blob = new Blob([md], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `critique-${evaluation_id}.md`
  a.click()
  URL.revokeObjectURL(url)
}

function ExportButton({ onClick, icon, label }: { onClick: () => void; icon: React.ReactNode; label: string }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200"
      style={{ background: '#FAFAF8', border: '1px solid #EBEBEB', color: '#888888' }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLButtonElement).style.borderColor = '#E8143A'
        ;(e.currentTarget as HTMLButtonElement).style.color = '#E8143A'
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLButtonElement).style.borderColor = '#EBEBEB'
        ;(e.currentTarget as HTMLButtonElement).style.color = '#888888'
      }}
    >
      {icon} {label}
    </button>
  )
}

export default function Result() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const evaluationId = Number(id)

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['evaluation', evaluationId],
    queryFn: () => getEvaluation(evaluationId),
    enabled: !isNaN(evaluationId),
  })

  return (
    <div style={{ background: '#FAFAF8', minHeight: 'calc(100vh - 57px)' }}>
      {/* Red page header strip */}
      <div style={{ background: '#E8143A' }} className="px-6 pt-6 pb-8">
        <div className="max-w-4xl mx-auto">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-sm mb-5 transition-opacity duration-200 hover:opacity-70"
            style={{ color: 'rgba(255,255,255,0.75)' }}
          >
            <ArrowLeft size={15} />
            New Evaluation
          </button>

          {data && (
            <div>
              <p className="text-sm italic mb-2" style={{ color: 'rgba(255,255,255,0.6)' }}>
                "{data.idea}"
              </p>
              <div className="flex items-start gap-3">
                <h1
                  className="font-display font-black text-2xl italic text-white leading-snug flex-1"
                  style={{ letterSpacing: '-0.02em' }}
                >
                  {data.idea_summary}
                </h1>
                <RiskBadge risk={data.overall_risk} />
              </div>
            </div>
          )}

          {isLoading && (
            <div>
              <div className="h-3 w-48 rounded mb-3" style={{ background: 'rgba(255,255,255,0.2)' }} />
              <div className="h-6 w-full rounded" style={{ background: 'rgba(255,255,255,0.2)' }} />
            </div>
          )}
        </div>
      </div>

      {/* White content area */}
      <main className="max-w-4xl mx-auto px-6 py-8">

        {isLoading && (
          <div className="space-y-4">
            <div className="rounded-2xl p-8 bg-white" style={{ border: '1px solid #EBEBEB' }}>
              <div className="h-8 w-48 rounded mb-4 shimmer-bg" />
              <div className="h-4 w-full rounded mb-2 shimmer-bg" />
              <div className="h-4 w-2/3 rounded shimmer-bg" />
            </div>
            {[1, 2, 3].map((n) => <SkeletonCard key={n} />)}
          </div>
        )}

        {isError && (
          <div className="flex flex-col items-center gap-4 py-20 text-center">
            <AlertCircle size={40} style={{ color: '#E8143A' }} />
            <h2 className="text-xl font-bold" style={{ color: '#111111' }}>Failed to load evaluation</h2>
            <p className="text-sm" style={{ color: '#888888' }}>
              {error instanceof Error ? error.message : 'An unexpected error occurred.'}
            </p>
            <button
              onClick={() => refetch()}
              className="mt-2 px-6 py-2 rounded-xl text-sm font-semibold text-white"
              style={{ background: '#E8143A' }}
            >
              Try Again
            </button>
          </div>
        )}

        {data && (
          <div className="space-y-6">
            {/* Verdict */}
            <VerdictCard verdict={data.critique.verdict} />

            {/* Section header + export */}
            <div className="flex items-center justify-between pt-2">
              <div>
                <span
                  className="text-[10px] font-bold tracking-widest uppercase"
                  style={{ color: '#E8143A', letterSpacing: '0.2em' }}
                >
                  Assumption Analysis
                </span>
                <p className="text-xs mt-0.5" style={{ color: '#BBBBBB' }}>
                  {data.critique.critiques.length} assumptions stress-tested
                </p>
              </div>
              <div className="flex items-center gap-2">
                <ExportButton onClick={() => exportJSON(data)} icon={<Download size={13} />} label="JSON" />
                <ExportButton onClick={() => exportMarkdown(data)} icon={<FileText size={13} />} label="Markdown" />
              </div>
            </div>

            {/* Critique cards */}
            <div className="space-y-4">
              {data.critique.critiques.map((critique, i) => (
                <div
                  key={critique.assumption_id}
                  className="opacity-0 animate-fade-in-up"
                  style={{ animationDelay: `${i * 80}ms`, animationFillMode: 'forwards' }}
                >
                  <CritiqueCard critique={critique} index={i} />
                </div>
              ))}
            </div>

            {/* Bottom export */}
            <div className="flex justify-end gap-2 pt-4" style={{ borderTop: '1px solid #EBEBEB' }}>
              <ExportButton onClick={() => exportJSON(data)} icon={<Download size={13} />} label="Export JSON" />
              <ExportButton onClick={() => exportMarkdown(data)} icon={<FileText size={13} />} label="Export Markdown" />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
