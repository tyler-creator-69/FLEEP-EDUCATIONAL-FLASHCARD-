from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QBrush
from PyQt6.QtWidgets import QWidget


class ToggleSwitch(QWidget):
    # This signal emits True (dark mode) or False (light mode)
    toggle_signal = pyqtSignal(bool)

    def __init__(self, parent=None, checked=False):
        super().__init__(parent)
        self.setFixedSize(50, 28)
        self._checked = checked
        self._circle_pos = 26 if checked else 2
        self.animation = QPropertyAnimation(self, b"circle_pos", self)
        self.animation.setDuration(150)

    def get_circle_pos(self):
        return self._circle_pos

    def set_circle_pos(self, pos):
        self._circle_pos = pos
        self.update()

    circle_pos = property(get_circle_pos, set_circle_pos)

    def mousePressEvent(self, event):
        self.toggle()

    def toggle(self):
        self._checked = not self._checked
        start = 26 if not self._checked else 2
        end = 2 if not self._checked else 26
        self.animation.stop()
        self.animation.setStartValue(start)
        self.animation.setEndValue(end)
        self.animation.start()
        self.update()

        # Emit signal so MainWindow can react
        self.toggle_signal.emit(self._checked)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Track background
        if self._checked:
            track_color = QColor("#a07f5a")  # warm brown (Dark mode)
        else:
            track_color = QColor("#d6b88d")  # beige (Light mode)
        p.setBrush(QBrush(track_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect(), 14, 14)

        # Circle
        circle_color = QColor("#f3e9d2") if self._checked else QColor("#2b2b2b")
        p.setBrush(QBrush(circle_color))
        p.drawEllipse(QRect(self._circle_pos, 2, 24, 24))
        p.end()
