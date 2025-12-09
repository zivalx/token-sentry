"""
TokenHealth LLM Agent
Generates human-readable summary using LLM (with deterministic fallback)
"""
import json
from typing import Dict, List, Any


class LLMAgent:
    """LLM-powered agent for generating token analysis summaries"""

    def __init__(self):
        pass

    def generate_summary(
        self,
        symbol: str,
        contract: str,
        metrics: Dict[str, Any],
        graph_summary: str,
        reasons: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate summary, top risks, and next checks
        Returns: {summary: [...], top_risks: [...], next_checks: [...]}
        """

        # TODO: In production, integrate with external LLM API
        # For now, use deterministic rule-based summary
        return self._generate_deterministic_summary(symbol, contract, metrics, graph_summary, reasons)

    def _generate_llm_summary(
        self,
        symbol: str,
        contract: str,
        metrics: Dict[str, Any],
        graph_summary: str,
        reasons: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Call LLM API to generate summary
        In production, this would call Claude API or similar
        """
        # Build prompt
        prompt = self._build_prompt(symbol, contract, metrics, graph_summary)

        # TODO: Actual LLM API call would go here
        # For now, return deterministic fallback
        return self._generate_deterministic_summary(symbol, contract, metrics, graph_summary, reasons)

    def _build_prompt(
        self,
        symbol: str,
        contract: str,
        metrics: Dict[str, Any],
        graph_summary: str
    ) -> str:
        """Build prompt for LLM"""

        # Limit metrics to top 8 most important
        key_metrics = [
            f"total_supply: {metrics.get('total_supply', 0):,}",
            f"circulating: {metrics.get('circulating', 0):,}",
            f"market_cap: ${metrics.get('market_cap_usd', 0):,}",
            f"top1_pct: {metrics.get('top1_pct', 0):.1f}%",
            f"top3_pct: {metrics.get('top3_pct', 0):.1f}%",
            f"top10_pct: {metrics.get('top10_pct', 0):.1f}%",
            f"holder_count: {metrics.get('holder_count', 0)}",
            f"liquidity_usd: ${metrics.get('liquidity_usd', 0):,}",
        ]

        prompt = f"""[SYSTEM]
You are TokenHealth AGENT. Your job: given concise token metrics + graph summary (holders, liquidity, owner control), produce:

a short 4-line human summary (one sentence each): one-line verdict, one-line reasons, one-line quick evidence, one-line suggested next verification steps.

list top-3 risks as numbered bullets (each 1 sentence).

recommend 3 immediate checks (e.g., check multisig on owner, verify liquidity lock tx hash).

[USER]
Token: {symbol} ({contract})
Metrics:

{chr(10).join(key_metrics)}

recent_minted: {metrics.get('recent_minted', 0):,}
recent_large_transfer_pct: {metrics.get('recent_large_transfer_pct', 0):.1f}%
source_verified: {metrics.get('source_verified', False)}
owner_has_admin: {metrics.get('owner_has_admin', False)}

Graph summary: {graph_summary}

Instructions: produce JSON only with fields: "summary" (array of 4 strings), "top_risks" (array of 3 strings), "next_checks" (array of 3 strings).
Do not include any extraneous text.
"""

        return prompt

    def _generate_deterministic_summary(
        self,
        symbol: str,
        contract: str,
        metrics: Dict[str, Any],
        graph_summary: str,
        reasons: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate deterministic summary based on heuristics
        Used as fallback when LLM is not available
        """

        # Sort reasons by contribution (absolute value)
        top_reasons = sorted(reasons, key=lambda x: abs(x.get("contribution", 0)), reverse=True)[:3]

        # Generate verdict
        risk_score = sum(r.get("contribution", 0) for r in reasons)
        risk_score = max(0, min(100, risk_score))

        if risk_score >= 70:
            verdict = f"{symbol} shows HIGH RISK signals ({risk_score:.0f}/100)"
            risk_level = "high"
        elif risk_score >= 40:
            verdict = f"{symbol} shows MODERATE RISK signals ({risk_score:.0f}/100)"
            risk_level = "moderate"
        elif risk_score >= 20:
            verdict = f"{symbol} shows LOW-MODERATE RISK signals ({risk_score:.0f}/100)"
            risk_level = "low-moderate"
        else:
            verdict = f"{symbol} shows LOW RISK signals ({risk_score:.0f}/100)"
            risk_level = "low"

        # Generate summary lines
        summary = [verdict]

        # Reasons line
        if top_reasons:
            reason_text = ", ".join([r.get("id", "unknown").replace("_", " ") for r in top_reasons[:2]])
            summary.append(f"Primary concerns: {reason_text}.")
        else:
            summary.append("No major risk factors identified.")

        # Evidence line
        if len(top_reasons) > 0:
            top_reason = top_reasons[0]
            summary.append(top_reason.get("note", "See detailed metrics for evidence."))
        else:
            summary.append(f"Token has {metrics.get('holder_count', 0)} holders and ${metrics.get('liquidity_usd', 0):,.0f} liquidity.")

        # Next steps line
        summary.append("Verify on-chain data independently before making decisions.")

        # Generate top risks
        top_risks = []
        for reason in top_reasons:
            risk_text = reason.get("note", reason.get("id", "Unknown risk"))
            top_risks.append(risk_text)

        # Pad to 3 risks if needed
        while len(top_risks) < 3:
            if len(top_risks) == 0:
                top_risks.append("Always verify contract source code on block explorer.")
            elif len(top_risks) == 1:
                top_risks.append("Check liquidity depth and trading volume on DEX aggregators.")
            else:
                top_risks.append("Review recent transaction patterns for suspicious activity.")

        # Generate next checks
        next_checks = []

        if not metrics.get("source_verified", True):
            next_checks.append("Verify contract source code on Etherscan or similar explorer.")

        if metrics.get("owner_has_admin", False):
            next_checks.append("Check if owner address is a multisig or DAO contract.")

        if not metrics.get("liquidity_locked", True):
            next_checks.append("Verify liquidity lock status and expiration date.")

        if metrics.get("top1_pct", 0) > 30:
            next_checks.append("Investigate top holder addresses (exchange, team, or whale).")

        if len(next_checks) < 3:
            next_checks.append("Monitor social channels and community sentiment.")

        if len(next_checks) < 3:
            next_checks.append("Test buy/sell on DEX with small amount to check for honeypot.")

        # Limit to 3 checks
        next_checks = next_checks[:3]

        return {
            "summary": summary,
            "top_risks": top_risks,
            "next_checks": next_checks
        }

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM JSON response with error handling"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback to empty structure
            return {
                "summary": ["Error parsing LLM response."],
                "top_risks": ["Unable to generate risk analysis."],
                "next_checks": ["Verify contract manually."]
            }
