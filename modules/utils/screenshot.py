from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPainter, QColor
from PIL import ImageGrab
import sys

class ScreenSnipper(QWidget):
    def __init__(self, app=None, translation=None):
        super().__init__()
        self.app = app
        self.translation = translation
        
        self.setAutoFillBackground(False)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowFullScreen)
        self.setCursor(Qt.CrossCursor)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.origin = QPoint()
        self.current_pos = QPoint()
        self.selecting = False
        self.selection_rect = QRect()

        # --- Capture the entire virtual desktop as background ---
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        screens = app.screens()
        bounding_rect = screens[0].geometry()
        for s in screens[1:]:
            bounding_rect = bounding_rect.united(s.geometry())
        self.virtual_geometry = bounding_rect
        # Capture the whole virtual desktop
        self.desktop_pixmap = screens[0].grabWindow(
            0,
            bounding_rect.left(),
            bounding_rect.top(),
            bounding_rect.width(),
            bounding_rect.height()
        )
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.current_pos = event.pos()
            self.selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.selecting:
            self.current_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.selecting:
            self.selecting = False
            self.selection_rect = QRect(self.origin, self.current_pos).normalized()
            self.update()
            # Get global coordinates
            global_selection_rect = (
                self.mapToGlobal(self.selection_rect.topLeft()).x(),
                self.mapToGlobal(self.selection_rect.topLeft()).y(),
                self.mapToGlobal(self.selection_rect.bottomRight()).x(),
                self.mapToGlobal(self.selection_rect.bottomRight()).y()
            )
            screenshot = self.take_screenshot(global_selection_rect)
            self.hide()
            if screenshot:
                self.save_screenshot(screenshot)

    def paintEvent(self, event):
        painter = QPainter(self)
        offset = self.virtual_geometry.topLeft()
        # Draw the correct part of the virtual desktop
        painter.drawPixmap(
            0, 0, self.desktop_pixmap,
            self.x() + offset.x(), self.y() + offset.y(), self.width(), self.height()
        )
        # Draw semi-transparent overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
        # Draw the selection rectangle area as a "hole" (showing the desktop)
        if self.selecting:
            rect = QRect(self.origin, self.current_pos).normalized()
        else:
            rect = self.selection_rect
        if not rect.isNull():
            global_rect = rect.translated(self.x() + offset.x(), self.y() + offset.y())
            painter.drawPixmap(rect, self.desktop_pixmap, global_rect)
            # No border drawn

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.app:
                self.app._toggle_image(on=False)
            self.close()

    def take_screenshot(self, bbox):
        try:
            img = ImageGrab.grab(bbox=bbox, all_screens=True, include_layered_windows=False)
            return img
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            return None

    def save_screenshot(self, image):
        if self.translation:
            text_extracted, text_romaji, text_translated = self.translation.translate_image(image)
        if self.app:
            self.app.translation_overlay.set_texts(text_extracted, text_romaji, text_translated)
            self.app._toggle_image(on=False)
        else:
            import matplotlib.pyplot as plt
            plt.imshow(image)
            plt.show()
            
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     main_window = ScreenSnipper()
#     main_window.show()
#     sys.exit(app.exec_())