"""
Ancestor Tree Layout Engine.
Calculates 2D coordinates (X, Y) for hierarchical ancestor trees with Ahnentafel M-F-M-F ordering.
Ensures parents are placed directly above their respective child without crossing lines.
"""

from typing import Dict, Tuple, Set, List, Optional


class AncestorsLayout:
    def __init__(self, node_width: float = 180.0, node_height: float = 75.0, h_gap: float = 25.0, v_gap: float = 90.0):
        self.node_width = node_width
        self.node_height = node_height
        self.h_gap = h_gap
        self.v_gap = v_gap

    def calculate_layout(
        self,
        root_id: str,
        graph_engine,
        max_generations: int = 4,
        max_descendants: int = 1
    ) -> Tuple[Dict[str, Tuple[float, float]], List[Tuple[str, str]]]:
        """Calculates (x, y) coordinates for root person, ancestors (Y <= 0) and descendants (Y > 0)."""
        positions: Dict[str, Tuple[float, float]] = {}
        edges: List[Tuple[str, str]] = []

        # 1. Map persons to Ahnentafel slots: (level, slot_index) -> person_id
        ahnentafel: Dict[Tuple[int, int], str] = {}

        spouses = graph_engine.get_spouses(root_id) if hasattr(graph_engine, "get_spouses") else []
        num_level0_slots = 1

        if spouses:
            partner_id = spouses[0]
            num_level0_slots = 2
            root_sex = graph_engine.nodes_data.get(root_id, {}).get("sex", "U")
            partner_sex = graph_engine.nodes_data.get(partner_id, {}).get("sex", "U")

            if root_sex == "F" and partner_sex == "M":
                ahnentafel[(0, 0)] = partner_id
                ahnentafel[(0, 1)] = root_id
            else:
                ahnentafel[(0, 0)] = root_id
                ahnentafel[(0, 1)] = partner_id

            edges.append((ahnentafel[(0, 0)], ahnentafel[(0, 1)]))
        else:
            ahnentafel[(0, 0)] = root_id

        for level in range(max_generations - 1):
            num_slots = num_level0_slots * (2 ** level)
            for slot_idx in range(num_slots):
                person_id = ahnentafel.get((level, slot_idx))
                if not person_id:
                    continue

                # Get parents of person_id
                parents = list(graph_engine.graph.predecessors(person_id))
                father_id = None
                mother_id = None

                for p in parents:
                    p_sex = graph_engine.nodes_data.get(p, {}).get("sex", "U")
                    if p_sex == "M" and not father_id:
                        father_id = p
                    elif p_sex == "F" and not mother_id:
                        mother_id = p

                # Fallback if sex is unknown: first is father, second is mother
                if parents:
                    if not father_id:
                        father_id = parents[0]
                    if not mother_id and len(parents) > 1:
                        mother_id = parents[1] if parents[1] != father_id else None

                if father_id:
                    ahnentafel[(level + 1, 2 * slot_idx)] = father_id
                    edges.append((father_id, person_id))
                if mother_id:
                    ahnentafel[(level + 1, 2 * slot_idx + 1)] = mother_id
                    edges.append((mother_id, person_id))

        # 2. Compute X positions for ancestors (Y <= 0)
        max_level = max_generations - 1
        num_bottom_slots = num_level0_slots * (2 ** max_level)

        slot_width = self.node_width + self.h_gap

        def get_slot_x(level: int, slot_idx: int) -> float:
            span = 2 ** (max_level - level)
            center_slot_index = slot_idx * span + (span - 1) / 2.0
            return (center_slot_index - (num_bottom_slots - 1) / 2.0) * slot_width

        # 3. Calculate (x, y) coordinates for ancestors
        for (level, slot_idx), node_id in ahnentafel.items():
            x = get_slot_x(level, slot_idx)
            y = -level * (self.node_height + self.v_gap)
            positions[node_id] = (x, y)

        # 4. Calculate Descendants Layout (Y > 0)
        if max_descendants > 0:
            level0_nodes = [node_id for (l, s), node_id in ahnentafel.items() if l == 0]
            current_parents = set(level0_nodes)

            for desc_gen in range(1, max_descendants + 1):
                children_set = set()
                for p_id in current_parents:
                    if p_id in graph_engine.graph:
                        for child in graph_engine.graph.successors(p_id):
                            children_set.add(child)

                children = sorted([c for c in children_set if c not in positions])
                if not children:
                    break

                parent_xs = [positions[p][0] for p in current_parents if p in positions]
                mid_x = sum(parent_xs) / len(parent_xs) if parent_xs else 0.0

                num_children = len(children)
                y_pos = desc_gen * (self.node_height + self.v_gap)

                for idx, child_id in enumerate(children):
                    x_pos = mid_x + (idx - (num_children - 1) / 2.0) * slot_width
                    positions[child_id] = (x_pos, y_pos)

                    for p_id in current_parents:
                        if graph_engine.graph.has_edge(p_id, child_id):
                            edges.append((p_id, child_id))

                current_parents = set(children)

        return positions, edges
