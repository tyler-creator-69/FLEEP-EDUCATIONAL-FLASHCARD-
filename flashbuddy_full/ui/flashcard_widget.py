from PyQt6.QtCore import Qt, QPropertyAnimation
from PyQt6.QtGui import QPainter, QFont
from PyQt6.QtWidgets import QLabel


class FlashcardWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setText("No cards")
        self.is_animating = False

    def flip(self, on_finished=None):
        """Safe flip animation with state flag."""
        if self.is_animating:
            return
        self.is_animating = True

        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(200)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)

        def halfway():
            anim_back = QPropertyAnimation(self, b"windowOpacity", self)
            anim_back.setDuration(200)
            anim_back.setStartValue(0.0)
            anim_back.setEndValue(1.0)
            anim_back.finished.connect(lambda: self._finish_flip(on_finished))
            anim_back.start()

        anim.finished.connect(halfway)
        anim.start()

    def _finish_flip(self, on_finished):
        self.is_animating = False
        if callable(on_finished):
            on_finished()
