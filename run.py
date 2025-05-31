from PyQt5.QtWidgets import QApplication
import sys
from modules.main import MainApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())