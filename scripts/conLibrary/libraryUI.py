import pprint
from PySide2 import QtWidgets, QtCore, QtGui
from maya import cmds

import controllerLib
reload(controllerLib)


class ControllerLibraryUI(QtWidgets.QDialog):
    """
    The ControllerLibraryUI is a dialog that lets us know save and import ctrls
    """

    def __init__(self):
        super(ControllerLibraryUI, self).__init__()

        self.setWindowTitle('Asset Library')

        # The library variable points to an instance of our controller library
        self.library = controllerLib.ControllerLibrary()

        # Every time we create a new instance, we will automatically build UI and populate it
        self.buildUI()
        self.populate()

    def buildUI(self):
        """This method build out UI"""
        #This is master layout
        layout = QtWidgets.QVBoxLayout(self)

        # This is child horizontal widget
        saveWidget = QtWidgets.QWidget()
        saveLayout = QtWidgets.QHBoxLayout(saveWidget)
        layout.addWidget(saveWidget)

        self.saveNameField = QtWidgets.QLineEdit()
        saveLayout.addWidget(self.saveNameField)

        saveBtn = QtWidgets.QPushButton('Save')
        saveBtn.clicked.connect(self.save)
        saveLayout.addWidget(saveBtn)

        # These are parameters for our thumbnail size
        size = 74
        buffer = 12

        # This will create a grid list widget to display our controller thumbnails
        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.setViewMode(QtWidgets.QListWidget.IconMode)
        self.listWidget.setIconSize(QtCore.QSize(size, size))
        self.listWidget.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.listWidget.setGridSize(QtCore.QSize(size+buffer, size+buffer))
        layout.addWidget(self.listWidget)

        # This is our widget that holds all the buttons
        btnWidget = QtWidgets.QWidget()
        btnLayout = QtWidgets.QHBoxLayout(btnWidget)
        layout.addWidget(btnWidget)

        importBtn = QtWidgets.QPushButton('Import')
        importBtn.clicked.connect(self.load)
        btnLayout.addWidget(importBtn)

        refreshBtn = QtWidgets.QPushButton('Refresh')
        refreshBtn.clicked.connect(self.populate)
        btnLayout.addWidget(refreshBtn)

        closeBtn = QtWidgets.QPushButton('Close')
        closeBtn.clicked.connect(self.close)
        btnLayout.addWidget(closeBtn)

    def populate(self):
        """This clears the listWidget and then repopulates it with the contents of our lib"""
        self.listWidget.clear()
        self.library.find()

        for name, info in self.library.items():
            item = QtWidgets.QListWidgetItem(name)
            self.listWidget.addItem(item)

            screenshot = info.get('screenshot')
            if screenshot:
                icon = QtGui.QIcon(screenshot)
                item.setIcon(icon)

            item.setToolTip(pprint.pformat(info))

    def load(self):
        """This loads the current selected controller"""
        currentItem = self.listWidget.currentItem()

        if not currentItem:
            return

        name = currentItem.text()
        self.library.load(name)

    def save(self):
        """This saves the controller with given file name"""
        name = self.saveNameField.text()
        if not name.strip():
            cmds.warning("Plz give a name")
            return
        self.library.save(name)
        self.populate()
        self.saveNameField.setText('')
        print("Name:" + str(name))


def showUI():
    """
    This shows and returns a handle to the UI
    Returns:
        QDialog
    """
    ui = ControllerLibraryUI()
    ui.show()
    return ui