# This script is used to render screen elements over the rest of the game
import pygame
import typing

# get globals
import env
import input_handler # for buttons

# Display for drawing onto
display = env.display

# Sprite groups
allSprites = env.all_sprites
topSprites = env.top_sprites

# Custom types
# Used for defining the colour and transparency of an object's fill
class Fill(typing.TypedDict):
    Colour: typing.Tuple[int, int, int]
    Transparency: float

# Defines the properties of the outer line around a rectangular frame
class Outline(typing.TypedDict):
    Thickness: float
    Colour: typing.Tuple[int, int, int]
    Transparency: float

# Defines the font face, size, colour etc of text in a text label
class TextData(typing.TypedDict):
    Font: pygame.font.Font
    Colour: typing.Tuple[int, int, int]
    Size: float
    Transparency: float
    Text: str
    TextWraps: bool

# Used for detailed buttons; defines image and text
class ButtonData(typing.TypedDict):
    Image: pygame.Surface
    Text: TextData
    ButtonDown: callable # functions run by button
    ButtonUp: callable

# Helper functions
# Wraps text around so that it fits within constraints
def wrapText(text: str, font: pygame.font.Font, maxWidth: int):
    words = text.split(" ")
    lines = []
    currentLine = ""

    for word in words:
        testLine = currentLine + (" " if currentLine else "") + word
        if font.size(testLine)[0] <= maxWidth:
            currentLine = testLine
        else:
            if currentLine:
                lines.append(currentLine)
            currentLine = word

    if currentLine:
        lines.append(currentLine)

    return lines
    # newText = ""
    # finalLineIdx = len(lines)-1
    # for idx, line in enumerate(lines):
    #     newText.append(line)
    #     if idx != finalLineIdx:
    #         newText.append("\n")
    
    # return text

# Checks whether a point is within bounds
def isPointInBounds(point: tuple, boundsPos: tuple, boundsSize: tuple):
    if (point[0] > boundsPos[0]) and (point[0] < (boundsPos[0] + boundsSize[0])) and (point[1] > boundsPos[1]) and (point[1] < (boundsPos[1] + boundsSize[1])):
        # print("Mouse x:", point[0], ">", "Rect x:", boundsPos[0])
        # print("Mouse x:", point[0], "<", "Rect outer x:", boundsPos[0] + boundsSize[0])
        return True

# Default values for types
def getFill(fill: Fill):
    # Don't crash if empty
    if not fill:
        fill = {}

    colour = (0,0,0)
    if "Colour" in fill:
        colour = fill["Colour"]
    transparency = 255
    if "Transparency" in fill:
        transparency = fill["Transparency"]
        transparency = 1-transparency
        transparency *= 255
        transparency = int(transparency)

    newFill = {
        "Colour": colour,
        "Transparency": transparency
    }
    return newFill

def getOutline(outline: Outline):
    if not outline:
        outline = {}

    thickness = 0
    if "Thickness" in outline:
        thickness = outline["Thickness"]
    colour = (0,0,0)
    if "Colour" in outline:
        colour = outline["Colour"]
    transparency = 255
    if "Transparency" in outline:
        transparency = outline["Transparency"]
        transparency = 1-transparency
        transparency *= 255
        transparency = int(transparency)

    newOutline = {
        "Thickness": thickness,
        "Colour": colour,
        "Transparency": transparency,
    }
    return newOutline

def getText(text: TextData):
    if not text:
        text = {}

    textContent = ""
    if "Text" in text:
        textContent = text["Text"]

    colour = (0,0,0)
    if "Colour" in text:
        colour = text["Colour"]

    fontName = env.DEFAULT_FONT
    if "Font" in text:
        fontName = text["Font"]

    size = 20
    if "Size" in text:
        size = text["Size"]
    
    font = pygame.font.Font(fontName, size)

    transparency = 255
    if "Transparency" in text:
        transparency = text["Transparency"]
        transparency = 1-transparency
        transparency *= 255
        transparency = int(transparency)
    
    textWraps = True
    if "TextWraps" in text:
        textWraps = text["TextWraps"]

    newText = {
        "Text": textContent,
        "Font": font,
        "Size": size,
        "Colour": colour,
        "Transparency": transparency,
        "TextWraps": textWraps,
    }
    return newText

# prevents erroring when reading data
def pass_func():
    print("PASSINg")
    pass

