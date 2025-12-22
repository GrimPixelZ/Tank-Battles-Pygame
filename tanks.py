import pygame
import random
import math
import copy
import numpy

# custom modules
import env
import ui
import input_handler

# load enemy data
from Data import enemy_data, pickup_data, weapon_data

# load data from env
#values for window size
WIDTH = env.WIDTH
HEIGHT = env.HEIGHT
FPS = env.FPS #frames per second

#predefined colours
BLACK = env.BLACK
WHITE = env.WHITE
RED = env.RED
GREEN = env.GREEN
BLUE = env.BLUE

# player recolour options
PLAYER_COLOURS = [
  (102, 171, 255), # blue
  (137, 205, 82), # green
  (140, 0, 255), # purple
  (0, 249, 255), # teal
]

# whether to show debug values etc
DEBUG_MODE = env.DEBUG_MODE

display = env.display # sets the pygame display
clock = env.clock # sets the pygame clock (used for timer-based events)
bottom_sprites = env.bottom_sprites
all_sprites = env.all_sprites # group for updating all sprites
top_sprites = env.top_sprites # sprites that go at the very top

#assign background music and its volume
background_music = env.background_music
pygame.mixer.music.set_volume(1)

img_assets = env.img_assets
audio_assets = env.audio_assets

default_font = env.DEFAULT_FONT

# helper functions
draw_text = env.draw_text

def place_pickup(type: str, position: tuple, value: int):
  if type == "health":
    pickup = HealthPickup(position, True, type, value)
  elif type == "coin":
    pickup = Coin(position, True, type, value)
  bottom_sprites.add(pickup)

# changes all pixels of given color in image; outsourced externally
def recolour_image(image: pygame.image, target_colour: list, replacement_colour: list, tolerance: float=30):
  arr = pygame.surfarray.pixels3d(image)
    
  # Calculate color difference per pixel
  diff = numpy.sqrt(numpy.sum((arr - target_colour) ** 2, axis=2))
  
  # Mask of pixels within tolerance
  mask = diff <= tolerance
  
  # Replace colors
  arr[mask] = replacement_colour

# collides with walls, etc
class PhysicsObject(pygame.sprite.Sprite):
  def _stay_in_bounds(self):
    #keeps the object within bounds of the map
    if self.rect.right > WIDTH:
      self.x = WIDTH - self.rect.width/2
      self.rect.centerx = self.x
    if self.rect.left < 0:
      self.x = 0 + self.rect.width/2
      self.rect.centerx = self.x
    if self.rect.bottom > HEIGHT:
      self.y = HEIGHT - self.rect.height/2
      self.rect.centery = self.y
    if self.rect.top < 0:
      self.y = 0 + self.rect.height/2
      self.rect.centery = self.y     

  def update(self):
    #keeps the object within bounds of the map
    self._stay_in_bounds()

