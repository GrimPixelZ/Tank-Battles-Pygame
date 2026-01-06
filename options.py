# used for the options screen
import pygame
# custom imports
import ui, env, input_handler

Y_PIXEL_STEP = 100 # gap between options
LABEL_WIDTH = 600
SLIDER_X_CLAMP = 300

options = [] # holds all options
options_count = 0 # number of options elements currently active

def _get_y_offset():
    y_offset = options_count * Y_PIXEL_STEP + 50
    return y_offset

def _correct_toggle_image(toggle_button: ui.Button, button_state):
    if button_state:
        toggle_button.set_image(env.img_assets["tick"])
    else:
        toggle_button.set_image(None)

def _create_option_label(option_name: str, y_pos: int):
    # create text for option name
    text_label = ui.TextLabel(
        (env.WIDTH/4, y_pos),
        (LABEL_WIDTH, 200),
        {"Text": option_name, "Size": 50},
        background={"Transparency": 1}
    )
    options.append(text_label)

def create_toggle_option(option_name: str, toggle_func: callable, initial_state: bool=False):
    global options_count
    y_offset = _get_y_offset()

    # create text for option name
    _create_option_label(option_name, y_offset)

    # defined above for use in wrapper func
    toggle_button = None

    # create button to toggle option
    # wrapped so that it can pass in button state
    button_state = initial_state
    def toggle_wrapper():
        nonlocal button_state # required to access
        button_state = not button_state
        toggle_func(button_state)

        _correct_toggle_image(toggle_button, button_state)

    BUTTON_LENGTH = 50
    toggle_button = ui.Button(
        (env.WIDTH/4+LABEL_WIDTH-BUTTON_LENGTH/2, y_offset+BUTTON_LENGTH/2),
        (BUTTON_LENGTH, BUTTON_LENGTH),
        {"ButtonUp": toggle_wrapper},
        background={"Colour":env.WHITE},
        outline={"Thickness":10}
    )
    options.append(toggle_button)

    # ensure image is correct
    _correct_toggle_image(toggle_button, button_state)

    options_count += 1

# shows slider values every frame
class SliderController(pygame.sprite.Sprite):
    def __init__(self, update_func: callable):
        super().__init__()
        self.update_func = update_func

        # create blank image and rect
        self.image = pygame.Surface((0,0))
        self.rect = pygame.rect.Rect(0,0,0,0)
    
    def try_destroy(self):
        self.kill()

    def update(self):
        self.update_func()

def create_slider_option(option_name: str, slider_func: callable, slider_start: int=1, slider_end: int=100, slider_step: int=1, current_value: int=1):
    global options_count
    y_offset = _get_y_offset()

    _create_option_label(option_name, y_offset)

    # precalculate slider button position
    SLIDER_HEIGHT = 50
    SLIDER_WIDTH = 100
    button_pos = (500+2*SLIDER_X_CLAMP-SLIDER_WIDTH/2, y_offset+SLIDER_HEIGHT/2)
    button_size = (SLIDER_WIDTH, SLIDER_HEIGHT)

    # create background of slider
    BACKGROUND_HEIGHT = 10
    slider_background = ui.Frame(
        (500+SLIDER_X_CLAMP, button_pos[1]+SLIDER_HEIGHT/2-BACKGROUND_HEIGHT/2),
        (SLIDER_X_CLAMP*2, BACKGROUND_HEIGHT),
        0,
        {
            "Colour": env.BLACK
        }
    )
    options.append(slider_background)

    # defined early for use in function
    slider_button = None
    slider_controller = None

    def get_slider_value():
        slider_x_prop = (slider_button.x - slider_button.min_x) / (slider_button.max_x - slider_button.min_x)
        slider_current_value = (slider_end - slider_start) * slider_x_prop + slider_start
        rounded_to_step = (slider_current_value // slider_step) * slider_step
        return rounded_to_step

    # ensures slider starts in the correct position
    def get_slider_position(current_pos: int):
        slider_x_prop = (current_pos - slider_start) / (slider_end - slider_start)
        slider_x = slider_x_prop * (slider_button.max_x - slider_button.min_x) + slider_button.min_x
        return slider_x

    # empty function used so buttons make clicking sounds
    def sound_maker():
        pass

    def slider_button_up():
        if slider_button.is_dragging:
            rounded_to_step = get_slider_value()
            slider_func(rounded_to_step)

            # emulates button press (for sound etc)
            slider_button._activate(sound_maker)
    
    # input must be listened to outside of button (otherwise it checks if mouse is in button)
    input_handler.bind_to_input(1, slider_button_up, "keyup") # this is okay because leaving options unbinds all inputs

    slider_button = ui.DraggableButton(
        button_pos, 
        button_size, 
        {"XClamp":SLIDER_X_CLAMP, "YClamp": 0, "ButtonDown": sound_maker},
        background={"Colour":env.WHITE},
        outline={"Thickness":10}
    )
    options.append(slider_button)

    # correct slider position
    slider_button.x =  get_slider_position(current_value)
    slider_button.rect.centerx = slider_button.x

    slider_value_label = ui.TextLabel(
        button_pos,
        button_size,
        {
            "Text": str(current_value),
            "Size": 25
        },
        2,
        {
            "Transparency": 1
        }
    )
    options.append(slider_value_label)

    # runs every frame to show current slider value
    def update_func():
        nonlocal slider_value_label

        rounded_to_step = get_slider_value()

        slider_value_label.try_destroy()
        slider_value_label = ui.TextLabel(
            (slider_button.x-SLIDER_WIDTH/4, slider_button.y-SLIDER_HEIGHT/2),
            button_size,
            {
                "Text": str(int(rounded_to_step)),
                "Size": 25
            },
            2,
            {
                "Transparency": 1
            }
        )
        options.append(slider_value_label)

    slider_controller = SliderController(update_func)
    options.append(slider_controller)
    env.top_sprites.add(slider_controller)

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

def _set_FPS(slider_pos: int):
    env.FPS = slider_pos

def _set_volume(volume: float):
    volume /= 100
    pygame.mixer.music.set_volume(volume)

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
    # create_toggle_option("Music:", _toggle_music, music_on)
    create_slider_option("FPS:", _set_FPS, 15, 240, 5, env.FPS)
    create_slider_option("Music:", _set_volume, 0, 100, 1, volume*100)