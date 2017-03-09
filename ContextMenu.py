from pandac.PandaModules import *
from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame,DirectButton,DirectScrolledFrame,DGG ,OnscreenText
from direct.interval.IntervalGlobal import Sequence
from direct.task import Task
from types import IntType


SEQUENCE_TYPES=(tuple,list)
atLeast16=PandaSystem.getMajorVersion()*10+PandaSystem.getMinorVersion()>=16
asList=lambda nc: nc if atLeast16 else nc.asList()


class ScrolledButtonsList(DirectObject):
  """
     A class to display a list of selectable buttons.
     It is displayed using scrollable window (DirectScrolledFrame).
  """
  def __init__(self, parent=None, frameSize=(.8,1.2), buttonTextColor=(1,1,1,1),
               font=None, itemScale=.045, itemTextScale=1, itemTextZ=0,
               command=None, contextMenu=None, autoFocus=0,
               colorChange=1, colorChangeDuration=1.0, newItemColor=(0,1,0,1),
               rolloverColor=Vec4(1,.8,.2,1),
               suppressMouseWheel=1, modifier='control'):
      self.focusButton=None
      self.command=command
      self.contextMenu=contextMenu
      self.autoFocus=autoFocus
      self.colorChange=colorChange
      self.colorChangeDuration=colorChangeDuration*.5
      self.newItemColor=Vec4(*newItemColor)
      self.rolloverColor=Vec4(*rolloverColor)
      self.rightClickTextColors=(Vec4(0,1,0,1),Vec4(0,35,100,1))
      self.font=font
      if font:
         self.fontHeight=font.getLineHeight()
      else:
         self.fontHeight=TextNode.getDefaultFont().getLineHeight()
      self.fontHeight*=1.2 # let's enlarge font height a little
      self.xtraSideSpace=.2*self.fontHeight
      self.itemTextScale=itemTextScale
      self.itemTextZ=itemTextZ
      self.buttonTextColor=buttonTextColor
      self.suppressMouseWheel=suppressMouseWheel
      self.modifier=modifier
      self.buttonsList=[]
      self.numItems=0
      self.__eventReceivers={}
      # DirectScrolledFrame to hold items
      self.itemScale=itemScale
      self.itemVertSpacing=self.fontHeight*self.itemScale
      self.frameWidth,self.frameHeight=frameSize
      # I set canvas' Z size smaller than the frame to avoid the auto-generated vertical slider bar
      self.frame = DirectScrolledFrame(
                   parent=parent,pos=(-self.frameWidth*.5,0,.5*self.frameHeight), relief=DGG.GROOVE,
                   state=DGG.NORMAL, # to create a mouse watcher region
                   frameSize=(0, self.frameWidth, -self.frameHeight, 0), frameColor=(0,0,0,.7),
                   canvasSize=(0, 0, -self.frameHeight*.5, 0), borderWidth=(0.01,0.01),
                   manageScrollBars=0, enableEdit=0, suppressMouse=0, sortOrder=-1 )
      # the real canvas is "self.frame.getCanvas()",
      # but if the frame is hidden since the beginning,
      # no matter how I set the canvas Z pos, the transform would be resistant,
      # so just create a new node under the canvas to be my canvas
      self.canvas=self.frame.getCanvas().attachNewNode('myCanvas')
      # slider background
      SliderBG=DirectFrame( parent=self.frame,frameSize=(-.025,.025,-self.frameHeight,0),
                   frameColor=(0,0,0,.7), pos=(-.03,0,0),enableEdit=0, suppressMouse=0)
      # slider thumb track
      sliderTrack = DirectFrame( parent=SliderBG, relief=DGG.FLAT, #state=DGG.NORMAL,
                   frameColor=(1,1,1,.2), frameSize=(-.015,.015,-self.frameHeight+.01,-.01),
                   enableEdit=0, suppressMouse=0)
      # page up
      self.pageUpRegion=DirectFrame( parent=SliderBG, relief=DGG.FLAT, state=DGG.NORMAL,
                   frameColor=(1,.8,.2,.1), frameSize=(-.015,.015,0,0),
                   enableEdit=0, suppressMouse=0)
      self.pageUpRegion.setAlphaScale(0)
      self.pageUpRegion.bind(DGG.B1PRESS,self.__startScrollPage,[-1])
      self.pageUpRegion.bind(DGG.WITHIN,self.__continueScrollUp)
      self.pageUpRegion.bind(DGG.WITHOUT,self.__suspendScrollUp)
      # page down
      self.pageDnRegion=DirectFrame( parent=SliderBG, relief=DGG.FLAT, state=DGG.NORMAL,
                   frameColor=(1,.8,.2,.1), frameSize=(-.015,.015,0,0),
                   enableEdit=0, suppressMouse=0)
      self.pageDnRegion.setAlphaScale(0)
      self.pageDnRegion.bind(DGG.B1PRESS,self.__startScrollPage,[1])
      self.pageDnRegion.bind(DGG.WITHIN,self.__continueScrollDn)
      self.pageDnRegion.bind(DGG.WITHOUT,self.__suspendScrollDn)
      self.pageUpDnSuspended=[0,0]
      # slider thumb
      self.vertSliderThumb=DirectButton(parent=SliderBG, relief=DGG.FLAT,
                   frameColor=(1,1,1,.6), frameSize=(-.015,.015,0,0),
                   enableEdit=0, suppressMouse=0)
      self.vertSliderThumb.bind(DGG.B1PRESS,self.__startdragSliderThumb)
      self.vertSliderThumb.bind(DGG.WITHIN,self.__enteringThumb)
      self.vertSliderThumb.bind(DGG.WITHOUT,self.__exitingThumb)
      self.oldPrefix=base.buttonThrowers[0].node().getPrefix()
      self.sliderThumbDragPrefix='draggingSliderThumb-'
      # GOD & I DAMN IT !!!
      # These things below don't work well if the canvas has a lot of buttons.
      # So I end up checking the mouse region every frame by myself using a continuous task.
