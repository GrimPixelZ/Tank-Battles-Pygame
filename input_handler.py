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

offsets = {
    "keydown": {
        # pygame.key: [(int, offset(int))]
    },
    "keyup": {
    },
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

# checks if a key is being pressed down
def _run_bound_functions(button, functions_list: dict):
    if button in functions_list:
        # runs all bound functions
        for function in functions_list[button]:
            function()

# runs every frame, handles all bound events
def handle_inputs():
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
        _run_bound_functions(button, keydown_functions)
    elif event.type == pygame.MOUSEBUTTONUP:
        button = event.button
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
        

# initialises the offset
def _init_offset(key: pygame.key, keydown_or_keyup="keydown"):
    offsets[keydown_or_keyup][key] = []

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
        _init_offset(key, keydown_or_keyup)
    
    idx = len(target_functions[key])-1
    # print("Would return", idx, "for", key)
    # shift idx by offset (so it remains accurate)
    offset = _get_offset(key, idx, keydown_or_keyup)
    idx -= offset

    # print("Returning", idx, "for", key)
    return idx

def _get_offset(key: pygame.key, idx: int, keydown_or_keyup="keydown"):
     # get offset (from previously removed idx)
    offset_list = offsets[keydown_or_keyup][key]
    target_offset = 0 # offset to use
    for offset_tuple in offset_list:
        if offset_tuple[0] >= idx:
            break
        target_offset = offset_tuple[1]
    return target_offset

# unbinds a function from an input
def unbind_input(key: pygame.key, idx: int, keydown_or_keyup="keydown"):
    # get offset (from previously removed idx)
    offset_list = offsets[keydown_or_keyup][key]
    target_offset = _get_offset(key, idx, keydown_or_keyup)
    new_idx = idx + target_offset
    # offset the offsets due to item getting removed
    target_idx = 0 # gets index to insert at
    insert_new = True # whether to create new offset
    for offset_idx, offset_tuple in enumerate(offset_list):
        if offset_tuple[0] > idx:
            offset_list[offset_idx] -= 1
        elif offset_tuple[0] == idx: # exact idx found, do not insert new
            insert_new = False
            offset_list[offset_idx] = (idx, offset_tuple[1]-1)
        else:
            target_idx = offset_idx
    if insert_new:
        offset_list.insert(target_idx, (idx, -1))
    # remove the item from the list
    target_functions = _get_variable(keydown_or_keyup)
    target_functions[key].pop(new_idx)

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

