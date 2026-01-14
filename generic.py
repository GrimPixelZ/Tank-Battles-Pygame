# script for generic classes and functions used by many modules
import pygame, numpy
# custom imports
import env

# changes all pixels of given color in image; outsourced externally
def recolour_image(image: pygame.image, target_colour: list, replacement_colour: list, tolerance: float=50):
  arr = pygame.surfarray.pixels3d(image)
    
  # Calculate color difference per pixel
  diff = numpy.sqrt(numpy.sum((arr - target_colour) ** 2, axis=2))
  
  # Mask of pixels within tolerance
  mask = diff <= tolerance
  
  # Replace colors
  arr[mask] = replacement_colour

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


# collides with walls, etc
class PhysicsObject(pygame.sprite.Sprite):
  def _stay_in_bounds(self):
    #keeps the object within bounds of the map
    if self.rect.right > env.WIDTH:
      self.x = env.WIDTH - self.rect.width/2
      self.rect.centerx = self.x
    if self.rect.left < 0:
      self.x = 0 + self.rect.width/2
      self.rect.centerx = self.x
    if self.rect.bottom > env.HEIGHT:
      self.y = env.HEIGHT - self.rect.height/2
      self.rect.centery = self.y
    if self.rect.top < 0:
      self.y = 0 + self.rect.height/2
      self.rect.centery = self.y     

  def update(self):
    #keeps the object within bounds of the map
    self._stay_in_bounds()

# fades out an object over time (e.g. bullets)

class FadeOut(pygame.sprite.Sprite):
  def __init__(self, surface: pygame.surface.Surface, alpha_per_sec: float):
    super().__init__()
    # create blank image and rect
    self.image = pygame.Surface((0,0))
    self.rect = pygame.rect.Rect(0,0,0,0)

    self.target_surface = surface
    self.alpha_per_sec = alpha_per_sec

    # add to top sprites for updating
    env.top_sprites.add(self)
  
  def update(self):
    dt = env.get_deltatime()

    current_alpha = self.target_surface.get_alpha()
    new_alpha = current_alpha - dt * self.alpha_per_sec
    self.target_surface.set_alpha(new_alpha)

    # destroy after fade complete
    if new_alpha <= 0:
      self.kill()
