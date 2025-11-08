from PyQt6.QtWidgets import QApplication
import sys
from ui.login_window import LoginWindow
from ui.main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    login = LoginWindow()
    if login.exec() == LoginWindow.DialogCode.Accepted:
        user_id = login.user_id
        w = MainWindow(user_id)
        w.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)
