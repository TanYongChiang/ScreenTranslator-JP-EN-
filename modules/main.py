import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QPixmap, QMouseEvent
from PyQt5.QtCore import Qt, QPoint

from .utils.translation import TranslationHandler, TranslationOverlay
from .utils.screenshot import ScreenSnipper

class MainApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Screen Translator (JA -> EN)")

        # List of image paths to toggle between
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.image_filenames = ["nier.png", "nier2.png"]
        self.image_paths = [os.path.join(self.current_dir, 'utils', filename) for filename in self.image_filenames]
        self.toggled = False # Index to keep track of the currently displayed image

        # Load the QPixmaps from the image files and scale them
        # Using scaledToHeight to maintain aspect ratio and set a consistent height.
        # Qt.SmoothTransformation provides better quality scaling.
        self.scaled_to_height = 500
        self.pixmap1 = QPixmap(self.image_paths[0]).scaledToHeight(self.scaled_to_height, mode=Qt.SmoothTransformation)
        self.pixmap2 = QPixmap(self.image_paths[1]).scaledToHeight(self.scaled_to_height, mode=Qt.SmoothTransformation)
        
        # Set window size to match the dimensions of the scaled first image
        self.setFixedSize(self.pixmap1.size())

        # Set window flags for transparency and framelessness
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Create a QLabel to display the image
        self.image_label = QLabel(self)
        self.image_label.setPixmap(self.pixmap1) # Set initial image
        self.image_label.setAlignment(Qt.AlignCenter) # Center the image within the label
        # Set the label's geometry to fill the entire window
        self.image_label.setGeometry(0, 0, self.width(), self.height())

        # --- Variables for dragging the window ---
        self.old_pos = QPoint() # Stores the mouse position when dragging starts
        self.click_threshold = 5 # Pixels: if mouse moves more than this, it's a drag, not a click
        self.is_dragging = False # Flag to indicate if a drag operation is in progress

        # Handle Translations
        self.translation = TranslationHandler('ja', 'en')
        self.translation_overlay = TranslationOverlay(self, self.image_label)
        self.translation_overlay.setGeometry(0, 0, self.image_label.width(), self.image_label.height())
        self.translation_overlay_timer = 20
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.translation_overlay.hide()
    
    def mousePressEvent(self, event: QMouseEvent):
        """
        Handles mouse press events.
        Records the initial mouse position for both click detection and dragging.
        """
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos() # Store global position for dragging
            self.click_start_pos = event.globalPos() # Store global position for click detection
            self.is_dragging = False # Reset drag flag

    def mouseMoveEvent(self, event: QMouseEvent):
        """
        Handles mouse move events.
        If the left mouse button is held down and moved beyond a threshold, it drags the window.
        """
        if event.buttons() == Qt.LeftButton:
            # Calculate the distance moved from the initial press
            distance = (event.globalPos() - self.click_start_pos).manhattanLength()

            if distance > self.click_threshold:
                # If moved beyond threshold, it's a drag
                self.is_dragging = True
                delta = QPoint(event.globalPos() - self.old_pos)
                self.move(self.x() + delta.x(), self.y() + delta.y())
                self.old_pos = event.globalPos() # Update old_pos for continuous dragging

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Handles mouse release events.
        If it was a click (not a drag), it toggles the image.
        """
        if event.button() == Qt.LeftButton:
            if not self.is_dragging:
                # If no significant dragging occurred, treat it as a click
                self._toggle_image(on=True)
            self.is_dragging = False # Reset drag flag

    def _toggle_image(self, on=True):
        """
        Toggles the displayed image between image1.png and image2.png.
        """
        if self.toggled and not on: # if toggled on and try to turn off
            self._set_image(self.pixmap1)
            self.toggled = not self.toggled
        elif not self.toggled and on: # if toggled off and try to turn on
            self.translation_overlay.hide()
            self._set_image(self.pixmap2)
            self.toggled = not self.toggled
            
            self.snipper = ScreenSnipper(self, self.translation)
            self.snipper.show()
                
    def _set_image(self, pixmap):
        self.image_label.setPixmap(pixmap)
        QApplication.processEvents() # force GUI update
        # Adjust window size if the new pixmap has a different size
        if self.size() != pixmap.size():
            self.setFixedSize(pixmap.size())
            self.image_label.setGeometry(0, 0, self.width(), self.height())

if __name__ == "__main__":
    app = QApplication(sys.argv) # Create the QApplication instance
    window = MainApp() # Create an instance of our custom window
    window.show() # Show the window
    sys.exit(app.exec_()) # Start the application's event loop
