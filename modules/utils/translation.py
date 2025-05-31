from google.genai import types
from google import genai
import os
import io

class TranslationHandler:
    def __init__(self, language_from, language_to):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.language_from = language_from
        self.language_to = language_to
        self._read_config()
        self.genai_client = genai.Client(api_key=self.api_keys[0])
        
    def translate_image(self, image):
        text_extracted = self._extract_text_from_image(image)
        text_translated = self._translate_text(text_extracted)
        text_romaji = self._convert_ja_romaji(text_extracted)
        print('text_extracted: ', text_extracted)
        print('text_romaji: ', text_romaji)
        print('text_translated: ', text_translated)
        return (text_extracted, text_romaji, text_translated)
    
    def _prompt_gemini(self, prompt: str, model: str, image=None):
        contents = [prompt]
        if image:
            imgByteArr = io.BytesIO() # file-like buffer stored in memory
            image.save(imgByteArr, format='PNG')
            imgByteArr = imgByteArr.getvalue()
            contents.insert(0, types.Part.from_bytes(
                                    data=imgByteArr,
                                    mime_type='image/jpeg',
                                ))
        response = self.genai_client.models.generate_content(
            model=model,
            contents=contents
        )
        return response.text
    
    def _extract_text_from_image(self, image):
        prompt = f'Extract text in this attached image (language code: {self.language_from}). '
        prompt += 'Retain punctuation. '
        prompt += 'Do not say anything else.'
        return self._prompt_gemini(prompt, 'gemini-2.0-flash', image)
    
    def _translate_text(self, text):
        prompt = f'translate text: "{text}" (language code source: {self.language_from}, destination: {self.language_to}). '
        prompt += 'Retain punctuation. '
        prompt += 'Do not say anything else.'
        return self._prompt_gemini(prompt, 'gemini-2.0-flash')
    
    def _convert_ja_romaji(self, text):
        prompt = f'convert text to romaji: "{text}" (language code: {self.language_from}). '
        prompt += 'Retain punctuation. '
        prompt += 'Do not say anything else.'
        return self._prompt_gemini(prompt, 'gemini-2.0-flash')
    
    def _read_config(self):
        '''
        GEMINI_API_KEY = self.api_keys (sep = " ")
        '''
        self.config_path = os.path.join(self.current_dir, '..', '..', '..', 'config.txt')
        with open(self.config_path, 'r') as file:
            for line in file:
                if line[:14] == 'GEMINI_API_KEY':
                    line_api_keys = line.split(sep='=')[1]
                    self.api_keys = [i for i in line_api_keys.split(" ") if i]
                    
                    
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QFont, QPainterPath, QPixmap
from PyQt5.QtCore import Qt, QRect, QRectF

class TranslationOverlay(QWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.texts = ("", "", "")
        self.background_image_path = os.path.join(self.current_dir, 'tr_overlay_background.png')
        self.q_image_from_path = QPixmap(self.background_image_path)
        self.background_pixmap = self.q_image_from_path.scaledToHeight(self.app.scaled_to_height, mode=Qt.SmoothTransformation)
        self.padding_v, self.padding_h = 10, 40 # Padding around the overlay content
        self.corner_radius = 15 # Radius for rounded corners
        
        self.hide()

    def set_texts(self, extracted, romaji, translated):
        """
        Sets the texts and optionally the background image for the overlay.
        background_image_pil should be a PIL Image object.
        """
        self.texts = (extracted, romaji, translated)
        
        self.show()
        self.update()

        # # timer to hide overlay after some time
        # self.timer = QTimer(self)
        # self.timer.setSingleShot(True)
        # self.timer.timeout.connect(self.hide)
        # self.timer.start(20 * 1000) # 20 seconds

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing) # For smoother rounded corners

        w, h = self.width(), int(self.height() / 2)

        left = 0
        top = int(self.height() / 2) # overlay at bottom half of image
        inner_rect = QRect(left + self.padding_h, top + self.padding_v,
                           w - 2 * self.padding_h, h - 2 * self.padding_v)

        if self.background_pixmap:
            # Draw the pixmap clipped to the rounded rectangle
            painter.save()
            path = QPainterPath()
            path.addRoundedRect(QRectF(inner_rect), self.corner_radius, self.corner_radius)
            painter.setClipPath(path)
            painter.drawPixmap(inner_rect, self.background_pixmap, self.background_pixmap.rect())
            painter.restore()

        painter.setPen(QColor(255, 255, 255)) # White text color
        self.fonts = ("Hina Mincho", "Arial", "Arial")
        self.font_sizes = (13, 9, 10)
        self.font_configs = [QFont(f, fs) for f, fs in zip(self.fonts, self.font_sizes)]

        text_margin = 5 # Margin from the inner rectangle's edge
        text_area_x = inner_rect.x() + text_margin
        text_area_width = inner_rect.width() - 2 * text_margin

        # Use a QRect for text drawing to leverage word wrapping and alignment
        total_text_block_height = 0
        line_spacing = 2 # Adjusted for better visual spacing

        # Calculate heights for each line with their respective fonts
        line_heights = []
        for i, text in enumerate(self.texts):
            painter.setFont(self.font_configs[i])

            # Get bounding rect for wrapped text within the available width
            # Use a dummy rect for height calculation, only width matters for wrapping
            bounding_rect = painter.fontMetrics().boundingRect(
                QRect(0, 0, text_area_width, 0), Qt.TextWordWrap, text
            )
            height_of_this_line = bounding_rect.height()
            line_heights.append(height_of_this_line)
            total_text_block_height += height_of_this_line
            if i < len(self.texts) - 1: # Add spacing for all but the last line
                total_text_block_height += line_spacing

        # Calculate starting Y position to center the entire text block vertically
        start_y_for_centered_text = inner_rect.y() + (inner_rect.height() - total_text_block_height) / 2
        current_y_offset = 0 # Offset relative to start_y_for_centered_text

        # Draw each text line
        for i, text in enumerate(self.texts):
            painter.setFont(self.font_configs[i])

            # Calculate the drawing rectangle for each line of text
            text_draw_rect = QRect(text_area_x,
                                   int(start_y_for_centered_text + current_y_offset),
                                   text_area_width,
                                   line_heights[i]) # Use pre-calculated height for this line

            # Draw the text, ensuring it wraps and is horizontally centered
            painter.drawText(text_draw_rect, Qt.TextWordWrap | Qt.AlignCenter, text)

            # Move y for the next line
            current_y_offset += line_heights[i] + line_spacing