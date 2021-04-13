from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.lang import Builder
import cv2 as cv
import numpy as np
from kivy.graphics.texture import Texture
from kivy.uix.boxlayout import BoxLayout

Window.size = (340, 610)

# MDToolbar:
#     title: 'Simple Gray'
#     left_action_items: [["menu", lambda x: app.myfun()]]
#     elevation: 10.5
# MDLabel:
#     text: 'hello world'
#     halign: 'center'


screenHelper = """

Screen:
    NavigationLayout:
        ScreenManager:
            Screen:
                BoxLayout:
                    orientation: 'vertical'

                    MDToolbar:
                        title: "Simple Gray"
                        elevation: 10
                        left_action_items: [['menu', lambda x: nav_drawer.set_state("open")]]
                    BoxLayout:
                        padding: '15dp'
                        spacing: '15dp'
                        Image:
                            id: loadedImage 
                            source:''
                            size: self.texture_size     
                            size_hint_y: 1
                    
                    MDSlider:
                        size_hint_y: 0.1
                        id: slider
                        min: -100
                        max: 100
                        value: 1
                        step: 1
                        on_value_normalized: app.editImage(self.value)
                        
                    MDBottomNavigation:

                        # MDBottomNavigationItem:
                        #     name: 'screen 1'
                        #     # text: 'Auto'
                        #     icon: 'menu'

                        MDBottomNavigationItem:
                            name: 'screen 2'
                            text: 'Auto'
                            icon: 'creation'
                            on_tab_press: app.setMode(1)       # Auto process 

                        MDBottomNavigationItem:
                            # name: 'screen 3'
                            text: 'Bright'
                            icon: 'brightness-4'
                            on_tab_press: app.setMode(2)       # brightness
                            
                        MDBottomNavigationItem:
                            name: 'screen 4'
                            text: 'Contrast'
                            icon: 'contrast-circle'
                            on_tab_press: app.setMode(3)       # contrast

                        MDBottomNavigationItem:
                            name: 'screen 5'
                            text: '2 color'
                            icon: 'arrow-split-vertical'
                            on_tab_press: app.setMode(4)       # thresholding 

                        MDBottomNavigationItem:
                            name: 'screen 6'
                            text: 'slice'
                            icon: 'circle-slice-1'
                            on_tab_press: app.setMode(5)       # bit planes 

        MDNavigationDrawer:
            id: nav_drawer
            BoxLayout:
                orientation: 'vertical'
                padding: '0dp'
                spacing: '0dp'
                MDList:
                    OneLineListItem:
                        text: 'Simple Gray'
                        font_style:'H5'
                    OneLineIconListItem:
                        text: 'Save'        
                        on_press: app.saveImage() 
                        IconLeftWidget:
                            icon: 'content-save'
                    
                    OneLineIconListItem:
                        text: 'Choose Image'
                        on_press: app.myfun()
                        IconLeftWidget:
                            icon: 'folder-multiple-image'
                            # on_press: app.myfun()
                BoxLayout:
                    orientation: 'vertical'
                    padding: '0dp'
                    spacing: '0dp'
                    FileChooserListView:
                        id: fileChooser
                        rootpath: '/'
                        filters: ['*.png','*.jpg','*.gif']
                        on_selection: app.openImage(fileChooser.selection)
                                          
"""


class MainApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Dark"  # "Light"
        self.theme_cls.primary_palette = 'Amber'
        screen = Builder.load_string(screenHelper)
        return screen

    def __init__(self):
        MDApp.__init__(self)
        self.cvImage = None
        self.processMode = None
        self.lastCVProcessedImage = None
        self.fileImageName = ''

    def myfun(self):
        print('hi')
        # self.root.ids.slider.value

    def convertTexture(self, cvImage):
        # img = cv.imread('no-smoke.png')
        imgStr = cv.flip(cvImage, 0)
        imgStr = imgStr.tobytes()
        if self.processMode == 4  or self.processMode == 5:
            texture = Texture.create(size=(cvImage.shape[1], cvImage.shape[0]), colorfmt='luminance')
            texture.blit_buffer(imgStr, colorfmt='luminance', bufferfmt='ubyte')
        else:
            texture = Texture.create(size=(cvImage.shape[1], cvImage.shape[0]), colorfmt='bgr')
            texture.blit_buffer(imgStr, colorfmt='bgr', bufferfmt='ubyte')

        # display image from the texture
        # self.img1.texture = texture1
        # self.root.ids.loadedImage.texture = texture1
        # self.root.ids.loadedImage.texture_size = texture1.size
        return texture

    def openImage(self, fileName):
        self.cvImage = cv.imread(fileName[0])
        self.lastCVProcessedImage = self.cvImage
        self.root.ids.loadedImage.source = fileName[0]
        self.fileImageName = fileName[0]

    def setMode(self, modeNumber):
        self.processMode = modeNumber
        print('mode = ' + str(self.processMode))
        self.editImage(self.root.ids.slider.value)

    def editImage(self, sliderValue):
        print('hello' + str(sliderValue))
        mode = self.processMode
        image = self.cvImage
        newCVImage = None
        if mode == 1:  # auto
            gamma = 2.5
            lookUpTable = np.empty((1, 256), np.uint8)
            for i in range(256):
                lookUpTable[0, i] = np.clip(pow(i / 255.0, gamma) * 255.0, 0, 255)

            newCVImage = cv.LUT(image, lookUpTable)
            ## [changing-contrast-brightness-gamma-correction]

            # img_gamma_corrected = cv.hconcat([image, res])

        elif mode == 2:  # brightness
            beta = sliderValue
            newCVImage = cv.convertScaleAbs(image, alpha=1, beta=beta)

        elif mode == 3:  # contrast
            alpha = 1
            if sliderValue == 0:  # slider value between -100 and 100, if 0 -> 1
                alpha = 1  # if -100 < sliderValue < 0 --> 0.01 < alpha < 0.99 so
            elif sliderValue < 0:  # slope = 0.0098 and equation will be:
                alpha = ((0.0098 * sliderValue) + 0.99)  # alpha = 0.0098*sliderValue + 0.99
            elif sliderValue > 0:
                alpha = 0.5 * sliderValue
                alpha = 1 if alpha == 0.5 else alpha

            newCVImage = cv.convertScaleAbs(image, alpha=alpha, beta=0)

        elif mode == 4:  # thresholding
            newCVImage = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
            newImage = cv.medianBlur(newCVImage, 5)
            blockSize = (sliderValue/2) + 53
            blockSize = int(blockSize)
            blockSize = blockSize if blockSize%2 == 1 else blockSize+1      # blockSize should be even
            newCVImage = cv.adaptiveThreshold(newCVImage, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, blockSize, 1)
            # ret, new_image1 = cv.threshold(new_image, 127, 255, cv.THRESH_BINARY)

        elif mode == 5:  # extract bit planes
            bitValue = ((254/255)*sliderValue) + 128
            imageGray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
            ret, mask = cv.threshold(imageGray, bitValue, 255, cv.THRESH_BINARY)
            newCVImage = cv.bitwise_and(imageGray, imageGray, mask=mask)
        if mode is not None and mode >= 1:
            kivyTexture = self.convertTexture(newCVImage)
            self.root.ids.loadedImage.texture = kivyTexture
            self.root.ids.loadedImage.texture_size = kivyTexture.size
            self.lastCVProcessedImage = newCVImage

    def saveImage(self):
        image = self.lastCVProcessedImage
        # cv.imshow('New Image', image)
        fileImageNameArr = self.fileImageName.split('\\')
        fileImageNameArr = fileImageNameArr[-1].split('.')
        print(fileImageNameArr[0])
        print(fileImageNameArr[1])
        newFileName = fileImageNameArr[0] + "(1)." + fileImageNameArr[1]
        res = cv.imwrite(newFileName, image)
        print(str(res))

demo = MainApp()
demo.run()



# https://groups.google.com/g/kivy-users/c/N18DmblNWb0/m/IzIM7xOgvv8J?pli=1