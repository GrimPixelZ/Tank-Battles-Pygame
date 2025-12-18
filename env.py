# stores all globals
import pygame
import os

# whether game is running
running = True

#values for window size
WIDTH = 1920
HEIGHT = 1080
FPS = 60 #frames per second

#predefined colours
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# whether to show debug values etc
DEBUG_MODE = True
current_debug_output = "" # shows on screen for debugging purposes

# whether multiplayer is enabled
MULTIPLAYER = False
player_count = 0 # number of players currently connected

pygame.init() # initialises pygame
pygame.mixer.init() # initialises audio 
display = pygame.display.set_mode((WIDTH, HEIGHT)) # sets the pygame display
clock = pygame.time.Clock() # sets the pygame clock (used for timer-based events)
bottom_sprites = pygame.sprite.Group()
all_sprites = pygame.sprite.Group() # group for updating all sprites
top_sprites = pygame.sprite.LayeredUpdates() # sprites that go at the very top
pygame.display.set_caption("Tank Battles") #sets the window title

#folders where files are stored
game_folder = os.path.dirname(__file__)
img_folder = os.path.join(game_folder, "Assets")
audio_folder = os.path.join(game_folder, "Audio")

#assign background music and its volume
background_music = pygame.mixer.music.load(os.path.join(audio_folder, "accion.mp3"))
pygame.mixer.music.set_volume(1)

img_assets = {
  # player
  "tank_base": None,
  "tank_gun": None,
  "minigun": None,
  "shotgun": None,

  # ui
  "crosshair": None,
  "health_container": None,
  "health_container_inner": None,

  # enemies
  "soldier": None,
  "unspawned_enemy": None,
  "brute": None,
  "enemy_tank_base": None,
  "enemy_tank_gun": None,
  "enemy_bullet": None,
  "ferret": None,

  # enemy/player
  "bullet": None,

  # map objects
  "health_pickup": None,
  "unspawned_pickup": None,
  "coin": None,
}

# load all image assets
for key in img_assets:
  img_assets[key] = pygame.image.load(os.path.join(img_folder, key+".png")).convert_alpha()

audio_assets = {
  # gameplay
  "tank_shoot": 0.3,
  # "bullet_hit": 0.5,
  "tank_hit": 1,
  "kill": 0.4,
  "heal": 0.5,
  "coin": 0.25,
}

# load all sound assets
for key in audio_assets:
  sound = pygame.mixer.Sound(os.path.join(audio_folder, key+".mp3"))
  sound.set_volume(audio_assets[key])
  audio_assets[key] = sound
  

DEFAULT_FONT = pygame.font.match_font('arial')

ticks_paused = 0

# helper functions
def draw_text(surf, text, size, x, y):
    font = pygame.font.Font(DEFAULT_FONT, size)
    text_surface = font.render(text, True, BLACK)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surf.blit(text_surface, text_rect)

def output_for_debugging(text):
   global current_debug_output
   if not DEBUG_MODE:
      return

   current_debug_output = text

# for scaling with framerate
def get_deltatime():
  dt = clock.get_time()/1000
  # must account for time paused to avoid teleporting
  dt -= ticks_paused/1000
  return dt