#       self.accept(DGG.WITHIN+self.frame.guiId,self.__enteringFrame)
#       self.accept(DGG.WITHOUT+self.frame.guiId,self.__exitingFrame)
      self.isMouseInRegion=False
      self.mouseOutInRegionCommand=(self.__exitingFrame,self.__enteringFrame)
      taskMgr.doMethodLater(.2,self.__getFrameRegion,'getFrameRegion')

  def __getFrameRegion(self,t):
      for g in range(base.mouseWatcherNode.getNumGroups()):
          region=base.mouseWatcherNode.getGroup(g).findRegion(self.frame.guiId)
          if region!=None:
             self.frameRegion=region
             taskMgr.add(self.__mouseInRegionCheck,'mouseInRegionCheck')
             break

  def __mouseInRegionCheck(self,t):
      """
         check if the mouse is within or without the scrollable frame, and
         upon within or without, run the provided command
      """
      if not base.mouseWatcherNode.hasMouse(): return Task.cont
      m=base.mouseWatcherNode.getMouse()
      bounds=self.frameRegion.getFrame()
      inRegion=bounds[0]<m[0]<bounds[1] and bounds[2]<m[1]<bounds[3]
      if self.isMouseInRegion==inRegion: return Task.cont
      self.isMouseInRegion=inRegion
      self.mouseOutInRegionCommand[inRegion]()
      return Task.cont

  def __startdragSliderThumb(self,m=None):
      mpos=base.mouseWatcherNode.getMouse()
      parentZ=self.vertSliderThumb.getParent().getZ(render2d)
      sliderDragTask=taskMgr.add(self.__dragSliderThumb,'dragSliderThumb')
      sliderDragTask.ZposNoffset=mpos[1]-self.vertSliderThumb.getZ(render2d)+parentZ
#       sliderDragTask.mouseX=base.winList[0].getPointer(0).getX()
      self.oldPrefix=base.buttonThrowers[0].node().getPrefix()
      base.buttonThrowers[0].node().setPrefix(self.sliderThumbDragPrefix)
      self.acceptOnce(self.sliderThumbDragPrefix+'mouse1-up',self.__stopdragSliderThumb)

  def __dragSliderThumb(self,t):
      if not base.mouseWatcherNode.hasMouse():
         return
      mpos=base.mouseWatcherNode.getMouse()
#       newY=base.winList[0].getPointer(0).getY()
      self.__updateCanvasZpos((t.ZposNoffset-mpos[1])/self.canvasRatio)
#       base.winList[0].movePointer(0, t.mouseX, newY)
      return Task.cont

  def __stopdragSliderThumb(self,m=None):
      taskMgr.remove('dragSliderThumb')
      self.__stopScrollPage()
      base.buttonThrowers[0].node().setPrefix(self.oldPrefix)
      if self.isMouseInRegion:
         self.mouseOutInRegionCommand[self.isMouseInRegion]()

  def __startScrollPage(self,dir,m):
      self.oldPrefix=base.buttonThrowers[0].node().getPrefix()
      base.buttonThrowers[0].node().setPrefix(self.sliderThumbDragPrefix)
      self.acceptOnce(self.sliderThumbDragPrefix+'mouse1-up',self.__stopdragSliderThumb)
      t=taskMgr.add(self.__scrollPage,'scrollPage',extraArgs=[int((dir+1)*.5),dir*.01/self.canvasRatio])
      self.pageUpDnSuspended=[0,0]

  def __scrollPage(self,dir,scroll):
      if not self.pageUpDnSuspended[dir]:
         self.__scrollCanvas(scroll)
      return Task.cont

  def __stopScrollPage(self,m=None):
      taskMgr.remove('scrollPage')

  def __suspendScrollUp(self,m=None):
      self.pageUpRegion.setAlphaScale(0)
      self.pageUpDnSuspended[0]=1
  def __continueScrollUp(self,m=None):
      if taskMgr.hasTaskNamed('dragSliderThumb'):
         return
      self.pageUpRegion.setAlphaScale(1)
      self.pageUpDnSuspended[0]=0

  def __suspendScrollDn(self,m=None):
      self.pageDnRegion.setAlphaScale(0)
      self.pageUpDnSuspended[1]=1
  def __continueScrollDn(self,m=None):
      if taskMgr.hasTaskNamed('dragSliderThumb'):
         return
      self.pageDnRegion.setAlphaScale(1)
      self.pageUpDnSuspended[1]=0

  def __suspendScrollPage(self,m=None):
      self.__suspendScrollUp()
      self.__suspendScrollDn()

  def __enteringThumb(self,m=None):
      self.vertSliderThumb['frameColor']=(1,1,1,1)
      self.__suspendScrollPage()

  def __exitingThumb(self,m=None):
      self.vertSliderThumb['frameColor']=(1,1,1,.6)

  def __scrollCanvas(self,scroll):
      if self.vertSliderThumb.isHidden():
         return
      self.__updateCanvasZpos(self.canvas.getZ()+scroll)

  def __updateCanvasZpos(self,Zpos):
      newZ=clamp(Zpos, .0, self.canvasLen-self.frameHeight+.015)
      self.canvas.setZ(newZ)
      thumbZ=-newZ*self.canvasRatio
      self.vertSliderThumb.setZ(thumbZ)
      self.pageUpRegion['frameSize']=(-.015,.015,thumbZ-.01,-.01)
      self.pageDnRegion['frameSize']=(-.015,.015,-self.frameHeight+.01,thumbZ+self.vertSliderThumb['frameSize'][2])

  def __adjustCanvasLength(self,numItem):
      self.canvasLen=float(numItem)*self.itemVertSpacing
      self.canvasRatio=(self.frameHeight-.015)/(self.canvasLen+.01)
      if self.canvasLen<=self.frameHeight-.015:
         canvasZ=.0
         self.vertSliderThumb.hide()
         self.pageUpRegion.hide()
         self.pageDnRegion.hide()
         self.canvasLen=self.frameHeight-.015
      else:
         canvasZ=self.canvas.getZ()
         self.vertSliderThumb.show()
         self.pageUpRegion.show()
         self.pageDnRegion.show()
      self.__updateCanvasZpos(canvasZ)
      self.vertSliderThumb['frameSize']=(-.015,.015,-self.frameHeight*self.canvasRatio,-.01)
      thumbZ=self.vertSliderThumb.getZ()
      self.pageUpRegion['frameSize']=(-.015,.015,thumbZ-.01,-.01)
      self.pageDnRegion['frameSize']=(-.015,.015,-self.frameHeight+.01,thumbZ+self.vertSliderThumb['frameSize'][2])

  def __acceptAndIgnoreWorldEvent(self,event,command,extraArgs=[]):
      receivers=messenger.whoAccepts(event)
      if receivers is None:
         self.__eventReceivers[event]={}
      else:
         newD={}
         for r in receivers:
             newr=messenger._getObject(r) if type(r)==tuple else r
             newD[newr]=receivers[r]
         self.__eventReceivers[event]=newD
      for r in self.__eventReceivers[event].keys():
          r.ignore(event)
      self.accept(event,command,extraArgs)

  def __ignoreAndReAcceptWorldEvent(self,events):
      for event in events:
          self.ignore(event)
          if self.__eventReceivers.has_key(event):
             for r, method_xtraArgs_persist in self.__eventReceivers[event].items():
                 messenger.accept(event,r,*method_xtraArgs_persist)
          self.__eventReceivers[event]={}

  def __enteringFrame(self,m=None):
      # sometimes the WITHOUT event for page down region doesn't fired,
      # so directly suspend the page scrolling here
      self.__suspendScrollPage()
      BTprefix=base.buttonThrowers[0].node().getPrefix()
      if BTprefix==self.sliderThumbDragPrefix:
         return
      self.inOutBTprefix=BTprefix
      if self.suppressMouseWheel:
         self.__acceptAndIgnoreWorldEvent(self.inOutBTprefix+'wheel_up',
              command=self.__scrollCanvas, extraArgs=[-.07])
         self.__acceptAndIgnoreWorldEvent(self.inOutBTprefix+'wheel_down',
              command=self.__scrollCanvas, extraArgs=[.07])
      else:
         self.accept(self.inOutBTprefix+self.modifier+'-wheel_up',self.__scrollCanvas, [-.07])
         self.accept(self.inOutBTprefix+self.modifier+'-wheel_down',self.__scrollCanvas, [.07])
      print 'enteringFrame'

  def __exitingFrame(self,m=None):
      if not hasattr(self,'inOutBTprefix'):
         return
      if self.suppressMouseWheel:
         self.__ignoreAndReAcceptWorldEvent( (
                                             self.inOutBTprefix+'wheel_up',
                                             self.inOutBTprefix+'wheel_down',
                                             ) )
      else:
         self.ignore(self.inOutBTprefix+self.modifier+'-wheel_up')
         self.ignore(self.inOutBTprefix+self.modifier+'-wheel_down')
      print 'exitingFrame'

  def __setFocusButton(self,button,item):
      if self.focusButton:
         self.deselect()
      self.focusButton=button
      self.select()
      if callable(self.command):
         # run user command and pass the selected item, it's index, and the button
         self.command(item,self.buttonsList.index(button),button)

  def __rightPressed(self,button,m):
      self.__isRightIn=True
