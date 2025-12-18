import math

weapons = {
    "pellet": {
        "Pierce": 0,
        "Range": math.inf,
        "Cooldown": 400,
        "Bullets": 1,
        # visuals
        "Image": "tank_gun",
        "ImageSize": (66, 32),
        "Pivot": (50, 16),
    },
    "minigun": {
        "Pierce": 0,
        "Range": 300,
        "Cooldown": 100,
        "Bullets": 1,
        # visuals
        "Image": "minigun",
        "ImageSize": (107, 35),
        "Pivot": (90, 17),
    },
    "shotgun": {
        "Pierce": 0,
        "Range": 200,
        "Cooldown": 600,
        "Bullets": 3,
        # visuals
        "Image": "shotgun",
        "ImageSize": (59, 32),
        "Pivot": (43, 15),
    },
    "mega_shotgun": {
        "Pierce": 0,
        "Range": 200,
        "Cooldown": 600,
        "Bullets": 21,
        # visuals
        "Image": "minigun",
        "ImageSize": (107, 35),
        "Pivot": (90, 16),
    },

    # for enemy tanks
    "enemy_tank_gun": {
        # visuals
        "Image": "enemy_tank_gun",
        "ImageSize": (66, 32),
        "Pivot": (50, 16),
    },
}