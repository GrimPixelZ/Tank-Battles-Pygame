# stores all buyable items, their prices and their prerequisites
shop = [
    # slot 0; pellet upgrades
    {
        # visuals
        "Title": "Pellet",
        "Name": "+1 Pierce", # displayed name of upgrade
        "Image": "soldier", # image used to represent upgrade
        "ImageSize": (100, 100), # resolution of image; will always be centred in corner
        # data
        "Cost": 100, # in money
        "Function": { # what runs to apply the upgrade (defined in player class)
            "Name": "add_stat_to_weapon",
            "Args": ["pellet", "pierce", 1],
        },
        "Next": { # upgrade after first obtained
            # visuals
            "Name": "-20% Cooldown",
            "Image": "soldier", # image used to represent upgrade
            "ImageSize": (100, 100), # resolution of image; will always be centred in corner
            # Data
            "Cost": 250,
            "Function": { # what runs to apply the upgrade (defined in player class)
                "Name": "add_stat_to_weapon",
                "Args": ["pellet", "shot_cooldown", -0.08]
            },
            "Next": {
                # visuals
                "Name": "+1 Pierce", # displayed name of upgrade
                "Image": "soldier", # image used to represent upgrade
                "ImageSize": (100, 100), # resolution of image; will always be centred in corner
                # data
                "Cost": 1000, # in money
                "Function": { # what runs to apply the upgrade (defined in player class)
                    "Name": "add_stat_to_weapon",
                    "Args": ["pellet", "pierce", 1],
                },
                "Next": {
                    # visuals
                    "Name": "-20% Cooldown",
                    "Image": "soldier", # image used to represent upgrade
                    "ImageSize": (100, 100), # resolution of image; will always be centred in corner
                    # Data
                    "Cost": 1250,
                    "Function": { # what runs to apply the upgrade (defined in player class)
                        "Name": "add_stat_to_weapon",
                        "Args": ["pellet", "shot_cooldown", -0.08]
                    },
                    "Next": {
                        # visuals
                        "Name": "+3 Pierce", # displayed name of upgrade
                        "Image": "soldier", # image used to represent upgrade
                        "ImageSize": (100, 100), # resolution of image; will always be centred in corner
                        # data
                        "Cost": 5000, # in money
                        "Function": { # what runs to apply the upgrade (defined in player class)
                            "Name": "add_stat_to_weapon",
                            "Args": ["pellet", "pierce", 3],
                        },
                        "Next": {
                            # visuals
                            "Name": "+5 Pierce", # displayed name of upgrade
                            "Image": "soldier", # image used to represent upgrade
                            "ImageSize": (100, 100), # resolution of image; will always be centred in corner
                            # data
                            "Cost": 10000, # in money
                            "Function": { # what runs to apply the upgrade (defined in player class)
                                "Name": "add_stat_to_weapon",
                                "Args": ["pellet", "pierce", 5],
                            },
                        }
                    }
                }
            },
        }
    },
    # slot 1; shotgun upgrades
    {
        # Visuals
        "Title": "Shotgun",
        "Name": "Shotgun",
        "Image": "soldier",
        "ImageSize": (100, 100),
        # Data
        "Cost": 250,
        "Function": {
            "Name": "award_weapon",
            "Args": ["shotgun"],
        },
        "Next": {
            "Name": "+2 Bullets",
            # Data
            "Cost": 750,
            "Function": {
                "Name": "add_stat_to_weapon",
                "Args": ["shotgun", "bullets", 2]
            },
            "Next": {
                "Name": "+1 Pierce",
                # Data
                "Cost": 1500,
                "Function": {
                    "Name": "add_stat_to_weapon",
                    "Args": ["shotgun", "pierce", 1]
                },
                "Next": {
                    "Name": "+25% Range",
                    # Data
                    "Cost": 1750,
                    "Function": {
                        "Name": "add_stat_to_weapon",
                        "Args": ["shotgun", "range", 100]
                    },
                    "Next": {
                        "Name": "-20% Cooldown",
                        # Data
                        "Cost": 3000,
                        "Function": {
                            "Name": "add_stat_to_weapon",
                            "Args": ["shotgun", "shot_cooldown", -120]
                        },
                        "Next": {
                            "Name": "+2 Bullets",
                            # Data
                            "Cost": 10000,
                            "Function": {
                                "Name": "add_stat_to_weapon",
                                "Args": ["shotgun", "bullets", 2]
                            },
                        }
                    }
                }
            }
        }
    },
    # slot 3, minigun
    {
        # Visuals
        "Title": "Minigun",
        "Name": "Minigun",
        "Image": "soldier",
        "ImageSize": (100, 100),
        # Data
        "Cost": 2000,
        "Function": {
            "Name": "award_weapon",
            "Args": ["minigun"],
        },
        "Next": {
            "Name": "-20% Cooldown",
            # Data
            "Cost": 1500,
            "Function": {
                "Name": "add_stat_to_weapon",
                "Args": ["minigun", "shot_cooldown", -20]
            },
            "Next": {
                "Name": "-20% Cooldown",
                # Data
                "Cost": 3000,
                "Function": {
                    "Name": "add_stat_to_weapon",
                    "Args": ["minigun", "shot_cooldown", -20]
                },
                "Next": {
                    "Name": "-20% Cooldown",
                    # Data
                    "Cost": 7500,
                    "Function": {
                        "Name": "add_stat_to_weapon",
                        "Args": ["minigun", "shot_cooldown", -20]
                    },
                    "Next": {
                        "Name": "-20% Cooldown",
                        # Data
                        "Cost": 15000,
                        "Function": {
                            "Name": "add_stat_to_weapon",
                            "Args": ["minigun", "shot_cooldown", -20]
                        }
                    }
                }
            }
        }
    },
    # slot 4, pickup range upgrades
    {
        "Title": "Pickup",
        "Name": "+50% Radius",
        "Image": "soldier",
        "ImageSize": (100, 100),
        # Data
        "Cost": 250,
        "Function": {
            "Name": "add_stat",
            "Args": ["pickup_range", 75],
        },
        "Next": {
            "Name": "+50% Radius",
            "Image": "soldier",
            "ImageSize": (100, 100),
            # Data
            "Cost": 500,
            "Function": {
                "Name": "add_stat",
                "Args": ["pickup_range", 75],
            },
                "Next": {
                    "Name": "+50% Radius",
                "Image": "soldier",
                "ImageSize": (100, 100),
                # Data
                "Cost": 2000,
                "Function": {
                    "Name": "add_stat",
                    "Args": ["pickup_range", 75],
                },
                "Next": {
                    "Name": "+50% Radius",
                    "Image": "soldier",
                    "ImageSize": (100, 100),
                    # Data
                    "Cost": 5000,
                    "Function": {
                        "Name": "add_stat",
                        "Args": ["pickup_range", 75],
                    },
                },
            },
        }
    },
    {
        "Title": "Movement",
        "Name": "+20% Speed",
        # data
        "Cost": 1500,
        "Function": {
            "Name": "add_stat",
            "Args": ["speed", 77]
        },
        "Next": {
            "Name": "+20% Speed",
            # data
            "Cost": 5000,
            "Function": {
                "Name": "add_stat",
                "Args": ["speed", 77]
            },
            "Next": {
                "Name": "+20% Speed",
                # data
                "Cost": 20000,
                "Function": {
                    "Name": "add_stat",
                    "Args": ["speed", 77]
                },
            }
        }
    },
    {
        "Title": "Max Health",
        "Name": "+2 Max Health",
        # data
        "Cost": 2000,
        "Function": {
            "Name": "add_stat",
            "Args": ["max_health", 2]
        },
        "Next": {
            "Name": "+2 Max Health",
            # data
            "Cost": 6000,
            "Function": {
                "Name": "add_stat",
                "Args": ["max_health", 2]
            },
            "Next": {
                "Name": "+2 Max Health",
                # data
                "Cost": 12000,
                "Function": {
                    "Name": "add_stat",
                    "Args": ["max_health", 2]
                },
                "Next": {
                   "Name": "+4 Max Health",
                    # data
                    "Cost": 30000,
                    "Function": {
                        "Name": "add_stat",
                        "Args": ["max_health", 4]
                    }, 
                }
            }
        }
    }
]