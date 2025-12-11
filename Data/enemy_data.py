# stores the data of all spawnable enemies
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
        "SpawnWeight": 30, # weighted spawn system
        "MinClusterSize": 1,
        "MaxClusterSize": 5, # how many can spawn in one cluster
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
        "SpawnWeight": 15, # weighted spawn system
        "MinClusterSize": 1,
        "MaxClusterSize": 3, # how many can spawn in one cluster
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
    "tank": {
        # stats
        "Health": 3,
        "Damage": 1,
        "Speed": 200,
        "Score": 15,
        # spawning
        "SpawningScore": 500,
        "SpawnWeight": 5,
        "MinClusterSize": 1,
        "MaxClusterSize": 1, # how many can spawn in one cluster
        "Class": "EnemyTank", # class override
        # visual overrides
        "Image": "enemy_tank_base",
        "ImageSize": (50, 50),
        # loot drops
        "Loot": {
            "health": {
                "Amount": 1,
                "Value": [1],
                "Chance": 0.02
            },
            "coin": {
                "Amount": (1, 4),
                "Value": (8, 15),
                "Chance": 1
            },
        }
    },
    "ferret": {
        # stats
        "Health": 2,
        "Damage": 1,
        "Speed": 20,
        "Score": 15,
        # spawning
        "SpawningScore": 1000,
        "SpawnWeight": 10,
        "MinClusterSize": 1,
        "MaxClusterSize": 2, # how many can spawn in one cluster
        "Class": "SpeedsterEnemy",
        # visual overrides
        "Image": "ferret",
        "ImageSize": (104, 52),
        # loot drops
        "Loot": {
            "health": {
                "Amount": 1,
                "Value": [1],
                "Chance": 0.02
            },
            "coin": {
                "Amount": (1, 4),
                "Value": (8, 15),
                "Chance": 1
            },
        }
    }
}