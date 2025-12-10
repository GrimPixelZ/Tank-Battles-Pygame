# This script is used to render screen elements over the rest of the game
import pygame
import typing

# get globals
import env
import input_handler # for buttons

# Display for drawing onto
display = env.display

# Sprite groups
allSprites = env.allSprites
topSprites = env.topSprites

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
class Text(typing.TypedDict):
    Font: pygame.font.Font
    Colour: typing.Tuple[int, int, int]
    Size: float
    Transparency: float
    Text: str
    TextWraps: bool

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

def getText(text: Text):
    if not text:
        text = {}

    textContent = ""
    if "Text" in text:
        textContent = text["Text"]

    colour = (0,0,0)
    if "Colour" in text:
        colour = text["Colour"]

    fontName = "arial"
    if "Font" in text:
        fontName = text["Font"]
    fontName = pygame.font.match_font(fontName)

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


# Actual classes
class Frame(pygame.sprite.Sprite):
    def __init__(self, position: tuple, size: tuple, layer: int, fill: Fill = None, outline: Outline = None):
        pygame.sprite.Sprite.__init__(self)
        self.rect = pygame.Rect(position[0], position[1], size[0], size[1])
        self.image = pygame.Surface(size, pygame.SRCALPHA)

        # Layer element renders at
        self._layer = layer

        # Calculate outline to be applied, if applicable
        outlineRect = None
        if outline:
            outline = getOutline(outline)
            thickness = outline["Thickness"]
            outlineRect = pygame.Rect(position[0]+thickness, position[1]+thickness, size[0]-2*thickness, size[1]-2*thickness)
            r, g, b = outline["Colour"]
            a = outline["Transparency"]
            self.image.fill((r,g,b,a))

        # Fill rect (excluding outline) with fill colour
        fill = getFill(fill)
        r, g, b = fill["Colour"]
        a = fill["Transparency"]
        self.image.fill((r, g, b, a), outlineRect)
        self.visible = False
        topSprites.add(self)
    

# Renders text placed onto a frame
class TextLabel(Frame):
    def __init__(self, position: tuple, size: tuple, text: Text, layer: int=1, background: Fill = None, outline: Outline = None):
        super().__init__(position, size, layer, background, outline)
        text = getText(text)
        font = text["Font"]
        colour = text["Colour"]
        
        # wrap text or not
        if text["TextWraps"]:
            # Wrap text to fit the frame width
            lines = wrapText(text["Text"], font, self.rect.width)

            # Render each line
            y_offset = 0
            line_height = font.get_linesize()
            for line in lines:
                surface = font.render(line, True, colour)
                self.image.blit(surface, (0, y_offset))
                y_offset += line_height
        else:
            surface = font.render(text["Text"], True, colour)
            self.image.blit(surface, (0,0))

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
    def __init__(self, position: tuple, size: tuple, func: callable, layer: int=1, background: Fill = None, outline: Outline = None):
        super().__init__(position, size, layer, background, outline)
        self.func = func # function run when button is pressed

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

        input_handler.bindToInput(1, self._activate, "keyup")
    
    def _activate(self):
        # run bound function
        self.func()
        # play button sound

    def update(self):
        # get position and pressed state of mouse
        mousePos = pygame.mouse.get_pos()
        mouseDown = pygame.mouse.get_pressed()[0]
        # mouse inside button
        if not isPointInBounds(mousePos, (self.rect.x, self.rect.y), (self.rect.size)):
            # remove any grey effect once mouse leaves
            self.image = self.baseImage
            return

        # apply grey hover effect
        self.image = self.greyImage