#       text0 : normal
#       text1 : pressed
#       text2 : rollover
#       text3 : disabled
      button._DirectGuiBase__componentInfo['text2'][0].setColorScale(self.rightClickTextColors[self.focusButton==button])
      button.bind(DGG.B3RELEASE,self.__rightReleased,[button])
      button.bind(DGG.WITHIN,self.__rightIn,[button])
      button.bind(DGG.WITHOUT,self.__rightOut,[button])

  def __rightIn(self,button,m):
      self.__isRightIn=True
      button._DirectGuiBase__componentInfo['text2'][0].setColorScale(self.rightClickTextColors[self.focusButton==button])
  def __rightOut(self,button,m):
      self.__isRightIn=False
      button._DirectGuiBase__componentInfo['text2'][0].setColorScale(Vec4(1,1,1,1))

  def __rightReleased(self,button,m):
      button.unbind(DGG.B3RELEASE)
      button.unbind(DGG.WITHIN)
      button.unbind(DGG.WITHOUT)
      button._DirectGuiBase__componentInfo['text2'][0].setColorScale(self.rolloverColor)
      if not self.__isRightIn:
         return
      if callable(self.contextMenu):
         # run user command and pass the selected item, it's index, and the button
         self.contextMenu(button['extraArgs'][1],self.buttonsList.index(button),button)

  def deselect(self):
      """
         stop highlighting item
      """
      if self.focusButton:
         self.focusButton['text_fg']=(1,1,1,1)
         self.focusButton['frameColor']=(0,0,0,0)

  def select(self,idx=None):
      """
         highlight the item
      """
      if idx is not None:
         if not 0<=idx<self.numItems:
            print 'SELECT : invalid index (%s)' %idx
            return
         self.focusButton=self.buttonsList[idx]
      if self.focusButton:
         self.focusButton['text_fg']=(.01,.01,.01,1)
         self.focusButton['frameColor']=(1,.8,.2,1)

  def clear(self):
      """
         clear the list
      """
      for c in self.buttonsList:
          c.remove()
      self.buttonsList=[]
      self.focusButton=None
      self.numItems=0

  def addItem(self,text,extraArgs=None,atIndex=None):
      """
         add item to the list
         text : text for the button
         extraArgs : the object which will be passed to user command(s)
                     (both command and contextMenu) when the button get clicked
         atIndex : where to add the item
                   <None> : put item at the end of list
                   <integer> : put item at index <integer>
                   <button> : put item at <button>'s index
      """
      button = DirectButton(parent=self.canvas,
          scale=self.itemScale,
          relief=DGG.FLAT,
          frameColor=(0,0,0,0),text_scale=self.itemTextScale,
          text=text, text_pos=(0,self.itemTextZ),text_fg=self.buttonTextColor,
          text_font=self.font, text_align=TextNode.ALeft,
          command=self.__setFocusButton,
          enableEdit=0, suppressMouse=0)

      l,r,b,t=button.getBounds()
      # top & bottom are blindly set without knowing where exactly the baseline is,
      # but this ratio fits most fonts
      baseline=-self.fontHeight*.25
      button['frameSize']=(l-self.xtraSideSpace,r+self.xtraSideSpace,baseline,baseline+self.fontHeight)

