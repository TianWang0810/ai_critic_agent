import type { EvaluationDetail, EvaluationSummary } from '../types/api'

const BASE_URL = '/api/v1'

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `Request failed with status ${res.status}`
    try {
      const body = await res.json()
      if (body?.detail) {
        message = typeof body.detail === 'string'
          ? body.detail
          : JSON.stringify(body.detail)
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(message)
  }
  return res.json() as Promise<T>
}

export async function submitCritique(idea: string): Promise<EvaluationDetail> {
  const res = await fetch(`${BASE_URL}/critique`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ idea }),
  })
  return handleResponse<EvaluationDetail>(res)
}

export async function getEvaluation(id: number): Promise<EvaluationDetail> {
  const res = await fetch(`${BASE_URL}/evaluations/${id}`)
  return handleResponse<EvaluationDetail>(res)
}

export async function listEvaluations(params?: {
  limit?: number
  offset?: number
  risk_filter?: string
}): Promise<EvaluationSummary[]> {
  const url = new URL(`${BASE_URL}/evaluations`, window.location.origin)
  if (params?.limit !== undefined) url.searchParams.set('limit', String(params.limit))
  if (params?.offset !== undefined) url.searchParams.set('offset', String(params.offset))
  if (params?.risk_filter) url.searchParams.set('risk_filter', params.risk_filter)

  const res = await fetch(url.toString())
  return handleResponse<EvaluationSummary[]>(res)
}
