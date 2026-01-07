# allows for binding functions to inputs beginning and ending
import pygame

# custom modules
import env

keydown_functions = {
  # pygame.key: [function, function]
}

keyup_functions = {
  # pygame.key: [function, function]
}

# stores all active joysticks
joysticks = []

# function for all inputs to be bound to joysticks
joystick_initialise_func = None

# similar to keydown/keyup funcs but for joysticks exclusively
joystick_functions = {
    # controller id: {event.type: {key: [function, function]}}
}

# store movement of axis
joystick_axis_movement = {
    # controller id: {axis: value}
}

mouse_pos = (0,0) # stores position of mouse from last click

# checks if a key is being pressed down
def _run_bound_functions(button, functions_list: dict):
    if button in functions_list:
        # runs all bound functions
        for function in functions_list[button]:
            function()

# runs every frame, handles all bound events
def handle_inputs():
  global mouse_pos
# handle all key presses
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
        env.running = False # ends the game if the window is cloxed
    elif event.type == pygame.KEYDOWN:
        _run_bound_functions(event.key, keydown_functions)
    elif event.type == pygame.KEYUP:
        _run_bound_functions(event.key, keyup_functions)
    # special support for mouse buttons (numbered)
    elif event.type == pygame.MOUSEBUTTONDOWN:
        button = event.button 
        mouse_pos = event.pos # save click position
        _run_bound_functions(button, keydown_functions)
    elif event.type == pygame.MOUSEBUTTONUP:
        button = event.button
        mouse_pos = event.pos
        _run_bound_functions(button, keyup_functions)
    # removes controllers when they are disconnected
    elif event.type == pygame.JOYDEVICEREMOVED:
        joystick_num = event.joy
        joystick = joysticks[joystick_num]
        joystick.quit()
        joysticks.remove(joystick)
    # sets up new joysticks
    elif event.type == pygame.JOYDEVICEADDED:
        id = event.device_index
        joystick = pygame.joystick.Joystick(id)
        joysticks.insert(id, joystick)
        # runs the initialisation function (if present)
        if joystick_initialise_func:
            joystick_initialise_func(joystick)
    # detect controller inputs
    elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
        # env.output_for_debugging(str(event.button))
        controller_id = event.joy
        bound_event_types = _get_dict(controller_id, joystick_functions)
        bound_keys = _get_list(event.type, bound_event_types)
        _run_bound_functions(event.button, bound_keys)
    # also detect controller axis inputs
    elif event.type == pygame.JOYAXISMOTION:
        # env.output_for_debugging(str(event.axis)+" "+str(event.value))
        controller_id = event.joy
        bound_event_types = _get_dict(controller_id, joystick_functions)
        bound_keys = _get_list(event.type, bound_event_types)
        # store value of axis
        controller_axes = _get_dict(controller_id, joystick_axis_movement)
        controller_axes[event.axis] = event.value
        # run functions after
        _run_bound_functions(event.axis, bound_keys)
        

# gets corresponding var for input type
def _get_variable(keydown_or_keyup: str):
    # assign to appropriate input type
    if keydown_or_keyup == "keydown":
        target_functions = keydown_functions
    else:
        target_functions = keyup_functions
    return target_functions

# makes sure dict exists 
def _get_dict(key, from_dict: dict):
    # creates new list if not present
    if not key in from_dict:
        from_dict[key] = {}
    return from_dict[key]

# makes sure list exists 
def _get_list(key, from_dict: dict):
    # creates new list if not present
    if not key in from_dict:
        from_dict[key] = []
    return from_dict[key]


# makes a function run when a key is down
def bind_to_input(key: pygame.key, func: callable, keydown_or_keyup="keydown"):
    global keydown_functions, keyup_functions

    # assign to appropriate input type
    target_functions = _get_variable(keydown_or_keyup)

    # creates new list if not present
    if key in target_functions:
        target_functions[key].append(func)
    else:
        target_functions[key] = []
        target_functions[key].append(func)
    
    return func

# binds an key to a function at an elevated priority (runs first)
def bind_at_priority(key: pygame.key, func: callable, keydown_or_keyup="keydown"):
    global keydown_functions, keyup_functions

    # assign to appropriate input type
    target_functions = _get_variable(keydown_or_keyup)

    # creates new list if not present
    if key in target_functions:
        target_functions[key].insert(0, func)
    else:
        target_functions[key] = []
        target_functions[key].insert(0, func)
    
    return func

# unbinds a function from an input
def unbind_input(key: pygame.key, func: callable, keydown_or_keyup="keydown"):
    # use appropriate input type
    target_functions = _get_variable(keydown_or_keyup)
    func_list = target_functions[key]

    # remove all instances of bound function
    for idx, stored_func in enumerate(func_list):
        if stored_func == func:
            func_list.pop(idx)

# binds to initialising a controller
def bind_to_joystick_init(func: callable):
    global joystick_initialise_func
    joystick_initialise_func = func

# similar to bind to input but for joysticks
def bind_to_joystick_input(key: int, func: callable, controller_id: int=0, event_type=pygame.JOYBUTTONDOWN):
    global joystick_functions

    # get list of existing bound functions or create new
    event_types = _get_dict(controller_id, joystick_functions)
    bound_keys = _get_dict(event_type, event_types)
    bound_functions = _get_list(key, bound_keys)

    bound_functions.append(func)

    return func

# binds joystick input at an elevated priority (runs first)
def bind_to_joystick_at_priority(key: int, func: callable, controller_id: int=0, event_type=pygame.JOYBUTTONDOWN):
    global joystick_functions

    # get list of existing bound functions or create new
    event_types = _get_dict(controller_id, joystick_functions)
    bound_keys = _get_dict(event_type, event_types)
    bound_functions = _get_list(key, bound_keys)

    bound_functions.insert(0, func)

    return func

def unbind_all_inputs():
    global keydown_functions, keyup_functions, joystick_functions
    keydown_functions = {}
    keyup_functions = {}
    joystick_functions = {}