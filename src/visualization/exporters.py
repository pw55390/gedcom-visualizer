"""
Vector and Raster Exporter Engine for Genealogy Graphics Scenes.
Exports diagrams to SVG, PNG, and PDF formats.
"""

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtGui import QPainter, QPixmap, QImage
from PySide6.QtSvg import QSvgGenerator
from PySide6.QtCore import QSize, QRectF


class DiagramExporter:
    @staticmethod
    def export_to_png(scene: QGraphicsScene, file_path: str, dpi_scale: float = 2.0):
        """Exports QGraphicsScene content to high-resolution PNG image."""
        rect = scene.itemsBoundingRect().adjusted(-50, -50, 50, 50)
        image = QImage(
            int(rect.width() * dpi_scale),
            int(rect.height() * dpi_scale),
            QImage.Format.Format_ARGB32
        )
        image.fill(0xff181825)  # Dark background fill

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        scene.render(painter, QRectF(image.rect()), rect)
        painter.end()

        image.save(file_path, "PNG")

    @staticmethod
    def export_to_svg(scene: QGraphicsScene, file_path: str):
        """Exports QGraphicsScene content to scalable SVG vector graphic file."""
        rect = scene.itemsBoundingRect().adjusted(-50, -50, 50, 50)
        generator = QSvgGenerator()
        generator.setFileName(file_path)
        generator.setSize(QSize(int(rect.width()), int(rect.height())))
        generator.setViewBox(rect)
        generator.setTitle("GEDCOM Visualizer Tree Diagram")

        painter = QPainter(generator)
        scene.render(painter)
        painter.end()

    @staticmethod
    def export_to_pdf(scene: QGraphicsScene, file_path: str):
        """Exports QGraphicsScene content directly to vector PDF file."""
        from PySide6.QtPrintSupport import QPrinter
        from PySide6.QtGui import QPageLayout
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file_path)

        painter = QPainter(printer)
        rect = scene.itemsBoundingRect().adjusted(-50, -50, 50, 50)
        scene.render(painter, QRectF(), rect)
        painter.end()
