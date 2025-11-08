from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QPropertyAnimation

class FlashcardWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)

    def flip(self, on_finished=None):
        anim = QPropertyAnimation(self, b'windowOpacity')
        anim.setDuration(240); anim.setStartValue(1.0); anim.setEndValue(0.0)
        def _after():
            if on_finished: on_finished()
            anim2 = QPropertyAnimation(self, b'windowOpacity')
            anim2.setDuration(240); anim2.setStartValue(0.0); anim2.setEndValue(1.0); anim2.start()
        anim.finished.connect(_after); anim.start()
