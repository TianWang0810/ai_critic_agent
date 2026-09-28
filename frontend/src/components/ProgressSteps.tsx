import { CheckCircle2, Clock } from 'lucide-react'

const STEPS = [
  { label: 'Decomposing idea',      description: 'Extracting key assumptions' },
  { label: 'Retrieving evidence',   description: 'Scanning 27 failure patterns' },
  { label: 'Critiquing assumptions', description: 'Stress-testing each claim' },
  { label: 'Synthesizing verdict',  description: 'Calculating overall risk' },
]

export default function ProgressSteps({ currentStep }: { currentStep: number }) {
  return (
    <div className="py-2">
      <div className="flex items-center gap-2 mb-6">
        <Clock size={13} style={{ color: '#BBBBBB' }} />
        <span className="text-xs" style={{ color: '#BBBBBB' }}>
          This takes ~10 seconds
        </span>
      </div>

      <div className="space-y-4">
        {STEPS.map((step, i) => {
          const isDone   = i < currentStep
          const isActive = i === currentStep
          const isPending = i > currentStep

          return (
            <div key={i} className="flex items-center gap-4">
              {/* Dot */}
              <div className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                {isDone ? (
                  <CheckCircle2 size={18} style={{ color: '#059669' }} />
                ) : isActive ? (
                  <div
                    className="w-2.5 h-2.5 rounded-full"
                    style={{
                      background: '#E8143A',
                      animation: 'pulse-red 1.5s cubic-bezier(0.4,0,0.6,1) infinite',
                    }}
                  />
                ) : (
                  <div className="w-2.5 h-2.5 rounded-full" style={{ background: '#EBEBEB' }} />
                )}
              </div>

              {/* Text */}
              <div className="flex-1 min-w-0">
                <p
                  className="text-sm font-medium transition-colors duration-300"
                  style={{
                    color: isDone ? '#BBBBBB' : isActive ? '#111111' : '#CCCCCC',
                    textDecoration: isDone ? 'line-through' : 'none',
                  }}
                >
                  {step.label}
                </p>
                {isActive && (
                  <p className="text-xs mt-0.5" style={{ color: '#AAAAAA' }}>
                    {step.description}
                  </p>
                )}
              </div>

              {/* Status tag */}
              <span
                className="text-[11px] font-medium flex-shrink-0"
                style={{
                  color: isDone ? '#059669' : isActive ? '#E8143A' : '#DDDDDD',
                }}
              >
                {isDone ? 'done' : isActive ? 'running…' : isPending ? 'pending' : ''}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
