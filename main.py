import sys
from PyQt6.QtWidgets import QApplication
from gene_app import GeneApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gene_app = GeneApp()
    gene_app.show()
    sys.exit(app.exec())