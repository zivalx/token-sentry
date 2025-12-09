"""
TokenHealth Graph Builder
Builds knowledge graph from token data using networkx
"""
import networkx as nx
from typing import Dict, List, Any


class GraphBuilder:
    """Builds knowledge graph for token analysis"""

    def __init__(self):
        self.G = nx.DiGraph()

    def build_from_seed(self, seed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build graph from seed data
        Returns: {nodes: [...], edges: [...]}
        """
        self.G.clear()

        contract = seed_data.get("contract", "0x0")
        symbol = seed_data.get("symbol", "TOKEN")
        name = seed_data.get("name", "Unknown Token")
        total_supply = seed_data.get("total_supply", 0)
        holders = seed_data.get("holders", [])
        liquidity = seed_data.get("liquidity", {})
        owner = seed_data.get("owner", "")

        # Add token node (central)
        self.G.add_node(
            contract,
            type="token",
            label=f"{symbol}",
            name=name,
            total_supply=total_supply
        )

        # Add owner node and edge
        if owner:
            self.G.add_node(
                owner,
                type="owner",
                label=f"Owner: {owner[:8]}..."
            )
            self.G.add_edge(owner, contract, type="owns", label="owns")

        # Add top holder nodes (limit to top 10)
        top_holders = sorted(holders, key=lambda x: x.get("balance", 0), reverse=True)[:10]

        for idx, holder in enumerate(top_holders):
            holder_addr = holder.get("address", "")
            balance = holder.get("balance", 0)
            pct_supply = (balance / total_supply * 100) if total_supply > 0 else 0

            # Skip if owner is already added as holder
            if holder_addr == owner:
                # Update edge with balance info
                self.G[holder_addr][contract]["balance"] = balance
                self.G[holder_addr][contract]["pct_supply"] = pct_supply
                continue

            self.G.add_node(
                holder_addr,
                type="holder",
                label=f"Holder #{idx+1}",
                balance=balance,
                pct_supply=pct_supply
            )
            self.G.add_edge(
                holder_addr,
                contract,
                type="holds",
                label=f"{pct_supply:.1f}%",
                balance=balance,
                pct_supply=pct_supply
            )

        # Add liquidity pool node
        if liquidity:
            pair_addr = liquidity.get("pair", "")
            liquidity_usd = liquidity.get("liquidity_usd", 0)
            locked = liquidity.get("locked", False)

            if pair_addr:
                self.G.add_node(
                    pair_addr,
                    type="liquidity_pool",
                    label=f"LP: ${liquidity_usd:,.0f}",
                    liquidity_usd=liquidity_usd,
                    locked=locked
                )
                self.G.add_edge(
                    contract,
                    pair_addr,
                    type="liquidity_pair",
                    label="liquidity"
                )

                # Add locker if present
                locker = liquidity.get("locker", "")
                if locker and locked:
                    self.G.add_node(
                        locker,
                        type="locker",
                        label=f"Locker: {locker[:8]}..."
                    )
                    self.G.add_edge(
                        pair_addr,
                        locker,
                        type="locked_in",
                        label="locked"
                    )

        # Convert to JSON-serializable format
        return self._to_dict()

    def _to_dict(self) -> Dict[str, Any]:
        """Convert networkx graph to dictionary format for frontend"""
        nodes = []
        edges = []

        for node_id, node_data in self.G.nodes(data=True):
            nodes.append({
                "id": node_id,
                "label": node_data.get("label", node_id[:10]),
                "type": node_data.get("type", "unknown"),
                **{k: v for k, v in node_data.items() if k not in ["label", "type"]}
            })

        for source, target, edge_data in self.G.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "label": edge_data.get("label", ""),
                "type": edge_data.get("type", ""),
                **{k: v for k, v in edge_data.items() if k not in ["label", "type"]}
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }

    def get_summary(self, graph: Dict[str, Any]) -> str:
        """Generate human-readable graph summary"""
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        node_types = {}
        for node in nodes:
            node_type = node.get("type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1

        summary_parts = []

        if "token" in node_types:
            summary_parts.append(f"{node_types['token']} token")

        if "owner" in node_types:
            summary_parts.append(f"{node_types['owner']} owner")

        if "holder" in node_types:
            summary_parts.append(f"{node_types['holder']} holders")

        if "liquidity_pool" in node_types:
            summary_parts.append(f"{node_types['liquidity_pool']} liquidity pool")

        if "locker" in node_types:
            summary_parts.append(f"{node_types['locker']} locker")

        summary = " => ".join(summary_parts) if summary_parts else "Empty graph"

        return f"{summary} ({len(nodes)} nodes, {len(edges)} edges)"
