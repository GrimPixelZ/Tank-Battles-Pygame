# for players and player-related objects
import pygame, math
# custom imports
import env, generic, ui
from Data import weapon_data

img_assets = env.img_assets

# player recolour options
PLAYER_COLOURS = [
  (102, 171, 255), # blue
  (137, 205, 82), # green
  (140, 0, 255), # purple
  (0, 249, 255), # teal
]

# create sprite groups for storing players
players = pygame.sprite.Group()
players_list = [] # used as stores length and indexes
player_bullets = pygame.sprite.Group()

class Player(generic.PhysicsObject):
  def __init__(self):
    pygame.sprite.Sprite.__init__(self) #marks object as a pygame sprite
    self.image = pygame.transform.scale(img_assets["tank_base"], (50, 50)) #applies image texture to player
    self.rect = self.image.get_rect() #assigns tillihe player's recent
    self.rect.center = (env.WIDTH / 2, env.HEIGHT / 2) #centres the player in the middle of the screen

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
    env.all_sprites.add(self)
    # also add to players lists
    players.add(self)
    players_list.append(self)

    # setup starter weapon and tank gun
    self._setup_weapon("pellet")

    # create health bar and money counter
    self.health_container = HealthContainer("container", self)
    self.coin_counter = CoinCounter(self)

  # changes colour (for multiplayer) along with making iframes appearance
  def _apply_player_colouring(self, player_num: int):
    # get player colour
    player_colour = PLAYER_COLOURS[player_num]

    # if not player one, recolour self
    if player_num > 0:
      generic.recolour_image(self.image, PLAYER_COLOURS[0], player_colour)

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
    generic.recolour_image(self.iframes_image, player_colour, iframes_colour)

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
    env.all_sprites.add(bullet) #adds the bullet to the list of all existing sprites, used for updating sprites each tick

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
        self._create_bullet(env.crosshair.rect.center)
      else:
        self._create_bullet_in_direction(direction[0], direction[1])
      # draw line for debugging
      # pygame.draw.line(display, RED, (self.rect.centerx, self.rect.centery), env.crosshair.rect.center, 3)
      # fire additional bullets (e.g. shotgun)
      if self.bullets > 1:
        adjacent_length = env.crosshair.rect.centerx-self.rect.centerx
        opposite_length = env.crosshair.rect.centery-self.rect.centery
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
      env.audio_assets["tank_shoot"].play()
  
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
      env.audio_assets["heal"].play()
    else:
      successful = False
    return successful
  
  def try_destroy(self, damage):
    if self.iticks == 0:
      if self.health >= 1:
        self.health -= damage
        self.iticks = self.maxiticks
        self.iticks_start = pygame.time.get_ticks()
        env.audio_assets["tank_hit"].play()
      else:
        env.all_sprites.remove(self)
        env.all_sprites.remove(self.tank_gun)
        self.rect.center = (-5000, -5000) # position offscreen
  
  # removes any otherwise lingering remnants of last weapon
  def _deload_weapon(self):
    # remove old tank gun
    self.tank_gun.kill()

  # loads new weapon
  def _setup_weapon(self, weapon: str):
    # create new tank gun
    self.tank_gun = TankGun(self, env.crosshair.rect, weapon)

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
    if env.ticks_paused != 0: #prevent pause abuse to remove shot cooldown
      self.initial_shot_time += env.ticks_paused
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
    env.all_sprites.add(self)
  
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
      rotation = math.atan(((env.HEIGHT-self.target.centery)-(env.HEIGHT-self.rect.centery))/(x_change))*(180/math.pi) #calculates the rotation needed to face the tank
      if self.target.centerx < self.rect.centerx:
        rotation += 180 #corrects rotation if the env.crosshair is on the left-hand side of the bullet
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
        generic.recolour_image(self.base_image, (255, 99, 99), PLAYER_COLOURS[player.player_num])
    self.rect = self.image.get_rect()
    self.rect.center = ((self.image.get_size()[0]/2+5, self.image.get_size()[1]/2+5))
    # shift along by player number
    BASE_SHIFT = 200
    shift = BASE_SHIFT * player.player_num
    self.rect.centerx += shift

    self.player = player

    self.type = type
    env.top_sprites.add(self)

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


  def try_destroy(self, killed_by_player=False):
    super().try_destroy(killed_by_player)

    # explode
    if self.health <= 0:
      AOE_RADIUS = 75
      BOMB_DAMAGE = 3

      self.radius = AOE_RADIUS

      # get all hit players
      for player in players:
        if generic.rect_circle_collide(player, self):
          player.try_destroy(BOMB_DAMAGE)
      
      # play explosion sound!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

