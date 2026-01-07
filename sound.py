# plays sounds such as sound effects
import pygame
# custom imports
import env

# plays a pre-loaded sound of a given name
def play_sound(sound_name: str):
    if not sound_name in env.audio_assets:
        print("Sound", sound_name, "does not exist and could not be played!")
        return

    sound = env.audio_assets[sound_name]
    channel = pygame.mixer.find_channel() #  ensures sounds can play at the same time
    # cannot play sound if at max channels
    if not channel:
        print("At maximum sound channels, cannot play sound", sound_name+"!")
        return
    channel.play(sound)
    