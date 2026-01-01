import pygame, random, math, copy
# custom imports
import env, generic, misc
import player as plr
from Data import enemy_data

# sprite group for storing enemies
mobs = pygame.sprite.Group()
env.mobs = mobs # to avoid circular import with players

# generic enemy base class
class Enemy(generic.PhysicsObject):
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
      self.image = pygame.transform.smoothscale(env.img_assets[image], my_data["ImageSize"])
    else:
      self.image = pygame.transform.smoothscale(env.img_assets[image])
    # set up recolours if applicable
    if "Recolour" in my_data:
      for recolour_data in my_data["Recolour"]:
        generic.recolour_image(self.image, recolour_data["TargetColour"], recolour_data["ReplacementColour"], recolour_data["Tolerance"])
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
    if env.DEBUG_MODE and hasattr(self, "radius"):
      # pygame.draw.circle(self.image, BLUE, (self.image.get_env.WIDTH() // 2, self.image.get_env.HEIGHT() // 2), self.radius)
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
    env.bottom_sprites.remove(self)
    #all_sprites.add(self)

  def prepare_spawn(self): #if not force spawned, create a spawn indicator
    self.image = pygame.transform.smoothscale(env.img_assets["unspawned_enemy"], (32, 32))
    if pygame.time.get_ticks() - self.initial_time >= 2000: #timer before spawning
      #initialises spawn
      self._spawn_complete()

  def _get_closest_player(self):
    closest_dist = math.inf
    closest_player = plr.players_list[0]

    for player in plr.players:
      dist_to, _, _ = self._get_distance_to(player)
      if dist_to < closest_dist:
        closest_dist = dist_to
        closest_player = player
    
    return closest_player

  def _get_distance_to(self, player: plr.Player):
    # move towards player by default
    target_pos = player.rect.center

    dx = target_pos[0] - self.x
    dy = target_pos[1] - self.y
    magnitude = math.hypot(dx, dy)

    return magnitude, dx, dy

  def _get_direction_to(self, player: plr.Player):
    # draw line of movement
    if env.DEBUG_MODE:
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
      self_radius = self.rect.env.WIDTH/2
    else:
      self_radius = self.radius

    if not hasattr(other_enemy, "radius"):
      other_enemy_radius = other_enemy.rect.env.WIDTH/2
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
    self.rotation = math.atan(((env.HEIGHT-target_rect.centery)-(env.HEIGHT-self.rect.centery))/(self.x_change))*(180/math.pi) #calculates the rotation needed to face the tank
    if target_rect.centerx < self.rect.centerx:
      self.rotation = self.rotation+180 #corrects rotation if the tank is on the left-hand side of the soldier
    #print("rotation", self.rotation)
    #print("tank base x", target_rect.x)
    #print("tank base y", target_rect.y)
    #print("enemy x", self.rect.x)
    #print("enemy y", self.rect.y)
    self.image = pygame.transform.rotozoom(self.image, self.rotation, 1) 

  def try_destroy(self, killed_by_player=False):
    if self.health > 0:
      self.health -= 1
    
    if self.health <= 0:
      self.kill()
      # drop loot
      if killed_by_player: #makes it not drop loot if player doesn't kill with gun
        LOOT_POSITION_VARIATION = 20

        env.audio_assets["kill"].play()
        # increment score by score value
        env.score += self.score_value

        for loot_type in self.loot:
          # get loot data
          loot_info = self.loot[loot_type]
          amount = loot_info["Amount"]
          value = loot_info["Value"]

          # place correct number of loot drops
          for i in range(0, amount):
            position = (self.rect.centerx+random.randint(-LOOT_POSITION_VARIATION,LOOT_POSITION_VARIATION),self.rect.centery+random.randint(-LOOT_POSITION_VARIATION,LOOT_POSITION_VARIATION))
            misc.place_pickup(loot_type, position, value[i])
  
  def update(self):
    super().update()
    if env.ticks_paused != 0: #makes sure pausing doesn't insta-spawn them
      self.initial_time += env.ticks_paused
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
    self.tank_gun = plr.TankGun(self, self.target.rect, "enemy_tank_gun")


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
      env.audio_assets["tank_shoot"].play()
      # gives bullets collision with each other
      mobs.add(bullet) # uses mob collision group to detect impact with player
      env.all_sprites.add(bullet) #adds the bullet to the list of all existing sprites, used for updating sprites each tick


  def update(self):
    generic.PhysicsObject.update(self)
    if env.env.ticks_paused != 0: #makes sure pausing doesn't insta-spawn them
      self.initial_time += env.env.ticks_paused
    if self.is_spawned == True:
      self.move() #calls movement subroutinea
      self.shoot() # fires towards player
    else:
      self.prepare_spawn()

# accelerates and doesn't lose speed; used by ferret
class SpeedsterEnemy(Enemy):
  def _stay_in_bounds(self):
    #keeps the object within bounds of the map
    if self.rect.right > env.WIDTH:
      self.x = env.WIDTH - self.rect.env.WIDTH/2
      self.rect.centerx = self.x
      self.xspeed = 0 # for ferret
    if self.rect.left < 0:
      self.x = 0 + self.rect.env.WIDTH/2
      self.rect.centerx = self.x
      self.xspeed = 0 # for ferret
    if self.rect.bottom > env.HEIGHT:
      self.y = env.HEIGHT - self.rect.env.HEIGHT/2
      self.rect.centery = self.y
      self.yspeed = 0 # for ferret
    if self.rect.top < 0:
      self.y = 0 + self.rect.env.HEIGHT/2
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
      for player in plr.players:
        if generic.rect_circle_collide(player, self):
          player.try_destroy(BOMB_DAMAGE)
      
      # play explosion sound!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# bullet used by enemies
class EnemyBullet(plr.PlayerBullet):
  # red bullet
  def _setup_image(self):
    self.image = pygame.transform.scale(env.img_assets["enemy_bullet"], (28, 14)) #sets image

  # get all players that have been hit
  def _collision_group_check(self):
    hit_players = pygame.sprite.spritecollide(self, plr.players, False, generic.rect_circle_collide)
    return hit_players