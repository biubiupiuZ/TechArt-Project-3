from __builtin__ import long
from PySide2 import QtWidgets, QtCore, QtGui
import pymel.core as pm
from functools import partial
import os
import json
import time
from shiboken2 import wrapInstance
from maya import OpenMayaUI as omui

import logging

logging.basicConfig()
logger = logging.getLogger('LightingManager')
logger.setLevel(logging.DEBUG)



def getMayaMainWindow():
    # Get Maya main window through OpenMayaUI API
    win = omui.MQtUtil_mainWindow()
    ptr = wrapInstance(long(win), QtWidgets.QMainWindow)
    return ptr


def getDock(name='LightingManagerDock'):
    deleteDock(name)
    ctrl = pm.workspaceControl(name, dockToMainWindow=('right', 1), label="Lighting Manager")
    # Get Qt info from OpenMayaUI API
    qtCtrl = omui.MQtUtil_findControl(ctrl)
    ptr = wrapInstance(long(qtCtrl), QtWidgets.QWidget)
    return ptr


def deleteDock(name='LightingManagerDock'):
    if pm.workspaceControl(name, query=True, exists=True):
        pm.deleteUI(name)


class LightManager(QtWidgets.QWidget):
    lightTypes = {
        "Point Light": pm.pointLight,
        "Spot Light": pm.spotLight,
        "Direction Light": pm.directionalLight,
        "Area Light": partial(pm.shadingNode, 'areaLight', asLight=True),
        "Volume Light": partial(pm.shadingNode, 'volumeLight', asLight=True),
    }

    def __init__(self, dock=True):
        # parent = getMayaMainWindow()
        if dock:
            parent = getDock()
        else:
            deleteDock()

            try:
                pm.deleteUI('lightingManager')

            except:
                logger.debug('No previous UI exists')

            parent = QtWidgets.QDialog(parent=getMayaMainWindow())
            parent.setObjectName('lightingManager')
            parent.setWindowTitle('Lighting Manager')
            layout = QtWidgets.QVBoxLayout(parent)


        super(LightManager, self).__init__(parent=parent)
        self.buildUI()
        self.populate()

        self.parent().layout().addWidget(self)

        if not dock:
            parent.show()

    def populate(self):
        while self.scrollLayout.count():

            widget = self.scrollLayout.takeAt(0).widget()
            if widget:
                widget.setVisible(False)
                widget.deleteLater()

        # Loop all light element in sense
        for light in pm.ls(type=["areaLight", "spotLight", "pointLight", "directionalLight", "volumeLight"]):
            self.addLight(light)

    def buildUI(self):
        layout = QtWidgets.QGridLayout(self)

        self.lightTypeCB = QtWidgets.QComboBox()
        for lightType in sorted(self.lightTypes):
            self.lightTypeCB.addItem(lightType)

        layout.addWidget(self.lightTypeCB, 0, 0, 1, 2)

        createBtn = QtWidgets.QPushButton('Create')
        createBtn.clicked.connect(self.createLight)
        layout.addWidget(createBtn, 0, 2)

        scrollWidget = QtWidgets.QWidget()

        scrollWidget.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        self.scrollLayout = QtWidgets.QVBoxLayout(scrollWidget)

        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setWidget(scrollWidget)
        layout.addWidget(scrollArea, 1, 0, 1, 3)

        saveBtn = QtWidgets.QPushButton('Save')
        saveBtn.clicked.connect(self.saveLights)
        layout.addWidget(saveBtn, 2, 0)

        importBtn = QtWidgets.QPushButton('Import')
        importBtn.clicked.connect(self.importLights)
        layout.addWidget(importBtn, 2, 1)

        refreshBtn = QtWidgets.QPushButton('Refresh')
        refreshBtn.clicked.connect(self.populate)
        layout.addWidget(refreshBtn, 2, 2)

    def saveLights(self):
        # save data sa json

        properties = {}

        for lightWidget in self.findChildren(LightWidget):
            # Get light transform attr
            light = lightWidget.light
            transform = light.getTransform()

            # Save data in properties
            properties[str(transform)] = {
                'translate': list(transform.translate.get()),
                'rotate': list(transform.rotate.get()),
                'lightType': pm.objectType(light),
                'intensity': light.intensity.get(),
                'color': light.color.get()
            }

        # Set saved file path
        directory = self.getDirectory()

        # Set saved file name
        lightFile = os.path.join(directory, 'lightFile_%s.json' % time.strftime('%m%d'))

        # Save as json
        with open(lightFile, 'w') as f:
            json.dump(properties, f, indent=4)

        logger.info('Saving file to %s' % lightFile)

    def getDirectory(self):
        # Get saved file path
        directory = os.path.join(pm.internalVar(userAppDir=True), 'lightManager')
        if not os.path.exists(directory):
            os.mkdir(directory)
        return directory

    def importLights(self):
        # Read json file

        # Get saved file path
        directory = self.getDirectory()
        # Open a new window to locate json file
        fileName = QtWidgets.QFileDialog.getOpenFileName(self, "light Browser", directory)

        # Read json data
        with open(fileName[0], 'r') as f:
            properties = json.load(f)

        # Generate light based on json file
        for light, info in properties.items():
            # Get light type
            lightType = info.get('lightType')
            for lt in self.lightTypes:
                if ('%sLight' % lt.split()[0].lower()) == lightType:
                    break
            else:
                logger.info('Cannot find a corresponding light type for %s (%s)' % (light, lightType))
                continue

            # create the light
            light = self.createLight(lightType=lt)

            # Set json data into attr
            light.intensity.set(info.get('intensity'))

            light.color.set(info.get('color'))

            transform = light.getTransform()
            transform.translate.set(info.get('translate'))
            transform.rotate.set(info.get('rotate'))

        # Refresh
        self.populate()

    def createLight(self, lightType=None, add=True):
        # Create light
        if not lightType:
            lightType = self.lightTypeCB.currentText()

        func = self.lightTypes[lightType]
        light = func()

        if add:
            self.addLight(light)

        return light

    def addLight(self, light):
        widget = LightWidget(light)
        self.scrollLayout.addWidget(widget)
        widget.onSolo.connect(self.onSolo)

    def onSolo(self, value):
        lightWidgets = self.findChildren(LightWidget)

        # loop all widget
        for widget in lightWidgets:
            if widget != self.sender():
                widget.disableLight(value)