#          Zc=NodePath(button).getBounds().getCenter()[1]-self.fontHeight*.5+.25
# #          Zc=button.getCenter()[1]-self.fontHeight*.5+.25
#          button['frameSize']=(l-self.xtraSideSpace,r+self.xtraSideSpace,Zc,Zc+self.fontHeight)

      button['extraArgs']=[button,extraArgs]
      button._DirectGuiBase__componentInfo['text2'][0].setColorScale(self.rolloverColor)
      button.bind(DGG.B3PRESS,self.__rightPressed,[button])
      isButton=isinstance(atIndex,DirectButton)
      if isButton:
         if atIndex.isEmpty():
            atIndex=None
         else:
            index=self.buttonsList.index(atIndex)
            self.buttonsList.insert(index,button)
      if atIndex==None:
         self.buttonsList.append(button)
         index=self.numItems
      elif not isButton:
         index=int(atIndex)
         self.buttonsList.insert(index,button)
      Zpos=(-.7-index)*self.itemVertSpacing
      button.setPos(.02,0,Zpos)
      if index!=self.numItems:
         for i in range(index+1,self.numItems+1):
             self.buttonsList[i].setZ(self.buttonsList[i],-self.fontHeight)
      self.numItems+=1
      self.__adjustCanvasLength(self.numItems)
      if self.autoFocus:
         self.focusViewOnItem(index)
      if self.colorChange:
         Sequence(
            button.colorScaleInterval(self.colorChangeDuration,self.newItemColor,Vec4(1,.2,0,1)),
            button.colorScaleInterval(self.colorChangeDuration,Vec4(1,1,1,1),self.newItemColor)
            ).start()

  def focusViewOnItem(self,idx):
      """
         Scroll the window so the newly added item will be displayed
         in the middle of the window, if possible.
      """
      Zpos=(idx+.7)*self.itemVertSpacing-self.frameHeight*.5
      self.__updateCanvasZpos(Zpos)

  def setAutoFocus(self,b):
      """
         set auto-view-focus state of newly added item
      """
      self.autoFocus=b

  def index(self,button):
      """
         get the index of button
      """
      if not button in self.buttonsList:
         return None
      return self.buttonsList.index(button)

  def getSelected(self):
      """
         get the currently selected button,
         returns None if no button is selected
      """
      return self.focusButton

  def getSelectedIndex(self):
      """
         get the currently selected button index,
         returns None if no button is selected
      """
      return self.index(self.focusButton)

  def getNumItems(self):
      """
         get the current number of items on the list
      """
      return self.numItems

  def disableItem(self,i):
      if not 0<=i<self.numItems:
         print 'DISABLING : invalid index (%s)' %i
         return
      self.buttonsList[i]['state']=DGG.DISABLED
      self.buttonsList[i].setColorScale(.3,.3,.3,1)

  def enableItem(self,i):
      if not 0<=i<self.numItems:
         print 'ENABLING : invalid index (%s)' %i
         return
      self.buttonsList[i]['state']=DGG.NORMAL
      self.buttonsList[i].setColorScale(1,1,1,1)

  def removeItem(self,index):
      if not 0<=index<self.numItems:
         print 'REMOVAL : invalid index (%s)' %index
         return
      if self.numItems==0: return
      if self.focusButton==self.buttonsList[index]:
         self.focusButton=None
      self.buttonsList[index].removeNode()
      del self.buttonsList[index]
      self.numItems-=1
      for i in range(index,self.numItems):
          self.buttonsList[i].setZ(self.buttonsList[i],self.fontHeight)
      self.__adjustCanvasLength(self.numItems)

  def destroy(self):
      self.clear()
      self.__exitingFrame()
      self.ignoreAll()
      self.frame.removeNode()
      taskMgr.remove('mouseInRegionCheck')

  def hide(self):
      self.frame.hide()
      self.isMouseInRegion=False
      self.__exitingFrame()
      taskMgr.remove('mouseInRegionCheck')

  def show(self):
      self.frame.show()
      if not hasattr(self,'frameRegion'):
         taskMgr.doMethodLater(.2,self.__getFrameRegion,'getFrameRegion')
      elif not taskMgr.hasTaskNamed('mouseInRegionCheck'):
         taskMgr.add(self.__mouseInRegionCheck,'mouseInRegionCheck')

  def toggleVisibility(self):
      if self.frame.isHidden():
         self.show()
      else:
         self.hide()

  def sort(self,reverse=False):
      buttonsTexts=[(b['text'],b) for b in self.buttonsList]
      buttonsTexts.sort()
      if reverse:
         buttonsTexts.reverse()
      self.buttonsList=[bt[1] for bt in buttonsTexts]
      for i in range(self.getNumItems()):
          Zpos=(-.7-i)*self.itemVertSpacing
          self.buttonsList[i].setPos(.02,0,Zpos)