def get_button_data(button_data: ButtonData):
    # makes sure it exists
    if not button_data:
        button_data = {}
    
    new_button_data = {}

    if "Text" in button_data:
        new_button_data["Text"] = button_data["Text"]
    
    if "Image" in button_data:
        new_button_data["Image"] = button_data["Image"]

    if "ButtonDown" in button_data:
        button_down_func = button_data["ButtonDown"]
        new_button_data["ButtonDown"] = button_down_func

    if "ButtonUp" in button_data:
        button_up_func = button_data["ButtonUp"]
        new_button_data["ButtonUp"] = button_up_func

    
    return new_button_data


# Actual classes
class Frame(pygame.sprite.Sprite):
    def _redraw(self, position: tuple, size: tuple, layer: int, fill: Fill = None, outline: Outline = None):
        self.rect = pygame.Rect(position[0], position[1], size[0], size[1])
        self.image = pygame.Surface(size, pygame.SRCALPHA)

        # Layer element renders at
        self._layer = layer

        # Calculate outline to be applied, if applicable
        outlineRect = None
        self.outline = outline
        if outline["Thickness"] > 0:
            thickness = outline["Thickness"]
            outlineRect = pygame.Rect(thickness, thickness, size[0]-2*thickness, size[1]-2*thickness)
            r, g, b = outline["Colour"]
            a = outline["Transparency"]
            self.image.fill((r,g,b,a))

        # Fill rect (excluding outline) with fill colour
        self.fill = fill
        r, g, b = fill["Colour"]
        a = fill["Transparency"]
        self.image.fill((r, g, b, a), outlineRect)
        self.visible = False

    def __init__(self, position: tuple, size: tuple, layer: int, fill: Fill = None, outline: Outline = None):
        pygame.sprite.Sprite.__init__(self)
        self._redraw(position, size, layer, getFill(fill), getOutline(outline))
        topSprites.add(self)
    
    # for removing the ui element
    def try_destroy(self):
        self.kill()
    

# Renders text placed onto a frame
class TextLabel(Frame):
    def __init__(self, position: tuple, size: tuple, text: TextData, layer: int=1, background: Fill = None, outline: Outline = None):
        super().__init__(position, size, layer, background, outline)
        self._setupText(text)
    
    # Renders text on the image
    def _setupText(self, text: TextData, x_offset=0, starting_y_offset=0):
        text = getText(text)
        font = text["Font"]
        colour = text["Colour"]

        # wrap text or not
        if text["TextWraps"]:
            # Wrap text to fit the frame width
            lines = wrapText(text["Text"], font, self.rect.width-x_offset)

            # Render each line
            y_offset = starting_y_offset
            line_height = font.get_linesize()
            for line in lines:
                surface = font.render(line, True, colour)
                self.image.blit(surface, (x_offset, y_offset))
                y_offset += line_height
        else:
            surface = font.render(text["Text"], True, colour)
            self.image.blit(surface, (0,starting_y_offset))

# Renders an image stretched to fit the frame
class ImageLabel(Frame):
    def __init__(self, position: tuple, size: tuple, image: pygame.image, layer: int=1, background: Fill = None, outline: Outline = None):
        super().__init__(position, size, layer, background, outline)
        imageSurface = pygame.transform.smoothscale(image, size)
        self.image.blit(imageSurface, (0,0))

# Creates an image that constantly follows the mouse cursor
class Cursor(ImageLabel):
    def __init__(self, size: tuple, image: pygame.image, layer: int=1, background: Fill = None, outline: Outline = None):
        super().__init__((0,0), size, layer, image, background, outline)

    def update(self):
        #sets its position to the mouse's position
        size = self.rect.size
        self.rect.x = pygame.mouse.get_pos()[0]-size[0]/2 #adjusts for offset so that it's centred
        self.rect.y = pygame.mouse.get_pos()[1]-size[1]/2

