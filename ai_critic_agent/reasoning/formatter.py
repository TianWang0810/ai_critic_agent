"""
Output Formatter
Converts structured CriticResponse into human-readable formats
"""

from typing import List
from common.schemas import CriticResponse, Critique, RiskLevel


class CriticFormatter:
    """
    Formats critique responses into various output formats
    
    Supports:
    - Plain text (console output)
    - Markdown (documentation/reports)
    - HTML (web display)
    - Summary (quick overview)
    """
    
    @staticmethod
    def to_text(response: CriticResponse, verbose: bool = True) -> str:
        """
        Format as plain text for console output
        
        Args:
            response: CriticResponse object
            verbose: Include full details vs. summary only
            
        Returns:
            str: Formatted text output
        """
        lines = []
        lines.append("=" * 80)
        lines.append(" " * 25 + "STARTUP IDEA CRITIQUE")
        lines.append("=" * 80)
        
        # Header
        lines.append(f"\n💡 Idea: {response.idea_summary}")
        lines.append(f"\n📊 Overall Risk: {CriticFormatter._format_risk_badge(response.verdict.overall_risk)}")
        lines.append(f"📈 Success Probability: {response.verdict.success_probability.value.replace('_', ' ').title()}")
        
        # Key concerns
        lines.append(f"\n{'─' * 80}")
        lines.append("🚨 KEY CONCERNS")
        lines.append('─' * 80)
        for i, concern in enumerate(response.verdict.key_concerns, 1):
            lines.append(f"\n{i}. {concern}")
        
        # Detailed critiques
        if verbose:
            lines.append(f"\n{'─' * 80}")
            lines.append(f"💭 DETAILED CRITIQUES ({len(response.critiques)} assumptions analyzed)")
            lines.append('─' * 80)
            
            for i, critique in enumerate(response.critiques, 1):
                lines.append(f"\n[{i}] {CriticFormatter._format_risk_badge(critique.risk_level)}")
                lines.append(f"Assumption: {critique.assumption_text}")
                lines.append(f"\n📝 Analysis:")
                lines.append(CriticFormatter._wrap_text(critique.counterargument, indent=2))
                
                if critique.evidence_used:
                    lines.append(f"\n🔍 Evidence:")
                    for j, evidence in enumerate(critique.evidence_used[:3], 1):
                        lines.append(f"   {j}. {evidence}")
                    if len(critique.evidence_used) > 3:
                        lines.append(f"   ... and {len(critique.evidence_used) - 3} more")
                
                if i < len(response.critiques):
                    lines.append("")  # Spacing between critiques
        
        # Summary
        lines.append(f"\n{'─' * 80}")
        lines.append("⚖️  OVERALL ASSESSMENT")
        lines.append('─' * 80)
        lines.append(CriticFormatter._wrap_text(response.verdict.summary))
        
        lines.append(f"\n{'=' * 80}")
        
        return "\n".join(lines)
    
    @staticmethod
    def to_markdown(response: CriticResponse) -> str:
        """
        Format as Markdown for documentation/reports
        
        Args:
            response: CriticResponse object
            
        Returns:
            str: Markdown formatted output
        """
        lines = []
        
        # Title
        lines.append("# 🎯 Startup Idea Critique")
        lines.append("")
        lines.append(f"**Idea:** {response.idea_summary}")
        lines.append("")
        
        # Verdict badges
        risk_emoji = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🟠",
            "critical": "🔴"
        }
        prob_emoji = {
            "very_low": "📉",
            "low": "📊",
            "moderate": "📈"
        }
        
        lines.append("## 📊 Overall Assessment")
        lines.append("")
        lines.append(f"**Risk Level:** {risk_emoji.get(response.verdict.overall_risk.value, '')} "
                    f"**{response.verdict.overall_risk.value.upper()}**")
        lines.append(f"**Success Probability:** {prob_emoji.get(response.verdict.success_probability.value, '')} "
                    f"**{response.verdict.success_probability.value.replace('_', ' ').title()}**")
        lines.append("")
        
        # Summary
        lines.append("### 📝 Executive Summary")
        lines.append("")
        lines.append(response.verdict.summary)
        lines.append("")
        
        # Key concerns
        lines.append("## 🚨 Key Concerns")
        lines.append("")
        for i, concern in enumerate(response.verdict.key_concerns, 1):
            lines.append(f"{i}. {concern}")
        lines.append("")
        
        # Detailed critiques
        lines.append("## 💭 Detailed Analysis")
        lines.append("")
        
        for i, critique in enumerate(response.critiques, 1):
            risk_icon = risk_emoji.get(critique.risk_level.value, "⚪")
            lines.append(f"### {i}. {risk_icon} {critique.assumption_text}")
            lines.append("")
            lines.append(f"**Risk Level:** {critique.risk_level.value.title()}")
            lines.append("")
            lines.append("**Analysis:**")
            lines.append("")
            lines.append(critique.counterargument)
            lines.append("")
            
            if critique.evidence_used:
                lines.append("**Supporting Evidence:**")
                for evidence in critique.evidence_used:
                    lines.append(f"- {evidence}")
                lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def to_html(response: CriticResponse) -> str:
        """
        Format as HTML for web display
        
        Args:
            response: CriticResponse object
            
        Returns:
            str: HTML formatted output
        """
        risk_colors = {
            "low": "#28a745",
            "medium": "#ffc107",
            "high": "#fd7e14",
            "critical": "#dc3545"
        }
        
        html = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '    <meta charset="UTF-8">',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '    <title>Startup Critique Report</title>',
            '    <style>',
            '        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; line-height: 1.6; background: #f8f9fa; }',
            '        .container { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }',
            '        h1 { color: #333; border-bottom: 3px solid #333; padding-bottom: 15px; margin-bottom: 30px; }',
            '        h2 { color: #555; margin-top: 40px; border-bottom: 2px solid #ddd; padding-bottom: 12px; }',
            '        h3 { color: #666; margin-top: 30px; }',
            '        .idea-box { background: #e7f3ff; padding: 20px; border-left: 4px solid #007bff; margin: 20px 0; border-radius: 4px; }',
            '        .verdict { display: flex; gap: 40px; margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }',
            '        .verdict-item { flex: 1; }',
            '        .badge { display: inline-block; padding: 8px 16px; border-radius: 4px; font-weight: bold; color: white; margin-left: 10px; }',
            '        .critique { background: #fff; border: 1px solid #dee2e6; border-radius: 8px; padding: 25px; margin: 20px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }',
            '        .critique-header { font-weight: bold; font-size: 1.1em; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }',
            '        .risk-badge { padding: 4px 12px; border-radius: 4px; font-size: 0.85em; font-weight: bold; color: white; }',
            '        .evidence { background: #f8f9fa; padding: 15px; border-radius: 4px; margin-top: 15px; }',
            '        .evidence-list { margin: 10px 0; padding-left: 20px; }',
            '        .evidence-list li { margin: 8px 0; color: #495057; }',
            '        .summary { background: #fff3cd; border-left: 4px solid #ffc107; padding: 25px; margin: 30px 0; border-radius: 4px; }',
            '        .concern-list { background: #fff5f5; border-left: 4px solid #dc3545; padding: 20px; margin: 20px 0; border-radius: 4px; }',
            '        .concern-list ol { margin: 10px 0; padding-left: 25px; }',
            '        .concern-list li { margin: 12px 0; line-height: 1.6; }',
            '        .emoji { font-size: 1.2em; margin-right: 5px; }',
            '    </style>',
            '</head>',
            '<body>',
            '    <div class="container">',
            '        <h1>🎯 Startup Idea Critique</h1>',
            f'        <div class="idea-box"><strong>Idea:</strong> {response.idea_summary}</div>',
            '',
            '        <h2>📊 Overall Assessment</h2>',
            '        <div class="verdict">',
            f'            <div class="verdict-item">',
            f'                <strong>Risk Level</strong>',
            f'                <span class="badge" style="background-color: {risk_colors.get(response.verdict.overall_risk.value, "#666")}">{response.verdict.overall_risk.value.upper()}</span>',
            f'            </div>',
            f'            <div class="verdict-item">',
            f'                <strong>Success Probability</strong><br>',
            f'                {response.verdict.success_probability.value.replace("_", " ").title()}',
            f'            </div>',
            '        </div>',
            '',
            f'        <div class="summary"><strong>Executive Summary:</strong><br><br>{response.verdict.summary}</div>',
            '',
            '        <h2>🚨 Key Concerns</h2>',
            '        <div class="concern-list">',
            '            <ol>',
        ]
        
        for concern in response.verdict.key_concerns:
            html.append(f'                <li>{concern}</li>')
        
        html.extend([
            '            </ol>',
            '        </div>',
            '',
            '        <h2>💭 Detailed Analysis</h2>',
        ])
        
        for i, critique in enumerate(response.critiques, 1):
            risk_color = risk_colors.get(critique.risk_level.value, "#666")
            html.extend([
                f'        <div class="critique">',
                f'            <div class="critique-header">',
                f'                <span class="risk-badge" style="background-color: {risk_color}">{critique.risk_level.value.upper()}</span>',
                f'                <span>{critique.assumption_text}</span>',
                f'            </div>',
                f'            <p><strong>Analysis:</strong></p>',
                f'            <p>{critique.counterargument}</p>',
            ])
            
            if critique.evidence_used:
                html.append(f'            <div class="evidence">')
                html.append(f'                <strong>📚 Supporting Evidence:</strong>')
                html.append(f'                <ul class="evidence-list">')
                for evidence in critique.evidence_used:
                    html.append(f'                    <li>{evidence}</li>')
                html.append(f'                </ul>')
                html.append(f'            </div>')
            
            html.append('        </div>')
        
        html.extend([
            '    </div>',
            '</body>',
            '</html>'
        ])
        
        return "\n".join(html)
    
    @staticmethod
    def to_summary(response: CriticResponse) -> str:
        """
        Format as brief summary (for quick overview)
        
        Args:
            response: CriticResponse object
            
        Returns:
            str: Brief summary text
        """
        lines = [
            f"💡 Idea: {response.idea_summary}",
            f"📊 Risk: {response.verdict.overall_risk.value.upper()}",
            f"📈 Success Probability: {response.verdict.success_probability.value.replace('_', ' ').title()}",
            "",
            "🚨 Top Concerns:",
        ]
        
        for i, concern in enumerate(response.verdict.key_concerns[:3], 1):
            # Truncate long concerns
            concern_short = concern if len(concern) < 100 else concern[:97] + "..."
            lines.append(f"{i}. {concern_short}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _format_risk_badge(risk_level: RiskLevel) -> str:
        """Format risk level with colored badge (for terminal)"""
        badges = {
            RiskLevel.LOW: "🟢 LOW",
            RiskLevel.MEDIUM: "🟡 MEDIUM",
            RiskLevel.HIGH: "🟠 HIGH",
            RiskLevel.CRITICAL: "🔴 CRITICAL"
        }
        return badges.get(risk_level, risk_level.value.upper())
    
    @staticmethod
    def _wrap_text(text: str, width: int = 76, indent: int = 0) -> str:
        """Wrap text to specified width with optional indentation"""
        import textwrap
        indent_str = " " * indent
        wrapped = textwrap.fill(
            text,
            width=width - indent,
            initial_indent=indent_str,
            subsequent_indent=indent_str
        )
        return wrapped


# ============================================================
# Testing / Demo
# ============================================================

if __name__ == "__main__":
    from common.schemas import (
        CriticResponse, Critique, FinalVerdict,
        RiskLevel, SuccessProbability
    )
    
    # Create mock response for testing
    mock_response = CriticResponse(
        idea_summary="An AI tutor app for college students providing 24/7 personalized homework help",
        critiques=[
            Critique(
                assumption_id="assumption_1",
                assumption_text="College students will pay $20/month for AI tutoring",
                counterargument="Historical data shows college students have extremely low willingness to pay for educational subscriptions beyond streaming services. Quibi's failure and Chegg's struggles with retention demonstrate this pattern. The target demographic prioritizes free alternatives and has limited disposable income, with educational tools typically ranked last in spending priorities after entertainment and social activities.",
                evidence_used=[
                    "quibi_failure_2020.md: Only 8% conversion rate from free trial vs 25% industry standard",
                    "student_spending_study.md: Education tools receive $0-10/month vs $15-20 for entertainment"
                ],
                risk_level=RiskLevel.HIGH
            ),
            Critique(
                assumption_id="assumption_2",
                assumption_text="The AI can effectively understand and respond to complex academic questions",
                counterargument="Current AI limitations in understanding context and providing personalized feedback create significant quality gaps. Students consistently prefer human interaction for complex problem-solving, as evidenced by continued demand for in-person tutoring despite technology availability. AI struggles with nuanced subjects requiring creativity or deep conceptual understanding.",
                evidence_used=[
                    "ai_tutor_limitations.md: 45% accuracy on complex math problems vs 90%+ for human tutors"
                ],
                risk_level=RiskLevel.CRITICAL
            ),
            Critique(
                assumption_id="assumption_3",
                assumption_text="The app offers unique features not available in existing platforms",
                counterargument="Competing against free, established alternatives with massive user bases presents an almost insurmountable challenge. ChatGPT, Khan Academy, and free tutoring resources create significant barriers to entry. Network effects and brand recognition create competitive moats that are difficult to overcome without substantial differentiation.",
                evidence_used=[
                    "competition_moats.md: 98% of students use ChatGPT for homework help",
                    "chatgpt_education_dominance.md: Free alternatives capture majority of market"
                ],
                risk_level=RiskLevel.HIGH
            )
        ],
        verdict=FinalVerdict(
            overall_risk=RiskLevel.HIGH,
            key_concerns=[
                "Payment willingness: College students show 8% conversion rates vs 25% industry standard. Target demographic prioritizes entertainment spending over educational tools.",
                "AI capability gap: Current AI achieves only 45% accuracy on complex problems vs 90%+ for human tutors. Quality limitations undermine core value proposition.",
                "Free alternative dominance: 98% of students already use ChatGPT for homework help. Competing against established free solutions with massive user bases."
            ],
            success_probability=SuccessProbability.LOW,
            summary="This AI tutoring app faces severe market and competitive risks. The target demographic has historically shown resistance to educational subscription models, with conversion rates consistently below 8% compared to 25% industry standards. Technical limitations in AI tutoring quality further compound execution risks, with current systems achieving only 45% accuracy on complex problems versus 90%+ for human tutors. The competitive landscape dominated by free alternatives like ChatGPT creates nearly impossible differentiation challenges—98% of students already use these free tools for homework help. The combination of low payment willingness, technical capability gaps, and entrenched free competition creates a high-risk profile with less than 10% probability of achieving sustainable scale."
        )
    )
    
    formatter = CriticFormatter()
    
    # Test 1: Plain text
    print("=" * 80)
    print("TEST 1: PLAIN TEXT FORMAT")
    print("=" * 80)
    print(formatter.to_text(mock_response, verbose=True))
    
    # Test 2: Summary
    print("\n" + "=" * 80)
    print("TEST 2: SUMMARY FORMAT")
    print("=" * 80)
    print(formatter.to_summary(mock_response))
    
    # Test 3: Markdown
    print("\n" + "=" * 80)
    print("TEST 3: MARKDOWN FORMAT")
    print("=" * 80)
    print(formatter.to_markdown(mock_response)[:500] + "...")
    
    # Test 4: HTML (save to file)
    html_output = formatter.to_html(mock_response)
    with open("test_critique_output.html", "w", encoding="utf-8") as f:
        f.write(html_output)
    print("\n✅ HTML output saved to test_critique_output.html")