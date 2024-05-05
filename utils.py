from PyQt6.QtWidgets import QMessageBox

def confirmation_dialog(message, parent=None):
    dialog = QMessageBox(parent)
    dialog.setIcon(QMessageBox.Icon.Warning)
    dialog.setWindowTitle("Confirmation")
    dialog.setText(message)
    dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    return dialog.exec()