class Player(PhysicsObject):
  def __init__(self):
    pygame.sprite.Sprite.__init__(self) #marks object as a pygame sprite
    self.image = pygame.transform.scale(img_assets["tank_base"], (50, 50)) #applies image texture to player
    self.rect = self.image.get_rect() #assigns tillihe player's recent
    self.rect.center = (WIDTH / 2, HEIGHT / 2) #centres the player in the middle of the screen

    # get player number
    player_num = len(players_list)
    self.player_num = player_num

    # for multiplayer and iframes image
    self._apply_player_colouring(player_num)

    # set stats
    self.speed = 385 #initial speed of the player without power ups
    self.max_health = 10 #sets the maximum health of the player
    self.shot_cooldown = 400 #initialises the delay between weapon attacks
    self.pierce = 0 # number of enemies bullets can pierce
    self.pickup_range = 150 #initialises the player's pickup pickup range

    # set initial states
    self.health = self.max_health #sets the initial player health
    self.iticks = 0 #initialises the amount of ticks the player is invincible for
    self.maxiticks = 200 #sets the maximum number of invincibility ticks each time the player is damaged
    self.iticks_start = 0 #marks when the player's iticks were last started
    self.shooting = False #marks whether the player is currently shooting or not
    self.initial_shot_time = 200 #used for determining how long ago the last bullet was fired, reassigned each time
    self.bullet_direction = None # used to override bullet direction 
    self.money = 0 #initialises how much money the player has
    self.unlocked_weapons = ["pellet", "minigun", "shotgun", "mega_shotgun"] # which weapons the player has unlocked
    self.current_weapon = 0 # idx of current weapon
    # initial movement
    self.dx = 0
    self.dy = 0

    # add itself to the sprite group for updating
    all_sprites.add(self)
    # also add to players lists
    players.add(self)
    players_list.append(self)

    # setup starter weapon and tank gun
    self._setup_weapon("pellet")

    # create health bar
    self.health_container = HealthContainer("container", self)

  # changes colour (for multiplayer) along with making iframes appearance
  def _apply_player_colouring(self, player_num: int):
    # get player colour
    player_colour = PLAYER_COLOURS[player_num]

    # if not player one, recolour self
    if player_num > 0:
      recolour_image(self.image, PLAYER_COLOURS[0], player_colour)

    # create iframes appearance
    self.original_image = self.image.copy()
    self.iframes_image = self.image.copy()
    # create whitened version of normal image
    r = player_colour[0]
    g = player_colour[1]
    b = player_colour[2]
    R_SHIFT = 53
    G_SHIFT = 29
    B_SHIFT = 30
    new_r = min(255, r+R_SHIFT)
    new_g = min(255, g+G_SHIFT)
    new_b = min(255, b+G_SHIFT)
    iframes_colour = (new_r, new_g, new_b)
    recolour_image(self.iframes_image, player_colour, iframes_colour)

  # applies speed in a certain direction; used by inputs
  def apply_speed(self, axis: str, dir: int):
    if axis == "x":
      self.dx += dir
    elif axis == "y":
      self.dy += dir

  # sets speed to a given value
  def set_speed(self, axis: str, dir: int):
    if axis == "x":
      self.dx = dir
    elif axis == "y":
      self.dy = dir

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
  
  def _create_bullet(self, target_pos: tuple):
    bullet = PlayerBullet(self.rect.center, target_pos, self.pierce) #initialises a new bullet object at the player's location
    player_bullets.add(bullet) #adds the bullet to a list of player bullets, used for detecting collision with enemies
    all_sprites.add(bullet) #adds the bullet to the list of all existing sprites, used for updating sprites each tick

  # creates bullets that go in a specific direction
  def _create_bullet_in_direction(self, dx: float, dy: float):
     # make larger so they aren't interrupted by any sort of game delay
      DISTANCE = 500
      # get position of target
      target_y = self.rect.centery + dy * DISTANCE
      target_x = self.rect.centerx + dx * DISTANCE
      # draw line for debugging
      # pygame.draw.line(display, RED, (self.rect.centerx, self.rect.centery), (target_x, target_y), 3)
      # spawn bullet
      self._create_bullet((target_x, target_y))

  def shoot(self):
    if (pygame.time.get_ticks() - self.initial_shot_time) >= self.shot_cooldown: #determines whether the cooldown for shooting is over
      self.initial_shot_time = pygame.time.get_ticks() #sets how long ago the last bullet was fired
      direction = self.bullet_direction
      if not direction: # allow direction overrides (e.g. joycons)
        self._create_bullet(crosshair.rect.center)
      else:
        self._create_bullet_in_direction(direction[0], direction[1])
      # draw line for debugging
      # pygame.draw.line(display, RED, (self.rect.centerx, self.rect.centery), crosshair.rect.center, 3)
      # fire additional bullets (e.g. shotgun)
      if self.bullets > 1:
        adjacent_length = crosshair.rect.centerx-self.rect.centerx
        opposite_length = crosshair.rect.centery-self.rect.centery
        if not direction:
          start_dir = math.atan2(opposite_length, adjacent_length) # must use atan2 to take signs into consideration
        else:
          start_dir = math.atan2(direction[1], direction[0])
        ANGLE_INCREMENT = math.radians(5) # how separated new bullets should be
        # print("Start bullet direction:", start_dir)

        for bullet_num in range(1, self.bullets):
          # generate spread of bullets
          bullet_dir = ANGLE_INCREMENT
          angle_multiplier = bullet_num
          # switch sides if even
          if bullet_num % 2 == 0:
            # print("Changing side of bullet", bullet_num)
            bullet_dir *= -1
            # make sure all gaps are the same angle apart
            angle_multiplier /= 2
          # get correct angle for bullet
          bullet_dir *= angle_multiplier
          # print("Angle offset for bullet", bullet_num, "is", angle_multiplier*ANGLE_INCREMENT, "with mult", angle_multiplier)
          # offset by start direction
          bullet_dir += start_dir
          # print("Bullet direction: "+str(bullet_dir)+" bullet num: "+str(bullet_num))
          # split direction to spawn bullet in (relative to self)
          dy = math.sin(bullet_dir)
          dx = math.cos(bullet_dir)
          self._create_bullet_in_direction(dx, dy)

      # play firing sound
      audio_assets["tank_shoot"].play()
  
  # for changing aim direction
  def change_bullet_direction(self, axis: str, value: float):
    # do not change to default if joystick settles
    TOLERANCE = 0.02
    if abs(value) < TOLERANCE:
      return

    # make sure exists to avoid errors
    if not self.bullet_direction:
      self.bullet_direction = (0, 0)

    if axis == "x":
      self.bullet_direction = (value, self.bullet_direction[1])
    elif axis == "y":
      self.bullet_direction = (self.bullet_direction[0], value)


  def add_health(self, value):
    successful = True
    if self.health < self.max_health:
      self.health += value
      audio_assets["heal"].play()
    else:
      successful = False
    return successful
  
  def try_destroy(self, damage):
    if self.iticks == 0:
      if self.health >= 1:
        self.health -= damage
        self.iticks = self.maxiticks
        self.iticks_start = pygame.time.get_ticks()
        audio_assets["tank_hit"].play()
      else:
        all_sprites.remove(self)
        all_sprites.remove(self.tank_gun)
        self.rect.center = (-5000, -5000) # position offscreen
  
  # removes any otherwise lingering remnants of last weapon
  def _deload_weapon(self):
    # remove old tank gun
    self.tank_gun.kill()

  # loads new weapon
  def _setup_weapon(self, weapon: str):
    # create new tank gun
    self.tank_gun = TankGun(self, crosshair.rect, weapon)

    # load stats of weapon
    my_data = weapon_data.weapons[weapon]

    self.pierce = my_data["Pierce"]
    self.range = my_data["Range"]
    self.shot_cooldown = my_data["Cooldown"]
    self.bullets = my_data["Bullets"]

  def switch_weapon(self, step: int=1):
    new_idx = self.current_weapon + step
    new_idx = pygame.math.clamp(new_idx, 0, len(self.unlocked_weapons)-1) # ensure value is within bounds
    current_weapon = self.unlocked_weapons[new_idx]

    self._deload_weapon()
    self._setup_weapon(current_weapon)
    self.current_weapon = new_idx

  def update(self):
    super().update() #makes sure the player cannot leave the bounds of the map
    if ticks_paused != 0: #prevent pause abuse to remove shot cooldown
      self.initial_shot_time += ticks_paused
    self.move()
    if self.iticks == 0: #changes appearance to indicate invincibility
      self.image = self.original_image.copy()
    else:
      self.image = self.iframes_image.copy()
    if (pygame.time.get_ticks() - self.iticks_start) >= self.iticks: #resets iframes when over
      self.iticks = 0
    
    if self.shooting == True:
      self.shoot()
    
