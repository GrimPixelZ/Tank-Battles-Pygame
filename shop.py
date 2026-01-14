# sets up the shop, used for buying upgrades
import pygame
# custom imports
import env, ui, player as plr, sound, input_handler
from Data import shop_data

BUTTON_WIDTH = 450
BUTTON_HEIGHT = 150
BUTTON_GAP = 50 # pixels between buttons
BUTTONS_PER_ROW = 3 # how many buttons fit in one row

open = {
    # player: bool
} # whether shop is open for a given player
shop_objects = {
 # player: objects
} # ui elements in shop (for later deletion)

def _get_button_pos(slot_idx: int):
    row_position = slot_idx % BUTTONS_PER_ROW # position in its row
    x_pos = row_position * BUTTON_WIDTH + BUTTON_GAP * row_position + BUTTON_WIDTH/2
    column_position = slot_idx // BUTTONS_PER_ROW # which column button is on
    y_pos = column_position * BUTTON_HEIGHT + BUTTON_GAP * column_position + BUTTON_GAP
    return (x_pos, y_pos)

def get_data_for_level(slot_data: dict, upgrade_level: int):
    # correct data has been found
    if upgrade_level == 0:
        return slot_data
    # check if next upgrade is available
    if "Next" in slot_data:
        return get_data_for_level(slot_data["Next"], upgrade_level-1)
    else: # no further upgrade available
        return None

def _update_slot(player: plr.Player, slot_idx: int, slot_data: dict, clicks_required: int=0):
    # check which level player currently has upgraded to
    initial_slot_data = slot_data
    upgrade_level = 0
    unlocked_upgrades = player.unlocked_upgrades
    if slot_idx in unlocked_upgrades:
        upgrade_level = unlocked_upgrades[slot_idx]
    
    button_colour = env.WHITE
    # if multiplayer, change to player colour for visual clarity
    if env.MULTIPLAYER:
        button_colour = plr.Player.get_player_colour(player.player_num)

    # get data for correct level 
    slot_data = get_data_for_level(slot_data, upgrade_level)
    if not slot_data: # create empty frame if no upgrade available
        max_frame = ui.TextLabel(
            _get_button_pos(slot_idx),
            (BUTTON_WIDTH, BUTTON_HEIGHT),
            {"Text": "MAX", "Size": 100},
            2,
            {"Colour":button_colour},
            {"Thickness": 10}
        )
        shop_objects[player].append(max_frame)
        return

    upgrade_name = slot_data["Name"] + " £" + str(slot_data["Cost"])
    upgrade_button = None
    # function run when upgrade is obtained
    def upgrade_func():
        nonlocal clicks_required
        # ensure player can afford upgrade
        # debounce check to ensure one click does not buy an upgrade and the upgrade after
        if clicks_required > 0:
            clicks_required -= 1
            return

        if slot_data["Cost"] > player.money:
            sound.play_sound("fail")
            return
        # disable button
        upgrade_button.try_destroy()

        sound.play_sound("purchase")
        # save upgrade
        player.save_upgrade(slot_idx, upgrade_level+1)
        # deduct money
        player.money -= slot_data["Cost"]
        # award stat increase/weapon/etc
        func_name = slot_data["Function"]["Name"]
        func_args = slot_data["Function"]["Args"]
        method = getattr(player, func_name)
        method(*func_args)

        # destroy old and update button after purchase
        shop_objects[player].remove(upgrade_button)
        _update_slot(player, slot_idx, initial_slot_data, 1)

    upgrade_button = ui.Button(
        _get_button_pos(slot_idx),
        (BUTTON_WIDTH, BUTTON_HEIGHT),
        {
            "ButtonUp": upgrade_func,
            "Text": {"Text": upgrade_name, "Size": 40, "Alignment": "monkey"},
        },
        2,
        {"Colour": button_colour},
        {"Thickness": 10},
    )
    shop_objects[player].append(upgrade_button)

def _try_enable_joystick_cursor(player: plr.Player):
    # enable controller mouse if joysticks or multiplayer
    if len(input_handler.joysticks) > 0:
        if env.MULTIPLAYER and player.player_num == 0: # player 0 cannot have controller on multiplayer
            return

        cursor = player.create_controller_cursor()
        shop_objects[player].append(cursor)


def open_shop(player: plr.Player):
    global open
    # pause the game
    env.paused = True
    # allow other scripts to know shop is open
    open[player] = True
    shop_objects[player] = [] # initialise shop objects list

    # enable controller mouse if joysticks or multiplayer
    _try_enable_joystick_cursor(player)

    # create a button for each slot in the shop
    for slot_idx, slot_data in enumerate(shop_data.shop):
        # create title for slot
        button_pos = _get_button_pos(slot_idx)
        title_label = ui.TextLabel(
            (button_pos[0], button_pos[1] - BUTTON_HEIGHT/4),
            (BUTTON_WIDTH, BUTTON_HEIGHT/2),
            {"Text": slot_data["Title"], "Size": 25},
            2,
            background={"Transparency":1}
        )
        shop_objects[player].append(title_label)
        _update_slot(player, slot_idx, slot_data)

# closes the shop, removing all ui elements
def close_shop(player: plr.Player):
    for object in shop_objects[player]:
        object.try_destroy()
    shop_objects[player] = []
    open[player] = False
    env.paused = False