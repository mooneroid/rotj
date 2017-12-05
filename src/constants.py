# -*- coding: UTF-8 -*-

from pygame.locals import *

# colors
WHITE = (255,255,255)
BLACK = (0,0,0)
COPPER = (164, 82, 41)

# sizes
TILE_SIZE = 16 # pixels
GAME_WIDTH = 256 # pixels (before scaling)
GAME_HEIGHT = 240 # pixels (before scaling)

DEFAULT_ENCOUNTER_CHANCE = 0.01

EXP_REQUIRED_BY_LEVEL = {
    1: 0,
    2: 20,
    3: 50,
    4: 95,
    5: 162,
    6: 263,
    7: 404,
    8: 602,
    9: 897,
    10: 1267,
    11: 1811,
    12: 2518,
    13: 3438,
    14: 4634,
    15: 6189,
    16: 8210,
    17: 10636,
    18: 13547,
    19: 17040,
    20: 21232,
    21: 26263,
    22: 31797,
    23: 34884,
    24: 44579,
    25: 51944,
    26: 60045,
    27: 68956,
    28: 78759,
    29: 89542,
    30: 101403,
    31: 114451,
    32: 128730,
    33: 144591,
    34: 161957,
    35: 181060,
    36: 202073,
    37: 225188,
    38: 250614,
    39: 278583,
    40: 309349,
    41: 343191,
    42: 380417,
    43: 421365,
    44: 466408,
    45: 515956,
    46: 549978,
    47: 627686,
    48: 687775,
    49: 750868,
    50: 817116,
    51: 884309,
    52: 955962,
    53: 1032881,
    54: 1110470,
    55: 1191665,
    56: 1276485,
    57: 1359203,
    58: 1443282,
    59: 1530096,
    60: 1622747,
    61: 1715894,
    62: 1810001,
    63: 1913924,
    64: 2014406,
    65: 2115299,
    66: 2218765,
    67: 2320459,
    68: 2431120,
    69: 2542803,
    70: 2658109,
    71: 2774038,
    72: 2894345,
    73: 3023302,
    74: 3168479,
    75: 3329104,
    76: 3501820,
    77: 3712346,
    78: 3942986,
    79: 4210954,
    80: 4554987,
    81: 4889056,
    82: 5221743,
    83: 5689201,
    84: 6129743,
    85: 6638102,
    86: 7200105,
    87: 7823489,
    88: 8510201,
    89: 9255308,
    90: 9999999,
}

MAX_NUM = 99999999 # theoretical max num of soldiers, max num of food and money. But exp maxes at 9,999,999.

