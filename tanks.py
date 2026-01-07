import pygame
import random
import objgraph

# custom modules
import env, enemy, generic, ui, input_handler, misc, player as plr, save_handler, options, mouse

# load enemy data
from Data import enemy_data

display = env.display

#assign background mw usic and its volume
pygame.mixer.music.set_volume(1)

# runs every frame
game_loop = None

# creates cursors for all controller players
def create_joystick_cursors(*args):
 # must have controllers connected
 if len(input_handler.joysticks) == 0:
   return
 for idx, joystick in enumerate(input_handler.joysticks):
      if env.MULTIPLAYER:
        idx += 1 # controllers cannot be main player on multiplayer
      mouse.PlayerCursor(plr.Player.get_player_colour(idx), idx)


# runs every frame when the main menu is open
def main_menu_loop():
  env.top_sprites.update() # update menu buttons

# runs every frame when a round is in progress
def mid_game_loop():
  global pause_initial_time
  #do not run if paused
  if paused and pause_initial_time == -1: #checks whether the game is paused for the first time
    pause_initial_time = pygame.time.get_ticks() #sets the last time the game was paused
  if not paused:
    if env.ticks_paused != 0: #resets variable for how long the game was paused for
      env.ticks_paused = 0
    if pause_initial_time != -1:
      env.ticks_paused = pygame.time.get_ticks()-pause_initial_time #sets how long the game was paused for
      pause_initial_time = -1 #resets paused state
    spawn_enemies()
    spawn_loot()
    # env.score = collisions(env.score)
    env.bottom_sprites.update()
    enemy.mobs.update()
    env.all_sprites.update()
    env.top_sprites.update()
    # checks if any enemies can spawn now
    check_score_enemies()

    # draws all to the screen
    draw_all()
    # collisions done after they are shown
    collisions()
    # show shot cooldownwwa
    plr.show_cooldown()
    # show score and money earned
    env.draw_text(env.display, "Score: "+str(env.score), 18, env.WIDTH / 2, 20)
    env.draw_text(env.display, "Money: "+str(tank_base.money), 18, env.WIDTH / 2, 40)
    # show additional stats in debug mode
    if env.DEBUG_MODE:
      env.draw_text(env.display, "Health: "+str(tank_base.health)+"/"+str(tank_base.max_health), 18, env.WIDTH / 2, 60)
      env.draw_text(env.display, "Ticks: "+str(pygame.time.get_ticks()), 18, env.WIDTH / 2, 80)
      env.draw_text(env.display, "FPS: "+str(round(env.clock.get_fps(), 1)), 18, env.WIDTH / 2, 100)
      env.draw_text(env.display, env.current_debug_output, 18, env.WIDTH / 2, 120)
  env.top_sprites.update()

  if env.clock.get_fps() >= 30:
    pygame.mouse.set_visible(False) #makes the mouse invisible if game isn't lagging
  else:
    pygame.mouse.set_visible(True)

# creates the main menu
def initialise_main_menu():
  global game_loop
  game_loop = main_menu_loop
  menu_objects = []
  # game title
  game_title = ui.TextLabel(
    (500, 0),
    (900, 300),
    {"Text": "Tank Battles: Pygame", "Size": 100},
    1,
    {"Transparency": 1}
  )
  menu_objects.append(game_title)

  def close_menu():
    for obj in menu_objects:
      obj.try_destroy()
    mouse.clear_joystick_cursors()
    input_handler.unbind_all_inputs()
  
  # button for playing the game
  def play_func():
    close_menu()
    initialise_round()
  play_button = ui.Button(
    (600, 400), 
    (735, 180), 
    {"Text": {"Text": "PLAY", "Size": 100, "Font": env.font_assets["connection"]}, "ButtonUp": play_func}, 
    1, 
    {"Colour": env.WHITE}, 
    {"Thickness": 10}
  )
  menu_objects.append(play_button)
  # button for accessing options
  def options_func():
    close_menu()
    options.initialise_options(initialise_main_menu)
    create_joystick_cursors()
  options_button = ui.Button(
    (600, 600), 
    (735, 180), 
    {"Text": {"Text": "OPTIONS", "Size": 100, "Font": env.font_assets["connection"]}, "ButtonUp": options_func}, 
    1, 
    {"Colour": env.WHITE}, 
    {"Thickness": 10}
  )
  menu_objects.append(options_button)
  # button for exiting game
  def exit_func():
    env.running = False
  exit_button = ui.Button(
    (600, 800), 
    (735, 180), 
    {"Text": {"Text": "EXIT", "Size": 100, "Font": env.font_assets["connection"]}, "ButtonUp": exit_func}, 
    1, 
    {"Colour": env.WHITE}, 
    {"Thickness": 10}
  )
  menu_objects.append(exit_button)
  # indicator for high score
  score = str(env.high_score)
  text = "High Score: "+score
  x_offset = 35*len(score)-35
  high_score_indicator = ui.TextLabel(
    (env.WIDTH-400-x_offset, 0),
    (400+x_offset, 100),
    {"Text": text, "Size": 50},
    1,
    {"Transparency": 1}
  )
  menu_objects.append(high_score_indicator)

  # bind inputs for quickly exiting and starting the game
  input_handler.bind_to_input(
    pygame.K_ESCAPE,
    exit_func
  )
  input_handler.bind_to_input(
    pygame.K_SPACE,
    play_func
  )

  # create console cursor if applicable
  create_joystick_cursors()
  # also work for joysticks initialised later
  input_handler.bind_to_joystick_init(create_joystick_cursors)
      

