#coding:utf-8
from maya import cmds


def tween(percentage, obj=None, attrs=None, selection=True):

    if not obj and not selection:
        raise ValueError("No object given to tween")


    if not obj:
        obj = cmds.ls(sl=1)[0]


    if not attrs:
        attrs = cmds.listAttr(obj, keyable=True)

    # Get current time
    currentTime = cmds.currentTime(query=True)

    # Loop all attrs
    for attr in attrs:
        # Get full name
        attrFull = '%s.%s' % (obj, attr)

        # check keyframe
        keyframes = cmds.keyframe(attrFull, query=True)

        if not keyframes:
            continue

        # save previous keyframes in list
        previousKeyframes = []

        for k in keyframes:
            if k < currentTime:
                previousKeyframes.append(k)

        laterKeyframes = [frame for frame in keyframes if frame > currentTime]

        if not previousKeyframes and not laterKeyframes:
            continue

        if previousKeyframes:
            previousFrame = max(previousKeyframes)
        else:
            previousFrame = None

        nextFrame = min(laterKeyframes) if laterKeyframes else None

        if previousFrame is None:
            previousFrame = nextFrame

        nextFrame = previousFrame if nextFrame is None else nextFrame

        previousValue = cmds.getAttr(attrFull, time=previousFrame)
        nextValue = cmds.getAttr(attrFull, time=nextFrame)

        if nextFrame is None:
            currentValue = previousValue
        elif previousFrame is None:
            currentValue = nextValue
        elif previousValue == nextValue:
            currentValue = previousValue
        else:
            difference = nextValue - previousValue
            biasedDifference = (difference * percentage) / 100.0
            currentValue = previousValue + biasedDifference

        cmds.setAttr(attrFull, currentValue)
        cmds.setKeyframe(attrFull, time=currentTime, value=currentValue)


class TweenerWindow(object):
    windowName = "TweenerWindow"

    def show(self):
        if cmds.window(self.windowName, query=True, exists=True):
            cmds.deleteUI(self.windowName)

        cmds.window(self.windowName)

        self.buildUI()

        cmds.showWindow()

    def buildUI(self):
        column = cmds.columnLayout()
        cmds.text(label="Use this slider to set the tween amount")

        row = cmds.rowLayout(numberOfColumns=2)

        # create slider
        self.slider = cmds.floatSlider(min=-500, max=500, value=500, step=1, changeCommand=tween)

        cmds.button(label="Reset", command=self.reset)
        cmds.setParent(column)

        cmds.button(label="Close", command=self.close)

    def reset(self, *args):
        cmds.floatSlider(self.slider, edit=True, value=50)

    def close(self, *args):
        cmds.deleteUI(self.windowName)