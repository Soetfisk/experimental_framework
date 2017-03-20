import Tkinter as tk
from tkColorChooser import askcolor

#from direct.showbase.ShowBase import ShowBase
#from panda3d.core import AmbientLight, DirectionalLight, LightAttrib
#from panda3d.core import NodePath
#from panda3d.core import LVector3
#from direct.interval.IntervalGlobal import *  # Needed to use Intervals
#from direct.gui.DirectGui import *

# Importing math constants and functions
#from math import pi, sin

#class test(ShowBase):
#    def __init__(self):
#        ShowBase.__init__(self)
#        base.startTk()
#        self.tkRoot.withdraw()
#
#        frame = Frame()
#        frame.pack()
#        frame.QUIT =  Button(frame)
#        frame.QUIT['text'] = "QUIT"
#        frame.QUIT.pack({"side":"left"})
#
#t = test()
#t.run()

content = [
    { 'className': 'ScreenText', 'file_message': 'experiments/HiddenCalibration/data/introExperiment.txt',
          'color_background': (0.3, 0.3, 0.4, 1), 'name': 'introText1' },
    { 'className': 'ScreenText', 'file_message': 'experiments/HiddenCalibration/data/introExperiment.txt',
      'color_background': (0.3, 0.3, 0.4, 1), 'name': 'introText2' },
    { 'className': 'ScreenText', 'file_message': 'experiments/HiddenCalibration/data/introExperiment.txt',
        'color_background': (0.3, 0.3, 0.4, 1), 'name': 'introText3' }
]

# basic text, with pencil for large editing.
# color entry with color picker
# floating point number
# integer number
# boolean
# list of strings
# file entry with file chooser
# keys go inside a group -- keys bindings (key, callback, arguments)


complete_elements_list = ("element1 element2 element3 element4 5 6 7 8 9 0 12 123 1234 5123 983212")

def filter_changed(x,y,z):
    filter = filter_text.get()
    values_in_list = complete_elements_list.split()
    new_list = ""
    for i in values_in_list:
        if filter in i:
            new_list = new_list + " " + i
    list_elements.set(new_list)
    if filter == '':
        f3.grid(column=1,row=1, sticky=spreadHorizontal)
        f3_bis.grid_remove()
    else:
        f3_bis.grid(column=1,row=1, sticky=spreadHorizontal)
        f3.grid_remove()

root = tk.Tk()
root.title("Element browser")
spreadHorizontal = tk.E + tk.W

f1 = tk.Frame(root)
f1.grid(column=0,row=0, columnspan=2, sticky=spreadHorizontal )
tk.Label(f1, text="frame 1").pack()


f2 = tk.Frame(root)
f2.grid(column=0,row=1, sticky=spreadHorizontal)
filter_text = tk.StringVar()
filter_text.trace('w', filter_changed)

scrollbar = tk.Scrollbar(f2)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
entry_filter = tk.Entry(f2, textvariable = filter_text )
entry_filter.pack()
list_elements = tk.StringVar()
list_elements.set(complete_elements_list)
listbox = tk.Listbox(f2, listvariable = list_elements, yscrollcommand = scrollbar.set)
listbox.pack()
scrollbar.config(command = listbox.yview)

def makeEntry(parent,labelText, row, tuple = 1, buttonList = []):
    label = tk.Label(parent, text = labelText)
    label.grid(column=0, row=row)
    for i in range(tuple):
        entry = tk.Entry(parent)
        entry.grid(column=1+i, row=row, ipadx=100, sticky=tk.E+tk.W)
    for column,(img,callback) in enumerate(buttonList):
        image = tk.PhotoImage(file=img)
        b = tk.Button(parent, image = image, command = callback)
        b.photo = image
        b.grid(column=column+tuple+2, row=row)

f3_bis = tk.Frame(root)
tk.Label(f3_bis, text="testing123").pack()

f3 = tk.Frame(root)
f3.grid(column=1,row=1, sticky=spreadHorizontal)

def testButton():
    print 'hey!'

def getColor():
    c = askcolor()
    print c

makeEntry(f3, "label 1", 0, 1, [('common/images/pencil.gif', testButton),('common/images/color.gif', getColor)])
makeEntry(f3, "label 2", 1, 1)
makeEntry(f3, "label 3", 2, 1)
makeEntry(f3, "label 4", 3, 1)
makeEntry(f3, "label 5", 4, 1)

f4 = tk.Frame(root)
f4.grid(column=0,row=2, columnspan=2, sticky=spreadHorizontal)
tk.Label(f4, text="frame 4").pack()

f5 = tk.Frame(root)
f5.grid(column=0,row=3, columnspan=2, sticky=spreadHorizontal)
tk.Label(f5, text="frame 5").pack()

#tk.Label(root, text="Enter your Password:").pack()
#tk.Button(root, text="Search").pack()
#tk.Checkbutton(root, text="Remember Me", variable=v).pack()
#tk.Entry(root, width=30).pack()
#tk.Radiobutton(root, text="Male", variable=v2).pack()
#tk.Radiobutton(root, text="Female", variable=v2).pack()
#tk.OptionMenu(root, var, "Select Country", "USA", "UK", "India", "Others").pack()
#tk.Scrollbar(root, orient=tk.VERTICAL).pack() # command= text.yview)
#for k in content.keys():
#    label = tk.Label(root, text = k)
#    label.pack()
#test = tk.Button(root, text='test')
#test.pack()
#tk.Button(root, text='save').pack()
root.mainloop()