class PopupMenu(DirectObject):
  '''
  A class to create a popup or context menu.
  Features :
    [1] it's destroyed by pressing ESCAPE, or LMB/RMB click outside of it
    [2] menu item's command is executed by pressing ENTER/RETURN or SPACE when
        it's hilighted
    [3] you can use arrow UP/DOWN to navigate
    [4] separator lines
    [5] menu item image
    [6] menu item hotkey
        If there are more than 1 item using the same hotkey,
        those items will be hilighted in cycle when the hotkey is pressed.
    [7] shortcut key text at the right side of menu item
    [8] multiple lines item text
    [9] menu item can have sub menus
    [10] it's offscreen-proof, try to put your pointer next to screen edge or corner
        before creating it
  '''
  grayImages={} # storage of grayed images,
                # so the same image will be converted to grayscale only once

  def __init__(self,items, parent=None, buttonThrower=None, onDestroy=None,
               font=None, baselineOffset=.0,
               scale=.05, itemHeight=0.9, leftPad=.0, separatorHeight=.5,
               underscoreThickness=1,
               BGColor=(0,0,0,.7),
               BGBorderColor=(1,.85,.4,1),
               separatorColor=(1,1,1,1),
               frameColorHover=(1,.85,.4,1),
               frameColorPress=(0,1,0,1),
               textColorReady=(1,1,1,1),
               textColorHover=(0,0,0,1),
               textColorPress=(0,0,0,1),
               textColorDisabled=(.5,.5,.5,1),
               minZ=None,
               useMouseZ=True
               ):
      '''
      items : a collection of menu items
         Item format :
            ( 'Item text', 'path/to/image', command )
                        OR
            ( 'Item text', 'path/to/image', command, arg1,arg2,.... )
         If you don't want to use an image, pass 0.

         To create disabled item, pass 0 for the command :
            ( 'Item text', 'path/to/image', 0 )
         so, you can easily switch between enabled or disabled :
            ( 'Item text', 'path/to/image', command if commandEnabled else 0 )
                        OR
            ( 'Item text', 'path/to/image', (0,command)[commandEnabled] )

         To create submenu, pass a sequence of submenu items for the command.
         To create disabled submenu, pass an empty sequence for the command.

         To enable hotkey, insert an underscore before the character,
         e.g. hotkey of 'Item te_xt' is 'x' key.

         To add shortcut key text at the right side of the item, append it at the end of
         the item text, separated by "more than" sign, e.g. 'Item text>Ctrl-T'.

         To insert separator line, pass 0 for the whole item.


      parent : where to attach the menu, defaults to aspect2d

      buttonThrower : button thrower whose thrown events are blocked temporarily
                      when the menu is displayed. If not given, the default
                      button thrower is used

      onDestroy : user function which will be called after the menu is fully destroyed

      font           : text font
      baselineOffset : text's baseline Z offset

      scale       : text scale
      itemHeight  : spacing between items, defaults to 1
      leftPad     : blank space width before text
      separatorHeight : separator line height, relative to itemHeight

      underscoreThickness : underscore line thickness

      BGColor, BGBorderColor, separatorColor, frameColorHover, frameColorPress,
      textColorReady, textColorHover, textColorPress, textColorDisabled
      are some of the menu components' color

      minZ : minimum Z position to restrain menu's bottom from going offscreen (-1..1).
             If it's None, it will be set a little above the screen's bottom.
      '''
      self.parent=parent if parent else aspect2d
      self.onDestroy=onDestroy
      self.BT=buttonThrower if buttonThrower else base.buttonThrowers[0].node()
      self.menu=NodePath('menu-%s'%id(self))
      self.parentMenu=None
      self.submenu=None
      self.BTprefix=self.menu.getName()+'>'
      self.submenuCreationTaskName='createSubMenu-'+self.BTprefix
      self.submenuRemovalTaskName='removeSubMenu-'+self.BTprefix
      self.font=font if font else TextNode.getDefaultFont()
      self.baselineOffset=baselineOffset
      self.scale=scale
      self.itemHeight=itemHeight
      self.leftPad=leftPad
      self.separatorHeight=separatorHeight
      self.underscoreThickness=underscoreThickness
      self.BGColor=BGColor
      self.BGBorderColor=BGBorderColor
      self.separatorColor=separatorColor
      self.frameColorHover=frameColorHover
      self.frameColorPress=frameColorPress
      self.textColorReady=textColorReady
      self.textColorHover=textColorHover
      self.textColorPress=textColorPress
      self.textColorDisabled=textColorDisabled
      self.minZ=minZ
      self.mpos=Point2(base.mouseWatcherNode.getMouse())

      self.itemCommand=[]
      self.hotkeys={}
      self.numItems=0
      self.sel=-1
      self.selByKey=False

      bgPad=self.bgPad=.0125
      texMargin=self.font.getTextureMargin()*self.scale*.25
      b=DirectButton( parent=NodePath(''), text='^|g_', text_font=self.font, scale=self.scale)
      fr=b.node().getFrame()
      b.getParent().removeNode()
      baselineToCenter=(fr[2]+fr[3])*self.scale
      LH=(fr[3]-fr[2])*self.itemHeight*self.scale
      imageHalfHeight=.5*(fr[3]-fr[2])*self.itemHeight*.85
      arrowHalfHeight=.5*(fr[3]-fr[2])*self.itemHeight*.5
      baselineToTop=(fr[3]*self.itemHeight*self.scale/LH)/(1.+self.baselineOffset)
      baselineToBot=LH/self.scale-baselineToTop
      itemZcenter=(baselineToTop-baselineToBot)*.5
      separatorHalfHeight=.5*separatorHeight*LH
      LSseparator=LineSegs()
      LSseparator.setColor(.5,.5,.5,.2)

      arrowVtx=[
        (0,itemZcenter),
        (-2*arrowHalfHeight,itemZcenter+arrowHalfHeight),
        (-arrowHalfHeight,itemZcenter),
        (-2*arrowHalfHeight,itemZcenter-arrowHalfHeight),
      ]
      tri=Triangulator()
      vdata = GeomVertexData('trig', GeomVertexFormat.getV3(), Geom.UHStatic)
      vwriter = GeomVertexWriter(vdata, 'vertex')
      for x,z in arrowVtx:
          vi = tri.addVertex(x, z)
          vwriter.addData3f(x, 0, z)
          tri.addPolygonVertex(vi)
      tri.triangulate()
      prim = GeomTriangles(Geom.UHStatic)
      for i in xrange(tri.getNumTriangles()):
          prim.addVertices(tri.getTriangleV0(i),
                           tri.getTriangleV1(i),
                           tri.getTriangleV2(i))
          prim.closePrimitive()
      geom = Geom(vdata)
      geom.addPrimitive(prim)
      geomNode = GeomNode('arrow')
      geomNode.addGeom(geom)
      realArrow=NodePath(geomNode)
      z=-baselineToTop*self.scale-bgPad
      maxWidth=.1/self.scale
      shortcutTextMaxWidth=0
      anyImage=False
      anyArrow=False
      anyShortcut=False
      arrows=[]
      shortcutTexts=[]
      loadPrcFileData('','text-flatten 0')
      for item in items:
          if item:
             t,imgPath,f=item[:3]
             haveSubmenu=type(f) in SEQUENCE_TYPES
             anyArrow|=haveSubmenu
             anyImage|=bool(imgPath)
             disabled=not len(f) if haveSubmenu else not callable(f)
             args=item[3:]
             underlinePos=t.find('_')
             t=t.replace('_','')
             shortcutSepPos=t.find('>')
             if shortcutSepPos>-1:
                if haveSubmenu:
                   print "\nA SHORTCUT KEY POINTING TO A SUBMENU IS NON-SENSE, DON'T YOU AGREE ?"
                else:
                   shortcutText=NodePath( OnscreenText(
                        parent=self.menu, text=t[shortcutSepPos+1:], font=self.font,
                        scale=1, fg=(1,1,1,1), align=TextNode.ARight,
                   ))
                   shortcutTextMaxWidth=max(shortcutTextMaxWidth,abs(shortcutText.getTightBounds()[0][0]))
                   anyShortcut=True
                t=t[:shortcutSepPos]
             else:
                shortcutText=''
             EoLcount=t.count('\n')
             arrowZpos=-self.font.getLineHeight()*EoLcount*.5
             if disabled:
                b=NodePath( OnscreenText(
                     parent=self.menu, text=t, font=self.font,
                     scale=1, fg=textColorDisabled, align=TextNode.ALeft,
                  ))
                # don't pass the scale and position to OnscreenText constructor,
                # to maintain correctness between the OnscreenText and DirectButton items
                # due to the new text generation implementation
                b.setScale(self.scale)
                b.setZ(z)
                maxWidth=max(maxWidth,b.getTightBounds()[1][0]/self.scale)
                if shortcutText:
                   shortcutText.reparentTo(b)
                   shortcutText.setColor(Vec4(*textColorDisabled),1)
                   shortcutText.setZ(arrowZpos)
                   shortcutTexts.append(shortcutText)
             else:
                b=DirectButton(
                    parent=self.menu, text=t, text_font=self.font, scale=self.scale,
                    pos=(0,0,z),
                    text_fg=textColorReady,
                    # text color when mouse over
                    text2_fg=textColorHover,
                    # text color when pressed
                    text1_fg=textColorHover if haveSubmenu else textColorPress,
                    # framecolor when pressed
                    frameColor=frameColorHover if haveSubmenu else frameColorPress,
                    command=(lambda:0) if haveSubmenu else self.__runCommand,
                    extraArgs=[] if haveSubmenu else [f,args],
                    text_align=TextNode.ALeft,
                    relief=DGG.FLAT, rolloverSound=0, clickSound=0, pressEffect=0
                    )
                b.stateNodePath[2].setColor(*frameColorHover) # framecolor when mouse over
                b.stateNodePath[0].setColor(0,0,0,0) # framecolor when ready
                bframe=Vec4(b.node().getFrame())
                if EoLcount:
                   bframe.setZ(EoLcount*10)
                   b['frameSize']=bframe
                maxWidth=max(maxWidth,bframe[1])
                if shortcutText:
                   for snpi,col in ((0,textColorReady),(1,textColorPress),(2,textColorHover)):
                       sct=shortcutText.copyTo(b.stateNodePath[snpi],sort=10)
                       sct.setColor(Vec4(*col),1)
                       sct.setZ(arrowZpos)
                       shortcutTexts.append(sct)
                   shortcutText.removeNode()
             if imgPath:
                img=loader.loadTexture(imgPath)
                if disabled:
                   if imgPath in PopupMenu.grayImages:
                      img=PopupMenu.grayImages[imgPath]
                   else:
                      pnm=PNMImage()
                      img.store(pnm)
                      pnm.makeGrayscale(.2,.2,.2)
                      img=Texture()
                      img.load(pnm)
                      PopupMenu.grayImages[imgPath]=img
                img.setMinfilter(Texture.FTLinearMipmapLinear)
                img.setWrapU(Texture.WMClamp)
                img.setWrapV(Texture.WMClamp)
                CM=CardMaker('')
                CM.setFrame(-2*imageHalfHeight-leftPad,-leftPad, itemZcenter-imageHalfHeight,itemZcenter+imageHalfHeight)
                imgCard=b.attachNewNode(CM.generate())
                imgCard.setTexture(img)
             if underlinePos>-1:
                oneLineText=t[:underlinePos+1]
                oneLineText=oneLineText[oneLineText.rfind('\n')+1:]
                tn=TextNode('')
                tn.setFont(self.font)
                tn.setText(oneLineText)
                tnp=NodePath(tn.getInternalGeom())
                underlineXend=tnp.getTightBounds()[1][0]
                tnp.removeNode()
                tn.setText(t[underlinePos])
                tnp=NodePath(tn.getInternalGeom())
                b3=tnp.getTightBounds()
                underlineXstart=underlineXend-(b3[1]-b3[0])[0]
                tnp.removeNode()
                underlineZpos=-.7*baselineToBot-self.font.getLineHeight()*t[:underlinePos].count('\n')
                LSunder=LineSegs()
                LSunder.setThickness(underscoreThickness)
                LSunder.moveTo(underlineXstart+texMargin,0,underlineZpos)
                LSunder.drawTo(underlineXend-texMargin,0,underlineZpos)
                if disabled:
                   underline=b.attachNewNode(LSunder.create())
                   underline.setColor(Vec4(*textColorDisabled),1)
                else:
                   underline=b.stateNodePath[0].attachNewNode(LSunder.create())
                   underline.setColor(Vec4(*textColorReady),1)
                   underline.copyTo(b.stateNodePath[1],10).setColor(Vec4(*textColorHover if haveSubmenu else textColorPress),1)
                   underline.copyTo(b.stateNodePath[2],10).setColor(Vec4(*textColorHover),1)
                   hotkey=t[underlinePos].lower()
                   if hotkey in self.hotkeys:
                      self.hotkeys[hotkey].append(self.numItems)
                   else:
                      self.hotkeys[hotkey]=[self.numItems]
                      self.accept(self.BTprefix+hotkey,self.__processHotkey,[hotkey])
                      self.accept(self.BTprefix+'alt-'+hotkey,self.__processHotkey,[hotkey])
             if haveSubmenu:
                if disabled:
                   arrow=realArrow.instanceUnderNode(b,'')
                   arrow.setColor(Vec4(*textColorDisabled),1)
                   arrow.setZ(arrowZpos)
                else:
                   arrow=realArrow.instanceUnderNode(b.stateNodePath[0],'r')
                   arrow.setColor(Vec4(*textColorReady),1)
                   arrow.setZ(arrowZpos)
                   arrPress=realArrow.instanceUnderNode(b.stateNodePath[1],'p')
                   arrPress.setColor(Vec4(*textColorHover),1)
                   arrPress.setZ(arrowZpos)
                   arrHover=realArrow.instanceUnderNode(b.stateNodePath[2],'h')
                   arrHover.setColor(Vec4(*textColorHover),1)
                   arrHover.setZ(arrowZpos)
                   # weird, if sort order is 0, it's obscured by the frame
                   for a in (arrPress,arrHover):
                       a.reparentTo(a.getParent(),sort=10)
             if not disabled:
                extraArgs=[self.numItems,f if haveSubmenu else 0]
                self.accept(DGG.ENTER+b.guiId,self.__hoverOnItem,extraArgs)
                self.accept(DGG.EXIT+b.guiId,self.__offItem)
                #~ self.itemCommand.append((None,0) if haveSubmenu else (f,args))
                self.itemCommand.append((f,args))
                if self.numItems==0:
                   self.firstButtonIdx=int(b.guiId[2:])
                self.numItems+=1
             z-=LH + self.font.getLineHeight()*self.scale*EoLcount
          else: # SEPARATOR LINE
             z+=LH-separatorHalfHeight-baselineToBot*self.scale
             LSseparator.moveTo(0,0,z)
             LSseparator.drawTo(self.scale*.5,0,z)
             LSseparator.drawTo(self.scale,0,z)
             z-=separatorHalfHeight+baselineToTop*self.scale
      maxWidth+=7*arrowHalfHeight*(anyArrow or anyShortcut)+.2+shortcutTextMaxWidth
      arrowXpos=maxWidth-arrowHalfHeight
      realArrow.setX(arrowXpos)
      if anyImage:
         leftPad+=2*imageHalfHeight+leftPad
      for sct in shortcutTexts:
          sct.setX(maxWidth-2*(arrowHalfHeight*anyArrow+.2))
      for c in asList(self.menu.findAllMatches('**/DirectButton*')):
          numLines=c.node().getFrame()[2]
          c.node().setFrame(Vec4( -leftPad,maxWidth,
                                  -baselineToBot-(numLines*.1*self.itemHeight if numLines>=10 else 0),
                                  baselineToTop))
      loadPrcFileData('','text-flatten 1')

      try:
         minZ=self.menu.getChild(0).getRelativePoint(b,Point3(0,0,b.node().getFrame()[2]))[2]
      except:
         minZ=self.menu.getChild(0).getRelativePoint(self.menu,Point3(0,0,b.getTightBounds()[0][2]))[2]-baselineToBot*.5
      try:
         top=self.menu.getChild(0).node().getFrame()[3]
      except:
         top=self.menu.getChild(0).getZ()+baselineToTop
      l,r,b,t = -leftPad-bgPad/self.scale, maxWidth+bgPad/self.scale, minZ-bgPad/self.scale, top+bgPad/self.scale
      menuBG = DirectFrame( parent=self.menu.getChild(0),
         frameSize=(l, r, b, t), frameColor=BGColor,
         state=DGG.NORMAL, suppressMouse=1
      )
      menuBorder=self.menu.getChild(0).attachNewNode('border')
      borderVtx=(
        (l,0,b),
        (l,0,.5*(b+t)),
        (l,0,t),
        (.5*(l+r),0,t),
        (r,0,t),
        (r,0,.5*(b+t)),
        (r,0,b),
        (.5*(l+r),0,b),
        (l,0,b),
      )
      LSborderBG=LineSegs()
      LSborderBG.setThickness(4)
      LSborderBG.setColor(0,0,0,.7)
      LSborderBG.moveTo(*(borderVtx[0]))
      for v in borderVtx[1:]:
          LSborderBG.drawTo(*v)
      # fills the gap at corners
      for v in range(0,7,2):
          LSborderBG.moveTo(*(borderVtx[v]))
      menuBorder.attachNewNode(LSborderBG.create())
      LSborder=LineSegs()
      LSborder.setThickness(2)
      LSborder.setColor(*BGBorderColor)
      LSborder.moveTo(*(borderVtx[0]))
      for v in borderVtx[1:]:
          LSborder.drawTo(*v)
      menuBorder.attachNewNode(LSborder.create())
      for v in range(1,8,2):
          LSborderBG.setVertexColor(v,Vec4(0,0,0,.1))
          LSborder.setVertexColor(v,Vec4(.3,.3,.3,.5))
      menuBorderB3=menuBorder.getTightBounds()
      menuBorderDims=menuBorderB3[1]-menuBorderB3[0]
      menuBG.wrtReparentTo(self.menu,sort=-1)
      self.menu.reparentTo(self.parent)
      x=-menuBorderB3[0][0]*self.scale
      for c in asList(self.menu.getChildren()):
          c.setX(x)
      self.maxWidth=maxWidth=menuBorderDims[0]
      self.height=menuBorderDims[2]
      maxWidthR2D=maxWidth*self.menu.getChild(0).getSx(render2d)
      separatorLines=self.menu.attachNewNode(LSseparator.create(),10)
      separatorLines.setSx(maxWidth)
      for v in range(1,LSseparator.getNumVertices(),3):
          LSseparator.setVertexColor(v,Vec4(*separatorColor))
      x=clamp( -.98,.98-maxWidthR2D,self.mpos[0]-maxWidthR2D*.5)
      minZ=(-.98 if self.minZ is None else self.minZ)
      z=clamp(minZ+menuBorderDims[2]*self.scale*self.parent.getSz(render2d),.98,self.mpos[1] if useMouseZ else -1000)
      self.menu.setPos(render2d,x,0,z)
      self.menu.setTransparency(1)

      self.origBTprefix=self.BT.getPrefix()
      self.BT.setPrefix(self.BTprefix)
      self.accept(self.BTprefix+'escape',self.destroy)
      for e in ('mouse1','mouse3'):
          self.accept(self.BTprefix+e,self.destroy,[True])
      self.accept(self.BTprefix+'arrow_down',self.__nextItem)
      self.accept(self.BTprefix+'arrow_down-repeat',self.__nextItem)
      self.accept(self.BTprefix+'arrow_up',self.__prevItem)
      self.accept(self.BTprefix+'arrow_up-repeat',self.__prevItem)
      self.accept(self.BTprefix+'enter',self.__runSelItemCommand)
      self.accept(self.BTprefix+'space',self.__runSelItemCommand)

  def __offItem(self,crap):
      self.sel=-1
      self.__cancelSubmenuCreation()

  def __hoverOnItem(self,idx,menu,crap):
      self.sel=idx
      self.__cancelSubmenuCreation()
      if self.BT.getPrefix()==self.BTprefix or \
           (self.submenu and self.submenuIdx==idx):
         self.__cancelSubmenuRemoval()
      if menu:
         if not (self.submenu and self.submenuIdx==idx):
            #~ if self.selByKey:
               #~ self.selByKey=False
               #~ self.__createSubmenu(idx,menu)
            #~ else:
               taskMgr.doMethodLater(.3,self.__createSubmenu,self.submenuCreationTaskName,extraArgs=[idx,menu])
      else:
         taskMgr.doMethodLater(.5,self.__removeSubmenu,self.submenuRemovalTaskName,extraArgs=[])

  def __cancelSubmenuCreation(self):
      taskMgr.removeTasksMatching('createSubMenu-*')

  def __createSubmenu(self,idx,menu):
      self.__cancelSubmenuCreation()
      self.__removeSubmenu()
      self.submenu = PopupMenu( items=menu,
         parent=self.parent, buttonThrower=self.BT,
         font=self.font, baselineOffset=self.baselineOffset,
         scale=self.scale, itemHeight=self.itemHeight,
         leftPad=self.leftPad, separatorHeight=self.separatorHeight,
         underscoreThickness=self.underscoreThickness,
         BGColor=self.BGColor,
         BGBorderColor=self.BGBorderColor,
         separatorColor=self.separatorColor,
         frameColorHover=self.frameColorHover,
         frameColorPress=self.frameColorPress,
         textColorReady=self.textColorReady,
         textColorHover=self.textColorHover,
         textColorPress=self.textColorPress,
         textColorDisabled=self.textColorDisabled,
         minZ=self.minZ, useMouseZ=False
      )
      self.submenuIdx=idx
      self.submenu.parentMenu=self
      if self.menu.getBinName():
         self.submenu.menu.setBin(self.menu.getBinName(),self.menu.getBinDrawOrder()+1)
      sb3=self.submenu.menu.getTightBounds()
      sb=sb3[1]-sb3[0]
      b3=self.menu.getTightBounds()
      x=b3[1][0]
      if render2d.getRelativePoint(self.parent,Point3(x+sb[0],0,0))[0]>.98:
         x=b3[0][0]-sb[0]
      if render2d.getRelativePoint(self.parent,Point3(x,0,0))[0]<-.98:
         x=self.parent.getRelativePoint(render2d,Point3(-.98,0,0))[0]
      item=self.menu.find('**/*-pg%s'%(self.firstButtonIdx+idx))
      z=self.parent.getRelativePoint(item,Point3(0,0,item.node().getFrame()[3]))[2]+self.bgPad
      self.submenu.menu.setPos(x,0,max(z,self.submenu.menu.getZ()))