# deloads the game and opens the menu
def end_game():
  env.all_sprites.empty()
  env.top_sprites.empty()
  env.bottom_sprites.empty()
  misc.pickups.empty()
  enemy.mobs.empty()
  plr.players.empty()
  plr.players_list = []
  # update high score if new record achieved
  if env.score > env.high_score:
    env.update_high_score(env.score)
    # also saves new score
    save_handler.update_save()

  env.score = 0
  pygame.mouse.set_visible(True)
  pygame.mixer.music.stop()
  mouse.clear_joystick_cursors()
  input_handler.unbind_all_inputs()
  initialise_main_menu()

# starts a game round
tank_base = None
paused = None
pause_initial_time = None # <0 to indicate no pause to check for
def initialise_round():
  global tank_base, paused, game_loop, pause_initial_time
  crosshair = ui.Cursor((25,25), 10, env.img_assets["crosshair"], {"Transparency": 1}) # initialise cursor
  env.crosshair = crosshair
  tank_base = plr.Player()

  pygame.mixer.music.play(loops=-1) #infinitely loops the bgm
  pause_initial_time = -1 # <0 to indicate no pause to check for
  paused = False #initialises the variable for whether the game is paused

  # initialise any joystick players who failed to join
  if env.MULTIPLAYER:
    for joystick in input_handler.joysticks:
      setup_controller_player(joystick)
  else:
    # also initialise controller for singleplayer
    if len(input_handler.joysticks) > 0:
      bind_controller_inputs()

  input_handler.bind_to_joystick_init(setup_controller_player)
  bind_all_inputs()

  game_loop = mid_game_loop

# set initial game loop
initialise_main_menu()

# game helper functionsind
# gets random item from a weighted pool
def weighted_random(weighted_pool: dict):
  total_weight = 0
  for enemy in weighted_pool:
    total_weight += weighted_pool[enemy]
  roll = random.randint(1, total_weight)
  # go through enemies again and pick enemy that roll landed on
  total_weight = 0
  for enemy in weighted_pool:
    total_weight += weighted_pool[enemy]
    # roll lands within enemy's weight range
    if total_weight >= roll:
      return enemy



spawn_pool = {
  "soldier": enemy_data.enemies["soldier"]["SpawnWeight"] 
} # all enemies that are currently spawnable
def spawn_enemies():  
  BASE_SPAWN_CHANCE = 0.33
  # increase spawn chance with env.score
  spawn_chance = BASE_SPAWN_CHANCE
  CHANCE_PER_SCORE = 0.001
  spawn_chance += CHANCE_PER_SCORE*env.score
  # do not spawn more/less enemies depending on frame-rate
  dt = env.get_deltatime()
  spawn_chance *= dt

  if random.random() < spawn_chance:
    # pick enemy to spawn using weighted system
    enemy = weighted_random(spawn_pool)
    # load enemy's data for its cluster size
    my_data = enemy_data.enemies[enemy] 
    #spawns enemies in clusters close together
    xpos = random.randint(0, env.WIDTH) #generates 'centre' of enemy cluster
    ypos = random.randint(0, env.HEIGHT)
    VARIATION = 100 # random spread from positions
    # increase max cluster size with env.score
    max_cluster_size = my_data["MaxClusterSize"]
    max_cluster_size += max_cluster_size*env.score/1000
    max_cluster_size = int(max_cluster_size)

    cluster_size = random.randint(my_data["MinClusterSize"], max_cluster_size)
    for _ in range(cluster_size):
      new_xpos = random.randint(max(0, xpos - VARIATION), min(env.WIDTH, xpos + VARIATION))
      new_ypos = random.randint(max(0, ypos - VARIATION), min(env.HEIGHT, ypos + VARIATION))
      place_object((new_xpos, new_ypos), enemy)