class CoinCounter(pygame.sprite.Sprite):
    def __init__(self, player: Player=None):
      super().__init__()
      START_OFFSET = 5
      HEALTH_WIDTH = 730/4
      HEALTH_HEIGHT = 670/4

      # save player to represent
      self.player = player

      # create blank image and rect
      self.image = pygame.Surface((0,0))
      self.rect = pygame.rect.Rect(0,0,0,0)

      self.x = 0
      self.y = 0

      # shift by offset
      self.x += START_OFFSET
      self.x += HEALTH_WIDTH/2
      self.y += START_OFFSET
      self.y += HEALTH_HEIGHT

      # shift along by player number
      BASE_SHIFT = 200
      shift = BASE_SHIFT * player.player_num
      self.x += shift

      # add to sprites for updating
      env.top_sprites.add(self)
    
    def update(self):
      text = "£"+str(self.player.money)
      TEXT_SIZE = 25
      env.draw_text(env.display, text, TEXT_SIZE, self.x, self.y)

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

    #points towards env.crosshair
    if target_pos[0]-self.x != 0:
      self.rotation = math.atan(((env.HEIGHT-target_pos[1])-(env.HEIGHT-self.y))/(target_pos[0]-self.x))*(180/math.pi) # calculates the rotation needed to face the tank
      if target_pos[0] < self.x:
        self.rotation = self.rotation+180 # corrects rotation if the env.crosshair is on the left-hand side of the bullet
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
  def collide(self, colliding_with: generic.PhysicsObject):
    colliding_with.try_destroy(True) # True: player damaged enemy
    self.try_destroy()

  # can be overwritten to change the group that is checked for collision
  def _collision_group_check(self):
    hit_mobs = pygame.sprite.spritecollide(self, env.mobs, False, pygame.sprite.collide_circle)
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
    if self.rect.top > env.HEIGHT:
      self.kill()
    if self.rect.right < 0:
      self.kill()
    if self.rect.left > env.WIDTH:
      self.kill()


# shows the cooldown between shots
def show_cooldown():
    # calculate time until cooldown ends
    start_time = players_list[0].initial_shot_time
    current_time = pygame.time.get_ticks()
    cooldown = players_list[0].shot_cooldown
    end_time = start_time+cooldown
    time_remaining = end_time-current_time

    # only show if cooldown active
    if time_remaining <= 0:
      return

    # get position to draw at
    x = env.crosshair.rect.centerx
    y = env.crosshair.rect.centery + 16

    # draw a cooldown bar
    bar_height = 5
    bar_width = 20

    # offset bar to be centred
    x -= bar_width/2

    # draw background of bar
    empty_bar = pygame.rect.Rect(x, y, bar_width, bar_height)
    pygame.draw.rect(env.display, (150, 150, 150), empty_bar)
    
    # calculate proportion full
    proportion = time_remaining/cooldown
    full_bar_width = proportion*bar_width
    full_bar = pygame.rect.Rect(x, y, full_bar_width, bar_height)

    # draw full part of bar
    pygame.draw.rect(env.display, env.BLACK, full_bar)
