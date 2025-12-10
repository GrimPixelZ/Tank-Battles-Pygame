enemies = {
    "soldier": {
        # stats
        "Health": 1,
        "Damage": 1,
        "Speed": 5,
        "Score": 5,
        # visual overrides
        "ImageSize": (32, 52),
        # loot drops
        "Loot": {
            "health": {
                "Amount": 1,
                "Value": [1],
                "Chance": 0.02
            },
            "coin": {
                "Amount": (2, 4),
                "Value": (5, 10),
                "Chance": 1
            },
        }
    },
    "brute": {
        # stats
        "Health": 3,
        "Damage": 2,
        "Speed": 3,
        "Score": 10,
        # visual overrides
        "Image": "soldier",
        "ImageSize": (32, 52),
        "Recolour": [ # changes colour of enemy
            {
                "TargetColour": (255, 0, 0),
                "ReplacementColour": (0,0,255)
            }
        ],
        # loot drops
        "Loot": {
            "health": {
                "Amount": 1,
                "Value": [1],
                "Chance": 0.02
            },
            "coin": {
                "Amount": (2, 4),
                "Value": (10, 20),
                "Chance": 1
            },
        }
    },
}