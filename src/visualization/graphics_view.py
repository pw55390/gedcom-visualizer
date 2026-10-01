"""
Interactive High-Performance Genealogy Canvas Viewport (QGraphicsView / QGraphicsScene).
Includes Virtual Viewport Culling, Smooth Pan/Zoom, and Node Interactivity.
"""

from typing import Dict, Optional, Callable
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QWheelEvent, QMouseEvent, QPainter

from src.visualization.items.person_node_item import PersonNodeItem
from src.visualization.items.relationship_edge_item import RelationshipEdgeItem
from src.visualization.layouts.ancestors_layout import AncestorsLayout


class GenealogyGraphicsView(QGraphicsView):
    def __init__(self, parent=None, on_person_selected_cb: Optional[Callable[[str], None]] = None):
        super().__init__(parent)
        self.on_person_selected_cb = on_person_selected_cb

        self.scene_obj = QGraphicsScene(self)
        self.setScene(self.scene_obj)

        # Performance flags
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.setBackgroundBrush(Qt.GlobalColor.black)
        self.node_items: Dict[str, PersonNodeItem] = {}
        self._is_panning = False
        self._pan_start_pos = QPointF()

    def render_ancestors_tree(self, root_id: str, graph_engine, max_generations: int = 4, max_descendants: int = 1):
        """Renders tree for root_id using AncestorsLayout up to max_generations ancestors and max_descendants descendants."""
        self.setUpdatesEnabled(False)
        try:
            self.scene_obj.clear()
            self.node_items.clear()

            layout_engine = AncestorsLayout()
            positions, edges = layout_engine.calculate_layout(
                root_id, graph_engine, max_generations=max_generations, max_descendants=max_descendants
            )

            # Add Nodes
            for node_id, pos in positions.items():
                data = graph_engine.nodes_data.get(node_id, {"name": "Nieznany", "sex": "U"})
                item = PersonNodeItem(
                    person_id=node_id,
                    name=data["name"],
                    sex=data["sex"],
                    birth_info=data.get("birth_info", ""),
                    death_info=data.get("death_info", ""),
                    width=180.0,
                    height=75.0
                )
                item.setPos(pos[0], pos[1])
                self.scene_obj.addItem(item)
                self.node_items[node_id] = item

            # Add Edges
            for parent_id, child_id in edges:
                if parent_id in self.node_items and child_id in self.node_items:
                    p_item = self.node_items[parent_id]
                    c_item = self.node_items[child_id]
                    edge_item = RelationshipEdgeItem(p_item.pos(), c_item.pos())
                    self.scene_obj.addItem(edge_item)

            self.scene_obj.setSceneRect(self.scene_obj.itemsBoundingRect().adjusted(-100, -100, 100, 100))
        finally:
            self.setUpdatesEnabled(True)

    def wheelEvent(self, event: QWheelEvent):
        """Smooth Zooming anchored on cursor."""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.position().toPoint())
            if isinstance(item, PersonNodeItem):
                self._click_item = item
            else:
                self._click_item = None
            self._is_panning = True
            self._pan_start_pos = event.position()
            self._drag_distance = 0.0
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_panning:
            delta = event.position() - self._pan_start_pos
            self._drag_distance += (delta.x() ** 2 + delta.y() ** 2) ** 0.5
            self._pan_start_pos = event.position()
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - delta.x()))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta.y()))
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            if self._drag_distance < 5.0 and getattr(self, "_click_item", None):
                if self.on_person_selected_cb:
                    self.on_person_selected_cb(self._click_item.person_id)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
