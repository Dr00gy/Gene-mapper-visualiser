from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QFrame, QMessageBox, QGridLayout, QDialog, QCheckBox

def create_vertical_layout(parent=None):
    layout = QVBoxLayout(parent)
    return layout

def create_horizontal_layout(parent=None):
    layout = QHBoxLayout(parent)
    return layout
