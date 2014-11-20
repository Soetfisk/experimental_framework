
class Button():
    """
    button class created with LibRocket
    """

    def __init__(self, context, url):
        self.button = context.LoadDocument(url)
        self.button.AddEventListener('click', self.OnClick, True)

    def OnClick(self):
        print "Button clicked"
        
    def Show(self):
        self.button.Show()

    def Hide(self):
        self.button.Hide()