# checks whether the core threshold has been met to unlock any new enemies
old_score = 0
def check_score_enemies():
  global old_score
  # only check if score changed
  if env.score == old_score:
    return
  
  old_score = env.score # update old env.score

  for enemy in enemy_data.enemies:
    # enemy must not already be spawned
    if enemy in spawn_pool:
      continue

    # adds enemy to spawn pool
    if enemy_data.enemies[enemy]["SpawningScore"] <= env.score:
      env.output_for_debugging("added "+enemy+" to spawn pool")
      spawn_pool[enemy] = enemy_data.enemies[enemy]["SpawnWeight"]


def spawn_loot():
    if random.randint(1,5000) == 5:
      health_pickup_amount = 0
      for item in misc.pickups:
        if item.type == "health":
          health_pickup_amount += 1
      if health_pickup_amount < 2:
        xpos = random.randint(0, env.WIDTH) 
        ypos = random.randint(0, env.HEIGHT)
        p = misc.HealthPickup((xpos, ypos), False, "health") 
        env.bottom_sprites.add(p)

def place_object(position, type):
  # misc.pickups
  if type == "health": #for placing objects manually (e.g. debug tools)
    object = misc.HealthPickup(position, False, "health") 
    env.bottom_sprites.add(object)
  elif type == "coin":
    for x in range(5):
      object = misc.Coin(position, True, type, 10)
      env.bottom_sprites.add(object)
    env.output_for_debugging("Coins: "+str(len(misc.pickups)))
  else:
    my_data = enemy_data.enemies[type]
    # apply class override for special enemies:
    if "Class" in my_data:
      my_class = getattr(enemy, my_data["Class"])
    else:
      my_class = enemy.Enemy
    object = my_class(position, False, type) 
    env.bottom_sprites.add(object)


def collisions():
  mobs_hit_player = pygame.sprite.groupcollide(plr.players, enemy.mobs, False, False, generic.rect_circle_collide)
  player_touched_pickup = pygame.sprite.groupcollide(plr.players, misc.pickups, False, False, generic.rect_circle_collide)

  for player in mobs_hit_player:
    hit_mobs = mobs_hit_player[player]
    for mob in hit_mobs:
      mob.try_destroy()
      player.try_destroy(mob.damage)
  
  for player in player_touched_pickup:
    hit_pickups = player_touched_pickup[player]
    for pickup in hit_pickups:
      pickup.try_destroy()

# draws all sprites to screen
def draw_all():
  env.bottom_sprites.draw(env.display)
  enemy.mobs.draw(env.display)
  env.all_sprites.draw(env.display) #draws the sprites to the screen
  env.top_sprites.draw(env.display)

# controller input helper functions
# gets current player
def get_player_by_num(player_num: int):
  return plr.players_list[player_num]

# used for handling joycon axis movement
def get_controller_axis_value(axis: int, player_num: int):
  offset = max(0, player_num-1)
  controller_axes = input_handler.joystick_axis_movement[offset]
  axis_value = controller_axes[axis]
  return axis_value

def try_right_trigger_shoot(player_num: int):
  axis_value = get_controller_axis_value(pygame.CONTROLLER_AXIS_TRIGGERRIGHT, player_num)
  player = get_player_by_num(player_num)
  if axis_value > 0.9: # fully held down
    player.shooting = True
  else:
    player.shooting = False # let go

def controller_set_speed(axis: int, x_or_y: str, player_num: int):
  axis_value = get_controller_axis_value(axis, player_num)
  TOLERANCE = 0.02
  player = get_player_by_num(player_num)
  if abs(axis_value) < TOLERANCE:
    player.set_speed(x_or_y, 0)
  else:
    player.set_speed(x_or_y, axis_value)