class LightWidget(QtWidgets.QWidget):
    onSolo = QtCore.Signal(bool)

    def __init__(self, light):
        super(LightWidget, self).__init__()
        # Switch to pymel, if light is string
        if isinstance(light, basestring):
            logger.debug('Converting node to a PyNode')
            light = pm.PyNode(light)

        # Jump to shape node, if selected is transform node
        if isinstance(light, pm.nodetypes.Transform):
            light = light.getShape()

        # Save shape node
        self.light = light
        self.buildUI()

    def buildUI(self):
        layout = QtWidgets.QGridLayout(self)

        self.name = QtWidgets.QCheckBox(str(self.light.getTransform()))
        self.name.setChecked(self.light.visibility.get())
        self.name.toggled.connect(lambda val: self.light.getTransform().visibility.set(val))
        layout.addWidget(self.name, 0, 0)

        # SoloBtn
        soloBtn = QtWidgets.QPushButton('Solo')
        soloBtn.setCheckable(True)
        soloBtn.toggled.connect(lambda val: self.onSolo.emit(val))
        layout.addWidget(soloBtn, 0, 1)

        # Delete Btn
        deleteBtn = QtWidgets.QPushButton('Delete')
        deleteBtn.clicked.connect(self.deleteLight)
        deleteBtn.setMaximumWidth(60)
        layout.addWidget(deleteBtn, 0, 2)

        # Intensity slider
        intensity = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        intensity.setMinimum(1)
        intensity.setMaximum(1000)
        intensity.setValue(self.light.intensity.get())
        intensity.valueChanged.connect(lambda val: self.light.intensity.set(val))
        layout.addWidget(intensity, 1, 0, 1, 2)

        # Color Btn
        self.colorBtn = QtWidgets.QPushButton()
        self.colorBtn.setMaximumWidth(20)
        self.colorBtn.setMaximumHeight(20)
        self.setButtonColor()
        self.colorBtn.clicked.connect(self.setColor)
        layout.addWidget(self.colorBtn, 1, 2)

    def setButtonColor(self, color=None):
        # Get light color, if no choose color
        if not color:
            color = self.light.color.get()

        # if not len(color) == 3:
        #       raise Exception("You must provide a list of 3 colors")
        assert len(color) == 3, "You must provide a list of 3 colors"

        # Set color data into r,g,b
        r, g, b = [c * 255 for c in color]
        self.colorBtn.setStyleSheet('background-color:rgba(%s,%s,%s,1)' % (r, g, b))

    def setColor(self):
        # Get current light color
        lightColor = self.light.color.get()
        # Open Maya colorEditor
        color = pm.colorEditor(rgbValue=lightColor)

        # Maya will return string, set them as variable
        r, g, b, a = [float(c) for c in color.split()]

        # Save and set new color
        color = (r, g, b)
        self.light.color.set(color)
        self.setButtonColor(color)

    def disableLight(self, value):
        self.name.setChecked(not bool(value))

    def deleteLight(self):
        self.setParent(None)
        self.setVisible(False)
        self.deleteLater()

        pm.delete(self.light.getTransform())