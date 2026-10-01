"""
Custom QGraphicsItem for Person Node with Level-of-Detail (LOD) Rendering.
Renders person name, birth date/place, and death date/place under the name.
"""

from typing import Optional
from PySide6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QBrush, QPen, QColor, QFont, QPainterPath


class PersonNodeItem(QGraphicsItem):
    def __init__(
        self,
        person_id: str,
        name: str,
        sex: str = "U",
        birth_info: str = "",
        death_info: str = "",
        width: float = 180.0,
        height: float = 75.0
    ):
        super().__init__()
        self.person_id = person_id
        self.name = name
        self.sex = sex
        self.birth_info = birth_info
        self.death_info = death_info
        self.width = width
        self.height = height
        self.is_highlighted = False

        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

    def boundingRect(self) -> QRectF:
        return QRectF(-self.width / 2.0, -self.height / 2.0, self.width, self.height)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        lod = option.levelOfDetailFromTransform(painter.worldTransform())
        rect = self.boundingRect()

        # Color schemes by sex
        if self.sex == "M":
            bg_color = QColor("#1e293b")
            border_color = QColor("#38bdf8")
        elif self.sex == "F":
            bg_color = QColor("#3b1e2e")
            border_color = QColor("#f472b6")
        else:
            bg_color = QColor("#334155")
            border_color = QColor("#94a3b8")

        if self.isSelected() or self.is_highlighted:
            border_color = QColor("#facc15")  # Bright Yellow Highlight

        # LEVEL OF DETAIL (LOD) OPTIMIZATION
        if lod < 0.25:
            # Low LOD: Render simplified solid pill (Ultra fast for 50k+ nodes)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(border_color))
            painter.drawRoundedRect(rect, 4.0, 4.0)
            return

        # High LOD: Full Detailed Card
        path = QPainterPath()
        path.addRoundedRect(rect, 8.0, 8.0)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillPath(path, QBrush(bg_color))

        pen = QPen(border_color, 2.0 if (self.isSelected() or self.is_highlighted) else 1.2)
        painter.setPen(pen)
        painter.drawPath(path)

        # 1. Draw Name (Top)
        name_rect = QRectF(rect.x() + 4, rect.y() + 6, rect.width() - 8, 22)
        painter.setPen(QPen(QColor("#f8fafc")))
        font_name = QFont("Segoe UI", 9.5, QFont.Weight.Bold)
        painter.setFont(font_name)
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignCenter, self.name)

        # 2. Draw Birth Date / Place (Middle)
        font_sub = QFont("Segoe UI", 8, QFont.Weight.Normal)
        painter.setFont(font_sub)
        painter.setPen(QPen(QColor("#cbd5e1")))

        if self.birth_info:
            b_rect = QRectF(rect.x() + 4, rect.y() + 30, rect.width() - 8, 18)
            painter.drawText(b_rect, Qt.AlignmentFlag.AlignCenter, self.birth_info)

        # 3. Draw Death Date / Place (Bottom)
        if self.death_info:
            d_rect = QRectF(rect.x() + 4, rect.y() + 50, rect.width() - 8, 18)
            painter.drawText(d_rect, Qt.AlignmentFlag.AlignCenter, self.death_info)
