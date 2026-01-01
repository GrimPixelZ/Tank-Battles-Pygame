# for ingame objects such as pickups
import pygame, math
# custom imports
import env, player as plr, enemy
from Data import pickup_data

bottom_sprites = env.bottom_sprites

# custom group for storing pickups
pickups = pygame.sprite.Group()

# helper functions
def place_pickup(type: str, position: tuple, value: int):
  if type == "health":
    pickup = HealthPickup(position, True, type, value)
  elif type == "coin":
    pickup = Coin(position, True, type, value)
  bottom_sprites.add(pickup)

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
      self.image = pygame.transform.smoothscale(env.img_assets[image], my_data["ImageSize"])
    else:
      self.image = pygame.transform.smoothscale(env.img_assets[image])
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
    self.target = plr.players_list[0]
  
  def prepare_spawn(self):
    if env.ticks_paused != 0: #makes sure pausing doesn't insta-spawn them
      self.initial_time += env.ticks_paused

    self.image = pygame.transform.smoothscale(env.img_assets["unspawned_pickup"], (32, 32))
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
    return enemy.Enemy._get_closest_player(self)

  # required for get closest player
  def _get_distance_to(self, player: plr.Player):
    return enemy.Enemy._get_distance_to(self, player)

  def move_to(self, target: plr.Player):
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
    env.audio_assets["coin"].play()
    self.kill()
