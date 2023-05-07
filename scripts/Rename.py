import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore


class RenameUI(QtWidgets.QWidget):
    def __init__(self):
        super(RenameUI, self).__init__()
        self.setWindowTitle('Rename Tool')
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.buildUI()

    def buildUI(self):
        """This method build out UI"""
        # Create controls
        self.guide01_label = QtWidgets.QLabel('Plz select the obj you want to rename')
        self.rename_label = QtWidgets.QLabel('New Name:')
        self.rename_field = QtWidgets.QLineEdit()
        self.rename_button = QtWidgets.QPushButton('Rename')

        spacer = QtWidgets.QSpacerItem(10, 30, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        self.guide02_label = QtWidgets.QLabel('Plz type the word you want to replace')
        self.search_label = QtWidgets.QLabel('Search Name:')
        self.search_field = QtWidgets.QLineEdit()
        self.replace_label = QtWidgets.QLabel('Replace Name:')
        self.replace_field = QtWidgets.QLineEdit()

        self.replace_button = QtWidgets.QPushButton('Rename')

        # Set layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.guide01_label)
        layout.addWidget(self.rename_label)
        layout.addWidget(self.rename_field)
        layout.addWidget(self.rename_button)
        layout.addItem(spacer)
        layout.addWidget(self.guide02_label)
        layout.addWidget(self.search_label)
        layout.addWidget(self.search_field)
        layout.addWidget(self.replace_label)
        layout.addWidget(self.replace_field)
        layout.addWidget(self.replace_button)
        self.setLayout(layout)
        self.setLayout(layout)

        # Set connections
        self.rename_button.clicked.connect(self.rename)
        self.replace_button.clicked.connect(self.replace)

    def rename(self):
        """Rename selected object"""
        # Get new name from field
        new_name = self.rename_field.text()

        # Get selected objects
        selected_objects = cmds.ls(selection=True)

        # Rename selected objects
        for obj in selected_objects:
            cmds.rename(obj, new_name)

    def replace(self):
        """Search all objects and replace the same word"""
        search_name = self.search_field.text()
        replace_name = self.replace_field.text()
        all_objects = cmds.ls()
        objects_to_rename = []

        for obj in all_objects:
            if search_name in obj:
                objects_to_rename.append(obj)

        for obj in objects_to_rename:
            new_replace_name = obj.replace(search_name, replace_name)
            try:
                cmds.rename(obj, new_replace_name)
            except:
                print("Failed to rename object: {}".format(obj))


def showUI():
    """
    This shows and returns a handle to the UI
    Returns:
        QDialog
    """
    ui = RenameUI()
    ui.show()
    return ui