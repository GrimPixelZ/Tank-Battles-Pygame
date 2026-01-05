# used for the options screen
import pygame
# custom imports
import ui, env, input_handler

Y_PIXEL_STEP = 100 # gap between options

options = [] # holds all options
options_count = 0 # number of options elements currently active

def correct_toggle_image(toggle_button: ui.Button, button_state):
    if button_state:
        toggle_button.set_image(env.img_assets["tick"])
    else:
        toggle_button.set_image(None)

def create_toggle_option(option_name: str, toggle_func: callable, initial_state: bool=False):
    global options_count
    y_offset = options_count * Y_PIXEL_STEP + 50

    # create text for option name
    LABEL_WIDTH = 600
    text_label = ui.TextLabel(
        (env.WIDTH/4, y_offset),
        (LABEL_WIDTH, 200),
        {"Text": option_name, "Size": 50},
        background={"Transparency": 1}
    )
    options.append(text_label)

    # defined above for use in wrapper func
    toggle_button = None

    # create button to toggle option
    # wrapped so that it can pass in button state
    button_state = initial_state
    def toggle_wrapper():
        nonlocal button_state # required to access
        button_state = not button_state
        toggle_func(button_state)

        correct_toggle_image(toggle_button, button_state)

    BUTTON_LENGTH = 50
    toggle_button = ui.Button(
        (env.WIDTH/4+LABEL_WIDTH, y_offset+BUTTON_LENGTH/2),
        (BUTTON_LENGTH, BUTTON_LENGTH),
        {"ButtonUp": toggle_wrapper},
        background={"Colour":env.WHITE},
        outline={"Thickness":10}
    )
    options.append(toggle_button)

    # ensure image is correct
    correct_toggle_image(toggle_button, button_state)

    options_count += 1


def _close_game():
    env.running = False

def _toggle_multiplayer(state: bool):
    env.MULTIPLAYER = state

def _toggle_music(state: bool):
    if state:
        pygame.mixer.music.set_volume(1)
    else:
        pygame.mixer.music.set_volume(0)

def initialise_options(return_func: callable=_close_game):
    global options
    # wrapper for return function
    def return_wrapper():
        global options_count
        for option in options:
            option.try_destroy()
        options_count = 0
        input_handler.unbind_all_inputs()
        return_func()

    input_handler.bind_to_input(
        pygame.K_ESCAPE,
        return_wrapper
    )

    # create return button
    options_button = ui.Button(
        (50, 50),
        (300, 180),
        {"ButtonUp": return_wrapper, "Text": {"Text": "BACK", "Size": 100}},
        background={"Colour":env.WHITE},
        outline={"Thickness": 10}
    )
    options.append(options_button)

    create_toggle_option("Multiplayer:", _toggle_multiplayer, env.MULTIPLAYER)
    volume = pygame.mixer.music.get_volume()
    music_on = volume > 0
    create_toggle_option("Music:", _toggle_music, music_on)