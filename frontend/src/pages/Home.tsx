import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { submitCritique } from '../api/client'
import ProgressSteps from '../components/ProgressSteps'

const PROGRESS_INTERVALS = [0, 2500, 5500, 8000]

export default function Home() {
  const [idea, setIdea] = useState('')
  const [loading, setLoading] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const timerRefs = useRef<ReturnType<typeof setTimeout>[]>([])

  function clearTimers() {
    timerRefs.current.forEach(clearTimeout)
    timerRefs.current = []
  }

  useEffect(() => () => clearTimers(), [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = idea.trim()
    if (!trimmed || loading) return

    setError(null)
    setLoading(true)
    setCurrentStep(0)
    clearTimers()

    PROGRESS_INTERVALS.forEach((delay, i) => {
      timerRefs.current.push(setTimeout(() => setCurrentStep(i), delay))
    })

    try {
      const data = await submitCritique(trimmed)
      clearTimers()
      navigate(`/result/${data.evaluation_id}`)
    } catch (err) {
      clearTimers()
      setLoading(false)
      setCurrentStep(0)
      setError(err instanceof Error ? err.message : 'Something went wrong.')
    }
  }

  const canSubmit = idea.trim().length >= 10 && !loading

  return (
    <main
      className="min-h-[calc(100vh-57px)] flex flex-col"
      style={{ background: '#E8143A' }}
    >
      {/* Top red section — headline */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 pt-16 pb-10">
        {/* Eyebrow */}
        <div className="mb-6">
          <span
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold tracking-widest uppercase"
            style={{ background: 'rgba(255,255,255,0.15)', color: 'rgba(255,255,255,0.85)', letterSpacing: '0.14em' }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-white inline-block" />
            Venture Evaluation Engine
          </span>
        </div>

        {/* Headline */}
        <h1
          className="font-display text-center text-white leading-[1.06] mb-4"
          style={{ fontSize: 'clamp(2.8rem, 7vw, 4.5rem)', letterSpacing: '-0.03em' }}
        >
          Your idea,
          <br />
          <span className="italic" style={{ color: 'rgba(255,255,255,0.75)' }}>
            critically reviewed.
          </span>
        </h1>

        {/* Subtitle */}
        <p
          className="text-center text-base leading-relaxed max-w-sm"
          style={{ color: 'rgba(255,255,255,0.65)' }}
        >
          GPT-4 stress-tests your startup assumptions against 27 real failure cases.
        </p>
      </div>

      {/* White bottom section — card + stats */}
      <div
        className="w-full rounded-t-3xl px-6 pt-8 pb-14 flex flex-col items-center"
        style={{ background: '#FFFFFF', minHeight: '52%' }}
      >
        <div className="w-full max-w-xl">
          {/* Form card */}
          <div
            className="rounded-2xl p-6 mb-8"
            style={{ background: '#FAFAF8', border: '1px solid #EBEBEB' }}
          >
            {loading ? (
              <ProgressSteps currentStep={currentStep} />
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <textarea
                  value={idea}
                  onChange={(e) => setIdea(e.target.value)}
                  placeholder="Describe your startup idea..."
                  rows={5}
                  disabled={loading}
                  className="w-full text-sm leading-relaxed rounded-xl px-4 py-3 outline-none resize-none transition-all duration-200"
                  style={{
                    background: '#FFFFFF',
                    border: '1px solid #EBEBEB',
                    color: '#111111',
                    minHeight: '120px',
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.border = '1.5px solid #E8143A'
                    e.currentTarget.style.boxShadow = '0 0 0 3px rgba(232,20,58,0.07)'
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.border = '1px solid #EBEBEB'
                    e.currentTarget.style.boxShadow = 'none'
                  }}
                />

                <div className="flex justify-end">
                  <span className="text-[11px]" style={{ color: '#CCCCCC' }}>
                    {idea.length} / 1000
                  </span>
                </div>

                {error && (
                  <div
                    className="flex items-center gap-2 px-4 py-3 rounded-xl text-sm"
                    style={{ background: '#FFF0F2', color: '#E8143A', border: '1px solid #FECDD3' }}
                  >
                    <span>⚠</span> {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={!canSubmit}
                  className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-semibold text-sm transition-all duration-200"
                  style={{
                    background: canSubmit ? '#E8143A' : '#EBEBEB',
                    color: canSubmit ? '#FFFFFF' : '#BBBBBB',
                    cursor: canSubmit ? 'pointer' : 'not-allowed',
                    boxShadow: canSubmit ? '0 4px 20px rgba(232,20,58,0.25)' : 'none',
                  }}
                  onMouseEnter={(e) => {
                    if (canSubmit) (e.currentTarget as HTMLButtonElement).style.filter = 'brightness(1.08)'
                  }}
                  onMouseLeave={(e) => {
                    (e.currentTarget as HTMLButtonElement).style.filter = 'none'
                  }}
                >
                  Analyze Idea <ArrowRight size={15} />
                </button>

                <p className="text-center text-xs" style={{ color: '#CCCCCC' }}>
                  Results are saved and can be reviewed in History
                </p>
              </form>
            )}
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-0">
            {[
              { value: '27', label: 'Failure Cases' },
              { value: '~10s', label: 'Analysis Time' },
              { value: '5–8', label: 'Assumptions' },
            ].map((s, i) => (
              <div
                key={s.label}
                className="text-center px-4 py-2"
                style={i > 0 ? { borderLeft: '1px solid #EBEBEB' } : {}}
              >
                <div
                  className="font-display font-black text-2xl italic mb-0.5"
                  style={{ color: '#E8143A' }}
                >
                  {s.value}
                </div>
                <div className="text-xs" style={{ color: '#BBBBBB' }}>
                  {s.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  )
}
