"""
Custom QGraphicsPathItem for Relationship Connectors (Edges).
"""

from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainterPath, QPen, QColor


class RelationshipEdgeItem(QGraphicsPathItem):
    def __init__(self, source_pos: QPointF, target_pos: QPointF):
        super().__init__()
        self.source_pos = source_pos
        self.target_pos = target_pos

        self.setPen(QPen(QColor("#64748b"), 1.5))
        self.setZValue(-1)  # Draw underneath node cards
        self.update_path()

    def update_path(self):
        path = QPainterPath()
        path.moveTo(self.source_pos)

        # Smooth Bezier curve connector
        mid_y = (self.source_pos.y() + self.target_pos.y()) / 2.0
        ctrl1 = QPointF(self.source_pos.x(), mid_y)
        ctrl2 = QPointF(self.target_pos.x(), mid_y)

        path.cubicTo(ctrl1, ctrl2, self.target_pos)
        self.setPath(path)
