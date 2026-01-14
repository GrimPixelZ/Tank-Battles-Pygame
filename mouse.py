# used for controller support during ui navigation
import pygame, math
# custom imports
import env, generic, input_handler

mouse_speed = 750

mice = []
last_mouse_positions = {
    # player_num: pos
} # for newly spawned mice to use their prior position

# helper functions
# used for handling joycon axis movement
def get_controller_axis_value(axis: int, player_num: int):
  offset = max(0, player_num-1)
  controller_axes = input_handler.joystick_axis_movement[offset]
  axis_value = controller_axes[axis]
  return axis_value

# changes the global mouse speed
def change_mouse_speed(new_speed: float):
    global mouse_speed
    for mouse in mice:
        mouse.speed = new_speed
    mouse_speed = new_speed

# returns the closest mouse position to another position (used by UI for grey hover effect and sliders)
def get_nearest_pos(position: tuple):
    closest_distance = math.inf
    closest_pos = None

    def check_pos_is_closer(mouse_pos: tuple):
        nonlocal closest_distance, closest_pos
        # calculate magnitude to position
        dx = position[0] - mouse_pos[0]
        dy = position[1] - mouse_pos[1]
        magnitude = math.hypot(dx, dy)
        if magnitude < closest_distance:
            closest_distance = magnitude
            closest_pos = mouse_pos

    # check all active mice to see if they are closer
    for mouse in mice:
        mouse_pos = mouse.get_pos()
        check_pos_is_closer(mouse_pos)
    
    # also check true mouse
    check_pos_is_closer(pygame.mouse.get_pos())

    return closest_pos
    
# removes all currently active controller cursors
def clear_joystick_cursors():
  for cursor in mice:
    cursor.try_destroy()

class PlayerCursor(generic.PhysicsObject):
    # used for trying to click with right trigger
    def _try_right_trigger_click(self):
        axis_value = get_controller_axis_value(pygame.CONTROLLER_AXIS_TRIGGERRIGHT, self.player_num)
        if axis_value > 0.9: # fully held down
            self.left_click_down()
        else:
            self.left_click_up() # let go

    def __init__(self, colour: pygame.Color, player_num: int=0):
        super().__init__()

        self.image = pygame.transform.smoothscale(env.img_assets["cursor"], (50, 60))
        self.rect = self.image.get_rect()
        generic.recolour_image(self.image, env.WHITE, colour)

        # try to set position to last position if possible
        if player_num in last_mouse_positions:
            pos = last_mouse_positions[player_num]
            self.rect.center = pos

        # set stats of mouse
        self.speed = mouse_speed

        # save player mouse is for
        self.player_num = player_num

        # set initial state of move directions
        self.dx = 0
        self.dy = 0

        # set last input type (up or down)
        # this is needed to prevent mouse up events firing without mouse down being fired first
        self.last_event = None

        # make sure always on top
        self._layer = 5

        # listen to inputs from controller
        controller_id = max(player_num-1, 0)
        # store keys to unbind later
        self.stored_keys = []
        # detect right trigger "clicks"
        key = input_handler.bind_to_joystick_input(
            pygame.CONTROLLER_AXIS_TRIGGERRIGHT,
            lambda: self._try_right_trigger_click(),
            controller_id,
            pygame.JOYAXISMOTION
        )
        self.stored_keys.append(key)

        # move in given directions
        key = input_handler.bind_to_joystick_input(
            pygame.CONTROLLER_AXIS_LEFTY,
            lambda: self.set_speed(pygame.CONTROLLER_AXIS_LEFTY, "y"),
            controller_id,
            pygame.JOYAXISMOTION
        )
        self.stored_keys.append(key)

        key = input_handler.bind_to_joystick_input(
            pygame.CONTROLLER_AXIS_LEFTX,
            lambda: self.set_speed(pygame.CONTROLLER_AXIS_LEFTX, "x"),
            controller_id,
            pygame.JOYAXISMOTION
        )
        self.stored_keys.append(key)

        # add to top sprites for updating
        env.top_sprites.add(self)
        # add to mice list for tracking
        mice.append(self)

    
    # return the current position of the mouse pointer
    def get_pos(self):
        pos = self.rect.topleft

        # apply offset (to tip of finger)
        X_OFFSET = 34/2
        Y_OFFSET = 7/2

        true_pos = (pos[0]+X_OFFSET, pos[1]+Y_OFFSET)
        return true_pos

    # sets speed to a given value
    def set_speed(self, axis: int, x_or_y: str):
        axis_value = get_controller_axis_value(axis, self.player_num)
        TOLERANCE = 0.02
        if abs(axis_value) < TOLERANCE:
            axis_value = 0
        
        if x_or_y == "x":
            self.dx = axis_value
        elif x_or_y == "y":
            self.dy = axis_value

    def move(self):
        # makes movement ignore FPS
        dt = env.get_deltatime()

        # calculate magnitude of direction
        magnitude = math.hypot(self.dx, self.dy)

        # do not proceed if 0 magnitude (no movement direction)
        if magnitude == 0:
            return

        # calculate x and y proportions
        x_prop = self.dx/magnitude
        y_prop = self.dy/magnitude

        x_speed = x_prop * self.speed
        y_speed = y_prop * self.speed

        self.rect.x += x_speed*dt # moves player position by speed
        self.rect.y += y_speed*dt
    
    # for when left click is initially pressed
    def left_click_down(self):
        # custom events to emulate mouse clicks
        mouse_down = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=self.get_pos(),
            player=self.player_num # pass in player who click belonged to
        )

        # tell pygame mouse was clicked
        pygame.event.post(mouse_down)

        self.last_event = pygame.MOUSEBUTTONDOWN
    
    # for when left click is released
    def left_click_up(self):
        # must only fire if the "mouse" was previously pressed down
        if self.last_event != pygame.MOUSEBUTTONDOWN:
            return

        # custom events to emulate mouse clicks
        mouse_up = pygame.event.Event(
            pygame.MOUSEBUTTONUP,
            button=1,
            pos=self.get_pos(),
            player=self.player_num
        )

        # tell pygame mouse was clicked
        pygame.event.post(mouse_up)

        self.last_event = pygame.MOUSEBUTTONUP

    # move in direction every frame
    def update(self):
        # give physics-like behaviour to prevent exiting screen
        super().update()
        self.move()

    # unbind all inputs and remove self
    def try_destroy(self):
        # unbind all bound inputs
        for key in self.stored_keys:
            pass
        mice.remove(self)
        # save current position (for if respawned)
        last_mouse_positions[self.player_num] = self.rect.center
        # remove self
        self.kill()
