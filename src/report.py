# -*- coding: UTF-8 -*-

import json

import pygame

from constants import BLACK, COPPER, GAME_WIDTH, GAME_HEIGHT
from helpers import get_equip_based_stat_value, get_tactics, load_image, load_stats
from text import MenuGrid, TextBox

STATS = [
    {
        'name': 'strength',
        'abbr': 'STR',
    },
    {
        'name': 'defense',
        'abbr': 'DEF',
    },
    {
        'name': 'intelligence',
        'abbr': 'INT',
    },
    {
        'name': 'agility',
        'abbr': 'AGI',
    },
    {
        'name': 'evasion',
        'abbr': 'EVA',
    },
    {
        'name': 'tactical_points',
        'abbr': 'T.P',
    },
    {
        'name': 'attack_points',
        'abbr': 'A.P',
    },
    {
        'name': 'armor_class',
        'abbr': 'A.C',
    },
]


class Bars(object):
    def __init__(self, number):
        self.num_bars = int(number/255.0*20)
        self.surface = pygame.Surface((80, 8))
        for i in range(self.num_bars):
            pygame.draw.rect(self.surface, COPPER, (i*4, 1, 3, 6))


class Report(object):
    def __init__(self, name=None, level=None, equips=None, stats=None):
        '''
        Either provide (name, level, equips) or provide (stats)
        '''
        self.equips = equips
        self.name = name.lower() if name else None
        self.level = level
        self.surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.surface.fill(BLACK)
        if name == None: # This is an enemy report
            self.stats = stats
            self.name = stats['name']
            self.stats_provided = True
        else:
            self.stats = load_stats(self.name)
            self.stats_provided = False
        self.portrait = load_image('portraits/{}.png'.format(self.name))
        self.blit_stats()

    def blit_stats(self):
        self.surface.blit(self.portrait, (16, 32))
        self.surface.blit(TextBox(self.name.title()).surface, (16, 16))
        for i, stat in enumerate(STATS):
            if stat['name'] in ['attack_points', 'armor_class']:
                if self.stats_provided:
                    stat_value = self.stats[stat['name']]
                else:
                    stat_value = get_equip_based_stat_value(stat['name'], self.equips)
            elif stat['name'] == 'tactical_points':
                if self.stats_provided:
                    stat_value = self.stats[stat['name']]
                else:
                    stat_value = self.get_tactical_points()
            else:
                stat_value = self.stats[stat['name']]
            self.surface.blit(TextBox("{}~{:~>3}".format(stat['abbr'], stat_value)).surface, (96, i*16+32))
            self.surface.blit(Bars(stat_value).surface, (160, i*16+32))
        tactics = self.get_tactics()
        tactics = [tactics[:3], tactics[3:]]
        grid = MenuGrid(tactics, border=True, title='TACTICS')
        self.surface.blit(grid.surface, (48, 160))
        self.surface.blit(TextBox("SOLDIERS").surface, (16, 96))
        soldiers = "{:~>8}".format(self.get_max_soldiers())
        self.surface.blit(TextBox(soldiers).surface, (16, 112))

    def get_max_soldiers(self):
        if 'max_soldiers_by_level' in self.stats:
            return self.stats['max_soldiers_by_level'][self.level-1]
        return self.stats['max_soldiers']

    def get_tactical_points(self):
        if 'tactical_points_by_level' in self.stats:
            return self.stats['tactical_points_by_level'][self.level-1]
        return self.stats['tactical_points']

    def get_tactics(self):
        return get_tactics(self.stats, self.level)