class TankGun(pygame.sprite.Sprite):
  def __init__(self, parent, target: pygame.rect.Rect, gun_name: str="pellet"): 
    pygame.sprite.Sprite.__init__(self)
    # load data
    my_data = weapon_data.weapons[gun_name]
    pivot = my_data["Pivot"]
    image_size = my_data["ImageSize"]
    image_name = my_data["Image"]

    self.image = pygame.transform.smoothscale(img_assets[image_name], image_size)
    self.rect = self.image.get_rect()
    self.rect.centerx = parent.rect.centerx-17
    self.rect.centery = parent.rect.centery
    self.parent = parent
    self.original_image = self.image
    # recolour for multiplayer and iframes
    if hasattr(self.parent, "player_num"):
      Player._apply_player_colouring(self, self.parent.player_num)

    # set target to point at
    self.target = target
    # set direction override (if applicable)
    self.direction = None
    # set pivot point to rotate around
    self.pivot = pivot

    # add itself to sprite group for updating
    all_sprites.add(self)
  
  def rotate(self):
    pos = self.parent.rect.center
    # self.image = self.original_image.copy()
    # pivot_pos = (self.image.get_size()[0]-16, self.image.get_size()[1]-16)
    pivot_pos = self.pivot

    #calculates the angle of rotation
    if not self.direction:
      if self.target.centerx-self.rect.centerx == 0: #prevents division by zero
        x_change = self.target.centerx-self.rect.centerx+1
      else:
        x_change = self.target.centerx-self.rect.centerx
      rotation = math.atan(((HEIGHT-self.target.centery)-(HEIGHT-self.rect.centery))/(x_change))*(180/math.pi) #calculates the rotation needed to face the tank
      if self.target.centerx < self.rect.centerx:
        rotation += 180 #corrects rotation if the crosshair is on the left-hand side of the bullet
      rotation += 180 #corrects rotation
    else: # used by joycon
      rotation = math.atan2(self.direction[1], -self.direction[0])*(180/math.pi)
      # env.output_for_debugging("Angle: "+str(rotation))

    #offset from pivot to center
    image_rect = self.image.get_rect(topleft = (pos[0]-pivot_pos[0], pos[1]-pivot_pos[1]))
    offset_center_to_pivot = pygame.math.Vector2(pos)-image_rect.center
    
    #rotated offset from pivot to center
    rotated_offset = offset_center_to_pivot.rotate(-rotation)

    #rotated image center
    rotated_image_center = (pos[0]-rotated_offset.x, pos[1]-rotated_offset.y)

    # get a rotated image
    rotated_image = pygame.transform.rotozoom(self.image, rotation, 1)
    rotated_image_rect = rotated_image.get_rect(center = rotated_image_center)

    #switch to rotated image
    #surf.blit(rotated_image, rotated_image_rect)
    self.image = rotated_image
    self.rect = rotated_image_rect
    # draw rectangle around the image
    #pygame.draw.rect(surf, (255, 0, 0), (*rotated_image_rect.topleft, *rotated_image.get_size()),2)
  
  def update(self):
    #resets image to original appearance
    # only works for players
    if hasattr(self.parent, "iticks"): #changes appearance to indicate invincibility
      if self.parent.iticks != 0:
        self.image = self.iframes_image.copy()
      else:
        self.image = self.original_image.copy()
    else:
      self.image = self.original_image.copy()
    
    # apply direction override (if joycon)
    if hasattr(self.parent, "bullet_direction"):
      if self.parent.bullet_direction:
        self.direction = self.parent.bullet_direction
      else:
        self.direction = None
    
    self.rect.centerx = self.parent.rect.centerx-17 #offsets appearance relative to base
    self.rect.centery = self.parent.rect.centery
    self.rotate() #sets image to rotated version
    #self.blit_rotate(display, self.image, (self.parent.rect.center), (self.image.get_size()[0]-16, self.image.get_size()[1]-16), self.rotation)

class HealthContainer(pygame.sprite.Sprite):
  def __init__(self, type="container", player: Player=None):
    pygame.sprite.Sprite.__init__(self)
    #different behaviour based on whether it is the outer image or inner image
    # image is 730 by 670
    self.WIDTH = 730/4
    self.HEIGHT = 670/4

    if type == "container":
      self.image = pygame.transform.smoothscale(img_assets["health_container"], (self.WIDTH, self.HEIGHT))
    elif type == "inner":
      self.image = pygame.transform.smoothscale(img_assets["health_container_inner"], (self.WIDTH, self.HEIGHT))
      self.base_image = self.image.copy()
      if env.MULTIPLAYER:
        recolour_image(self.base_image, (255, 99, 99), PLAYER_COLOURS[player.player_num])
    self.rect = self.image.get_rect()
    self.rect.center = ((self.image.get_size()[0]/2+5, self.image.get_size()[1]/2+5))
    # shift along by player number
    BASE_SHIFT = 200
    shift = BASE_SHIFT * player.player_num
    self.rect.centerx += shift

    self.player = player

    self.type = type
    top_sprites.add(self)

    if type == "container":
      health_container_inner = HealthContainer("inner", player) 
      health_container_inner.parent = self
  
  def update(self):
    if self.type == "inner":
      #calculates what size it should be to represent the current health
      dampening_factor = 0.9
      # must be greater than 0 (or crash)
      player = self.player
      multiplier = (player.health/player.max_health)*dampening_factor
      x_size = max(0, ((self.WIDTH)*multiplier))
      y_size = max(0, ((self.HEIGHT)*multiplier))
      size = (x_size, y_size)

      self.image = self.base_image.copy()
      self.image = pygame.transform.smoothscale(self.image, size)
      self.rect = self.image.get_rect()
      self.rect.center = self.parent.rect.center


