"""
LLM REASONING
=============
DeepSeek explains estimates in natural language. It does NOT predict numbers —
it explains numbers the engine already calculated.
"""

import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class DeepSeekReasoner:
    """Uses DeepSeek to explain net worth estimates in natural language."""

    def __init__(self, use_gateway=False):
        """
        Initialize DeepSeek client.

        Args:
            use_gateway: If True, use Vercel AI Gateway. If False, use direct DeepSeek API.
        """
        if use_gateway:
            api_key = os.getenv('AI_GATEWAY_API_KEY')
            if not api_key:
                raise ValueError("AI_GATEWAY_API_KEY not found in .env")
            self.client = OpenAI(
                api_key=api_key,
                base_url='https://ai-gateway.vercel.sh/v1'
            )
            self.model = 'deepseek/deepseek-v4-flash'
            self.mode = 'vercel_gateway'
        else:
            api_key = os.getenv('DEEPSEEK_API_KEY')
            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY not found in .env")
            self.client = OpenAI(
                api_key=api_key,
                base_url='https://api.deepseek.com'
            )
            self.model = 'deepseek-chat'
            self.mode = 'direct_deepseek'

        print(f"✓ DeepSeek reasoner initialized ({self.mode})")

    def explain_estimate(self, name, breakdown, similar_people=None):
        """
        Explain a net worth estimate in natural language.
        """
        nw = breakdown.get('net_worth_range', {})
        income = breakdown.get('income_analysis', {})
        assets = breakdown.get('asset_breakdown', {})
        ownership = breakdown.get('ownership_tier', 'unknown')
        stage = breakdown.get('career_stage', 'unknown')
        entity = breakdown.get('entity_type', 'unknown')
        owns_masters = breakdown.get('ownership_status', {}).get('owns_masters', False)
        owns_publishing = breakdown.get('ownership_status', {}).get('owns_publishing', False)
        label = breakdown.get('label_situation', 'Unknown')
        notes = breakdown.get('notes', '')

        prompt = f"""
You are a music industry financial analyst. Explain WHY {name} is estimated at ${nw.get('mid', 0)/1e6:.0f}M.

DATA (use these exact numbers — do not invent new ones):
- Entity type: {entity}
- Net worth range: ${nw.get('low', 0)/1e6:.0f}M – ${nw.get('high', 0)/1e6:.0f}M
- Ownership tier: {ownership}
- Owns masters: {owns_masters}
- Owns publishing: {owns_publishing}
- Label situation: {label}
- Career stage: {stage}
- Annual income: ${income.get('estimated_annual_gross', 0)/1e6:.1f}M
- Streaming: ${income.get('streaming_estimate', 0)/1e6:.1f}M
- Touring: ${income.get('touring_estimate', 0)/1e6:.1f}M
- Merch: ${income.get('merch_estimate', 0)/1e6:.1f}M
- Known assets: ${assets.get('total_known_assets', 0)/1e6:.1f}M
- Catalog value: ${assets.get('catalog_value_estimated', 0)/1e6:.1f}M
- Notes: {notes}

{f"Similar artists used: {', '.join([s['name'] for s in similar_people])}" if similar_people else ""}

Write a clear, 3-paragraph explanation that:
1. States the estimate and its range
2. Explains the main factors driving the number (ownership, income streams, assets)
3. Acknowledges uncertainty and what could change the estimate

Use hedging language ("estimated", "based on available data"). Be specific with numbers. Do not invent facts not in the data above. Keep it under 300 words.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
            max_tokens=600,
        )

        return response.choices[0].message.content

    def explain_adjustment(self, name, base_estimate, adjusted_estimate, adjustments):
        """Explain why refinement changed the estimate."""
        base_mid = base_estimate.get('mid', 0) / 1e6
        adj_mid = adjusted_estimate.get('mid', 0) / 1e6
        change = adj_mid - base_mid
        change_pct = (change / base_mid * 100) if base_mid > 0 else 0

        adj_list = "\n".join([
            f"- {a['fact']}: {a['multiplier']}x ({a['impact']}) — {a['reason']}"
            for a in adjustments
        ])

        prompt = f"""
Explain how {name}'s estimate changed after the user added facts.

Base estimate: ${base_mid:.1f}M
Adjusted estimate: ${adj_mid:.1f}M
Net change: {'+' if change >= 0 else ''}{change:.1f}M ({'+' if change_pct >= 0 else ''}{change_pct:.0f}%)

Adjustments applied:
{adj_list}

Write 2-3 sentences explaining the net effect. Which factors pushed it up? Which pushed it down? Keep it simple and direct.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
            max_tokens=300,
        )

        return response.choices[0].message.content


# ============================================================
# TEST
# ============================================================
