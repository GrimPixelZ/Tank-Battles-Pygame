# allows for binding functions to inputs beginning and ending
import pygame

# custom modules
import env

keydownFunctions = {
  # pygame.KEY: [function, function]
}

keyupFunctions = {
  # pygame.KEY: [function, function]
}

# runs every frame, handles all bound events
def handleInputs():
# handle all key presses
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
        env.running = False # ends the game if the window is cloxed
    elif event.type == pygame.KEYDOWN:
        if event.key in keydownFunctions:
            # runs all bound functions
            for function in keydownFunctions[event.key]:
                function()
    elif event.type == pygame.KEYUP:
        if event.key in keyupFunctions:
            # runs all bound functions
            for function in keyupFunctions[event.key]:
                function()
    # special support for mouse buttons (numbered)
    elif event.type == pygame.MOUSEBUTTONDOWN:
        button = event.button 
        if button in keydownFunctions:
            # runs all bound functions
            for function in keydownFunctions[button]:
                function()
    elif event.type == pygame.MOUSEBUTTONUP:
        button = event.button
        if button in keyupFunctions:
            # runs all bound functions
            for function in keyupFunctions[button]:
                function()

# makes a function run when a key is down
def bindToInput(key: pygame.key, func: callable, keydownOrKeyup="keydown"):
    global keydownFunctions, keyupFunctions

    # assign to appropriate input type
    if keydownOrKeyup == "keydown":
        targetFunctions = keydownFunctions
    else:
        targetFunctions = keyupFunctions

    # creates new list if not present
    if key in targetFunctions:
        targetFunctions[key].append(func)
    else:
        targetFunctions[key] = []
        targetFunctions[key].append(func)