# generic enemy base class
class Enemy(PhysicsObject):
  def __init__(self, position, is_spawned=False, enemy_type="soldier"): #define stats and enemy_type
    pygame.sprite.Sprite.__init__(self)

    # get data of enemy enemy_type
    my_data = enemy_data.enemies[enemy_type]

    # setup appearance, hitbox and position
    # applies image override if applicable
    image = enemy_type
    if "Image" in my_data:
      image = my_data["Image"]
    
    # applies image size override if applicable
    if "ImageSize" in my_data:
      self.image = pygame.transform.smoothscale(img_assets[image], my_data["ImageSize"])
    else:
      self.image = pygame.transform.smoothscale(img_assets[image])
    # set up recolours if applicable
    if "Recolour" in my_data:
      for recolour_data in my_data["Recolour"]:
        recolour_image(self.image, recolour_data["TargetColour"], recolour_data["ReplacementColour"], recolour_data["Tolerance"])
    # sets radius for collision
    if "Radius" in my_data:
      self.radius = my_data["Radius"]
    
    # initialises rect
    self.rect = self.image.get_rect()
    self.rect.center = position
    self.rect.center = position
    self.x = self.rect.centerx
    self.y = self.rect.centery

    # show debug hitbox
    if DEBUG_MODE and hasattr(self, "radius"):
      # pygame.draw.circle(self.image, BLUE, (self.image.get_width() // 2, self.image.get_height() // 2), self.radius)
      pass

    # sets default image
    self.base_image = self.image.copy()

    # setup stats
    self.speed = my_data["Speed"] # enemy movement speed
    self.neg_speed = self.speed*(-1) # used to reduce calculations later
    self.xspeed = 2.0 # used so things don't sometimes break
    self.yspeed = 2.0
    self.damage = my_data["Damage"] # damage mob deals to player
    self.health = my_data["Health"]

    # load loot
    self.score_value = my_data["Score"]
    self.loot = copy.deepcopy(my_data["Loot"])
    loot_deletion_list = [] # list of loot to remove if chance is not met; dict cannot change size during iteration
    for loot_type in self.loot:
      # only drops if chance is met
      chance = self.loot[loot_type]["Chance"]
      if random.random() > chance:
        loot_deletion_list.append(loot_type)
        continue

      amount = self.loot[loot_type]["Amount"]
      amount_type = type(amount)
      if amount_type == tuple: # generates random amount
        amount = random.randint(amount[0], amount[1])
        self.loot[loot_type]["Amount"] = amount # must overwrite so it does not change later
      elif amount_type == list:
        amount = amount[0]

      for attribute in self.loot[loot_type]:
        # generates any random distributions
        potential_tuple = self.loot[loot_type][attribute]
        if type(potential_tuple) != tuple:
          continue
        # only run if tuple
        
        self.loot[loot_type][attribute] = []
        for idx in range(0, amount):
          new_value = random.randint(potential_tuple[0], potential_tuple[1])
          self.loot[loot_type][attribute].append(new_value)
      
    # deletes all loot that failed to drop
    for loot_type in loot_deletion_list:
      del self.loot[loot_type] # removes from loot table

    # setup spawn indicator or direct spawn
    self.is_spawned = is_spawned #determines whether to be an x or not
    if is_spawned == False:
      self.initial_time = pygame.time.get_ticks()
    self.neg_xspeed = None
    self.neg_yspeed = None

  # after spawn is prepared
  def _spawn_complete(self):
    #initialises spawn
    self.image = self.base_image
    self.is_spawned = True
    # find the nearest player to the enemy (their target)
    nearest_player = self._get_closest_player()
    self.target = nearest_player

    mobs.add(self)
    bottom_sprites.remove(self)
    #all_sprites.add(self)

  def prepare_spawn(self): #if not force spawned, create a spawn indicator
    self.image = pygame.transform.smoothscale(img_assets["unspawned_enemy"], (32, 32))
    if pygame.time.get_ticks() - self.initial_time >= 2000: #timer before spawning
      #initialises spawn
      self._spawn_complete()

  def _get_closest_player(self):
    closest_dist = math.inf
    closest_player = tank_base

    for player in players:
      dist_to, _, _ = self._get_distance_to(player)
      if dist_to < closest_dist:
        closest_dist = dist_to
        closest_player = player
    
    return closest_player

  def _get_distance_to(self, player: Player):
    # move towards player by default
    target_pos = player.rect.center

    dx = target_pos[0] - self.x
    dy = target_pos[1] - self.y
    magnitude = math.hypot(dx, dy)

    return magnitude, dx, dy

  def _get_direction_to(self, player: Player):
    # draw line of movement
    if DEBUG_MODE:
      # pygame.draw.line(display, RED, (self.x, self.y), target_pos, 3)
      pass

    magnitude, dx, dy = self._get_distance_to(player)

    # adjust for proportion
    dx /= magnitude
    dy /= magnitude
    
    return dx, dy

  def _move_in_direction(self, dx, dy):
    # makes movement ignore FPS
    dt = env.get_deltatime()

    # apply speed
    self.xspeed = dx*self.speed
    self.yspeed = dy*self.speed

    # move at end of frame
    self.x += self.xspeed*dt
    self.y += self.yspeed*dt #separate non-rounded x/y values used
    self.rect.centerx = self.x
    self.rect.centery = self.y

  # move directly towards player
  def _direct_movement(self):
    # get direction towards player
    dx, dy = self._get_direction_to(self.target)
    
    # move in direction
    self._move_in_direction(dx, dy)

  # for enemies with radii
  def _circle_collision(self, other_enemy):
    dx = self.x - other_enemy.x
    dy = self.y - other_enemy.y
    magnitude = math.hypot(dx, dy)

    # ignore magnitudes of 0 (to avoid crash)
    if magnitude == 0:
      return

    if not hasattr(self, "radius"):
      self_radius = self.rect.width/2
    else:
      self_radius = self.radius

    if not hasattr(other_enemy, "radius"):
      other_enemy_radius = other_enemy.rect.width/2
    else:
      other_enemy_radius = other_enemy.radius

    min_dist = self_radius + other_enemy_radius # overlap distance

    # enemies are colliding
    if magnitude < min_dist:
      overlap_dist = min_dist-magnitude # amount to push back by

      # normalise direction
      dx /= magnitude
      dy /= magnitude

      # push them apart; cut in half so both enemies move equally
      self.x += dx * overlap_dist * 0.5
      self.y += dy * overlap_dist * 0.5
      other_enemy.x -= dx * overlap_dist * 0.5
      other_enemy.y -= dy * overlap_dist * 0.5

      self.rect.center = (self.x, self.y)
      other_enemy.rect.center = (other_enemy.x, other_enemy.y)

  # bounce off other enemies
  def _collide_with_enemies(self):
    # collide with other enemies
    for other_enemy in mobs:
      # ignore itself
      if other_enemy == self:
        continue
      
      # # ignore rect enemies (like tank)
      # if not hasattr(other_enemy, "radius"):
      #   continue

      self._circle_collision(other_enemy)

  # move towards player
  def move(self):
    self._direct_movement()
    self._collide_with_enemies()

  def rotate(self, target_rect: pygame.rect.Rect):
    #point towards player``
    self.image = self.base_image.copy()
    if target_rect.centerx-self.rect.centerx == 0: #prevents division by zero
      self.x_change = target_rect.centerx-self.rect.centerx+1
    else:
      self.x_change = target_rect.centerx-self.rect.centerx
    self.rotation = math.atan(((HEIGHT-target_rect.centery)-(HEIGHT-self.rect.centery))/(self.x_change))*(180/math.pi) #calculates the rotation needed to face the tank
    if target_rect.centerx < self.rect.centerx:
      self.rotation = self.rotation+180 #corrects rotation if the tank is on the left-hand side of the soldier
    #print("rotation", self.rotation)
    #print("tank base x", target_rect.x)
    #print("tank base y", target_rect.y)
    #print("enemy x", self.rect.x)
    #print("enemy y", self.rect.y)
    self.image = pygame.transform.rotozoom(self.image, self.rotation, 1) 

  def try_destroy(self, killed_by_player=False):
    global score

    if self.health > 0:
      self.health -= 1
    
    if self.health <= 0:
      self.kill()
      # drop loot
      if killed_by_player: #makes it not drop loot if player doesn't kill with gun
        LOOT_POSITION_VARIATION = 20

        audio_assets["kill"].play()
        # increment score by score value
        score += self.score_value

        for loot_type in self.loot:
          # get loot data
          loot_info = self.loot[loot_type]
          amount = loot_info["Amount"]
          value = loot_info["Value"]

          # place correct number of loot drops
          for i in range(0, amount):
            position = (self.rect.centerx+random.randint(-LOOT_POSITION_VARIATION,LOOT_POSITION_VARIATION),self.rect.centery+random.randint(-LOOT_POSITION_VARIATION,LOOT_POSITION_VARIATION))
            place_pickup(loot_type, position, value[i])
  
  def update(self):
    super().update()
    if ticks_paused != 0: #makes sure pausing doesn't insta-spawn them
      self.initial_time += ticks_paused
    if self.is_spawned == True:
      self.move() #calls movement subroutine
      self.rotate(self.target.rect)
    else:
      self.prepare_spawn()