TACTICS = {
    'fire': {
        'min_damage': 30,
        'max_damage': 50,
        'type': 'enemy', # type can be enemy, ally, enemies, allies, defense, single
        'min_intelligence': 100,
        'min_level': 2,
        'success_probability_type': 'enemy_prob',
            # enemy_prob = ((intel-enemy_intel)/255+1)/2
            # one = 1
            # intel_prob = intel/255
            # assassin = enemy_prob/3
        'slot': 1,
        'tactical_points': 2,
    },
    'bomb': {
        'min_damage': 70,
        'max_damage': 150,
        'type': 'enemy',
        'min_intelligence': 110,
        'min_level': 9,
        'success_probability_type': 'enemy_prob',
        'slot': 1,
        'tactical_points': 4,
    },
    'lava': {
        'min_damage': 100,
        'max_damage': 200,
        'type': 'enemies',
        'min_intelligence': 130,
        'min_level': 16,
        'success_probability_type': 'enemy_prob',
        'slot': 1,
        'tactical_points': 6,
    },
    'brimstone': {
        'min_damage': 700,
        'max_damage': 1100,
        'type': 'enemy',
        'min_intelligence': 180,
        'min_level': 23,
        'success_probability_type': 'enemy_prob',
        'slot': 1,
        'tactical_points': 8,
    },
    'backdraft': {
        'min_damage': 1000,
        'max_damage': 2000,
        'type': 'enemies',
        'min_intelligence': 190,
        'min_level': 30,
        'success_probability_type': 'enemy_prob',
        'slot': 1,
        'tactical_points': 12,
    },
    'blue~flame': {
        'min_damage': 3000,
        'max_damage': 6000,
        'type': 'enemy',
        'min_intelligence': 210,
        'min_level': 35,
        'success_probability_type': 'enemy_prob',
        'slot': 1,
        'tactical_points': 16,
    },
    'volcano': {
        'min_damage': 10000,
        'max_damage': 20000,
        'type': 'enemies',
        'min_intelligence': 225,
        'min_level': 41,
        'success_probability_type': 'enemy_prob',
        'slot': 1,
        'tactical_points': 20,
    },
    'napalm': {
        'min_damage': 50000,
        'max_damage': 100000,
        'type': 'enemy',
        'min_intelligence': 235,
        'min_level': 52,
        'success_probability_type': 'enemy_prob',
        'slot': 1,
        'tactical_points': 24,
    },
    'baby~nuke': {
        'min_damage': 1000000,
        'max_damage': 2000000,
        'type': 'enemies',
        'min_intelligence': 245,
        'min_level': 73,
        'success_probability_type': 'enemy_prob',
        'slot': 1,
        'tactical_points': 32,
    },
    'flood': {
        'min_damage': 50,
        'max_damage': 70,
        'type': 'enemy',
        'min_intelligence': 100,
        'min_level': 4,
        'success_probability_type': 'enemy_prob',
        'slot': 2,
        'tactical_points': 3,
    },
    'geyser': {
        'min_damage': 90,
        'max_damage': 200,
        'type': 'enemy',
        'min_intelligence': 115,
        'min_level': 10,
        'success_probability_type': 'enemy_prob',
        'slot': 2,
        'tactical_points': 6,
    },
    'hailstorm': {
        'min_damage': 130,
        'max_damage': 250,
        'type': 'enemies',
        'min_intelligence': 130,
        'min_level': 17,
        'success_probability_type': 'enemy_prob',
        'slot': 2,
        'tactical_points': 9,
    },
    'monsoon': {
        'min_damage': 1000,
        'max_damage': 1600,
        'type': 'enemies',
        'min_intelligence': 160,
        'min_level': 22,
        'success_probability_type': 'enemy_prob',
        'slot': 2,
        'tactical_points': 12,
    },
    'tsunami': {
        'min_damage': 1800,
        'max_damage': 3000,
        'type': 'enemies',
        'min_intelligence': 190,
        'min_level': 29,
        'success_probability_type': 'enemy_prob',
        'slot': 2,
        'tactical_points': 15,
    },
    'blizzard': {
        'min_damage': 8000,
        'max_damage': 15000,
        'type': 'enemies',
        'min_intelligence': 225,
        'min_level': 40,
        'success_probability_type': 'enemy_prob',
        'slot': 2,
        'tactical_points': 21,
    },
    'sharknado': {
        'min_damage': 100000,
        'max_damage': 300000,
        'type': 'enemies',
        'min_intelligence': 240,
        'min_level': 59,
        'success_probability_type': 'enemy_prob',
        'slot': 2,
        'tactical_points': 27,
    },
    'hurricane': {
        'min_damage': 1000000,
        'max_damage': 4000000,
        'type': 'enemies',
        'min_intelligence': 255,
        'min_level': 76,
        'success_probability_type': 'enemy_prob',
        'slot': 2,
        'tactical_points': 36,
    },
    'salve': {
        'min_damage': 70,
        'max_damage': 100,
        'type': 'ally',
        'min_intelligence': 100,
        'min_level': 5,
        'success_probability_type': 'one',
        'slot': 3,
        'tactical_points': 3,
    },
    'remedy': {
        'min_damage': 400,
        'max_damage': 700,
        'type': 'ally',
        'min_intelligence': 160,
        'min_level': 15,
        'success_probability_type': 'one',
        'slot': 3,
        'tactical_points': 6,
    },
    'rejuvenate': {
        'min_damage': 900,
        'max_damage': 1500,
        'type': 'allies',
        'min_intelligence': 180,
        'min_level': 18,
        'success_probability_type': 'one',
        'slot': 3,
        'tactical_points': 9,
    },
    'restore': {
        'min_damage': 1000000000,
        'max_damage': 1000000000,
        'type': 'ally',
        'min_intelligence': 220,
        'min_level': 24,
        'success_probability_type': 'one',
        'slot': 3,
        'tactical_points': 12,
    },
    'heal': {
        'min_damage': 4000,
        'max_damage': 6000,
        'type': 'allies',
        'min_intelligence': 230,
        'min_level': 28,
        'success_probability_type': 'one',
        'slot': 3,
        'tactical_points': 4,
    },
    'healmore': {
        'min_damage': 40000,
        'max_damage': 60000,
        'type': 'allies',
        'min_intelligence': 240,
        'min_level': 45,
        'success_probability_type': 'one',
        'slot': 3,
        'tactical_points': 8,
    },
    'arise': {
        'min_damage': 400000,
        'max_damage': 600000,
        'type': 'allies',
        'min_intelligence': 250,
        'min_level': 61,
        'success_probability_type': 'one',
        'slot': 3,
        'tactical_points': 12,
    },
    'revive': {
        'min_damage': 1000000000,
        'max_damage': 1000000000,
        'type': 'allies',
        'min_intelligence': 255,
        'min_level': 78,
        'success_probability_type': 'one',
        'slot': 3,
        'tactical_points': 48,
    },
    'firewall': {
        'type': 'defense',
        'min_intelligence': 100,
        'min_level': 3,
        'success_probability_type': 'one',
        'slot': 4,
        'tactical_points': 4,
        'duration': 'temporary', # can be temporary or permanent. This is for status effects.
    },
    'extinguish': {
        'type': 'defense',
        'min_intelligence': 120,
        'min_level': 11,
        'success_probability_type': 'one',
        'slot': 4,
        'tactical_points': 8,
        'duration': 'temporary',
    },
    'shield': {
        'type': 'defense',
        'min_intelligence': 170,
        'min_level': 19,
        'success_probability_type': 'one',
        'slot': 4,
        'tactical_points': 12,
        'duration': 'temporary',
    },
    'repel': {
        'type': 'defense',
        'min_intelligence': 200,
        'min_level': 25,
        'success_probability_type': 'one',
        'slot': 4,
        'tactical_points': 16,
        'duration': 'temporary',
    },
    'deflect': {
        'type': 'defense',
        'min_intelligence': 240,
        'min_level': 33,
        'success_probability_type': 'one',
        'slot': 4,
        'tactical_points': 20,
        'duration': 'temporary',
    },
    'provoke': {
        'type': 'enemy',
        'min_intelligence': 130,
        'min_level': 6,
        'success_probability_type': 'enemy_prob',
        'slot': 5,
        'tactical_points': 5,
        'duration': 'permanent',
    },
    'disable': {
        'type': 'enemy',
        'min_intelligence': 160,
        'min_level': 12,
        'success_probability_type': 'enemy_prob',
        'slot': 5,
        'tactical_points': 10,
        'duration': 'permanent',
    },
    'dispel': {
        'type': 'single',
        'min_intelligence': 160,
        'min_level': 26,
        'success_probability_type': 'intel_prob',
        'slot': 5,
        'tactical_points': 15,
    },
    'plunder': {
        'type': 'single',
        'min_intelligence': 190,
        'min_level': 31,
        'success_probability_type': 'one',
        'slot': 5,
        'tactical_points': 20,
    },
    'train': {
        'type': 'defense',
        'min_intelligence': 220,
        'min_level': 36,
        'success_probability_type': 'one',
        'slot': 5,
        'tactical_points': 25,
        'duration': 'permanent',
    },
    'surrender': {
        'type': 'single',
        'min_intelligence': 250,
        'min_level': 50,
        'success_probability_type': 'one',
        'slot': 5,
        'tactical_points': 30,
    },
    'ninja': {
        'type': 'ally',
        'min_intelligence': 150,
        'min_level': 7,
        'success_probability_type': 'one',
        'slot': 6,
        'tactical_points': 4,
        'duration': 'permanent',
    },
    'double~tap': {
        'type': 'ally',
        'min_intelligence': 220,
        'min_level': 13,
        'success_probability_type': 'one',
        'slot': 6,
        'tactical_points': 6,
        'duration': 'permanent',
    },
    'confuse': {
        'type': 'enemy',
        'min_intelligence': 150,
        'min_level': 20,
        'success_probability_type': 'enemy_prob',
        'slot': 6,
        'tactical_points': 6,
        'duration': 'permanent',
    },
    'assassin': {
        'type': 'enemy',
        'min_damage': 1000000000,
        'max_damage': 1000000000,
        'min_intelligence': 180,
        'min_level': 32,
        'success_probability_type': 'assassin',
        'slot': 6,
        'tactical_points': 10,
    },
    'hulk~out': {
        'type': 'ally',
        'min_intelligence': 240,
        'min_level': 37,
        'success_probability_type': 'one',
        'slot': 6,
        'tactical_points': 10,
        'duration': 'permanent',
    },
}

