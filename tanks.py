import pygame
import random
import math
import copy

# custom modules
import env
import ui
import input_handler

# load enemy data
from Data import enemy_data, pickup_data

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

# whether to show debug values etc
DEBUG_MODE = env.DEBUG_MODE

display = env.display # sets the pygame display
clock = env.clock # sets the pygame clock (used for timer-based events)
bottomSprites = env.bottomSprites
allSprites = env.allSprites # group for updating all sprites
topSprites = env.topSprites # sprites that go at the very top

#assign background music and its volume
background_music = env.background_music
pygame.mixer.music.set_volume(1)

img_assets = env.img_assets
audio_assets = env.audio_assets

DEFAULT_FONT = env.DEFAULT_FONT

# helper functions
draw_text = env.draw_text

def placePickup(type: str, position: tuple, value: int):
  if type == "health":
    pickup = HealthPickup(position, True, type, value)
  elif type == "coin":
    pickup = Coin(position, True, type, value)
  bottomSprites.add(pickup)

# changes all pixels of given color in image
def recolourImage(image: pygame.image, targetColour: list, replacementColour: list):
  pixels = pygame.PixelArray(image)

  # must account for tolerance to not have oddly coloured edges

  pixels.replace(targetColour, replacementColour)
  del pixels
  

class Player(pygame.sprite.Sprite):
  def __init__(self):
    pygame.sprite.Sprite.__init__(self) #marks object as a Pygame sprite
    self.image = pygame.transform.scale(img_assets["tank_base"], (50, 50)) #applies image texture to player
    self.rect = self.image.get_rect() #assigns tillihe player's recent
    self.rect.center = (WIDTH / 2, HEIGHT / 2) #centres the player in the middle of the screen
    self.speed = 385 #initial speed of the player without power ups
    self.health = 10 #sets the initial player health
    self.maxHealth = 10 #sets the maximum health of the player
    self.iticks = 0 #initialises the amount of ticks the player is invincible for
    self.maxiticks = 200 #sets the maximum number of invincibility ticks each time the player is damaged
    self.iticksStart = 0 #marks when the player's iticks were last started
    self.shooting = False #marks whether the player is currently shooting or not
    self.initialShotTime = 200 #used for determining how long ago the last bullet was fired, reassigned each time
    self.shotCooldown = 400 #initialises the delay between weapon attacks
    self.pickupRange = 150 #initialises the player's pickup pickup range
    self.money = 0 #initialises how much money the player has


  def move(self):
    # makes movement ignore fps
    dt = clock.get_time()/1000
    env.outputForDebugging("Delta time: "+str(dt))

    self.speedx = 0 # initiates speed variables for each direction
    self.speedy = 0
    keystate = pygame.key.get_pressed() # gets pressed keys
    if keystate[pygame.K_LEFT] or keystate[pygame.K_a]: # detects which key was pressed
      self.speedx += (self.speed*(-1)) # using += so that it doesn't prefer a certain direction when both keys are held
    if keystate[pygame.K_RIGHT] or keystate[pygame.K_d]:
      self.speedx += self.speed # speed values are dynamic and stored in the player class
    if keystate[pygame.K_UP] or keystate[pygame.K_w]:
      self.speedy += (self.speed*(-1)) # multiplies by -1 to go in the opposite direction
    if keystate[pygame.K_DOWN] or keystate[pygame.K_s]:
      self.speedy += self.speed
    if self.speedx != 0 and self.speedy != 0: # using this to prevent diagonal movement being faster than straight movement
      self.speedx = self.speedx*0.70710678118
      self.speedy = self.speedy*0.70710678118 
    self.rect.x += self.speedx*dt # moves player position by speed
    self.rect.y += self.speedy*dt


  def shoot(self):
    if (pygame.time.get_ticks() - self.initialShotTime) >= self.shotCooldown: #determines whether the cooldown for shooting is over
      self.initialShotTime = pygame.time.get_ticks() #sets how long ago the last bullet was fired
      bullet = Bullet(self.rect.center, crosshair.rect) #initialises a new bullet object at the player's location
      audio_assets["tank_shoot"].play()
      playerBullets.add(bullet) #adds the bullet to a list of player bullets, used for detecting collision with enemies
      allSprites.add(bullet) #adds the bullet to the list of all existing sprites, used for updating sprites each tick
  
  def add_health(self, value):
    successful = True
    if self.health < self.maxHealth:
      self.health += value
      audio_assets["heal"].play()
    else:
      successful = False
    return successful
  
  def tryDestroy(self, damage):
    if self.iticks == 0:
      if self.health >= 1:
        self.health -= damage
        self.iticks = self.maxiticks
        self.iticksStart = pygame.time.get_ticks()
        audio_assets["tank_hit"].play()

  def update(self):
    if ticksPaused != 0: #prevent pause abuse to remove shot cooldown
      self.initialShotTime += ticksPaused
    self.move()
    if self.iticks == 0: #creates the visual effect of the tank flashing when it has iframes
      self.image = pygame.transform.scale(img_assets["tank_base"], (50, 50))
    else:
      self.image = pygame.transform.scale(img_assets["tank_base_iframes"], (50,50))
    if (pygame.time.get_ticks() - self.iticksStart) >= self.iticks: #resets iframes when over
      self.iticks = 0

    if self.rect.right > WIDTH: #makes sure the player cannot leave the bounds of the map
      self.rect.right = WIDTH
    if self.rect.left < 0:
      self.rect.left = 0
    if self.rect.bottom > HEIGHT:
      self.rect.bottom = HEIGHT
    if self.rect.top < 0:
      self.rect.top = 0
    
    if self.shooting == True:
      self.shoot()
    