# stays away from player and fires bullets at them  
class EnemyTank(Enemy):
  def __init__(self, position, is_spawned=False, enemy_type="soldier"):
    super().__init__(position, is_spawned, enemy_type)

    # initialise shooting-related stats
    self.shot_cooldown = 600
    self.initial_shot_time = 200 #used for determining how long ago the last bullet was fired, reassigned each time
    self.range = 750 # distance they go near to player for

  def move(self):
    # only move closer if more than their range away
    target_pos = self.target.rect
    dx = target_pos[0] - self.x
    dy = target_pos[1] - self.y
    magnitude = math.hypot(dx, dy)

    # tolerance in pixels where they do not move
    tolerance = 20

    if magnitude > self.range:
      self._direct_movement()
    elif magnitude < self.range-tolerance:
      # move away from player
      dx, dy = self._get_direction_to(self.target)
      self._move_in_direction(-dx, -dy)
    self._collide_with_enemies()

  # overwrite spawn complete to create tank gun
  def _spawn_complete(self):
    super()._spawn_complete()
    # set up tank gun
    self.tank_gun = TankGun(self, self.target.rect, "enemy_tank_gun")


  def try_destroy(self, killed_by_player: bool=False):
    super().try_destroy(killed_by_player)

    # also destroy gun
    if self.health <= 0:
      self.tank_gun.kill()
  
  # fires a bullet towards the player
  def shoot(self):
    if (pygame.time.get_ticks() - self.initial_shot_time) >= self.shot_cooldown: #determines whether the cooldown for shooting is over
      self.initial_shot_time = pygame.time.get_ticks() #sets how long ago the last bullet was fired
      bullet = EnemyBullet(self.rect.center, self.target.rect.center, 0) #initialises a new bullet object at the player's location
      audio_assets["tank_shoot"].play()
      # gives bullets collision with each other
      mobs.add(bullet) # uses mob collision group to detect impact with player
      all_sprites.add(bullet) #adds the bullet to the list of all existing sprites, used for updating sprites each tick


  def update(self):
    PhysicsObject.update(self)
    if ticks_paused != 0: #makes sure pausing doesn't insta-spawn them
      self.initial_time += ticks_paused
    if self.is_spawned == True:
      self.move() #calls movement subroutinea
      self.shoot() # fires towards player
    else:
      self.prepare_spawn()

# accelerates and doesn't lose speed; used by ferret
class SpeedsterEnemy(Enemy):
  def _stay_in_bounds(self):
    #keeps the object within bounds of the map
    if self.rect.right > WIDTH:
      self.x = WIDTH - self.rect.width/2
      self.rect.centerx = self.x
      self.xspeed = 0 # for ferret
    if self.rect.left < 0:
      self.x = 0 + self.rect.width/2
      self.rect.centerx = self.x
      self.xspeed = 0 # for ferret
    if self.rect.bottom > HEIGHT:
      self.y = HEIGHT - self.rect.height/2
      self.rect.centery = self.y
      self.yspeed = 0 # for ferret
    if self.rect.top < 0:
      self.y = 0 + self.rect.height/2
      self.rect.centery = self.y
      self.yspeed = 0 # for ferret

  def _move_in_direction(self, dx, dy):
    # makes movement ignore FPS
    dt = env.get_deltatime()

    # apply speed; only difference is that this is += instead of =
    self.xspeed += dx*self.speed
    self.yspeed += dy*self.speed

    # make sure it does not exceed max speed
    max_speed = self.speed*1000
    self.xspeed = min(max_speed, self.xspeed)
    self.xspeed = max(-max_speed, self.xspeed)
    self.yspeed = min(max_speed, self.yspeed)
    self.yspeed = max(-max_speed, self.yspeed)

    # move at end of frame
    self.x += self.xspeed*dt
    self.y += self.yspeed*dt #separate non-rounded x/y values used
    self.rect.centerx = self.x
    self.rect.centery = self.y

# explodes on death
class BomberEnemy(Enemy):
  def try_destroy(self, killed_by_player=False):
    super().try_destroy(killed_by_player)

    # explode
    if self.health <= 0:
      AOE_RADIUS = 75
      BOMB_DAMAGE = 3

      self.radius = AOE_RADIUS

      # get all hit players
      for player in players:
        if rect_circle_collide(player, self):
          player.try_destroy(BOMB_DAMAGE)
      
      # play explosion sound!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!