#       self.submenu.menu.setPos(x,0,z)

  def __nextItem(self):
      if self.numItems:
         self.sel=clamp(0,self.numItems-1,self.sel+1)
         self.__putPointerAtItem()
         self.selByKey=True

  def __prevItem(self):
      if self.numItems:
         self.sel=clamp(0,self.numItems-1,(self.sel-1) if self.sel>-1 else self.numItems-1)
         self.__putPointerAtItem()
         self.selByKey=True

  def __putPointerAtItem(self):
      item=self.menu.find('**/*-pg%s'%(self.firstButtonIdx+self.sel))
      fr=item.node().getFrame()
      c=Point3(.5*(fr[0]+fr[1]),0,.5*(fr[2]+fr[3]))
      cR2D=render2d.getRelativePoint(item,c)
      x,y=int(base.win.getXSize()*.5*(cR2D[0]+1)), int(base.win.getYSize()*.5*(-cR2D[2]+1))
      if '__origmovePointer' in base.win.DtoolClassDict:
         base.win.DtoolClassDict['__origmovePointer'](base.win,0,x,y)
      else:
         base.win.movePointer(0,x,y)

  def __processHotkey(self,hotkey):
      itemsIdx=self.hotkeys[hotkey]
      if len(itemsIdx)==1 and type(self.itemCommand[itemsIdx[0]][0]) not in SEQUENCE_TYPES:
         self.__runCommand(*self.itemCommand[itemsIdx[0]])
      else:
         if self.sel in itemsIdx:
            idx=itemsIdx.index(self.sel)+1
            idx%=len(itemsIdx)
            self.sel=itemsIdx[idx]
         else:
            self.sel=itemsIdx[0]
         self.selByKey=True
         # if it's already there, putting the pointer doesn't trigger the 'enter'
         # event, so just bypass it
         if not (self.submenu and self.submenuIdx==self.sel) and\
              type(self.itemCommand[itemsIdx[0]][0]) in SEQUENCE_TYPES:
            self.__createSubmenu(self.sel,self.itemCommand[itemsIdx[0]][0])
         self.__putPointerAtItem()

  def __doRunCommand(self,f,args):
      self.destroy(delParents=True)
      f(*args)

  def __runCommand(self,f,args):
      if callable(f):
         # must be done at next frame, so shortcut key event won't bleed to the scene
         taskMgr.doMethodLater(.01,self.__doRunCommand,'run menu command',extraArgs=[f,args])

  def __runSelItemCommand(self):
      if self.sel==-1: return
      self.__runCommand(*self.itemCommand[self.sel])

  def __cancelSubmenuRemoval(self):
      taskMgr.removeTasksMatching('removeSubMenu-*')

  def __removeSubmenu(self):
      self.__cancelSubmenuRemoval()
      if self.submenu:
         self.submenu.destroy()

  def destroy(self,delParents=False):
      self.__cancelSubmenuCreation()
      self.__removeSubmenu()
      self.subMenu=None
      self.ignoreAll()
      self.menu.removeNode()
#       if self.origBTprefix.find('menu-')==-1:
#          taskMgr.step()
      self.BT.setPrefix(self.origBTprefix)
      messenger.send(self.BTprefix+'destroyed')
      if delParents and self.parentMenu:
         parent=self.parentMenu
         while parent.parentMenu:
               parent=parent.parentMenu
         parent.destroy()
      if self.parentMenu:
         self.parentMenu.submenuIdx=None
         self.parentMenu=None
      if callable(self.onDestroy):
         self.onDestroy()