# for binding controllers to plr.players
def bind_controller_inputs(joystick: pygame.joystick.Joystick=None, player_num: int=0):
  player = get_player_by_num(player_num)
  controller_id = max(player_num-1, 0)

  # bound_inputs = [
  #   # [id, key, keydown]
  # ]

  # toggle pause
  input_handler.bind_to_joystick_input(
      7, # waffle
      # lambda: globals().__setitem__("paused", not paused),
      end_game,
      controller_id
  )

  # start shooting
  input_handler.bind_to_joystick_input(
      pygame.CONTROLLER_AXIS_TRIGGERRIGHT,
      lambda: try_right_trigger_shoot(player_num),
      controller_id,
      pygame.JOYAXISMOTION
  )

  # move in given directions
  input_handler.bind_to_joystick_input(
    pygame.CONTROLLER_AXIS_LEFTY,
    lambda: controller_set_speed(pygame.CONTROLLER_AXIS_LEFTY, "y", player_num),
    controller_id,
    pygame.JOYAXISMOTION
  )

  input_handler.bind_to_joystick_input(
    pygame.CONTROLLER_AXIS_LEFTX,
    lambda: controller_set_speed(pygame.CONTROLLER_AXIS_LEFTX, "x", player_num),
    controller_id,
    pygame.JOYAXISMOTION
  )

  # set aim direction
  input_handler.bind_to_joystick_input(
    pygame.CONTROLLER_AXIS_RIGHTX,
    lambda: player.change_bullet_direction("x", get_controller_axis_value(pygame.CONTROLLER_AXIS_RIGHTX, player_num)),
    controller_id,
    pygame.JOYAXISMOTION
  )

  input_handler.bind_to_joystick_input(
    pygame.CONTROLLER_AXIS_RIGHTY,
    lambda: player.change_bullet_direction("y", get_controller_axis_value(pygame.CONTROLLER_AXIS_RIGHTY, player_num)),
    controller_id,
    pygame.JOYAXISMOTION
  )

  input_handler.bind_to_joystick_input(
    5,
    lambda: player.switch_weapon(1),
    controller_id
  )

  input_handler.bind_to_joystick_input(
    4,
    lambda: player.switch_weapon(-1),
    controller_id
  )


# runs when a controller is connected; creates player and binds their inputs
def setup_controller_player(joystick: pygame.joystick.Joystick):
  if env.MULTIPLAYER:
    new_player = plr.Player()
    player_num = new_player.player_num
    bind_controller_inputs(joystick, player_num)
  else:
    bind_controller_inputs(joystick, 0)