class Tank_Gun(pygame.sprite.Sprite):
  def __init__(self, parent): 
    pygame.sprite.Sprite.__init__(self)
    self.image = pygame.transform.smoothscale(img_assets["tank_gun"], (66, 32))
    #self.rect = pygame.Rect((parent.rect.centerx, parent.rect.centery),(32,32))
    self.rect = self.image.get_rect()
    #self.image.set_colorkey()
    self.rect.centerx = parent.rect.centerx-17
    self.rect.centery = parent.rect.centery
    self.parent = parent
    self.originalImage = self.image
  
  def rotate(self, type="player"):
    pos = self.parent.rect.center
    self.image = self.originalImage
    pivotPos = (self.image.get_size()[0]-16, self.image.get_size()[1]-16)

    #calculates the angle of rotation
    if crosshair.rect.centerx-self.rect.centerx == 0: #prevents division by zero
      xChange = crosshair.rect.centerx-self.rect.centerx+1
    else:
      xChange = crosshair.rect.centerx-self.rect.centerx
    rotation = math.atan(((HEIGHT-crosshair.rect.centery)-(HEIGHT-self.rect.centery))/(xChange))*(180/math.pi) #calculates the rotation needed to face the tank
    if crosshair.rect.centerx < self.rect.centerx:
      rotation += 180 #corrects rotation if the crosshair is on the left-hand side of the bullet
    rotation += 180 #corrects rotation

    #offset from pivot to center
    image_rect = self.image.get_rect(topleft = (pos[0]-pivotPos[0], pos[1]-pivotPos[1]))
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
    if self.parent.iticks == 0: #changes appearance to indicate invincibility
      self.originalImage = pygame.transform.smoothscale(img_assets["tank_gun"], (66, 32)) # type: ignore
      self.image = self.originalImage
    else:
      self.originalImage = pygame.transform.smoothscale(img_assets["tank_gun_iframes"], (66, 32))
      self.image = self.originalImage
    self.rect.centerx = self.parent.rect.centerx-17 #offsets appearance relative to base
    self.rect.centery = self.parent.rect.centery
    self.rotate() #sets image to rotated version
    #self.blitRotate(display, self.image, (self.parent.rect.center), (self.image.get_size()[0]-16, self.image.get_size()[1]-16), self.rotation)


