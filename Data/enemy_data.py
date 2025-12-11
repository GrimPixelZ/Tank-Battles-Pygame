enemies = {
    "soldier": {
        # stats
        "Health": 1,
        "Damage": 1,
        "Speed": 275,
        "Score": 5,
        "Radius": 15, # for collisions
        # spawning
        "SpawningScore": 0, # score enemy spawns at
        "ClusterSize": 5, # how many can spawn in one cluster
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
                "Amount": (1, 2),
                "Value": (5, 10),
                "Chance": 1
            },
        }
    },
    "brute": {
        # stats
        "Health": 4,
        "Damage": 2,
        "Speed": 165,
        "Score": 10,
        "Radius": 17, # for collisions
        # spawning
        "SpawningScore": 200,
        "ClusterSize": 3,
        # visual overrides
        "Image": "brute",
        "ImageSize": (37, 59),
        # "Recolour": [ # changes colour of enemy
        #     {
        #         "TargetColour": (255, 0, 0),
        #         "ReplacementColour": (0,0,255)
        #     }
        # ],
        # loot drops
        "Loot": {
            "health": {
                "Amount": 1,
                "Value": [1],
                "Chance": 0.02
            },
            "coin": {
                "Amount": (1, 3),
                "Value": (8, 15),
                "Chance": 1
            },
        }
    },
}