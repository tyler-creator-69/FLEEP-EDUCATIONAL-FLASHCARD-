# dialogs.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QPushButton,
    QHBoxLayout, QLabel, QDialogButtonBox, QFrame, QFileDialog
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from utils import copy_image_to_storage

class CardDialog(QDialog):
    def __init__(self, parent=None, front='', back='', notes='', image_path=''):
        super().__init__(parent)
        self.setWindowTitle('Add / Edit Card')
        self.setModal(True)
        self.front = front
        self.back = back
        self.notes = notes
        self.image_path = image_path
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()
        self.front_input = QLineEdit(self.front)
        self.back_input = QTextEdit(self.back)
        self.notes_input = QTextEdit(self.notes)
        self.img_input = QLineEdit(self.image_path)
        self.img_input.setReadOnly(True)
        img_btn = QPushButton('Upload Image')
        img_btn.clicked.connect(self.upload_image)
        form.addRow('Word / Phrase:', self.front_input)
        form.addRow('Meaning / Answer:', self.back_input)
        form.addRow('Notes / Example:', self.notes_input)
        h = QHBoxLayout(); h.addWidget(self.img_input); h.addWidget(img_btn)
        form.addRow('Image:', h)
        layout.addLayout(form)
        self.preview = QLabel('Card preview'); self.preview.setFrameShape(QFrame.Shape.Box)
        self.preview.setFixedHeight(140); self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(QLabel('Preview:'))
        layout.addWidget(self.preview)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.front_input.textChanged.connect(self._update_preview)
        self.back_input.textChanged.connect(self._update_preview)
        self.notes_input.textChanged.connect(self._update_preview)
        self._update_preview()

    def upload_image(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select image', '', 'Images (*.png *.jpg *.jpeg *.bmp)')
        if path:
            stored = copy_image_to_storage(path)
            if stored:
                self.img_input.setText(stored)
                self._update_preview()

    def _update_preview(self):
        text = f"<b>{self.front_input.text()}</b><br/><i>{self.back_input.toPlainText()[:120]}</i>"
        if self.img_input.text():
            pix = QPixmap(self.img_input.text())
            if not pix.isNull():
                scaled = pix.scaledToHeight(80, Qt.TransformationMode.SmoothTransformation)
                self.preview.setPixmap(scaled)
                return
        self.preview.setText(text)

    def get_values(self):
        return {
            'front': self.front_input.text().strip(),
            'back': self.back_input.toPlainText().strip(),
            'notes': self.notes_input.toPlainText().strip(),
            'image_path': self.img_input.text().strip()
        }