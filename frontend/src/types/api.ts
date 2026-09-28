export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'
export type SuccessProbability = 'very_low' | 'low' | 'moderate'
export type RiskCategory = 'market' | 'competition' | 'execution' | 'monetization' | 'user_behavior' | 'timing' | 'general'

export interface Critique {
  assumption_id: string
  assumption_text: string
  counterargument: string
  evidence_used: string[]
  risk_level: RiskLevel
}

export interface FinalVerdict {
  overall_risk: RiskLevel
  key_concerns: string[]
  success_probability: SuccessProbability
  summary: string
}

export interface CriticResponse {
  idea_summary: string
  critiques: Critique[]
  verdict: FinalVerdict
}

export interface EvaluationDetail {
  evaluation_id: number
  idea: string
  idea_summary: string
  overall_risk: RiskLevel
  success_probability: SuccessProbability
  created_at: string
  critique: CriticResponse
}

export interface EvaluationSummary {
  evaluation_id: number
  idea: string
  idea_summary: string
  overall_risk: RiskLevel
  success_probability: SuccessProbability
  created_at: string
}