MAP_NAMES = [
    'overworld',
    'tunnels_of_the_north',
    'cave_of_gadianton',
    'sierra_pass',
    'cavity_of_a_rock',
    'passage_to_gid',
    'house_of_moroni',
    'melek',
    'melek_empty_house',
    'zarahemla',
]

MAPS_WITH_RANDOM_ENCOUNTERS = [
    'overworld',
    'tunnels_of_the_north',
    'cave_of_gadianton',
    'sierra_pass',
    'cavity_of_a_rock',
    'passage_to_gid',
]

CAVE_MUSIC = {
    'intro': 'data/audio/music/cave_intro.wav',
    'repeat': 'data/audio/music/cave.wav',
}

SHOP_MUSIC = {
    'intro': None,
    'repeat': 'data/audio/music/shop.wav',
}

CITY_MUSIC = {
    'intro': None,
    'repeat': 'data/audio/music/city.wav',
}

MAP_MUSIC = {
    'zarahemla': CITY_MUSIC,
    'melek': {
        'intro': None,
        'repeat': 'data/audio/music/menu.wav',
    },
    'house_of_moroni': SHOP_MUSIC,
    'melek_empty_house': SHOP_MUSIC,
    'overworld': {
        'intro': None,
        'repeat': 'data/audio/music/march.wav',
    },
    'tunnels_of_the_north': CAVE_MUSIC,
    'cave_of_gadianton': CAVE_MUSIC,
    'sierra_pass': CAVE_MUSIC,
    'cavity_of_a_rock': CAVE_MUSIC,
    'passage_to_gid': CAVE_MUSIC,
}

