from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QPushButton, QLabel, QDialogButtonBox, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from core.settings import IMG_DIR
from pathlib import Path
import shutil
from datetime import datetime

class AddCardDialog(QDialog):
    def __init__(self, parent=None, front='', back='', notes='', image_path=''):
        super().__init__(parent)
        self.setWindowTitle('Add / Edit Card')
        self.front = front; self.back = back; self.notes = notes; self.image_path = image_path
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(); form = QFormLayout()
        self.front_input = QLineEdit(self.front)
        self.back_input = QTextEdit(self.back)
        self.notes_input = QTextEdit(self.notes)
        self.img_input = QLineEdit(self.image_path); self.img_input.setReadOnly(True)
        upload_btn = QPushButton('Upload Image'); upload_btn.clicked.connect(self.upload_image)
        form.addRow('Word / Phrase:', self.front_input)
        form.addRow('Meaning / Answer:', self.back_input)
        form.addRow('Notes:', self.notes_input)

        # image controls
        form.addRow('Image:', self.img_input)
        form.addRow('', upload_btn)

        layout.addLayout(form)

        # preview
        self.preview = QLabel('Preview'); self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setFixedHeight(120); layout.addWidget(self.preview)
        # buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons); self.setLayout(layout)
        # update preview
        self.front_input.textChanged.connect(self._update_preview); self.back_input.textChanged.connect(self._update_preview)
        self._update_preview()

    def upload_image(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select image', str(Path.home()), 'Images (*.png *.jpg *.jpeg *.bmp)')
        if path:
            dest = IMG_DIR / f"{int(datetime.utcnow().timestamp())}_{Path(path).name}"
            shutil.copy(path, dest)
            self.img_input.setText(str(dest)); self._update_preview()

    def _update_preview(self):
        text = f"{self.front_input.text()}\n{self.back_input.toPlainText()[:120]}"
        if self.img_input.text():
            pix = QPixmap(self.img_input.text())
            if not pix.isNull():
                self.preview.setPixmap(pix.scaledToHeight(100))
                return
        self.preview.setText(text)

    def get_values(self):
        return {
            'front': self.front_input.text().strip(),
            'back': self.back_input.toPlainText().strip(),
            'notes': self.notes_input.toPlainText().strip(),
            'image_path': self.img_input.text().strip()
        }
