import sys
from PyQt6.QtWidgets import QApplication
from flashcard_app import FlashcardApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    flashcard_app = FlashcardApp()
    flashcard_app.show()
    sys.exit(app.exec())
