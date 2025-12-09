"""
TokenHealth Heuristics Engine
Implements all risk scoring rules
"""
from typing import Dict, List, Any
from datetime import datetime, timedelta


class HeuristicsEngine:
    """Computes risk score based on deterministic heuristics"""

    def __init__(self):
        self.heuristics = []
        self.reasons = []

    def compute(self, seed_data: Dict[str, Any], graph: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute risk score and reasons from seed data and graph
        Returns: {risk_score, reasons, metrics}
        """
        self.heuristics = []
        self.reasons = []

        # Extract metrics
        metrics = self._extract_metrics(seed_data, graph)

        # Run all heuristics
        total_risk = 0

        total_risk += self._check_unverified_source_code(metrics)
        total_risk += self._check_admin_privileges(metrics)
        total_risk += self._check_liquidity_locked(metrics)
        total_risk += self._check_top_holder_concentration(metrics)
        total_risk += self._check_recent_large_transfers(metrics)
        total_risk += self._check_minted_recently(metrics)
        total_risk += self._check_suspicious_tx_pattern(metrics)
        total_risk += self._check_low_liquidity(metrics)
        total_risk += self._check_low_holder_count(metrics)
        total_risk += self._check_honeypot(metrics)
        total_risk += self._check_audit_present(metrics)

        # Cap between 0 and 100
        risk_score = max(0, min(100, total_risk))

        return {
            "risk_score": risk_score,
            "reasons": self.reasons,
            "metrics": metrics
        }

    def _extract_metrics(self, seed_data: Dict[str, Any], graph: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize metrics from seed data"""
        total_supply = seed_data.get("total_supply", 0)
        holders = seed_data.get("holders", [])
        transfers = seed_data.get("transfers", [])
        liquidity = seed_data.get("liquidity", {})

        # Sort holders by balance
        sorted_holders = sorted(holders, key=lambda x: x.get("balance", 0), reverse=True)

        # Calculate holder percentages
        top1_pct = (sorted_holders[0]["balance"] / total_supply * 100) if len(sorted_holders) > 0 and total_supply > 0 else 0
        top3_pct = (sum(h["balance"] for h in sorted_holders[:3]) / total_supply * 100) if len(sorted_holders) >= 3 and total_supply > 0 else 0
        top10_pct = (sum(h["balance"] for h in sorted_holders[:10]) / total_supply * 100) if len(sorted_holders) >= 10 and total_supply > 0 else 0

        # Recent transfers analysis
        now = datetime.now().timestamp()
        thirty_days_ago = now - (30 * 24 * 60 * 60)

        recent_transfers = [t for t in transfers if t.get("timestamp", 0) > thirty_days_ago]
        recent_large_transfer_pct = 0
        recent_minted = 0

        for transfer in recent_transfers:
            transfer_pct = (transfer.get("value", 0) / total_supply * 100) if total_supply > 0 else 0
            if transfer_pct > recent_large_transfer_pct:
                recent_large_transfer_pct = transfer_pct

            # Check if minting (from 0x0)
            if transfer.get("from", "").lower() in ["0x0", "0x0000000000000000000000000000000000000000"]:
                recent_minted += transfer.get("value", 0)

        return {
            "contract": seed_data.get("contract", ""),
            "symbol": seed_data.get("symbol", ""),
            "name": seed_data.get("name", ""),
            "total_supply": total_supply,
            "circulating": total_supply - sum(h.get("balance", 0) for h in holders if h.get("address", "").lower() in ["0x0", "0xdead"]),
            "market_cap_usd": seed_data.get("market_cap_usd", 0),
            "top1_pct": top1_pct,
            "top3_pct": top3_pct,
            "top10_pct": top10_pct,
            "holder_count": len(holders),
            "liquidity_usd": liquidity.get("liquidity_usd", 0),
            "liquidity_locked": liquidity.get("locked", False),
            "recent_minted": recent_minted,
            "recent_large_transfer_pct": recent_large_transfer_pct,
            "source_verified": seed_data.get("contract_verified", False),
            "owner_has_admin": seed_data.get("owner_has_admin", False),
            "owner": seed_data.get("owner", ""),
            "transfer_count": len(transfers),
            "recent_transfer_count": len(recent_transfers),
            "audited": seed_data.get("audited", False),
            "honeypot_risk": seed_data.get("honeypot_risk", False),
        }

    def _check_unverified_source_code(self, metrics: Dict[str, Any]) -> float:
        """Unverified source code → +25 risk"""
        if not metrics["source_verified"]:
            self.reasons.append({
                "id": "unverified_source_code",
                "value": False,
                "contribution": 25,
                "note": "Contract source code is not verified on block explorer."
            })
            return 25
        return 0

    def _check_admin_privileges(self, metrics: Dict[str, Any]) -> float:
        """Admin privileges → +20 risk"""
        if metrics["owner_has_admin"]:
            self.reasons.append({
                "id": "admin_privileges",
                "value": True,
                "contribution": 20,
                "note": "Owner has privileged functions (mint, pause, upgrade, or setFee)."
            })
            return 20
        return 0

    def _check_liquidity_locked(self, metrics: Dict[str, Any]) -> float:
        """Liquidity locked → -30 risk (safety factor)"""
        if metrics["liquidity_locked"]:
            self.reasons.append({
                "id": "liquidity_locked",
                "value": True,
                "contribution": -30,
                "note": "Liquidity is locked in a verified locker contract."
            })
            return -30
        return 0

    def _check_top_holder_concentration(self, metrics: Dict[str, Any]) -> float:
        """Top holder concentration → up to +55 risk"""
        risk = 0
        notes = []

        if metrics["top1_pct"] > 40:
            risk += 25
            notes.append(f"Top holder owns {metrics['top1_pct']:.1f}% of supply")

        if metrics["top3_pct"] > 60:
            risk += 20
            notes.append(f"Top 3 holders own {metrics['top3_pct']:.1f}% of supply")

        if metrics["top10_pct"] > 80:
            risk += 10
            notes.append(f"Top 10 holders own {metrics['top10_pct']:.1f}% of supply")

        if risk > 0:
            self.reasons.append({
                "id": "top_holder_concentration",
                "value": metrics["top3_pct"],
                "contribution": risk,
                "note": " | ".join(notes) if notes else f"Top 3 holders own {metrics['top3_pct']:.1f}% of supply."
            })

        return risk

    def _check_recent_large_transfers(self, metrics: Dict[str, Any]) -> float:
        """Recent large transfers → +15 risk"""
        threshold = 5.0  # 5% of supply
        if metrics["recent_large_transfer_pct"] > threshold:
            self.reasons.append({
                "id": "recent_large_transfers",
                "value": metrics["recent_large_transfer_pct"],
                "contribution": 15,
                "note": f"Large transfer of {metrics['recent_large_transfer_pct']:.1f}% of supply in last 30 days."
            })
            return 15
        return 0

    def _check_minted_recently(self, metrics: Dict[str, Any]) -> float:
        """Minted recently → +30 risk"""
        threshold = metrics["total_supply"] * 0.05  # 5% of total supply
        if metrics["recent_minted"] > threshold:
            recent_minted_pct = (metrics["recent_minted"] / metrics["total_supply"] * 100) if metrics["total_supply"] > 0 else 0
            self.reasons.append({
                "id": "minted_recently",
                "value": metrics["recent_minted"],
                "contribution": 30,
                "note": f"Token minted {recent_minted_pct:.1f}% of supply in last 30 days."
            })
            return 30
        return 0

    def _check_suspicious_tx_pattern(self, metrics: Dict[str, Any]) -> float:
        """Suspicious transaction pattern → +15 risk"""
        # Simple heuristic: many recent transfers relative to holder count
        if metrics["holder_count"] > 0 and metrics["recent_transfer_count"] > metrics["holder_count"] * 3:
            self.reasons.append({
                "id": "suspicious_tx_pattern",
                "value": metrics["recent_transfer_count"],
                "contribution": 15,
                "note": f"High transaction count ({metrics['recent_transfer_count']}) relative to holder count ({metrics['holder_count']})."
            })
            return 15
        return 0

    def _check_low_liquidity(self, metrics: Dict[str, Any]) -> float:
        """Low liquidity → +20 risk"""
        threshold = 10000  # USD
        if metrics["liquidity_usd"] < threshold:
            self.reasons.append({
                "id": "low_liquidity",
                "value": metrics["liquidity_usd"],
                "contribution": 20,
                "note": f"Low liquidity pool (${metrics['liquidity_usd']:,.0f})."
            })
            return 20
        return 0

    def _check_low_holder_count(self, metrics: Dict[str, Any]) -> float:
        """Low holder count → +10 risk"""
        threshold = 100
        if metrics["holder_count"] < threshold:
            self.reasons.append({
                "id": "low_holder_count",
                "value": metrics["holder_count"],
                "contribution": 10,
                "note": f"Only {metrics['holder_count']} token holders."
            })
            return 10
        return 0

    def _check_honeypot(self, metrics: Dict[str, Any]) -> float:
        """Honeypot check → +50 risk (placeholder)"""
        if metrics.get("honeypot_risk", False):
            self.reasons.append({
                "id": "honeypot_check",
                "value": True,
                "contribution": 50,
                "note": "Token failed buy/sell simulation test (potential honeypot)."
            })
            return 50
        return 0

    def _check_audit_present(self, metrics: Dict[str, Any]) -> float:
        """Audit present → -20 risk (safety factor)"""
        if metrics.get("audited", False):
            self.reasons.append({
                "id": "audit_present",
                "value": True,
                "contribution": -20,
                "note": "Contract audited by a known auditor."
            })
            return -20
        return 0