# bind all keybinds
def bind_all_inputs():
  # lambda works to "define" functions
  # stop the game running
  # input_handler.bind_to_input(
  #     pygame.K_ESCAPE,
  #     lambda: setattr(env, "running", False)
  # )
  input_handler.bind_to_input(
    pygame.K_ESCAPE,
    end_game
  )

  # toggle pause
  input_handler.bind_to_input(
      pygame.K_p,
      lambda: globals().__setitem__("paused", not paused)
  )

  # start shooting when spacebar is pressed
  input_handler.bind_to_input(
      pygame.K_SPACE,
      lambda: setattr(tank_base, "shooting", True)
  )

  # also shoot for left mouse button
  input_handler.bind_to_input(
      1,
      lambda: setattr(tank_base, "shooting", True)
  )

  # stop shooting when spacebar let go
  input_handler.bind_to_input(
      pygame.K_SPACE,
      lambda: setattr(tank_base, "shooting", False),
      "keyup"
  )

  # also stop shooting when mouse let go
  input_handler.bind_to_input(
      1,
      lambda: setattr(tank_base, "shooting", False),
      "keyup"
  )

  # move in given directions
  input_handler.bind_to_input(
    pygame.K_w,
    lambda: tank_base.apply_speed("y", -1)
  )

  key1 = input_handler.bind_to_input(
    pygame.K_UP,
    lambda: tank_base.apply_speed("y", -1)
  )

  input_handler.bind_to_input(
    pygame.K_s,
    lambda: tank_base.apply_speed("y", 1)
  )

  input_handler.bind_to_input(
    pygame.K_DOWN,
    lambda: tank_base.apply_speed("y", 1)
  )

  input_handler.bind_to_input(
    pygame.K_a,
    lambda: tank_base.apply_speed("x", -1)
  )

  input_handler.bind_to_input(
    pygame.K_LEFT,
    lambda: tank_base.apply_speed("x", -1)
  )

  input_handler.bind_to_input(
    pygame.K_d,
    lambda: tank_base.apply_speed("x", 1)
  )

  input_handler.bind_to_input(
    pygame.K_RIGHT,
    lambda: tank_base.apply_speed("x", 1)
  )

  # apply opposite speed when let go
  input_handler.bind_to_input(
    pygame.K_w,
    lambda: tank_base.apply_speed("y", 1),
    "keyup"
  )

  input_handler.bind_to_input(
    pygame.K_UP,
    lambda: tank_base.apply_speed("y", 1),
    "keyup"
  )

  input_handler.bind_to_input(
    pygame.K_s,
    lambda: tank_base.apply_speed("y", -1),
    "keyup"
  )

  input_handler.bind_to_input(
    pygame.K_DOWN,
    lambda: tank_base.apply_speed("y", -1),
    "keyup"
  )

  input_handler.bind_to_input(
    pygame.K_a,
    lambda: tank_base.apply_speed("x", 1),
    "keyup"
  )

  input_handler.bind_to_input(
    pygame.K_LEFT,
    lambda: tank_base.apply_speed("x", 1),
    "keyup"
  )

  input_handler.bind_to_input(
    pygame.K_d,
    lambda: tank_base.apply_speed("x", -1),
    "keyup"
  )

  input_handler.bind_to_input(
    pygame.K_RIGHT,
    lambda: tank_base.apply_speed("x", -1),
    "keyup"
  )

  input_handler.bind_to_input(
    pygame.K_e,
    lambda: tank_base.switch_weapon(1)
  )

  input_handler.bind_to_input(
    pygame.K_q,
    lambda: tank_base.switch_weapon(-1)
  )

  input_handler.bind_to_input(
    pygame.K_PAGEDOWN,
    lambda: tank_base.switch_weapon(1)
  )

  input_handler.bind_to_input(
    pygame.K_PAGEUP,
    lambda: tank_base.switch_weapon(-1)
  )


  # dev tools
  if env.DEBUG_MODE:
    input_handler.bind_to_input(
        pygame.K_F1,
        lambda: setattr(tank_base, "health", tank_base.health + 1)
    )

    input_handler.bind_to_input(
        pygame.K_F2,
        lambda: place_object(pygame.mouse.get_pos(), "health")
    )

    input_handler.bind_to_input(
        pygame.K_F3,
        lambda: place_object(pygame.mouse.get_pos(), "soldier")
    )

    input_handler.bind_to_input(
        pygame.K_F4,
        lambda: place_object(pygame.mouse.get_pos(), "brute")
    )

    input_handler.bind_to_input(
        pygame.K_F5,
        lambda: place_object(pygame.mouse.get_pos(), "tank")
    )

    input_handler.bind_to_input(
        pygame.K_F6,
        lambda: place_object(pygame.mouse.get_pos(), "ferret")
    )

    input_handler.bind_to_input(
      pygame.K_F7,
      lambda: setattr(tank_base, "pierce", tank_base.pierce + 1)
    )

    input_handler.bind_to_input(
      pygame.K_F8,
      lambda: setattr(tank_base, "bullets", tank_base.bullets + 1)
    )

    def inc_score():
      env.score += 10000

    input_handler.bind_to_input(
      pygame.K_F9,
      inc_score
    )

    input_handler.bind_to_input(
      pygame.K_F10,
      lambda: place_object(pygame.mouse.get_pos(), "coin")
    )

    def wrapper():
      plr.Player()

    input_handler.bind_to_input(
      pygame.K_F11,
      # lambda: place_object(pygame.mouse.get_pos(), "bomber")
      wrapper
    )

  # for identifying memory leaks
  # def wrapper():
  #   print("Showing growth:")
  #   objgraph.show_growth(limit=30)


#main program
while env.running: #runs the game loop
  # draw background
  env.display.fill(env.WHITE) 

  env.clock.tick(env.FPS) #ticks the env.clock based on the set env.FPS
  
  # runs the current game loop
  game_loop()
  
  # draws all to the screen
  draw_all()

  pygame.display.flip() #shows everything that was drawn on the screen

  # handle all key presses
  input_handler.handle_inputs()

#print(pygame.mouse.get_pos()) #prints the mouse position to terminal (x, y)

pygame.quit() #quits program when it stops running