class Health_Container(pygame.sprite.Sprite):
  def __init__(self, type="container"):
    pygame.sprite.Sprite.__init__(self)
    #different behaviour based on whether it is the outer image or inner image
    if type == "container":
      self.image = pygame.transform.smoothscale(img_assets["health_container"], (730/4, 670/4)) #730 by 670
    elif type == "inner":
      self.image = pygame.transform.smoothscale(img_assets["health_container_inner"], (730/4, 670/4))
    self.rect = self.image.get_rect()
    self.rect.center = ((self.image.get_size()[0]/2+5, self.image.get_size()[1]/2+5))
    self.type = type
    topSprites.add(self)
  
  def update(self):
    if self.type == "inner":
      #calculates what size it should be to represent the current health
      self.image = pygame.transform.smoothscale(img_assets["health_container_inner"], (((730/4)*(tank_base.health/tank_base.maxHealth)*0.9), ((670/4)*(tank_base.health/tank_base.maxHealth)*0.9)))
      self.rect = self.image.get_rect()
      self.rect.center = health_container.rect.center


# generic enemy base class
class Enemy(pygame.sprite.Sprite):
  def __init__(self, position, isSpawned=False, enemyType="soldier"): #define stats and enemyType
    pygame.sprite.Sprite.__init__(self)

    # get data of enemy enemyType
    myData = enemy_data.enemies[enemyType]

    # setup appearance, hitbox and position
    # applies image override if applicable
    image = enemyType
    if "Image" in myData:
      image = myData["Image"]
    
    # applies image size override if applicable
    if "ImageSize" in myData:
      self.image = pygame.transform.smoothscale(img_assets[image], myData["ImageSize"])
    else:
      self.image = pygame.transform.smoothscale(img_assets[image])
    # set up recolours if applicable
    if "Recolour" in myData:
      for recolourData in myData["Recolour"]:
        recolourImage(self.image, recolourData["TargetColour"], recolourData["ReplacementColour"])
    # sets radius for collision
    if "Radius" in myData:
      self.radius = myData["Radius"]
    else:
      self.radius = 1
    
    # initialises rect
    self.rect = self.image.get_rect()
    self.rect.center = position
    self.rect.center = position
    self.x = self.rect.centerx
    self.y = self.rect.centery

    # show debug hitbox
    if DEBUG_MODE:
      pygame.draw.circle(self.image, BLUE, (self.image.get_width() // 2, self.image.get_height() // 2), self.radius)

    # sets default image
    self.baseImage = self.image

    # setup stats
    self.speed = myData["Speed"] # enemy movement speed
    self.negSpeed = self.speed*(-1) # used to reduce calculations later
    self.xspeed = 2.0 # used so things don't sometimes break
    self.yspeed = 2.0
    self.damage = myData["Damage"] # damage mob deals to player
    self.health = myData["Health"]

    # load loot
    self.scoreValue = myData["Score"]
    self.loot = copy.deepcopy(myData["Loot"])
    lootDeletionList = [] # list of loot to remove if chance is not met; dict cannot change size during iteration
    for lootType in self.loot:
      # only drops if chance is met
      chance = self.loot[lootType]["Chance"]
      if random.random() > chance:
        lootDeletionList.append(lootType)
        continue

      amount = self.loot[lootType]["Amount"]
      amountType = type(amount)
      if amountType == tuple: # generates random amount
        amount = random.randint(amount[0], amount[1])
        self.loot[lootType]["Amount"] = amount # must overwrite so it does not change later
      elif amountType == list:
        amount = amount[0]

      for attribute in self.loot[lootType]:
        # generates any random distributions
        potentialTuple = self.loot[lootType][attribute]
        if type(potentialTuple) != tuple:
          continue
        # only run if tuple
        
        self.loot[lootType][attribute] = []
        for idx in range(0, amount):
          newValue = random.randint(potentialTuple[0], potentialTuple[1])
          self.loot[lootType][attribute].append(newValue)
      
    # deletes all loot that failed to drop
    for lootType in lootDeletionList:
      del self.loot[lootType] # removes from loot table

    # setup spawn indicator or direct spawn
    self.isSpawned = isSpawned #determines whether to be an x or not
    if isSpawned == False:
      self.initialTime = pygame.time.get_ticks()
    self.negXspeed = None
    self.negYspeed = None

  def prepareSpawn(self): #if not force spawned, create a spawn indicator
    self.image = pygame.transform.smoothscale(img_assets["unspawned_enemy"], (32, 32))
    if pygame.time.get_ticks() - self.initialTime >= 2000: #timer before spawning
      #initialises spawn
      self.image = self.baseImage
      self.isSpawned = True
      mobs.add(self)
      bottomSprites.remove(self)
      #allSprites.add(self)

  # move towards player
  def move(self):
    # makes movement ignore fps
    dt = clock.get_time()/1000

    # move towards player by default
    targetPos = tank_base.rect.center

    # draw line of movement
    if DEBUG_MODE:
      pygame.draw.line(display, RED, (self.x, self.y), targetPos, 3)

    dx = targetPos[0] - self.x
    dy = targetPos[1] - self.y
    magnitude = math.hypot(dx, dy)

    # adjust for proportion
    dx /= magnitude
    dy /= magnitude

    # apply speed
    self.xspeed = dx*self.speed
    self.yspeed = dy*self.speed

    # move at end of frame
    self.x += self.xspeed*dt
    self.y += self.yspeed*dt #separate non-rounded x/y values used
    self.rect.centerx = self.x
    self.rect.centery = self.y

    # collide with other enemies
    for otherEnemy in mobs:
      # ignore itself
      if otherEnemy == self:
        continue
      
      dx = self.x - otherEnemy.x
      dy = self.y - otherEnemy.y
      magnitude = math.hypot(dx, dy)
      minDist = self.radius + otherEnemy.radius # overlap distance

      # enemies are colliding
      if magnitude < minDist:
        overlapDist = minDist-magnitude # amount to push back by

        # normalise direction
        dx /= magnitude
        dy /= magnitude

        # push them apart; cut in half so both enemies move equally
        self.x += dx * overlapDist * 0.5
        self.y += dy * overlapDist * 0.5
        otherEnemy.x -= dx * overlapDist * 0.5
        otherEnemy.y -= dy * overlapDist * 0.5

        self.rect.center = (self.x, self.y)
        otherEnemy.rect.center = (otherEnemy.x, otherEnemy.y)





  def rotate(self, targetRect: pygame.rect.Rect):
    #point towards player``
    self.image = pygame.transform.smoothscale(self.baseImage, (32, 52))
    if targetRect.centerx-self.rect.centerx == 0: #prevents division by zero
      self.xChange = targetRect.centerx-self.rect.centerx+1
    else:
      self.xChange = targetRect.centerx-self.rect.centerx
    self.rotation = math.atan(((HEIGHT-targetRect.centery)-(HEIGHT-self.rect.centery))/(self.xChange))*(180/math.pi) #calculates the rotation needed to face the tank
    if targetRect.centerx < self.rect.centerx:
      self.rotation = self.rotation+180 #corrects rotation if the tank is on the left-hand side of the soldier
    #print("Rotation", self.rotation)
    #print("Tank base x", targetRect.x)
    #print("Tank base y", targetRect.y)
    #print("Enemy x", self.rect.x)
    #print("Enemy y", self.rect.y)
    self.image = pygame.transform.rotozoom(self.image, self.rotation, 1) 

  def tryDestroy(self, killedByPlayer=False):
    global score

    if self.health > 0:
      self.health -= 1
    
    if self.health <= 0:
      self.kill()
      # drop loot
      if killedByPlayer: #makes it not drop loot if player doesn't kill with gun
        LOOT_POSITION_VARIATION = 20

        audio_assets["kill"].play()
        # increment score by score value
        score += self.scoreValue

        for lootType in self.loot:
          # get loot data
          lootInfo = self.loot[lootType]
          amount = lootInfo["Amount"]
          value = lootInfo["Value"]

          # place correct number of loot drops
          for i in range(0, amount):
            position = (self.rect.centerx+random.randint(-LOOT_POSITION_VARIATION,LOOT_POSITION_VARIATION),self.rect.centery+random.randint(-LOOT_POSITION_VARIATION,LOOT_POSITION_VARIATION))
            placePickup(lootType, position, value[i])

  
  def update(self):
    if ticksPaused != 0: #makes sure pausing doesn't insta-spawn them
      self.initialTime += ticksPaused
    if self.isSpawned == True:
      self.move() #calls movement subroutine
      self.rotate(tank_base.rect)
    else:
      self.prepareSpawn()

# generic pickup base class
class Pickup(pygame.sprite.Sprite):
  def __init__(self, position, isSpawned=False, type="health", value=1):
    pygame.sprite.Sprite.__init__(self)
     # get data of pickup type
    myData = pickup_data.pickups[type]

    # setup appearance, hitbox and position
    # applies image override if applicable
    image = type
    if "Image" in myData:
      image = myData["Image"]
    
    # applies image size override if applicable
    if "ImageSize" in myData:
      self.image = pygame.transform.smoothscale(img_assets[image], myData["ImageSize"])
    else:
      self.image = pygame.transform.smoothscale(img_assets[image])
    self.baseImage = self.image # for changing image and reverting changes
    self.rect = self.image.get_rect()
    self.rect.center = position
    self.x = self.rect.centerx
    self.y = self.rect.centery

    # pickup stats
    self.value = value # value of pickup
    self.speed = myData["Speed"] # speed pickup moves at
    self.negSpeed = self.speed*(-1)
    # self.radius = self.image.get_size()[0]/2
    self.isSpawned = isSpawned
    # adds to pickups if already spawned
    if isSpawned:
      pickups.add(self)

    self.initialTime = pygame.time.get_ticks()
    self.type = type
  
  def prepareSpawn(self):
    global ticksPaused
    if ticksPaused != 0: #makes sure pausing doesn't insta-spawn them
      self.initialTime += ticksPaused

    self.image = pygame.transform.smoothscale(img_assets["unspawned_pickup"], (32, 32))
    if pygame.time.get_ticks() - self.initialTime >= 2000:
      self.image = self.baseImage
      self.isSpawned = True
      pickups.add(self)
      #bottomSprites.remove(self)
      #allSprites.add(self)
  
  def tryDestroy(self):
    self.kill()
  
  def moveTo(self, targetRect: pygame.rect.Rect):
    # makes movement ignore fps
    dt = clock.get_time()/1000

    xChange = abs(targetRect.centerx - self.x)
    yChange = abs(targetRect.centery - self.y)
    distance = math.sqrt((xChange**2)+(yChange**2))

    # hardcoded behaviour
    if self.type == "health":
      if not tank_base.health < tank_base.maxHealth: #health only moves if the player needs health
        return

    # must be close enough to collect
    if distance > tank_base.pickupRange:
      return
    
    if targetRect.centerx - self.x < 0: #super high-tech move towards player code
      xDif = abs((targetRect.x - self.x))
    else:
      xDif = targetRect.centerx - self.rect.centerx
    if targetRect.y - self.y < 0:
      yDif = abs((targetRect.centery - self.y))
    else:
      yDif = targetRect.y - self.y
    totalDif = xDif+yDif
    if totalDif == 0:
      totalDif = 1
    xProp = xDif/totalDif
    yProp = yDif/totalDif
    if targetRect.centerx - self.x < 0:
      self.xspeed = xProp * self.negSpeed
    else:
      self.xspeed = xProp * self.speed
    if targetRect.centery - self.y < 0:
      self.yspeed = yProp * self.negSpeed
    else:
      self.yspeed = yProp * self.speed
    #print("xspeed", self.xspeed)
    #print("yspeed", self.yspeed)
    self.x += self.xspeed*dt
    self.y += self.yspeed*dt #this is here due to pixel rounding
    self.rect.centerx = self.x
    self.rect.centery = self.y
  
  def update(self):
    if self.isSpawned == False:
      self.prepareSpawn()
    else:
      self.moveTo(tank_base.rect)

# health pickups
class HealthPickup(Pickup):
  def tryDestroy(self):
    successful = tank_base.add_health(self.value)
    if successful:
      self.kill()

class Coin(Pickup):
  def tryDestroy(self):
    tank_base.money += self.value
    audio_assets["coin"].play()
    self.kill()

class Bullet(pygame.sprite.Sprite):
  def __init__(self, position, targetRect: pygame.rect.Rect, pierce=0):
    pygame.sprite.Sprite.__init__(self)
    self.image = pygame.transform.scale(img_assets["bullet"], (28, 14)) #sets image
    self.rect = self.image.get_rect()
    self.radius = 8 #sets size of bullet

    #hide bullet offscreen
    self.rect.x = -100
    self.rect.y = -100

    #self.image.set_colorkey(WHITE)

    #sets bullet position to provided parameters (with correct offset)
    self.x = position[0]-14
    self.y = position[1]-7
    
    #super high-tech calculate movement towards crosshair code
    self.speed = 880
    self.negSpeed = self.speed*(-1) #used to reduce calculations later on
    if targetRect.centerx - self.x < 0: 
      xDif = (targetRect.centerx - self.x)*(-1)
    else:
      xDif = targetRect.centerx - self.x
    if targetRect.centery - self.y < 0:
      yDif = (targetRect.centery - self.y)*(-1)
    else:
      yDif = targetRect.centery - self.y
    totalDif = xDif+yDif
    if totalDif == 0:
      totalDif = 1
    xProp = xDif/totalDif
    yProp = yDif/totalDif
    if targetRect.centerx - self.x < 0:
      self.xspeed = xProp * self.negSpeed
    else:
      self.xspeed = xProp * self.speed
    if targetRect.centery - self.y < 0:
      self.yspeed = yProp * self.negSpeed
    else:
      self.yspeed = yProp * self.speed

    #position in front of gun
    self.x += self.xspeed/55*3.6
    self.y += self.yspeed/55*3.6

    #points towards crosshair
    self.image = pygame.transform.scale(img_assets["bullet"], (28, 13))
    # self.image.set_colorkey("WHITE")
    if targetRect.centerx-self.x != 0:
      self.rotation = math.atan(((HEIGHT-targetRect.centery)-(HEIGHT-self.y))/(targetRect.centerx-self.x))*(180/math.pi) # calculates the rotation needed to face the tank
      if targetRect.centerx < self.x:
        self.rotation = self.rotation+180 # corrects rotation if the crosshair is on the left-hand side of the bullet
      self.image = pygame.transform.rotate(self.image, self.rotation) # moves visuals
    #self.initialTime = pygame.time.get_ticks()
    self.pierce = pierce # how many enemies a bullet can hit

  def move(self):
    # makes movement ignore fps
    dt = clock.get_time()/1000

    # applies movement to bullet
    self.x += self.xspeed*dt
    self.y += self.yspeed*dt
    self.rect.centerx = self.x
    self.rect.centery = self.y

  def tryDestroy(self):
    # destroys self if hit too many enemies
    if self.pierce > 0:
      self.pierce -= 1
    else:
      self.kill()
    # audio_assets["bullet_hit"].play()

  def update(self):
    #attempt movement
    self.move()

    #delete if off the edge of the screen
    if self.rect.bottom < 0:
      self.kill()
    if self.rect.top > HEIGHT:
      self.kill()
    if self.rect.right < 0:
      self.kill()
    if self.rect.left > WIDTH:
      self.kill()
    #pygame.draw.circle(self.image, RED, self.rect.center, self.radius)

# initialise sprites and groups
mobs = pygame.sprite.Group()
playerBullets = pygame.sprite.Group()
pickups = pygame.sprite.Group()
tank_base = Player()
tank_gun = Tank_Gun(tank_base)
crosshair = ui.Cursor((25,25), 10, img_assets["crosshair"], {"Transparency": 1})
health_container = Health_Container("container")
health_container_inner = Health_Container("inner") 
# shopBase = ui.Frame((0,0), (500,500), 1, {"Colour": (255,0,0)}, {"Thickness": 10, "Transparency": 0.3})
# randomText = ui.TextLabel((0,0), (200, 200), {"Text": "I am the ultimate sigma"}, 2, {"Transparency": 1})

def buttonFunc():
  tank_base.tryDestroy(1)
def evilFunc():
  for x in range(0,100):
    place_object((random.randint(0, WIDTH), random.randint(0, HEIGHT)), "soldier")

funnyButton = ui.DetailedButton((200, 200), (200, 100), buttonFunc, {"Text": {"Text": "sigma button?"}, "Image": img_assets["soldier"]}, 2, {"Colour": (255,0,0)}, {"Thickness": 10})
evilButton = ui.TextButton((750, 200), (200, 100), evilFunc, {"Text": "heheheh", "Size": 50}, 2, {"Colour": (255,0,0)}, {"Thickness": 10})
allSprites.add(tank_base, tank_gun)

pygame.mixer.music.play(loops=-1) #infinitely loops the BGM
score = 0 #initialises the score variable, which is updated with score increases
paused = False #initialises the variable for whether the game is paused
pauseInitialTime = -1 #sets the initial pause time (less than 0 so it's never higher than the current time)
ticksPaused = 0 #tracks how long the game was paused for
lastSpawnTime = 0 #time since last enemy spawned

# Subroutines
def spawn_enemies(lastSpawnTime=0):
  def spawn_soldiers():
    xpos = random.randint(0, WIDTH) #generates 'centre' of enemy cluster
    ypos = random.randint(0, HEIGHT)
    for x in range(1, random.randint(2, 7)):
      newXpos = random.randint(max(0, xpos - 100), min(WIDTH, xpos + 100))
      newYpos = random.randint(max(0, ypos - 100), min(HEIGHT, ypos + 100))
      m = Enemy((newXpos, newYpos)) #spawns enemies in clusters close together
      bottomSprites.add(m)
      #mobs.add(m)
  
  if random.randint(1, 150) == 5:
    #spawn_soldiers()
    lastSpawnTime = pygame.time.get_ticks()
  elif (pygame.time.get_ticks() - lastSpawnTime) >= 7500:
    spawn_soldiers()
    lastSpawnTime = pygame.time.get_ticks()
  return lastSpawnTime

def spawn_loot():
    if random.randint(1,5000) == 5:
      healthPickupAmount = 0
      for item in pickups:
        if item.type == "health":
          healthPickupAmount += 1
      if healthPickupAmount < 2:
        xpos = random.randint(0, WIDTH) 
        ypos = random.randint(0, HEIGHT)
        p = HealthPickup((xpos, ypos), False, "health") 
        bottomSprites.add(p)

def place_object(position, type):
  # pickups
  if type == "health": #for placing objects manually (e.g. debug tools)
    object = HealthPickup(position, False, "health") 
    bottomSprites.add(object)
  else:
    object = Enemy(position, False, type) 
    bottomSprites.add(object)

def collisions():
  mobsHitByBullets = pygame.sprite.groupcollide(mobs, playerBullets, False, False, pygame.sprite.collide_circle)
  # bulletsHitMobs = pygame.sprite.groupcollide(playerBullets, mobs, False, False, pygame.sprite.collide_circle)
  mobsHitPlayer = pygame.sprite.spritecollide(tank_base, mobs, False, pygame.sprite.collide_circle)
  playerTouchedPickup = pygame.sprite.spritecollide(tank_base, pickups, False, pygame.sprite.collide_circle)
  #mobsTouchingMobs = pygame.sprite.groupcollide(mobs, mobs, False, False, pygame.sprite.collide_circle) #<- this collision system is both laggy and does not function properly
  for mob in mobsHitByBullets:
    mob.tryDestroy(True)
    # score += 5
    # attempt to destroy all bullets
    bullets = mobsHitByBullets[mob]
    for bullet in bullets:
      bullet.tryDestroy()

  for mob in mobsHitPlayer:
    mob.tryDestroy()
    tank_base.tryDestroy(mob.damage)
  for pickup in playerTouchedPickup:
    if pickup.type == "health":
      pickup.tryDestroy()
    elif pickup.type == "coin":
      pickup.tryDestroy()
  #for mob in mobsTouchingMobs:
  #  otherMobs = mobsTouchingMobs[mob]
  #  if len(otherMobs) > 1:
  #    for otherMob in otherMobs:
  #      if (otherMob.x, otherMob.y) != (mob.x, mob.y): #does not count itself ;-;
  #        if abs(otherMob.x-mob.x) < 25 and abs(otherMob.y-mob.y) < 25:
  #          mob.collide((otherMob.x, otherMob.y))
  # return score

# shows the cooldown between shots
def showCooldown():
    # calculate time until cooldown ends
    startTime = tank_base.initialShotTime
    currentTime = pygame.time.get_ticks()
    cooldown = tank_base.shotCooldown
    endTime = startTime+cooldown
    timeRemaining = endTime-currentTime

    # only show if cooldown active
    if timeRemaining <= 0:
      return

    # get position to draw at
    x = crosshair.rect.centerx
    y = crosshair.rect.centery + 16

    # draw a cooldown bar
    BAR_HEIGHT = 5
    BAR_WIDTH = 20

    # offset bar to be centred
    x -= BAR_WIDTH/2

    # draw background of bar
    emptyBar = pygame.rect.Rect(x, y, BAR_WIDTH, BAR_HEIGHT)
    pygame.draw.rect(display, (150, 150, 150), emptyBar)
    
    # calculate proportion full
    proportion = timeRemaining/cooldown
    fullBarWidth = proportion*BAR_WIDTH
    fullBar = pygame.rect.Rect(x, y, fullBarWidth, BAR_HEIGHT)

    # draw full part of bar
    pygame.draw.rect(display, BLACK, fullBar)

# draws all sprites to screen
def drawAll():
  bottomSprites.draw(display)
  mobs.draw(display)
  allSprites.draw(display) #draws the sprites to the screen
  topSprites.draw(display)


# bind all inputs
# lambda works to "define" functions
# stop the game running
input_handler.bindToInput(
    pygame.K_ESCAPE,
    lambda: setattr(env, "running", False)
)

# toggle pause
input_handler.bindToInput(
    pygame.K_p,
    lambda: globals().__setitem__("paused", not paused)
)

# start shooting when spacebar is pressed
input_handler.bindToInput(
    pygame.K_SPACE,
    lambda: setattr(tank_base, "shooting", True)
)

# also shoot for left mouse button
input_handler.bindToInput(
    1,
    lambda: setattr(tank_base, "shooting", True)
)

# stop shooting when spacebar let go
input_handler.bindToInput(
    pygame.K_SPACE,
    lambda: setattr(tank_base, "shooting", False),
    "keyup"
)

# also stop shooting when mouse let go
input_handler.bindToInput(
    1,
    lambda: setattr(tank_base, "shooting", False),
    "keyup"
)

# dev tools
input_handler.bindToInput(
    pygame.K_F1,
    lambda: setattr(tank_base, "health", tank_base.health + 1)
)

input_handler.bindToInput(
    pygame.K_F2,
    lambda: place_object(pygame.mouse.get_pos(), "health")
)

input_handler.bindToInput(
    pygame.K_F3,
    lambda: place_object(pygame.mouse.get_pos(), "soldier")
)

input_handler.bindToInput(
    pygame.K_F4,
    lambda: place_object(pygame.mouse.get_pos(), "brute")
)


#Main program
while env.running: #runs the game loop
  display.fill(WHITE) 
  #do not run if paused
  if paused and pauseInitialTime == -1: #checks whether the game is paused for the first time
    pauseInitialTime = pygame.time.get_ticks() #sets the last time the game was paused
  if not paused:
    if ticksPaused != 0: #resets variable for how long the game was paused for
      ticksPaused = 0
    if pauseInitialTime != -1:
      ticksPaused = pygame.time.get_ticks()-pauseInitialTime #sets how long the game was paused for
      pauseInitialTime = -1 #resets paused state
    clock.tick(FPS) #ticks the clock based on the set FPS
    lastSpawnTime = spawn_enemies(lastSpawnTime)
    spawn_loot()
    # score = collisions(score)
    bottomSprites.update()
    mobs.update()
    allSprites.update()
    topSprites.update()

    # draws all to the screen
    drawAll()

    # collisions done after they are shown
    collisions()
    # show shot cooldown
    showCooldown()
    # show score and money earned
    draw_text(display, "Score: "+str(score), 18, WIDTH / 2, 20)
    draw_text(display, "Money: "+str(tank_base.money), 18, WIDTH / 2, 40)
    # show additional stats in debug mode
    if DEBUG_MODE:
      draw_text(display, "Health: "+str(tank_base.health)+"/"+str(tank_base.maxHealth), 18, WIDTH / 2, 60)
      draw_text(display, "Ticks: "+str(pygame.time.get_ticks()), 18, WIDTH / 2, 80)
      draw_text(display, "FPS: "+str(round(clock.get_fps(), 1)), 18, WIDTH / 2, 100)
      draw_text(display, env.currentDebugOutput, 18, WIDTH / 2, 120)

  topSprites.update()
  
  # draws all to the screen
  drawAll()

  if clock.get_fps() >= 30:
    pygame.mouse.set_visible(False) #makes the mouse invisible if game isn't lagging
  else:
    pygame.mouse.set_visible(True)
  pygame.display.flip() #shows everything that was drawn on the screen

  # handle all key presses
  input_handler.handleInputs()

#print(pygame.mouse.get_pos()) #prints the mouse position to terminal (x, y)

pygame.quit() #quits program when it stops running