# generic pickup base class
class Pickup(pygame.sprite.Sprite):
  def __init__(self, position, is_spawned=False, type="health", value=1):
    pygame.sprite.Sprite.__init__(self)
     # get data of pickup type
    my_data = pickup_data.pickups[type]

    # setup appearance, hitbox and position
    # applies image override if applicable
    image = type
    if "Image" in my_data:
      image = my_data["Image"]
    
    # applies image size override if applicable
    if "ImageSize" in my_data:
      self.image = pygame.transform.smoothscale(img_assets[image], my_data["ImageSize"])
    else:
      self.image = pygame.transform.smoothscale(img_assets[image])
    self.base_image = self.image # for changing image and reverting changes
    self.rect = self.image.get_rect()
    self.rect.center = position
    self.x = self.rect.centerx
    self.y = self.rect.centery

    # radius applied for collision detection
    self.radius = self.rect.width

    # pickup stats
    self.value = value # value of pickup
    self.speed = my_data["Speed"] # speed pickup moves at
    self.neg_speed = self.speed*(-1)
    # self.radius = self.image.get_size()[0]/2
    self.is_spawned = is_spawned
    # adds to pickups if already spawned
    if is_spawned:
      pickups.add(self)

    self.initial_time = pygame.time.get_ticks()
    self.type = type

    # fallback if dodgy
    self.target = tank_base
  
  def prepare_spawn(self):
    global ticks_paused
    if ticks_paused != 0: #makes sure pausing doesn't insta-spawn them
      self.initial_time += ticks_paused

    self.image = pygame.transform.smoothscale(img_assets["unspawned_pickup"], (32, 32))
    if pygame.time.get_ticks() - self.initial_time >= 2000:
      self.image = self.base_image
      self.is_spawned = True
      pickups.add(self)
      #bottom_sprites.remove(self)
      #all_sprites.add(self)
  
  def try_destroy(self):
    self.kill()

  # inherit from enemy; for being collected by nearest player
  def _get_closest_player(self):
    return Enemy._get_closest_player(self)

  # required for get closest player
  def _get_distance_to(self, player: Player):
    return Enemy._get_distance_to(self, player)

  def move_to(self, target: Player):
    # makes movement ignore FPS
    dt = env.get_deltatime()

    target_rect = target.rect

    x_change = abs(target_rect.centerx - self.x)
    y_change = abs(target_rect.centery - self.y)
    distance = math.sqrt((x_change**2)+(y_change**2))

    # hardcoded behaviour
    if self.type == "health":
      if not target.health < target.max_health: #health only moves if the player needs health
        return

    # must be close enough to collect
    if distance > target.pickup_range:
      return
    
    if target_rect.centerx - self.x < 0: #super high-tech move towards player code
      x_dif = abs((target_rect.x - self.x))
    else:
      x_dif = target_rect.centerx - self.rect.centerx
    if target_rect.y - self.y < 0:
      y_dif = abs((target_rect.centery - self.y))
    else:
      y_dif = target_rect.y - self.y
    total_dif = x_dif+y_dif
    if total_dif == 0:
      total_dif = 1
    x_prop = x_dif/total_dif
    y_prop = y_dif/total_dif
    if target_rect.centerx - self.x < 0:
      self.xspeed = x_prop * self.neg_speed
    else:
      self.xspeed = x_prop * self.speed
    if target_rect.centery - self.y < 0:
      self.yspeed = y_prop * self.neg_speed
    else:
      self.yspeed = y_prop * self.speed
    #print("xspeed", self.xspeed)
    #print("yspeed", self.yspeed)
    self.x += self.xspeed*dt
    self.y += self.yspeed*dt #this is here due to pixel rounding
    self.rect.centerx = self.x
    self.rect.centery = self.y
  
  def update(self):
    if self.is_spawned == False:
      self.prepare_spawn()
    else:
      self.target = self._get_closest_player()
      self.move_to(self.target)

# health pickups
class HealthPickup(Pickup):
  def try_destroy(self):
    successful = self.target.add_health(self.value)
    if successful:
      self.kill()

class Coin(Pickup):
  def try_destroy(self):
    self.target.money += self.value
    audio_assets["coin"].play()
    self.kill()

# generic bullet that moves in a straight line
class PlayerBullet(pygame.sprite.Sprite):
  # sets image; can be overwritten
  def _setup_image(self):
    self.image = pygame.transform.scale(img_assets["bullet"], (28, 14)) #sets image

  def __init__(self, position, target_pos: tuple, pierce=0):
    pygame.sprite.Sprite.__init__(self)
    self._setup_image()
    self.rect = self.image.get_rect()
    self.radius = 8 #sets size of bullet

    #hide bullet offscreen
    self.rect.x = -100
    self.rect.y = -100

    #sets bullet position to provided parameters (with correct offset)
    self.x = position[0]-14
    self.y = position[1]-7
    
    #super high-tech calculate movement towards target code
    self.speed = 880

    dx, dy = self._get_direction_to(target_pos)

    self.xspeed = dx * self.speed
    self.yspeed = dy * self.speed

    #position in front of gun
    self.x += self.xspeed/55*3.6
    self.y += self.yspeed/55*3.6

    #points towards crosshair
    if target_pos[0]-self.x != 0:
      self.rotation = math.atan(((HEIGHT-target_pos[1])-(HEIGHT-self.y))/(target_pos[0]-self.x))*(180/math.pi) # calculates the rotation needed to face the tank
      if target_pos[0] < self.x:
        self.rotation = self.rotation+180 # corrects rotation if the crosshair is on the left-hand side of the bullet
      self.image = pygame.transform.rotate(self.image, self.rotation) # moves visuals

    self.pierce = pierce # how many enemies a bullet can hit
    self.damage = 1 # damage bullet deals

  def _get_direction_to(self, target_pos: tuple):
    dx = target_pos[0] - self.x
    dy = target_pos[1] - self.y
    magnitude = math.hypot(dx, dy)

    # adjust for proportion
    dx /= magnitude
    dy /= magnitude
    
    return dx, dy

  def move(self):
    # makes movement ignore FPS
    dt = env.get_deltatime()

    # applies movement to bullet
    self.x += self.xspeed*dt
    self.y += self.yspeed*dt
    self.rect.centerx = self.x
    self.rect.centery = self.y

  # tries to destroy the bullet (e.g. if hit target)
  def try_destroy(self, hit_by_player=False): # extra arg only for bullets hitting bullets
    # destroys self if hit too many enemies
    if self.pierce > 0:
      self.pierce -= 1
    else:
      self.kill()
    # audio_assets["bullet_hit"].play()

  # run when the bullet hits a valid target
  def collide(self, colliding_with: Enemy):
    colliding_with.try_destroy(True) # True: player damaged enemy
    self.try_destroy()

  # can be overwritten to change the group that is checked for collision
  def _collision_group_check(self):
    hit_mobs = pygame.sprite.spritecollide(self, mobs, False, pygame.sprite.collide_circle)
    return hit_mobs

  # checks if the bullet is colliding with any enemies
  def check_collisions(self):
    hit_mobs = self._collision_group_check()
    for mob in hit_mobs:
      # attempt to destroy bullet and damage enemy
      self.collide(mob)

  def update(self):
    #attempt movement
    self.move()
    # check if colliding with any enemies
    self.check_collisions()
    #delete if off the edge of the screen
    if self.rect.bottom < 0:
      self.kill()
    if self.rect.top > HEIGHT:
      self.kill()
    if self.rect.right < 0:
      self.kill()
    if self.rect.left > WIDTH:
      self.kill()