BATTLE_MUSIC = {
    'regular': {
        'intro': 'data/audio/music/regular_battle_intro.wav',
        'repeat': 'data/audio/music/regular_battle_repeat.wav',
    },
    'warlord': {
        'intro': 'data/audio/music/warlord_battle_intro.wav',
        'repeat': 'data/audio/music/warlord_battle_repeat.wav',
    },
    'story': {
        'intro': 'data/audio/music/story_battle_intro.wav',
        'repeat': 'data/audio/music/story_battle_repeat.wav',
    },
    'giddianhi': {
        'intro': 'data/audio/music/giddianhi_intro.wav',
        'repeat': 'data/audio/music/giddianhi_repeat.wav',
    },
    'zemnarihah': {
        'intro': None,
        'repeat': 'data/audio/music/zemnarihah.wav',
    },
}

ITEMS = {
    # weapons
    'dagger': {
        'attack_points': 10,
        'equip_type': 'weapon',
        'cost': 50,
    },
    'flail': {
        'attack_points': 15,
        'equip_type': 'weapon',
        'cost': 100,
    },

    # armor
    'robe': {
        'armor_class': 20,
        'equip_type': 'armor',
        'cost': 100,
    },

    # helmets
    'bandana': {
        'armor_class': 10,
        'equip_type': 'helmet',
        'cost': 50,
    },

    # company items (elixirs, resurrect, etc)
    'elixir~a': {
        'map_usage': 'company', # means you can use the item on a member of the company (aka traveling party)
        'healing_points': 100, # exactly 100 soldiers recover strength
        'cost': 20,
    },
    'elixir~b': {
        'map_usage': 'company',
        'healing_points': 500,
        'cost': 50,
    },
    'elixir~c': {
        'map_usage': 'company',
        'healing_points': 1000,
        'cost': 200,
    },
    'elixir~d': {
        'map_usage': 'company',
        'healing_points': 4500,
        'cost': 500,
    },
    'resurrect': {
        'map_usage': 'company',
        'cost': 100,
    },

    # gullwing (city map usage)
    'gullwing': {
        'map_usage': 'city', # means it brings up a menu of main visited cities to teleport to
        'cost': 200,
    },

    # map items
    'key': {
        'map_usage': 'map', # means it interacts with the cell/tile you're on
    },
}

NAMED_TELEPORTS = {
    'zarahemla': [152,187],
}

MAX_COMPANY_SIZE = 7

# we may or may not reference these
EVENT_NAMES = {
    QUIT: 'QUIT',
    ACTIVEEVENT: 'ACTIVEEVENT',
    KEYDOWN: 'KEYDOWN',
    KEYUP: 'KEYUP',
    MOUSEMOTION: 'MOUSEMOTION',
    MOUSEBUTTONDOWN: 'MOUSEBUTTONDOWN',
    MOUSEBUTTONUP: 'MOUSEBUTTONUP',
    JOYAXISMOTION: 'JOYAXISMOTION',
    JOYBALLMOTION: 'JOYBALLMOTION',
    JOYHATMOTION: 'JOYHATMOTION',
    JOYBUTTONDOWN: 'JOYBUTTONDOWN',
    JOYBUTTONUP: 'JOYBUTTONUP',
    VIDEORESIZE: 'VIDEORESIZE',
    VIDEOEXPOSE: 'VIDEOEXPOSE',
}
