from PyQt6.QtWidgets import QLabel

class GeneLabel(QLabel):
    def __init__(self, gene):
        super().__init__(gene)
        self.active = True  # Flag active gene (for filtering functionality)