# bullet used by enemies
class EnemyBullet(PlayerBullet):
  # red bullet
  def _setup_image(self):
    self.image = pygame.transform.scale(img_assets["enemy_bullet"], (28, 14)) #sets image

  # get all players that have been hit
  def _collision_group_check(self):
    hit_players = pygame.sprite.spritecollide(self, players, False, rect_circle_collide)
    return hit_players

# initialise sprites and groups
players = pygame.sprite.Group()
players_list = []
mobs = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
pickups = pygame.sprite.Group()
crosshair = ui.Cursor((25,25), 10, img_assets["crosshair"], {"Transparency": 1})
tank_base = Player()
# shop_base = ui.frame((0,0), (500,500), 1, {"colour": (255,0,0)}, {"thickness": 10, "transparency": 0.3})
# random_text = ui.text_label((0,0), (200, 200), {"text": "i am the ultimate sigma"}, 2, {"transparency": 1})

def button_func():
  tank_base.try_destroy(1)
def evil_func():
  for x in range(0,100):
    place_object((random.randint(0, WIDTH), random.randint(0, HEIGHT)), "soldier")

# funny_button = ui.DetailedButton((200, 200), (200, 100), button_func, {"Text": {"Text": "sigma button?"}, "Image": img_assets["soldier"]}, 2, {"Colour": (255,0,0)}, {"Thickness": 10})
# evil_button = ui.TextButton((750, 200), (200, 100), evil_func, {"Text": "heheheh", "Size": 50}, 2, {"Colour": (255,0,0)}, {"Thickness": 10})

# create mobile ui
all_mobile_ui = [] # holds references to all ui elements
mobile_ui_active = False
# toggles all mobile ui elements
def toggle_mobile_controls_func():
  for ui_element in all_mobile_ui:
    if mobile_ui_active:
      top_sprites.remove(ui_element)
      mobile_ui_active = False
    else:
      top_sprites.add(ui_element)
      mobile_ui_active = False

# toggle_mobile_controls = ui.TextButton((750, 0), (100, 100), toggle_mobile_controls_func, {"Text": "Mobile"}, 2, {"Colour": WHITE}, {"Thickness": 5})

# up_button = ui.Te


pygame.mixer.music.play(loops=-1) #infinitely loops the bgm
score = 0 #initialises the score variable, which is updated with score increases
paused = False #initialises the variable for whether the game is paused
pause_initial_time = -1 #sets the initial pause time (less than 0 so it's never higher than the current time)
ticks_paused = 0 #tracks how long the game was paused for

# game helper functions
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
  # increase spawn chance with score
  spawn_chance = BASE_SPAWN_CHANCE
  CHANCE_PER_SCORE = 0.001
  spawn_chance += CHANCE_PER_SCORE*score
  # do not spawn more/less enemies depending on frame-rate
  dt = env.get_deltatime()
  spawn_chance *= dt

  if random.random() < spawn_chance:
    # pick enemy to spawn using weighted system
    enemy = weighted_random(spawn_pool)
    # load enemy's data for its cluster size
    my_data = enemy_data.enemies[enemy] 
    #spawns enemies in clusters close together
    xpos = random.randint(0, WIDTH) #generates 'centre' of enemy cluster
    ypos = random.randint(0, HEIGHT)
    VARIATION = 100 # random spread from positions
    # increase max cluster size with score
    max_cluster_size = my_data["MaxClusterSize"]
    max_cluster_size += max_cluster_size*score/1000
    max_cluster_size = int(max_cluster_size)

    cluster_size = random.randint(my_data["MinClusterSize"], max_cluster_size)
    for _ in range(cluster_size):
      new_xpos = random.randint(max(0, xpos - VARIATION), min(WIDTH, xpos + VARIATION))
      new_ypos = random.randint(max(0, ypos - VARIATION), min(HEIGHT, ypos + VARIATION))
      place_object((new_xpos, new_ypos), enemy)

# checks whether the score threshold has been met to unlock any new enemies
old_score = 0
def check_score_enemies():
  global old_score
  # only check if score changed
  if score == old_score:
    return
  
  old_score = score # update old score

  for enemy in enemy_data.enemies:
    # enemy must not already be spawned
    if enemy in spawn_pool:
      continue

    # adds enemy to spawn pool
    if enemy_data.enemies[enemy]["SpawningScore"] <= score:
      env.output_for_debugging("added "+enemy+" to spawn pool")
      spawn_pool[enemy] = enemy_data.enemies[enemy]["SpawnWeight"]


def spawn_loot():
    if random.randint(1,5000) == 5:
      health_pickup_amount = 0
      for item in pickups:
        if item.type == "health":
          health_pickup_amount += 1
      if health_pickup_amount < 2:
        xpos = random.randint(0, WIDTH) 
        ypos = random.randint(0, HEIGHT)
        p = HealthPickup((xpos, ypos), False, "health") 
        bottom_sprites.add(p)

def place_object(position, type):
  # pickups
  if type == "health": #for placing objects manually (e.g. debug tools)
    object = HealthPickup(position, False, "health") 
    bottom_sprites.add(object)
  elif type == "coin":
    for x in range(5):
      object = Coin(position, True, type, 10)
      bottom_sprites.add(object)
    env.output_for_debugging("Coins: "+str(len(pickups)))
  else:
    my_data = enemy_data.enemies[type]
    # apply class override for special enemies:
    if "Class" in my_data:
      my_class = globals()[my_data["Class"]]
    else:
      my_class = Enemy
    object = my_class(position, False, type) 
    bottom_sprites.add(object)

# custom function for detecting collision between a circle and rect
def rect_circle_collide(rect_sprite, circle_sprite):
  # use rect collision if not radius
  if not hasattr(circle_sprite, "radius"):
    return pygame.sprite.collide_rect(rect_sprite, circle_sprite)

  rect = rect_sprite.rect
  circle_center_x = circle_sprite.x
  circle_center_y = circle_sprite.y
  circle_radius = getattr(circle_sprite, "radius")
  

  # find the closest point on the rectangle to the center of the circle
  closest_x = max(rect.left, min(circle_center_x, rect.right))
  closest_y = max(rect.top, min(circle_center_y, rect.bottom))

  # calculate the distance between the closest point and the circle's center
  distance_x = circle_center_x - closest_x
  distance_y = circle_center_y - closest_y
  distance_squared = (distance_x * distance_x) + (distance_y * distance_y)

  # check if the distance is less than the radius squared
  # distance squared more performant than sqrt
  return distance_squared < (circle_radius * circle_radius)