# Creates a button that turns grey when hovered over and triggers a function when activated
class Button(Frame):
    # used to setup appearance of button
    def _setup_image(self, button_data: ButtonData):
        # load image (if applicable)
        if "Image" in button_data:
            new_image = button_data["Image"]
            # do not attempt to fill on outline 
            outline_thickness = 0
            if self.outline["Thickness"] > 0:
                outline_thickness = self.outline["Thickness"]
            # create rect to fill with
            rect_width = self.rect.width - outline_thickness*2
            rect_height = self.rect.height - outline_thickness*2
            new_image = pygame.transform.scale(new_image, (rect_width, rect_height))
            self.image.blit(new_image, (outline_thickness, outline_thickness))

        # for becoming grey/not
        GREY_LEVEL = 100 # level of darkness to apply

        # create black layer
        darkEffect = pygame.Surface(self.image.get_size())
        darkEffect.fill((0,0,0))
        darkEffect.set_alpha(GREY_LEVEL)

        #copy image
        self.baseImage = self.image.copy()
        self.greyImage = self.image.copy()

        # overlay dark layer with image
        self.greyImage.blit(darkEffect, (0, 0))

    # used for more effective inheritance
    def _setup_button(self, button_data: ButtonData):
        self._setup_image(button_data)

        # bind button press events and store keys for later
        self.stored_keys = {} # for unbinding when deleted
        if "ButtonDown" in button_data:
            def func():
                self._activate(button_data["ButtonDown"])
            self.stored_keys["keydown"] = input_handler.bind_to_input(1, func, "keydown")
        if "ButtonUp" in button_data:
            def func():
                self._activate(button_data["ButtonUp"])
            self.stored_keys["keyup"] = input_handler.bind_to_input(1, func, "keyup")
    

    def __init__(self, position: tuple, size: tuple, button_data: ButtonData, layer: int=1, background: Fill = None, outline: Outline = None):
        super().__init__(position, size, layer, background, outline)
        button_data = get_button_data(button_data)

        # setup text if applicable
        if "Text" in button_data:
            self._setup_text(button_data["Text"], outline)

        self._setup_button(button_data)

    def _get_outline_thickness(self, outline: Outline):
        # check if outline
        if outline:
            outlineThickness = outline["Thickness"]
        else:
            outlineThickness = 0
        
        return outlineThickness

    # for creating text buttons with centred text
    def _setup_text(self, textData: TextData, outline: Outline):
        # get thickness of outline
        outlineThickness = self._get_outline_thickness(outline)

        # add text to button
        y_offset = self.rect.height/2
        if "Size" in textData:
            y_offset -= textData["Size"]/2

        TextLabel._setupText(self, textData, outlineThickness, y_offset-outlineThickness)

    def _activate(self, func: callable):
        # mouse must be touching button
        mousePos = pygame.mouse.get_pos()
        if not isPointInBounds(mousePos, (self.rect.x, self.rect.y), (self.rect.size)):
            return

        # button must be visible
        if not topSprites.has(self):
            return

        # run bound function
        func()
        # play button sound
        env.audio_assets["button"].play()

    def update(self):
        # get position and pressed state of mouse
        mousePos = pygame.mouse.get_pos()
        # mouse inside button
        if not isPointInBounds(mousePos, (self.rect.x, self.rect.y), (self.rect.size)):
            # remove any grey effect once mouse leaves
            self.image = self.baseImage
            return

        # apply grey hover effect
        self.image = self.greyImage
    
    def try_destroy(self):
        super().try_destroy()

        # unbind all inputs
        for key in self.stored_keys:
            input_handler.unbind_input(1, self.stored_keys[key], key)

    def set_image(self, image: pygame.Surface | None):
        super()._redraw(self.rect.topleft, self.rect.size, self._layer, self.fill, self.outline)
        if image:
            self._setup_image({"Image": image})
        else:
            self._setup_image({})
        

# Creates a button with a side image and text
class DetailedButton(Button):
    def _setup_text(self, textData: TextData, outline: Outline):
        # get outline thickness
        outlineThickness = self._get_outline_thickness(outline)

        # add text to button
        x_offset = self.rect.width/3
        y_offset = self.rect.height/2
        TextLabel._setupText(self, textData, x_offset+outlineThickness, y_offset-outlineThickness)

    def _setup_image(self, image: pygame.image, outline: Outline):
        # get outline thickness
        outlineThickness = self._get_outline_thickness(outline)

        # add image to button
        imageSize = image.get_size()
        x_offset = self.rect.width/3
        scale = x_offset/imageSize[0]
        imageSize = (imageSize[0]*scale, imageSize[1]*scale)
        imageSurface = pygame.transform.smoothscale(image, imageSize)
        self.image.blit(imageSurface, (outlineThickness,0))

    def __init__(self, position: tuple, size: tuple, buttonData: ButtonData, layer: int=1, background: Fill = None, outline: Outline = None):
        Frame.__init__(self, position, size, layer, background, outline)

        Button._setup_button(self, buttonData)