def collisions():
  mobs_hit_player = pygame.sprite.groupcollide(players, mobs, False, False, rect_circle_collide)
  player_touched_pickup = pygame.sprite.groupcollide(players, pickups, False, False, rect_circle_collide)

  for player in mobs_hit_player:
    hit_mobs = mobs_hit_player[player]
    for mob in hit_mobs:
      mob.try_destroy()
      player.try_destroy(mob.damage)
  
  for player in player_touched_pickup:
    hit_pickups = player_touched_pickup[player]
    for pickup in hit_pickups:
      pickup.try_destroy()

# shows the cooldown between shots
def show_cooldown():
    # calculate time until cooldown ends
    start_time = tank_base.initial_shot_time
    current_time = pygame.time.get_ticks()
    cooldown = tank_base.shot_cooldown
    end_time = start_time+cooldown
    time_remaining = end_time-current_time

    # only show if cooldown active
    if time_remaining <= 0:
      return

    # get position to draw at
    x = crosshair.rect.centerx
    y = crosshair.rect.centery + 16

    # draw a cooldown bar
    bar_height = 5
    bar_width = 20

    # offset bar to be centred
    x -= bar_width/2

    # draw background of bar
    empty_bar = pygame.rect.Rect(x, y, bar_width, bar_height)
    pygame.draw.rect(display, (150, 150, 150), empty_bar)
    
    # calculate proportion full
    proportion = time_remaining/cooldown
    full_bar_width = proportion*bar_width
    full_bar = pygame.rect.Rect(x, y, full_bar_width, bar_height)

    # draw full part of bar
    pygame.draw.rect(display, BLACK, full_bar)

# draws all sprites to screen
def draw_all():
  bottom_sprites.draw(display)
  mobs.draw(display)
  all_sprites.draw(display) #draws the sprites to the screen
  top_sprites.draw(display)

# controller input helper functions
# gets current player
def get_player_by_num(player_num: int):
  return players_list[player_num]

# used for handling joycon axis movement
def get_controller_axis_value(axis: int, player_num: int):
  offset = max(0, player_num-1)
  controller_axes = input_handler.joystick_axis_movement[offset]
  axis_value = controller_axes[axis]
  return axis_value

# used for trying to shoot with right trigger
def try_right_trigger_shoot(player_num: int):
  print("Shooting with right trigger for", player_num)
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


# for binding controllers to players
def bind_controller_inputs(joystick: pygame.joystick.Joystick, player_num: int=0):
  player = get_player_by_num(player_num)
  controller_id = max(player_num-1, 0)

  # bound_inputs = [
  #   # [id, key, keydown]
  # ]

  # toggle pause
  input_handler.bind_to_joystick_input(
      7, # waffle
      lambda: globals().__setitem__("paused", not paused),
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
    new_player = Player()
    player_num = new_player.player_num
    bind_controller_inputs(joystick, player_num)
  else:
    bind_controller_inputs(joystick, 0)


input_handler.bind_to_joystick_init(setup_controller_player)

key1 = 0
key2 = 0
# bind all keybinds
def bind_all_inputs():
  global key1, key2
  # lambda works to "define" functions
  # stop the game running
  input_handler.bind_to_input(
      pygame.K_ESCAPE,
      lambda: setattr(env, "running", False)
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
  key2 = input_handler.bind_to_input(
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
    global score
    score += 10000

  input_handler.bind_to_input(
    pygame.K_F9,
    inc_score
  )

  input_handler.bind_to_input(
    pygame.K_F10,
    lambda: place_object(pygame.mouse.get_pos(), "coin")
  )

  input_handler.bind_to_input(
    pygame.K_F11,
    lambda: place_object(pygame.mouse.get_pos(), "bomber")
  )

bind_all_inputs()

#main program
while env.running: #runs the game loop
  display.fill(WHITE) 
  #do not run if paused
  if paused and pause_initial_time == -1: #checks whether the game is paused for the first time
    pause_initial_time = pygame.time.get_ticks() #sets the last time the game was paused
  if not paused:
    if ticks_paused != 0: #resets variable for how long the game was paused for
      ticks_paused = 0
      env.ticks_paused = ticks_paused
    if pause_initial_time != -1:
      ticks_paused = pygame.time.get_ticks()-pause_initial_time #sets how long the game was paused for
      env.ticks_paused = ticks_paused
      pause_initial_time = -1 #resets paused state
    clock.tick(FPS) #ticks the clock based on the set FPS
    spawn_enemies()
    spawn_loot()
    # score = collisions(score)
    bottom_sprites.update()
    mobs.update()
    all_sprites.update()
    top_sprites.update()
    # checks if any enemies can spawn now
    check_score_enemies()

    # draws all to the screen
    draw_all()
    # collisions done after they are shown
    collisions()
    # show shot cooldown
    show_cooldown()
    # show score and money earned
    draw_text(display, "score: "+str(score), 18, WIDTH / 2, 20)
    draw_text(display, "money: "+str(tank_base.money), 18, WIDTH / 2, 40)
    # show additional stats in debug mode
    if DEBUG_MODE:
      draw_text(display, "health: "+str(tank_base.health)+"/"+str(tank_base.max_health), 18, WIDTH / 2, 60)
      draw_text(display, "ticks: "+str(pygame.time.get_ticks()), 18, WIDTH / 2, 80)
      draw_text(display, "FPS: "+str(round(clock.get_fps(), 1)), 18, WIDTH / 2, 100)
      draw_text(display, env.current_debug_output, 18, WIDTH / 2, 120)

  top_sprites.update()
  
  # draws all to the screen
  draw_all()

  if clock.get_fps() >= 30:
    pygame.mouse.set_visible(False) #makes the mouse invisible if game isn't lagging
  else:
    pygame.mouse.set_visible(True)
  pygame.display.flip() #shows everything that was drawn on the screen

  # handle all key presses
  input_handler.handle_inputs()

#print(pygame.mouse.get_pos()) #prints the mouse position to terminal (x, y)

pygame.quit() #quits program when it stops running