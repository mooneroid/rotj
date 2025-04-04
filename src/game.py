# -*- coding: UTF-8 -*-

from collections import OrderedDict
import copy
import math
import os
import subprocess
import random
import sys
import time

import pygame
from pygame.locals import *

from battle import Battle
from battle_intro import BattleIntro
from beginning import Beginning
from constants import (
    BATTLE_MUSIC, BLACK, EXP_REQUIRED_BY_LEVEL, GAME_HEIGHT, GAME_WIDTH, HQ, ITEMS, MAP_MUSIC, MAX_COMPANY_SIZE,
    MAX_ITEMS_PER_PERSON, MAX_NUM, SHOP_MUSIC, TACTICS, CAMP_MUSIC, MAP_WIDTH, MAP_HEIGHT, VILLAGE_MUSIC,
    CREDITS_MUSIC, SELLING_DISCOUNT
)
from cutscene import Cutscene
from helpers import (
    can_level_up,
    get_armor_class_by_level,
    get_attack_points_by_level,
    get_intelligence,
    get_max_soldiers,   
    get_max_tactical_points,
    get_tactic_for_level,
    get_tactics,
    load_json_file_if_exists,
    load_stats,
    save_game_state,
    sort_items,
)
from menu_screen import MenuScreen
from narration import Narration
from pause_map import PauseMap
from pause_menu import PauseMenu
from tiled_map import Map
from title_page import TitlePage
from game_credits import Credits

REPEAT_CONDITIONS = [
    'got_javelin',
    'bought_scout',
    'found_title_of_liberty',
    'got_lost_and_found_item',
]


class Game(object):
    def __init__(self, screen, args):
        self.credits = None
        self.start_credits = False
        self.args = args # Parsed args from the command line
        self.devtools = OrderedDict((
            ('No encounters', False), # When on, disables all random encounters
            ('Infinity gauntlet', False), # When on, makes player very powerful/successful and enemies very weak/unsuccessful
            ('Fasting', False), # When on, food is not consumed while traveling
        ))
        self.current_cutscene = None
        self.next_cutscene = None
        self.cloak_steps_remaining = 0
        self.scout_steps_remaining = 0
        self.retreat_counter = 0
        self.battle_intro = None
        self.narration = None
        self.real_screen = screen
        self.virtual_width = GAME_WIDTH
        self.virtual_height = GAME_HEIGHT
        self.virtual_screen = pygame.Surface((self.virtual_width, self.virtual_height)).convert_alpha()
        self.clock = pygame.time.Clock()
        self.fps = 1000
        self.current_map = None
        self.title_page = TitlePage(self.virtual_screen, self)
        self.set_screen_state('title')
        pygame.event.set_blocked(MOUSEMOTION)
        pygame.event.set_blocked(ACTIVEEVENT)
        pygame.event.set_blocked(VIDEORESIZE)
        pygame.event.set_blocked(KEYUP)
        self.menu_screen = MenuScreen(self.virtual_screen, self)
        self.beginning_screen = Beginning(self, self.virtual_screen)
        self.game_state = {} # This will get initialized by menu_screen when a save slot is loaded
        self.fitted_screen = None # gets initialized in resize_window()
        self.window_size = screen.get_size()
        self.resize_window(self.window_size)
        self.change_map_time_elapsed = None
        self.walk_sound = pygame.mixer.Sound(os.path.join('data', 'audio', 'walk.wav'))
        self.encounter_sound = pygame.mixer.Sound(os.path.join('data', 'audio', 'encounter.wav'))
        self.fade_out = False
        self.continue_current_music = False
        self.next_map = None
        self.fade_alpha = None
        self.current_music = None
        self.battle = None
        self.pause_menu = None
        self.pause_map = None
        self._screen_state_after_pause = None
        self.last_overworld_position = [169, 190] # default to melek
        self.unprocessed_beaten_path = [] # This will get initialized by menu_screen when game_state is loaded
        self.play_walk_sound = True
        self.two_yuppies_state = False

        # See the bottom of this class for the defs of all these handlers
        self.condition_side_effects = {
            'talked_with_melek_merchant': self.handle_talked_with_melek_merchant,
            'ammah_and_manti_join': self.handle_ammah_and_manti_join,
            'talked_with_jeneum': self.handle_talked_with_jeneum,
            'talked_with_nehor': self.handle_talked_with_nehor,
            'talked_with_alma_after_nehor': self.handle_talked_with_alma_after_nehor,
            'talked_with_antionum': self.handle_talked_with_antionum,
            'alma_joins': self.handle_alma_joins,
            'ammon_joins': self.handle_ammon_joins,
            'mathoni_kingdom_rejected': self.handle_mathoni_kingdom_rejected,
            'anti_nephi_lehi_joins': self.handle_anti_nephi_lehi_joins,
            'entered_destroyed_ammonihah': self.handle_entered_destroyed_ammonihah,
            'lamoni_joins': self.handle_lamoni_joins,
            'muloki_joins': self.handle_muloki_joins,
            'entered_manti': self.handle_entered_manti,
            'lehi_and_aha_join': self.handle_lehi_and_aha_join,
            'rejected_amalickiah': self.handle_rejected_amalickiah,
            'got_title_of_liberty': self.handle_got_title_of_liberty,
            'found_title_of_liberty': self.handle_found_title_of_liberty,
            'got_javelin': self.handle_got_javelin,
            'bought_scout': self.handle_bought_scout,
            'bought_key': self.handle_bought_key,
            'battle27': self.handle_battle27,
            'battle34_sober': self.handle_battle34_sober,
            'battle34_drunk': self.handle_battle34_drunk,
            'battle34': self.handle_battle34,
            'recruited_prisoners': self.handle_recruited_prisoners,
            'recruited_prisoners_again': self.handle_recruited_prisoners_again,
            'corianton_joins': self.handle_corianton_joins,
            'corianton_runs_away': self.handle_corianton_runs_away,
            'battle37': self.handle_battle37,
            'battle39': self.handle_battle39,
            'helaman_joins': self.handle_helaman_joins,
            'battle44': self.handle_battle44,
            'cumeni_hq': self.handle_cumeni_hq,
            'showed_sign_to_seezoram': self.handle_showed_sign_to_seezoram,
            'talked_with_gadianton_in_bountiful': self.handle_talked_with_gadianton_in_bountiful,
            'talked_with_robbers': self.handle_talked_with_robbers,
            'moronihah_joins': self.handle_moronihah_joins,
            'got_lost_and_found_item': self.handle_got_lost_and_found_item,
            'gave_iron_ore_and_diamond': self.handle_gave_iron_ore_and_diamond,
            'state:two_yuppies': self.handle_two_yuppies,
            'state:one_yuppie': self.handle_one_yuppie,
            'got_explosive': self.handle_got_explosive,
            'pahoran_joins': self.handle_pahoran_joins,
            'battle48': self.handle_battle48,
            'battle49': self.handle_battle49,
            'battle55': self.handle_battle55,
            'got_gold_key': self.handle_got_gold_key,
            'returned_liahona': self.handle_returned_liahona,
            'got_liahona': self.handle_got_liahona,
            'corianton_joins_again': self.handle_corianton_joins_again,
            'corianton_leaves': self.handle_corianton_leaves,
            'nephi_joins': self.handle_nephi_joins,
            'start_battle59': self.handle_start_battle59,
            'start_battle60': self.handle_start_battle60,
            'start_battle61': self.handle_start_battle61,
            'gidgiddoni_joins': self.handle_gidgiddoni_joins,
            'battle71': self.handle_battle71,
            'entered_jerusalem': self.handle_entered_jerusalem,
            'battle79': self.handle_battle79,
            'battle84': self.handle_battle84,
            'lachoneus_joins': self.handle_lachoneus_joins,
            'battle69': self.handle_battle69,
            'battle80': self.handle_battle80,
            'battle90': self.handle_battle90,
            'start_with_shiz': self.handle_start_with_shiz,
            'roll_credits': self.handle_roll_credits,
        }

    def conditions_are_met(self, conditions):
        if conditions is None or len(conditions) == 0:
            return True
        if isinstance(conditions, str):
            conditions = {conditions: True}
        elif type(conditions) in (tuple, list):
            conditions = {condition: True for condition in conditions}
        for condition, expected in conditions.items():
            if expected and not self._condition_is_true(condition):
                return False
            if not expected and self._condition_is_true(condition):
                return False
        return True

    def _condition_is_true(self, condition_str):
        if condition_str.startswith("state:"):
            condition_state_checker_str = condition_str.split(":")[1]
            return getattr(self, condition_state_checker_str)()
        else:
            return condition_str in self.game_state.get('conditions', [])

    def get_dialog_for_condition(self, dialog):
        """
        Returns the first dialog text with a condition matching the game state.
        """
        is_chief_judge = False
        is_judge = False
        if isinstance(dialog, str):
            if dialog == 'judge_dialog':
                is_judge = True
                dialog = load_json_file_if_exists(os.path.join('data', 'maps', 'judge_dialog.json'))
                is_chief_judge = self.current_map.name == 'zarahemla_palace'
            else:
                return dialog
        if isinstance(dialog, (list, tuple)):
            for (i, potential_dialog) in enumerate(dialog):
                if self._condition_is_true(potential_dialog.get('condition', '')):
                    dialog = potential_dialog
                    break
                if i == len(dialog)-1:
                    dialog = potential_dialog

        # Now dialog is a dict with the correct dialog for the game state.
        if is_chief_judge and 'chief_judge' in dialog:
            dialog['text'] = dialog['chief_judge']['text']
            dialog['game_state_action'] = dialog['chief_judge'].get('game_state_action')
            dialog['prompt'] = dialog['chief_judge'].get('prompt')
        if is_judge and not is_chief_judge and not dialog.get('no_epistle'):
            current_chief_judge = dialog.get('current_chief_judge')
            if self.is_in_company(current_chief_judge) or self.is_in_reserve(current_chief_judge):
                prepend = "Yessir, we'll maintain this city for you."
            else:
                prepend = "An epistle arrived from our chief judge. It reads:"
            dialog['text'] = "{} {}".format(prepend, dialog['text'])
        if dialog.get('game_state_action'):
            self.set_game_state_condition(dialog['game_state_action'])
        return dialog

    def set_game_state_condition(self, condition):
        action_dialog = None
        side_effect = self.condition_side_effects.get(condition)
        condition_not_found = condition not in self.game_state['conditions']
        if side_effect and (condition_not_found or condition in REPEAT_CONDITIONS):
            action_dialog = side_effect()
        if not condition.startswith('state:'):
            conditions = list(self.game_state['conditions'])
            if condition_not_found:
                conditions.append(condition)
            self.update_game_state({
                'conditions': conditions,
            })
        the_map = self.current_map or self.next_map
        if the_map:
            the_map.handle_game_state_condition(condition)
        return action_dialog

    def get_music(self, map_name):
        music = MAP_MUSIC.get(map_name, SHOP_MUSIC)
        if type(music) in (list, tuple):
            for item in music:
                if self.conditions_are_met(item.get('conditions')):
                    return item
            return SHOP_MUSIC
        else:
            return music

    def reserve_multiplier(self):
        # Get a bonus to your exp when you have guys in the reserve.
        # Grows quartically based on number of guys in reserve,
        # from 1.0 to around 10.0 if you get all the guys you can.
        # (I think the max you can get isn't much higher than 160.)
        return 1.0 + (len(self.game_state['reserve']) / 92.0) ** 4

    def decrement_food(self):
        if self.devtools['Fasting']:
            return False
        food = copy.deepcopy(self.game_state['food'])
        soldiers = sum(warlord['soldiers'] for warlord in self.game_state['company'])
        reserve_discount = 0.01 * max(len(self.game_state['reserve']), 100)
        eaten = (1.0 - reserve_discount) * soldiers / 5000.0 # 5,000 steps per food unit per soldier, before the reserve_discount
        new_food = max(0, food - eaten)
        self.update_game_state({'food': new_food})
        if new_food == 0:
            self.starve_the_soldiers()
            # indicate that we ran out of food and whether we lost soldiers because of it
            return not all(warlord['soldiers'] <= 1 for warlord in self.game_state['company'])
        else:
            return False # indicate that we didn't run out of food

    def starve_the_soldiers(self):
        company = copy.deepcopy(self.game_state['company'])
        for warlord in company:
            max_soldiers = get_max_soldiers(warlord['name'], self.game_state['level'], is_ally=True)
            if warlord['soldiers'] != 0:
                warlord['soldiers'] = max(1, warlord['soldiers'] - int(round(0.01*max_soldiers)))
        self.update_game_state({'company': company})

    def walk_in_lava(self):
        company = copy.deepcopy(self.game_state['company'])
        for warlord in company:
            max_soldiers = get_max_soldiers(warlord['name'], self.game_state['level'], is_ally=True)
            if warlord['soldiers'] != 0:
                warlord['soldiers'] = max(1, warlord['soldiers'] - int(round(0.03*max_soldiers)))
        self.update_game_state({'company': company})

    def delete_member(self, warlord_index):
        company = copy.deepcopy(self.game_state['company'])
        surplus = copy.deepcopy(self.game_state['surplus'])
        reserve = copy.deepcopy(self.game_state['reserve'])
        for item in company[warlord_index]['items']:
            surplus.insert(0, item['name'])
        surplus = sort_items(surplus)
        warlord = company.pop(warlord_index)
        reserve.insert(0, warlord['name'])
        self.update_game_state({'company': company, 'surplus': surplus, 'reserve': reserve})
        map_to_update = self.current_map or self.next_map
        if map_to_update:
            map_to_update.load_company_sprites(
                map_to_update.hero.position,
                map_to_update.hero.direction,
                'inplace',
            )

    def recruit(self, reserve_index):
        company = copy.deepcopy(self.game_state['company'])
        reserve = copy.deepcopy(self.game_state['reserve'])
        warlord_name = reserve.pop(reserve_index)
        level = self.game_state['level']
        company.append({
            'name': warlord_name,
            'soldiers': get_max_soldiers(warlord_name, level, is_ally=True),
            'tactical_points': get_max_tactical_points(warlord_name, level),
            'items': [],
        })
        self.update_game_state({'company': company, 'reserve': reserve})
        if self.current_map:
            self.current_map.load_company_sprites(
                self.current_map.hero.position,
                self.current_map.hero.direction,
                'inplace',
            )

    def get_reserve_index(self, warlord_name):
        for i, name in enumerate(self.game_state['reserve']):
            if name == warlord_name:
                return i
        return None

    def fire(self, reserve_index):
        reserve = copy.deepcopy(self.game_state['reserve'])
        reserve.pop(reserve_index)
        self.update_game_state({'reserve': reserve})

    def get_surplus_item(self, surplus_index, warlord_index):
        company = copy.deepcopy(self.game_state['company'])
        surplus = copy.deepcopy(self.game_state['surplus'])
        item_name = surplus.pop(surplus_index)
        company[warlord_index]['items'].append({'name': item_name})
        company[warlord_index]['items'] = sort_items(company[warlord_index]['items'])
        self.update_game_state({'company': company, 'surplus': surplus})

    def try_toggle_equip_on_item(self, user, item_index):
        user_name = user.lower()
        company = copy.deepcopy(self.game_state['company'])
        for warlord in company:
            if warlord['name'] == user_name:
                user_dict = warlord
                break
        assert user_dict
        item = user_dict['items'][item_index]
        equip_type = ITEMS[item['name']].get('equip_type')
        if not equip_type:
            return
        equipped_before = item.get('equipped', False)
        item['equipped'] = not equipped_before
        if not equipped_before:
            for index, other_item in enumerate(user_dict['items']):
                if index == item_index:
                    continue
                if ITEMS[other_item['name']].get('equip_type') == equip_type:
                    other_item['equipped'] = False
        self.update_game_state({'company': company})

    def pass_item(self, user, recipient, item_index):
        user_name = user.lower()
        recipient_name = recipient.lower()
        company = copy.deepcopy(self.game_state['company'])
        for warlord in company:
            if warlord['name'] == recipient_name:
                recipient_dict = warlord
            elif warlord['name'] == user_name:
                user_dict = warlord
        assert recipient_dict
        assert user_dict
        item = user_dict['items'].pop(item_index)
        if 'equipped' in item:
            item['equipped'] = False
        recipient_dict['items'].append(item)
        recipient_dict['items'] = sort_items(recipient_dict['items'])
        self.update_game_state({'company': company})        

    def get_items(self, warlord):
        warlord = warlord.lower()
        for info in self.game_state['company']:
            if info['name'] == warlord:
                warlord_info = info
                break
        return list(warlord_info['items'])

    def get_teleport_cities(self):
        return [city['name'].title() for city in self.game_state['cities'] if city.get('teleport')]

    def get_level(self):
        return self.game_state['level']

    def get_leader(self):
        for warlord in self.game_state['company']:
            if warlord['soldiers'] > 0:
                return copy.deepcopy(warlord)

    def get_equips(self, warlord):
        for info in self.game_state['company']:
            if info['name'] == warlord:
                warlord_info = info
                break
        return [item for item in warlord_info['items'] if item.get('equipped')]

    def get_headless(self, warlord):
        for info in self.game_state['company']:
            if info['name'] == warlord:
                warlord_info = info
                break
        return info.get('headless')

    def get_tactician(self):
        for warlord in self.game_state['company']:
            if warlord.get('tactician'):
                return warlord

    def try_set_tactician(self, warlord):
        warlord_name = warlord.lower()
        company = copy.deepcopy(self.game_state['company'])
        for warlord in company:
            if warlord['name'] == warlord_name:
                warlord['tactician'] = True
            else:
                warlord['tactician'] = False
        self.update_game_state({'company': company})
        return True

    def retire_tactician(self, warlord):
        warlord_name = warlord.lower()
        company = copy.deepcopy(self.game_state['company'])
        for warlord in company:
            if warlord['name'] == warlord_name:
                warlord['tactician'] = False
                break
        self.update_game_state({'company': company})

    def get_company_names(self, omit=None, with_empty_item_slots=False, with_items=False):
        return [
            (u'★' if warlord.get('tactician') else '')
            + ('*' if warlord['soldiers'] == 0 else '')
            + warlord['name'].title()
            for warlord in self.game_state['company']
            if warlord['name'] != omit
            and (not with_empty_item_slots or len(warlord['items']) < 8)
            and (not with_items or len(warlord['items']) > 0)
        ]

    def heal(self, warlord, amount):
        warlord_name = warlord.lower()
        company = copy.deepcopy(self.game_state['company'])
        for warlord in company:
            if warlord['name'] == warlord_name:
                max_soldiers = get_max_soldiers(warlord_name, self.game_state['level'], is_ally=True)
                warlord['soldiers'] = min(warlord['soldiers']+amount, max_soldiers)
                break
        self.update_game_state({'company': company})

    def restore_head_of_shiz(self):
        company = copy.deepcopy(self.game_state['company'])
        for warlord in company:
            if warlord['name'] == 'shiz':
                warlord['soldiers'] = 1
                warlord['headless'] = False
                break
        self.update_game_state({'company': company})

    def remove_item(self, warlord, index):
        warlord_name = warlord.lower()
        company = copy.deepcopy(self.game_state['company'])
        for warlord in company:
            if warlord['name'] == warlord_name:
                del warlord['items'][index]
                break
        self.update_game_state({'company': company})

    def update_company_order(self, new_order):
        new_company = []
        for name in new_order:
            for warlord in self.game_state['company']:
                if name == warlord['name']:
                    new_company.append(warlord)
                    break
        self.update_game_state({'company': new_company})

    def start_sleep(self, sleep_music, dialog, heal=False):
        self.set_current_map(
            self.current_map.name, self.current_map.hero.position, self.current_map.hero.direction, followers='under',
            dialog=dialog,
        )
        self.set_screen_state('sleep')
        if heal:
            company = copy.deepcopy(self.game_state['company'])
            for warlord in company:
                if warlord['soldiers'] > 0:
                    warlord['soldiers'] = get_max_soldiers(warlord['name'], self.game_state['level'], is_ally=True)
                    warlord['tactical_points'] = get_max_tactical_points(warlord['name'], self.game_state['level'])
            self.update_game_state({'company': company})
        self.sleep_music = sleep_music

    def save(self):
        save_game_state(self.slot, self.game_state)

    def set_screen_state(self, state):
        '''
        Valid screen states are 'title', 'game', 'menu', 'beginning', 'change_map', 'battle', 'start_battle', 'sleep', 'pause_menu', 'pause_map', 'fade_cutscene', 'cutscene', 'credits'
        '''
        self._screen_state = state
        if state in ['title', 'menu', 'battle', 'pause_menu', 'battle_intro']:
            pygame.key.set_repeat(300, 300)
        else:
            pygame.key.set_repeat(200, 50)

        if state in ['change_map', 'sleep', 'fade_cutscene']:
            self.fade_out = True
            self.fade_alpha = 0
        elif state == 'battle' and not self.continue_current_music:
            battle_music_files = BATTLE_MUSIC[self.battle.battle_type]
            if battle_music_files.get('intro'):
                self.current_music = 'intro'
                music_file = battle_music_files['intro']
            else:
                self.current_music = 'repeat'
                music_file = battle_music_files['repeat']
            pygame.mixer.music.load(music_file)
            if not self.battle or self.battle.battle_name != 'nonbattle':
                pygame.mixer.music.play()
            self.continue_current_music = True
        elif state == 'title':
            self.battle = None
            self.current_map = None
            self.title_page.reset()
            self.menu_screen = MenuScreen(self.virtual_screen, self)
            self.beginning_screen = Beginning(self, self.virtual_screen)
        elif state == 'credits':
            self.current_map = None
            self.credits = Credits(self.virtual_screen, self)
            pygame.mixer.music.load(CREDITS_MUSIC['intro'])
            pygame.mixer.music.play()
            self.current_music = 'intro'

    def open_pause_menu(self):
        self._screen_state_after_pause = self._screen_state
        self.set_screen_state('pause_menu')
        self.pause_menu = PauseMenu(self.virtual_screen, self)
        pygame.mixer.music.set_volume(0.3)

    def close_pause_menu(self):
        if self._screen_state == 'pause_menu':
            self.pause_menu = None
        elif self._screen_state == 'pause_map':
            self.pause_map = None
            self.pause_menu = None
        self.set_screen_state(self._screen_state_after_pause)
        self._screen_state_after_pause = None
        pygame.mixer.music.set_volume(1.0)

    def open_pause_map(self):
        self.set_screen_state('pause_map')
        self.pause_map = PauseMap(self.virtual_screen, self, self.last_overworld_position) # position for now is at melek

    def close_pause_map(self):
        self.pause_map = None
        self.set_screen_state('pause_menu')

    def start_battle(
        self, enemies, battle_type, near_water, intro=None, exit=None, battle_name=None, narration=None,
        continue_music=False, offguard=None, enemy_retreat=False, chapter11_city=None,
        prev_experience=0, prev_money=0, prev_food=0, next_battle=None,
    ):
        self.set_screen_state('battle_intro' if prev_experience else 'start_battle')
        allies = copy.deepcopy([warlord for warlord in self.game_state['company'] if warlord['soldiers'] > 0])
        tactician = self.get_tactician()
        if tactician:
            tactical_points = tactician['tactical_points']
            tactics = get_tactics(load_stats(tactician['name']), self.game_state['level'], pretty=False)
            allies.remove(tactician)
            allies.append(tactician)
        else:
            tactical_points = 0
            tactics = None
        allies = allies[0:5]
        self.battle = Battle(
            self.virtual_screen, self, allies, enemies, battle_type, tactical_points, tactics, near_water, exit=exit,
            battle_name=battle_name, narration=narration, offguard=offguard, enemy_retreat=enemy_retreat, chapter11_city=chapter11_city,
            prev_experience=prev_experience, prev_money=prev_money, prev_food=prev_food, next_battle=next_battle,
        )
        if intro:
            intro_type = 'regular'
            if battle_name == 'battle81':
                if self.conditions_are_met('got_thundered'):
                    intro_type = 'zemnarihah2'
                else:
                    intro_type = 'zemnarihah1'
            self.battle_intro = BattleIntro(self.virtual_screen, self, enemies[0]['name'], intro, intro_type=intro_type)
        if prev_experience: # don't do encounter sound for double battles
            pygame.mixer.music.fadeout(2000)
            self.continue_current_music = False
            time.sleep(.1)
        elif not continue_music:
            pygame.mixer.music.stop()
            self.continue_current_music = False
            self.current_music = None
            time.sleep(.1)
            self.encounter_sound.play()
        else:
            self.continue_current_music = True
            time.sleep(.1)

    def collect_spoils(self, experience, money, food):
        self.update_game_state({
            'money': max(0, min(self.game_state['money'] + money, MAX_NUM)),
            'food': min(self.game_state['food'] + food, MAX_NUM),
            'experience': min(self.game_state['experience'] + experience, EXP_REQUIRED_BY_LEVEL[90]),
        })
        levels_earned = []
        level_to_check = self.game_state['level'] + 1
        level_reached = True
        while level_reached:
            exp_required = EXP_REQUIRED_BY_LEVEL.get(level_to_check)
            if exp_required is not None and self.game_state['experience'] >= exp_required:
                levels_earned.append(level_to_check)
                level_to_check += 1
            else:
                level_reached = False
        if len(levels_earned) > 0:
            self.update_game_state({'level': levels_earned[-1]})
        return levels_earned

    def increment_tactical_points(self):
        company = copy.deepcopy(self.game_state['company'])
        level = self.game_state['level']
        for warlord in company:
            if warlord['tactical_points'] < get_max_tactical_points(warlord['name'], level):
                warlord['tactical_points'] += 1
        self.update_game_state({'company': company})

    def end_battle(
        self, battle_company, tactical_points, battle_name=None, opening_dialog=None, chapter11_city=None, next_battle=None,
        prev_experience=0, prev_money=0, prev_food=0,
    ):
        if not next_battle:
            self.next_map = self.current_map
            self.current_map = None
            self.fade_alpha = 0
            self.continue_current_music = False
            self.set_screen_state('change_map')
        company = []
        for warlord in self.game_state['company']:
            if warlord['name'] in battle_company:
                battle_guy = battle_company[warlord['name']]
                new_warlord = {
                    'name': warlord['name'],
                    'soldiers': battle_guy['soldiers'],
                    'tactical_points': battle_guy['tactical_points'],
                    'items': battle_guy['items'],
                    'tactician': False if battle_guy['soldiers'] == 0 else warlord.get('tactician', False),
                }
                if battle_guy.get('headless'):
                    new_warlord['headless'] = True
            else:
                new_warlord = warlord
            if warlord.get('tactician'):
                new_warlord['tactical_points'] = tactical_points
            company.append(new_warlord)
        self.update_game_state({'company': company})
        followers = 'under' if battle_name == 'battle08' else 'inplace'
        if battle_name == 'battle08':
            direction = 'w'
        elif self.next_map:
            direction = self.next_map.hero.direction
        elif self.current_map:
            direction = self.current_map.hero.direction
        else:
            direction = 's'
        if not next_battle:
            self.next_map.load_company_sprites(self.next_map.hero.position, direction, followers)
        if battle_name:
            self.set_game_state_condition(battle_name)
        if chapter11_city:
            self.set_game_state_condition('battle_at_{}'.format(chapter11_city))
        if battle_name == 'battle08':
            self.next_map.load_ai_sprites()
            # This needs to happen after load_ai_sprites so that Alma appears in the overworld only once.
            self.set_game_state_condition('talked_with_alma_after_battle08')
        if battle_name == 'battle55':
            self.set_screen_state('fade_cutscene')
            self.next_cutscene = Cutscene(self, self.virtual_screen, 0)
        if not next_battle:
            self.next_map.opening_dialog = opening_dialog
        if next_battle:
            self.current_map.start_battle(next_battle, prev_experience=prev_experience, prev_money=prev_money, prev_food=prev_food)

    def update_game_state(self, updates):
        self.game_state.update(updates)

    def add_to_company(self, names):
        company = copy.deepcopy(self.game_state['company'])
        reserve = copy.deepcopy(self.game_state['reserve'])
        level = self.game_state['level']
        if isinstance(names, str):
            names = [names]
        for name in names:
            if len(company) < MAX_COMPANY_SIZE:
                company.append({
                    'name': name,
                    'soldiers': get_max_soldiers(name, level, is_ally=True),
                    'items': [],
                    'tactical_points': get_max_tactical_points(name, level),
                })
            else:
                reserve.insert(0, name)
        self.update_game_state({
            'company': company,
            'reserve': reserve,
        })

    def remove_from_company_and_reserve(self, name):
        if self.is_in_company(name):
            for i, warlord in enumerate(self.game_state['company']):
                if warlord['name'] == name:
                    warlord_index = i
                    break
            self.delete_member(warlord_index)
        if self.is_in_reserve(name):
            for i, warlord in enumerate(self.game_state['reserve']):
                if warlord == name:
                    warlord_index = i
                    break
            self.fire(warlord_index)

    def add_to_inventory(self, item_name, warlord_index=None):
        """
        This is for picking up items when warlord_index is None.
        This is used for buying items when warlord_index is not None, since the warlord who buys it is specified.
        """
        company = copy.deepcopy(self.game_state['company'])
        placed = False
        if warlord_index is not None:
            assert len(company[warlord_index]['items']) < MAX_ITEMS_PER_PERSON
            company[warlord_index]['items'].append({'name': item_name})
            company[warlord_index]['items'] = sort_items(company[warlord_index]['items'])
            placed = True
        else:
            for warlord in company:
                if len(warlord['items']) >= MAX_ITEMS_PER_PERSON or warlord['soldiers'] == 0:
                    continue
                placed = True
                warlord['items'].append({'name': item_name})
                warlord['items'] = sort_items(warlord['items'])
                break
        surplus = list(self.game_state['surplus'])
        if not placed:
            surplus.insert(0, item_name)
            surplus = sort_items(surplus)
        self.update_game_state({'company': company, 'surplus': surplus})

    def sell_item(self, warlord_index, item_index):
        company = copy.deepcopy(self.game_state['company'])
        item_name = company[warlord_index]['items'].pop(item_index)['name']
        value = int(ITEMS[item_name]['cost'] * SELLING_DISCOUNT)
        self.update_game_state({
            'money': min(MAX_NUM, self.game_state['money'] + value),
            'company': company,
        })

    def _find_first_item_in_inventory(self, item_name, equipped=None):
        company = copy.deepcopy(self.game_state['company'])
        for warlord in company:
            for index, item in enumerate(warlord['items']):
                if (
                    item['name'] == item_name
                    and (equipped is None or item.get('equipped', False) == equipped)
                ):
                    return warlord['name'], index
        return None, None

    def is_in_company(self, name):
        for warlord in self.game_state['company']:
            if warlord['name'] == name:
                return True
        return False

    def shiz_is_headless(self):
        for warlord in self.game_state['company']:
            if warlord['name'] == 'shiz':
                return warlord.get('headless', False)
        return False

    def is_in_reserve(self, name):
        return name in self.game_state['reserve']

    def try_set_hq(self):
            city = self.current_map.name.split('_')[0]
            if city not in HQ:
                return "I'm sorry, but this city does not have sufficient space for you to set up a base of operations."
            self.update_game_state({'hq': city})
            if city == 'cumeni' and self.battles34_37_44() and not self.conditions_are_met('cumeni_hq'):
                self.set_game_state_condition('cumeni_hq')
            return None

    def set_current_map(
        self, map_name, position, direction, followers='under', dialog=None, continue_current_music=False, play_walk_sound=True
    ):
        # set game state conditions for entering or exiting certain maps
        if self.current_map:
            if self.current_map.name == 'nephi' and map_name == 'overworld':
                self.set_game_state_condition('exited_nephi')
            elif map_name == 'jershon':
                self.set_game_state_condition('entered_jershon')
            elif map_name == 'destroyed_ammonihah':
                self.set_game_state_condition('entered_destroyed_ammonihah')
            elif map_name == 'manti':
                self.set_game_state_condition('entered_manti')
            elif map_name == 'jerusalem':
                self.set_game_state_condition('entered_jerusalem')

        assert followers in [
            'trail', # position the followers trailing behind the hero
            'under', # position the followers underneath the hero on the same tile
        ]
        self.next_map = Map(
            self.virtual_screen, map_name, self, position, direction=direction, followers=followers,
            opening_dialog=dialog,
        )
        self.continue_current_music = continue_current_music
        self.play_walk_sound = play_walk_sound
        self.fade_alpha = 0
        self.set_screen_state('change_map')
        self.retreat_counter = 0
        if map_name == 'overworld':
            self.mark_beaten_path(position)
            
    def _position_to_string(self, pos):
        pos = [int(x) for x in pos]
        return '{} {}'.format(*pos)

    # This should only be called for marking the latest position the player has walked in the overworld.
    # Loading the game in a palace counts, and menu_screen.py makes sure to call this for the HQ's location
    # on the overworld map when the game starts.
    def mark_beaten_path(self, position):
        self.last_overworld_position = position
        path_entry = self._position_to_string(position)
        if path_entry not in self.game_state['beaten_path']:
            self.game_state['beaten_path'][path_entry] = False
            self.unprocessed_beaten_path.append(path_entry)

    # This can be called by various screens whenever the game is fairly idle, to take advantage of the time
    # to pre-calculate the visible tiles for the pause map. Doing this during idle times minimizes how much
    # time it takes to actually load the map. This is also called repeatedly by the pause map when loading
    # until all beaten_path entries are True, in case they haven't been calculated yet by idle time or
    # previous map loads.
    def process_next_beaten_path_entry(self):
        more_to_process = False
        if len(self.unprocessed_beaten_path) == 0:
            return more_to_process
        entry = self.unprocessed_beaten_path.pop()
        X, Y = [int(i) for i in entry.split()]
        for x in range(X-8, X+9):
            if x <= 0 or x >= MAP_WIDTH:
                continue
            for y in range(Y-7, Y+8):
                if y <= 0 or y >= MAP_HEIGHT:
                    continue
                visible_tile = self._position_to_string((x, y))
                self.game_state['visible_tiles'][visible_tile] = True
        self.game_state['beaten_path'][entry] = True
        more_to_process = len(self.unprocessed_beaten_path) > 0
        return more_to_process

    def resize_window(self, size):
        self.real_screen = pygame.display.set_mode(size)
        (width, height) = size
        width_multiplier = width*1.0 / self.virtual_width
        height_multiplier = height*1.0 / self.virtual_height
        multiplier = min(width_multiplier, height_multiplier)
        fitted_width = int(self.virtual_width*multiplier)
        fitted_height = int(self.virtual_height*multiplier)
        fitted_x_pos = (width - fitted_width) // 2
        fitted_y_pos = (height - fitted_height) // 2
        self.fitted_screen = self.real_screen.subsurface(
            (fitted_x_pos, fitted_y_pos, fitted_width, fitted_height)
        )

    def scale(self):
        self.real_screen.fill(BLACK)
        pygame.transform.scale(self.virtual_screen, self.fitted_screen.get_size(), self.fitted_screen)

    def draw(self):
        if self._screen_state == 'game':
            self.current_map.draw()
        elif self._screen_state == 'title':
            self.title_page.draw()
        elif self._screen_state == 'menu':
            self.menu_screen.draw()
        elif self._screen_state == 'beginning':
            self.beginning_screen.draw()
        elif self._screen_state == 'battle':
            self.battle.draw()
        elif self._screen_state == 'battle_intro' and self.battle_intro:
            self.virtual_screen.fill(BLACK)
            self.battle_intro.draw()
        elif self._screen_state == 'narration' and self.narration:
            if self.current_map.map_menu:
                self.current_map.draw()
            else:
                self.narration.draw()
        elif self._screen_state == 'pause_menu':
            self.pause_menu.draw()
        elif self._screen_state == 'pause_map':
            self.pause_map.draw()
        elif self._screen_state == 'cutscene':
            self.current_cutscene.draw()
        elif self._screen_state == 'credits':
            self.credits.draw()
        self.scale()

    def update(self, dt):
        # handle music
        if self.current_music == 'intro' and not pygame.mixer.music.get_busy():
            if self._screen_state == 'battle' or self._screen_state_after_pause == 'battle':
                repeat_music = BATTLE_MUSIC[self.battle.battle_type]['repeat']
            elif self._screen_state == 'credits':
                repeat_music = CREDITS_MUSIC['repeat']
            elif self.current_map:
                repeat_music = self.get_music(self.current_map.name)['repeat']
            else:
                repeat_music = None
            if repeat_music:
                pygame.mixer.music.load(repeat_music)
                if not self.battle or self.battle.battle_name != 'nonbattle':
                    pygame.mixer.music.play(-1)
                self.current_music = 'repeat'

        if self._screen_state == 'game':
            self.current_map.update(dt)
        elif self._screen_state == 'title':
            self.title_page.update(dt)
        elif self._screen_state == 'menu':
            self.menu_screen.update(dt)
        elif self._screen_state == 'beginning':
            self.beginning_screen.update(dt)
        elif self._screen_state == 'change_map':
            if self.battle and self.battle_intro:
                self.battle_intro = None
            self.update_change_map(dt)
        elif self._screen_state == 'sleep':
            self.update_sleep(dt)
        elif self._screen_state == 'fade_cutscene':
            self.update_fade_cutscene(dt)
        elif self._screen_state == 'start_battle':
            self.update_battle_fade(dt)
        elif self._screen_state == 'battle':
            self.battle.update(dt)
        elif self._screen_state == 'battle_intro':
            if self.battle_intro:
                self.battle_intro.update(dt)
            else:
                self.set_screen_state('battle')
                self.battle_intro = None
        elif self._screen_state == 'narration':
            if self.current_map.map_menu:
                self.current_map.update(dt)
            else:
                self.update_narration(dt)
        elif self._screen_state == 'pause_menu':
            self.pause_menu.update(dt)
        elif self._screen_state == 'pause_map':
            self.pause_map.update(dt)
        elif self._screen_state == 'cutscene':
            self.current_cutscene.update(dt)
        elif self._screen_state == 'credits':
            self.credits.update(dt)

    def update_battle_fade(self, dt):
        if self.change_map_time_elapsed is None:
            self.change_map_time_elapsed = 0
            self.show_map = True
            self.triangle_size = 0
        self.change_map_time_elapsed += dt
        update_interval = .05
        if self.change_map_time_elapsed >= update_interval:
            self.change_map_time_elapsed = 0
            self.show_map = not self.show_map
            self.triangle_size += .2
            if self.show_map and self.current_map:
                self.current_map.draw()
                self.draw_triangle_transition()
            else:
                self.virtual_screen.fill(BLACK)

    def draw_triangle_transition(self):
        """
        Okay, okay, it's not really triangles. It's a reference to the triangle transition of DOAE.
        """
        block_size = 8
        for x in range(0, GAME_WIDTH, block_size):
            for y in range(0, GAME_HEIGHT, block_size):
                pygame.draw.rect(
                    self.virtual_screen,
                    BLACK,
                    (x,y,block_size,block_size),
                    min(int(math.ceil(self.triangle_size)), block_size),
                )
        if self.triangle_size > block_size:
            self.set_screen_state('battle_intro' if self.battle_intro else 'battle')

    def update_narration(self, dt):
        alpha_step = 50 # increments within the range of 0 to 255 for transparency (255 is black)
        # initializing the fade out process
        if self.change_map_time_elapsed is None:
            self.change_map_time_elapsed = 0
            self.fade_out = True
            pygame.mixer.music.stop()
            self.current_music = None
            time.sleep(.3)
        # execute the fade out
        if self.fade_out:
            self.change_map_time_elapsed += dt
            update_interval = .1
            if self.change_map_time_elapsed >= update_interval:
                self.change_map_time_elapsed -= update_interval
                self.fade_alpha = min(255, self.fade_alpha + alpha_step)
                if self.fade_alpha == 255:
                    self.fade_out = False # next we need to render the narration
                    self.current_map = self.next_map
                    self.next_map = None
            fade_box = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
            fade_box.set_alpha(self.fade_alpha)
            fade_box.fill(BLACK)
            self.current_map.draw()
            self.virtual_screen.blit(fade_box, (0,0))
        # when the user presses x after the dialog is done, we set dialog to None as an indicator here whether to
        # keep updating the narration or to start the fade in portion in the else block below
        elif not self.fade_out and self.narration.dialog:
            self.narration.update(dt)
        else: # time to fade back into the map
            if self.fade_alpha == 255:
                self.fade_alpha = 254
            else:
                self.fade_alpha = max(0, self.fade_alpha - alpha_step)
            if self.fade_alpha == 0:
                self.set_screen_state('game')
                music = self.get_music(self.current_map.name)
                if music['intro']:
                    pygame.mixer.music.load(music['intro'])
                    pygame.mixer.music.play()
                    self.current_music = 'intro'
                else:
                    pygame.mixer.music.load(music['repeat'])
                    pygame.mixer.music.play(-1)
                    self.current_music = 'repeat'
                self.change_map_time_elapsed = None
                self.fade_alpha = None
                self.narration = None
            else: # draw fading-in map
                fade_box = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
                fade_box.set_alpha(self.fade_alpha)
                fade_box.fill(BLACK)
                self.current_map.draw()
                self.virtual_screen.blit(fade_box, (0,0))

    def update_sleep(self, dt):
        if self.change_map_time_elapsed is None:
            self.change_map_time_elapsed = 0
            self.fade_out = True
            pygame.mixer.music.stop()
            self.current_music = None
            time.sleep(.3)
        self.change_map_time_elapsed += dt
        update_interval = .1
        alpha_step = 50 # increments within the range of 0 to 255 for transparency (255 is black)
        if self.change_map_time_elapsed >= update_interval:
            self.change_map_time_elapsed -= update_interval
            if self.fade_out:
                self.fade_alpha = min(255, self.fade_alpha + alpha_step)
                if self.fade_alpha == 255:
                    self.fade_out = False # next we need to fade in
                    if self.sleep_music:
                        pygame.mixer.music.load(self.sleep_music)
                        pygame.mixer.music.play()
                    self.current_map = self.next_map
                    self.next_map = None
            elif not pygame.mixer.music.get_busy():
                if self.fade_alpha == 255:
                    self.fade_alpha = 254
                else:
                    self.fade_alpha = max(0, self.fade_alpha - alpha_step)
                if self.fade_alpha == 0:
                    self.set_screen_state('game')
                    music = self.get_music(self.current_map.name)
                    if music['intro']:
                        pygame.mixer.music.load(music['intro'])
                        pygame.mixer.music.play()
                        self.current_music = 'intro'
                    else:
                        pygame.mixer.music.load(music['repeat'])
                        pygame.mixer.music.play(-1)
                        self.current_music = 'repeat'
                    self.change_map_time_elapsed = None
                    self.fade_alpha = None
                    return
        fade_box = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        fade_box.set_alpha(self.fade_alpha)
        fade_box.fill(BLACK)
        self.current_map.draw()
        self.virtual_screen.blit(fade_box, (0,0))

    def update_change_map(self, dt):
        if self.change_map_time_elapsed is None:
            self.change_map_time_elapsed = 0
            self.fade_out = True
            if not self.continue_current_music:
                pygame.mixer.music.stop()
                self.current_music = None
                time.sleep(.1)
                if self.play_walk_sound:
                    self.walk_sound.play()
        self.change_map_time_elapsed += dt
        update_interval = .1
        alpha_step = 50 # increments within the range of 0 to 255 for transparency (255 is black)
        if self.change_map_time_elapsed >= update_interval:
            self.change_map_time_elapsed -= update_interval
            if self.fade_out:
                self.fade_alpha = min(255, self.fade_alpha + alpha_step)
                if self.fade_alpha == 255:
                    self.fade_out = False # next we need to fade in
            else:
                if self.fade_alpha == 255:
                    self.fade_alpha = 254
                    self.current_map = self.next_map
                    self.next_map = None
                    self.battle_intro = None
                else:
                    self.fade_alpha = max(0, self.fade_alpha - alpha_step)
                if self.fade_alpha == 0:
                    self.set_screen_state('game')
                    if not self.continue_current_music:
                        music = self.get_music(self.current_map.name)
                        if music['intro']:
                            pygame.mixer.music.load(music['intro'])
                            pygame.mixer.music.play()
                            self.current_music = 'intro'
                        else:
                            pygame.mixer.music.load(music['repeat'])
                            pygame.mixer.music.play(-1)
                            self.current_music = 'repeat'
                    self.change_map_time_elapsed = None
                    self.fade_alpha = None
                    return
        fade_box = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        fade_box.set_alpha(self.fade_alpha)
        fade_box.fill(BLACK)
        if self.battle_intro:
            self.battle_intro.draw()
        elif self.current_map:
            self.current_map.draw()
        elif self.battle:
            self.battle.draw()
        self.virtual_screen.blit(fade_box, (0,0))

    def update_fade_cutscene(self, dt):
        if self.change_map_time_elapsed is None:
            self.change_map_time_elapsed = 0
            self.fade_out = True
            if not self.continue_current_music:
                self.continue_current_music = True
        self.change_map_time_elapsed += dt
        update_interval = .1
        alpha_step = 50 # increments within the range of 0 to 255 for transparency (255 is black)
        if self.change_map_time_elapsed >= update_interval:
            self.change_map_time_elapsed -= update_interval
            if self.fade_out:
                self.fade_alpha = min(255, self.fade_alpha + alpha_step)
                if self.fade_alpha == 255:
                    self.fade_out = False # next we need to fade in
                    if self.next_cutscene:
                        self.current_cutscene = self.next_cutscene
                        if self.current_cutscene.scene == 2:
                            self.next_cutscene = None
                            self.current_map = self.next_map
                            self.next_map = None
                        else:
                            self.next_cutscene = Cutscene(self, self.virtual_screen, self.current_cutscene.scene + 1)
                    else:
                        self.current_cutscene = None
            else:
                if self.fade_alpha == 255:
                    self.fade_alpha = 254
                else:
                    self.fade_alpha = max(0, self.fade_alpha - alpha_step)
                if self.fade_alpha == 0:
                    if self.current_cutscene:
                        self.set_screen_state('cutscene')
                        if self.current_cutscene.scene == 0:
                            pygame.mixer.music.load(CAMP_MUSIC['repeat'])
                            pygame.mixer.music.play(-1)
                            self.current_music = 'repeat'
                    else:
                        self.set_screen_state('game')
                        music = self.get_music(self.current_map.name)
                        if music['intro']:
                            pygame.mixer.music.load(music['intro'])
                            pygame.mixer.music.play()
                            self.current_music = 'intro'
                        else:
                            pygame.mixer.music.load(music['repeat'])
                            pygame.mixer.music.play(-1)
                            self.current_music = 'repeat'
                    self.change_map_time_elapsed = None
                    self.fade_alpha = None
                    return
        fade_box = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        fade_box.set_alpha(self.fade_alpha)
        fade_box.fill(BLACK)
        if self.current_map:
            self.current_map.draw()
        if self.current_cutscene:
            self.current_cutscene.draw()
        self.virtual_screen.blit(fade_box, (0,0))

    def try_retreat(self, agility_score, is_warlord_battle, is_story_battle):
        if self.scout_steps_remaining and not is_story_battle:
            return True
        prev_retreat_multiplier = 0.8
        multiplier = 1.0
        if self.retreat_counter > 0:
            multiplier *= prev_retreat_multiplier
        if self.retreat_counter > 1:
            multiplier *= prev_retreat_multiplier
        if self.retreat_counter > 2:
            multiplier *= prev_retreat_multiplier
        if is_warlord_battle:
            multiplier *= 0.9 # Changed from 0.8 to 0.9 cuz warlords often have more agility anyway - DCR 2019-07-29
        elif is_story_battle:
            multiplier *= 0.2
        success = random.random() < max(0.15, agility_score*multiplier)
        if success:
            self.retreat_counter += 1
        return success

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
                pygame.quit()
                return
            if event.type == KEYDOWN:
                pressed = pygame.key.get_pressed()
                if self.start_credits:
                    if (
                        (pressed[K_x] or pressed[K_z])
                        and self.current_map
                        and self.current_map.map_menu
                        and self.current_map.map_menu.prompt
                        and not self.current_map.map_menu.prompt.has_more_stuff_to_show()
                    ):
                        self.set_screen_state('credits')
                if self._screen_state == "game":
                    self.current_map.handle_input(pressed)
                elif self._screen_state == 'title':
                    self.title_page.handle_input(pressed)
                elif self._screen_state == 'menu':
                    self.menu_screen.handle_input(pressed)
                elif self._screen_state == 'beginning':
                    self.beginning_screen.handle_input(pressed)
                elif self._screen_state == 'battle':
                    self.battle.handle_input(pressed)
                elif self._screen_state == 'battle_intro' and self.battle_intro:
                    self.battle_intro.handle_input(pressed)
                    if pressed[K_x] and self.battle_intro.is_finished():
                        if self.battle_intro.got_thundered():
                            self.set_game_state_condition('got_thundered')
                            dialog = "Where are we? Zemnarihah attacked us with thunder. But I don't remember anything after that." 
                            self.set_current_map('zarahemla_inn', (12, 15), 's', dialog=dialog, play_walk_sound=False)
                        else:
                            self.set_screen_state('battle')
                            self.battle_intro.dialog.shutdown()
                elif self._screen_state == 'narration' and self.narration:
                    if self.current_map.map_menu:
                        self.current_map.handle_input(pressed)
                    else:
                        self.narration.handle_input(pressed)
                        if (
                            pressed[K_x]
                            and self.narration.dialog
                            and not self.narration.dialog.has_more_stuff_to_show()
                        ):
                            self.narration.dialog.shutdown()
                            self.narration.dialog = None
                elif self._screen_state == 'sleep':
                    if (pressed[K_x] or pressed[K_z]) and not self.fade_out:
                        pygame.mixer.music.stop()
                elif self._screen_state == 'pause_menu':
                    self.pause_menu.handle_input(pressed)
                elif self._screen_state == 'pause_map':
                    self.pause_map.handle_input(pressed)
                elif self._screen_state == 'cutscene':
                    self.current_cutscene.handle_input(pressed)
                elif self._screen_state == 'credits':
                    self.credits.handle_input(pressed)

    def run(self):
        self.running = True
        dt = 0.0
        try:
            while self.running:
                dt += self.clock.tick(self.fps)/1000.0
                if dt >= 0.01:
                    self.handle_input()
                    self.update(dt)
                    self.draw()
                    pygame.display.flip()
                    dt = 0.0
        except KeyboardInterrupt:
            self.running = False
            pygame.quit()

    ###########################################################
    # Condition state checkers get defined here               #
    ###########################################################

    # A condition state checker is a function that checks the game state in a way
    # other than the "conditions" set. If a condition gets checked by conditions_are_met()
    # that starts with "state:", then it looks for a function by the name that comes
    # after the colon. For example, "state:lamoni_leader" will call lamoni_leader().
    # If it's true, that "state" condition passes.

    def not_enough_money_for_scout(self):
        return self.game_state['money'] < ITEMS['scout']['cost']

    def not_enough_room_for_scout(self):
        for warlord in self.game_state['company']:
            if len(warlord['items']) < 8:
                return False
        return True

    def got_cloak(self):
        return self.conditions_are_met('onidah_treasure2') or self.conditions_are_met('tunnels_of_the_north_treasure1')

    def game_complete(self, current_condition=None):
        li = [
            'battle69',
            'battle80',
            'battle90',
        ]
        if current_condition:
            li.remove(current_condition)
        return self.conditions_are_met(li)

    def lamoni_leader(self):
        for warlord in self.game_state['company']:
            if warlord['soldiers'] > 0:
                return warlord['name'] == 'lamoni'
        return False

    def corianton_leader(self):
        for warlord in self.game_state['company']:
            if warlord['soldiers'] > 0:
                return warlord['name'] == 'corianton'
        return False

    def robe_and_spear(self):
        warlord, _index = self._find_first_item_in_inventory('robe', equipped=False)
        got_robe = warlord is not None
        warlord, _index = self._find_first_item_in_inventory('spear', equipped=False)
        got_spear = warlord is not None
        return got_robe and got_spear and self.conditions_are_met('battle20')

    def liahona(self):
        warlord, _index = self._find_first_item_in_inventory('liahona')
        got_liahona = warlord is not None
        return got_liahona

    def lost_title_of_liberty(self):
        return 't~of~liberty' in self.game_state.get('lost_and_found', [])

    def battle25_and_battle26(self):
        return self.conditions_are_met(['battle25', 'battle26'])

    def not_enough_money_for_first_javelin(self):
        return self.battle25_and_battle26() and self.game_state['money'] < ITEMS['javelin']['cost']

    def not_enough_money_for_javelin(self):
        return self.conditions_are_met('got_javelin') and self.game_state['money'] < ITEMS['javelin']['cost']

    def teancum_not_ready_for_javelin(self):
        teancum = next((w for w in self.game_state['company'] if w['name'] == 'teancum'), None)
        inventory_full = teancum and len(teancum['items']) >= MAX_ITEMS_PER_PERSON
        return not teancum or inventory_full

    def got_javelin_but_teancum_not_present_or_missing_item_slot(self):
        return (
            self.conditions_are_met('got_javelin')
            and self.battle25_and_battle26()
            and self.teancum_not_ready_for_javelin()
        )

    def first_javelin_but_teancum_not_present_or_missing_item_slot(self):
        return (
            not self.conditions_are_met('got_javelin')
            and self.battle25_and_battle26()
            and self.teancum_not_ready_for_javelin()
        )

    def have_javelin(self):
        in_surplus = 'javelin' in self.game_state['surplus']
        _, index = self._find_first_item_in_inventory('javelin')
        return in_surplus or index is not None

    def not_enough_for_key(self):
        return not self.conditions_are_met('bought_key') and self.game_state['money'] < ITEMS['silver~key']['cost']

    def laman_in_party(self):
        for warlord in self.game_state['company']:
            if warlord['name'] == 'laman':
                return True
        return False

    def battles34_37_44(self):
        return self.conditions_are_met(['battle34', 'battle37', 'battle44'])

    def lost_and_found_has_stuff(self):
        return len(self.game_state.get('lost_and_found', [])) > 0

    def iron_ore_and_diamond(self):
        iron_ore_carrier, _ = self._find_first_item_in_inventory('iron~ore')
        diamond_carrier, _ = self._find_first_item_in_inventory('diamond')
        return iron_ore_carrier and diamond_carrier

    def two_yuppies(self):
        return self.two_yuppies_state

    def corianton_in_company(self):
        for warlord in self.game_state['company']:
            if warlord['name'] == 'corianton':
                return True
        return False

    ###########################################################
    # Condition side effect handlers get defined here         #
    ###########################################################

    # Handlers should be added to self.condition_side_effects in __init__().
    # The handler cannot take any args (other than self).
    # The handler does not add the condition to self.game_state['conditions'].
    # That is the job of set_game_state_condition().

    def handle_talked_with_melek_merchant(self):
        self.update_game_state({
            'money': self.game_state['money'] + 200,
            'food': self.game_state['food'] + 20,
        })

    def handle_ammah_and_manti_join(self):
        self.add_to_company(['ammah', 'manti'])

    def handle_ammon_joins(self):
        self.add_to_company('ammon')

    def handle_talked_with_jeneum(self):
        battle_data = {
            'enemies': [
                {'name': 'jeneum', 'level': 9},
                {'name': 'limhah', 'level': 7},
                {'name': 'zenos', 'level': 7},
            ],
            'battle_type': 'story',
            'exit': (
                "Look, I'll tell you whatever you want to know! You're looking for Nehor? He's hiding out somewhere in "
                "Gideon to the north."
            ),
        }
        enemies = []
        for enemy in battle_data['enemies']:
            stats = load_stats(enemy['name'])
            stats['soldiers'] = get_max_soldiers(enemy['name'], enemy['level'], is_ally=False)
            stats['tactical_points'] = get_max_tactical_points(enemy['name'], enemy['level'])
            stats['attack_points'] = get_attack_points_by_level(enemy['level'])
            stats['armor_class'] = get_armor_class_by_level(enemy['level'])
            stats['tactics'] = get_tactics(enemy['name'], enemy['level'], pretty=False)
            enemies.append({
                'name': enemy['name'],
                'stats': stats,
            })
        self.current_map.start_battle_after_dialog(
            enemies, battle_data['battle_type'], exit=battle_data['exit'], battle_name="battle04",
        )

    def handle_talked_with_nehor(self):
        battle_data = {
            'enemies': [
                {'name': 'nehor', 'level': 8},
                {'name': 'gad', 'level': 11},
                {'name': 'emer', 'level': 8},
                {'name': 'jeneum', 'level': 9},
            ],
            'battle_type': 'story',
            'intro': (
                "You don't have to do this, Moroni. Join my religion and I will make you rich beyond your wildest "
                "dreams. ~~~~~~~~ ~~~~~~~~ ~~~~~~~~ ~~~~~~~~ ~~~~~~~~ ~~~~~~~~ ~~~~~~~~ No? Then we fight!"
            ),
            'exit': "Noooo!",
            'narration': (
                "You have succeeded in capturing Nehor! Take him back to Alma in Zarahemla so that he can be judged for "
                "his crimes."
            ),
        }
        enemies = []
        for enemy in battle_data['enemies']:
            stats = load_stats(enemy['name'])
            stats['soldiers'] = get_max_soldiers(enemy['name'], enemy['level'], is_ally=False)
            stats['tactical_points'] = get_max_tactical_points(enemy['name'], enemy['level'])
            stats['attack_points'] = get_attack_points_by_level(enemy['level'])
            stats['armor_class'] = get_armor_class_by_level(enemy['level'])
            stats['tactics'] = get_tactics(enemy['name'], enemy['level'], pretty=False)
            enemies.append({
                'name': enemy['name'],
                'stats': stats,
            })
        self.current_map.start_battle_after_dialog(
            enemies, battle_data['battle_type'], intro=battle_data['intro'], exit=battle_data['exit'],
            battle_name="battle05", narration=battle_data['narration'],
        )

    def handle_talked_with_alma_after_nehor(self):
        text = (
            "Nehor was delivered to Alma the chief judge and found guilty of shedding innocent blood. As punishment, "
            "he was taken promptly to Hill Manti, where he suffered an ignominious death."
        )
        self.narration = Narration(self.virtual_screen, text)
        self.set_screen_state('narration')
        self.next_map = self.current_map
        self.fade_alpha = 0

    def handle_talked_with_antionum(self):
        amlicites = {
            'name': 'amlicites',
            'stats': {
                "soldiers": 180,
                "strength": 48,
                "defense": 29,
                "intelligence": 30,
                "agility": 44,
                "evasion": 0,
                "tactical_points": 0,
                "attack_points": 25,
                "armor_class": 20,
            },
        }
        battle_data = {
            'enemies': [
                {'name': 'antionum', 'level': 10},
                amlicites,
                amlicites,
            ],
            'battle_type': 'story',
            'exit': "Retreat!",
        }
        enemies = []
        for enemy in battle_data['enemies']:
            if 'stats' in enemy:
                stats = enemy['stats']
            else:
                stats = load_stats(enemy['name'])
                stats['soldiers'] = get_max_soldiers(enemy['name'], enemy['level'], is_ally=False)
                stats['tactical_points'] = get_max_tactical_points(enemy['name'], enemy['level'])
                stats['attack_points'] = get_attack_points_by_level(enemy['level'])
                stats['armor_class'] = get_armor_class_by_level(enemy['level'])
                stats['tactics'] = get_tactics(enemy['name'], enemy['level'], pretty=False)
            enemies.append({
                'name': enemy['name'],
                'stats': stats,
            })
        self.current_map.start_battle_after_dialog(
            enemies, battle_data['battle_type'], exit=battle_data['exit'], battle_name="battle06",
        )

    def handle_alma_joins(self):
        self.add_to_company(['alma'])

    def handle_mathoni_kingdom_rejected(self):
        self.add_to_company(['mathoni'])

    def handle_anti_nephi_lehi_joins(self):
        self.add_to_company(['anti-nephi-lehi'])

    def handle_entered_destroyed_ammonihah(self):
        # if there is nobody alive left in the company, resurrect moroni or recruit him
        need_moroni = True
        for warlord in self.game_state['company']:
            if warlord['soldiers'] > 0 and warlord['name'] != 'amalickiah':
                need_moroni = False
                break
        if need_moroni:
            if 'moroni' in [warlord['name'] for warlord in self.game_state['company']]:
                self.heal('moroni', 100)
            else:
                reserve_index = self.get_reserve_index('moroni')
                self.recruit(reserve_index)

        # get rid of amalickiah
        self.remove_from_company_and_reserve('amalickiah')

    def handle_lamoni_joins(self):
        self.add_to_company(['lamoni'])

    def handle_muloki_joins(self):
        self.add_to_company(['muloki'])

    def handle_entered_manti(self):
        self.update_game_state({
            'cities': [
                {
                    'name': 'zarahemla',
                    'teleport': True,
                },
                {
                    'name': 'manti',
                    'teleport': True,
                },
            ]
        })

    def handle_lehi_and_aha_join(self):
        self.add_to_company(['lehi', 'aha'])

    def handle_rejected_amalickiah(self):
        kingmen = {
            'name': 'kingmen',
            'stats': {
                "soldiers": 1000,
                "strength": 75,
                "defense": 40,
                "intelligence": 60,
                "agility": 25,
                "evasion": 0,
                "tactical_points": 0,
                "attack_points": 45,
                "armor_class": 40,
            },
        }
        battle_data = {
            'enemies': [
                {'name': 'amalickiah', 'level': 24},
                kingmen,
            ],
            'battle_type': 'story',
            'exit': "So quick you are to throw our friendship away! We could have saved these people together. Nevertheless, I will obtain the kingdom. Don't try and stop me.",
        }
        enemies = []
        for enemy in battle_data['enemies']:
            if 'stats' in enemy:
                stats = enemy['stats']
            else:
                stats = load_stats(enemy['name'])
                stats['soldiers'] = get_max_soldiers(enemy['name'], enemy['level'], is_ally=False)
                stats['tactical_points'] = get_max_tactical_points(enemy['name'], enemy['level'])
                stats['attack_points'] = get_attack_points_by_level(enemy['level'])
                stats['armor_class'] = get_armor_class_by_level(enemy['level'])
                stats['tactics'] = get_tactics(enemy['name'], enemy['level'], pretty=False)
            enemies.append({
                'name': enemy['name'],
                'stats': stats,
            })
        self.current_map.start_battle_after_dialog(
            enemies, battle_data['battle_type'], exit=battle_data['exit'], battle_name="battle20", continue_music=True,
        )

    def handle_got_title_of_liberty(self):
        warlord, item_index = self._find_first_item_in_inventory('robe')
        self.remove_item(warlord, item_index)
        warlord, item_index = self._find_first_item_in_inventory('spear')
        self.remove_item(warlord, item_index)
        self.add_to_inventory('t~of~liberty')

    def handle_returned_liahona(self):
        warlord, item_index = self._find_first_item_in_inventory('liahona')
        self.remove_item(warlord, item_index)

    def handle_got_javelin(self):
        company = self.game_state['company']
        teancum_index = next((i for i in range(len(company)) if company[i]['name'] == 'teancum'), None)
        self.add_to_inventory('javelin', warlord_index=teancum_index)
        self.update_game_state({'money': self.game_state['money'] - ITEMS['javelin']['cost']})

    def handle_bought_scout(self):
        self.add_to_inventory('scout')
        self.update_game_state({'money': self.game_state['money'] - ITEMS['scout']['cost']})

    def handle_got_liahona(self):
        self.add_to_inventory('liahona')

    def handle_battle27(self):
        self.update_game_state({
            'cities': [
                {
                    'name': 'zarahemla',
                    'teleport': True,
                },
                {
                    'name': 'manti',
                    'teleport': True,
                },
                {
                    'name': 'bountiful',
                    'teleport': True,
                },
            ]
        })

    def handle_battle71(self):
        self.update_game_state({
            'cities': [
                {
                    'name': 'zarahemla',
                    'teleport': True,
                },
                {
                    'name': 'manti',
                    'teleport': True,
                },
                {
                    'name': 'bountiful',
                    'teleport': True,
                },
                {
                    'name': 'gid',
                    'teleport': True,
                },
                {
                    'name': 'nephihah',
                    'teleport': True,
                },
                {
                    'name': 'judea',
                    'teleport': True,
                },
                {
                    'name': 'cumeni',
                    'teleport': True,
                },
                {
                    'name': 'moroni',
                    'teleport': True,
                },
                {
                    'name': 'jerusalem',
                    'teleport': self.conditions_are_met('entered_jerusalem'),
                },
                {
                    'name': 'kishkumen',
                    'teleport': True,
                },
                {
                    'name': 'jashon',
                    'teleport': self.conditions_are_met('battle79'),
                },
                {
                    'name': 'teancum',
                    'teleport': self.conditions_are_met('battle84'),
                },
            ],
        })

    def handle_battle79(self):
        self.update_game_state({
            'cities': [
                {
                    'name': 'zarahemla',
                    'teleport': True,
                },
                {
                    'name': 'manti',
                    'teleport': True,
                },
                {
                    'name': 'bountiful',
                    'teleport': True,
                },
                {
                    'name': 'gid',
                    'teleport': True,
                },
                {
                    'name': 'nephihah',
                    'teleport': True,
                },
                {
                    'name': 'judea',
                    'teleport': True,
                },
                {
                    'name': 'cumeni',
                    'teleport': True,
                },
                {
                    'name': 'moroni',
                    'teleport': True,
                },
                {
                    'name': 'jerusalem',
                    'teleport': self.conditions_are_met('entered_jerusalem'),
                },
                {
                    'name': 'kishkumen',
                    'teleport': True,
                },
                {
                    'name': 'jashon',
                    'teleport': True,
                },
                {
                    'name': 'teancum',
                    'teleport': self.conditions_are_met('battle84'),
                },
            ],
        })

    def handle_battle84(self):
        self.update_game_state({
            'cities': [
                {
                    'name': 'zarahemla',
                    'teleport': True,
                },
                {
                    'name': 'manti',
                    'teleport': True,
                },
                {
                    'name': 'bountiful',
                    'teleport': True,
                },
                {
                    'name': 'gid',
                    'teleport': True,
                },
                {
                    'name': 'nephihah',
                    'teleport': True,
                },
                {
                    'name': 'judea',
                    'teleport': True,
                },
                {
                    'name': 'cumeni',
                    'teleport': True,
                },
                {
                    'name': 'moroni',
                    'teleport': True,
                },
                {
                    'name': 'jerusalem',
                    'teleport': self.conditions_are_met('entered_jerusalem'),
                },
                {
                    'name': 'kishkumen',
                    'teleport': True,
                },
                {
                    'name': 'jashon',
                    'teleport': self.conditions_are_met('battle79'),
                },
                {
                    'name': 'teancum',
                    'teleport': True,
                },
            ],
        })

    def handle_entered_jerusalem(self):
        self.update_game_state({
            'cities': [
                {
                    'name': 'zarahemla',
                    'teleport': True,
                },
                {
                    'name': 'manti',
                    'teleport': True,
                },
                {
                    'name': 'bountiful',
                    'teleport': True,
                },
                {
                    'name': 'gid',
                    'teleport': True,
                },
                {
                    'name': 'nephihah',
                    'teleport': True,
                },
                {
                    'name': 'judea',
                    'teleport': True,
                },
                {
                    'name': 'cumeni',
                    'teleport': True,
                },
                {
                    'name': 'moroni',
                    'teleport': True,
                },
                {
                    'name': 'jerusalem',
                    'teleport': True,
                },
                {
                    'name': 'kishkumen',
                    'teleport': self.conditions_are_met('battle71'),
                },
                {
                    'name': 'jashon',
                    'teleport': self.conditions_are_met('battle79'),
                },
                {
                    'name': 'teancum',
                    'teleport': self.conditions_are_met('battle84'),
                },
            ],
        })

    def handle_bought_key(self):
        self.add_to_inventory('silver~key')
        self.update_game_state({'money': self.game_state['money'] - ITEMS['silver~key']['cost']})

    def handle_battle34_sober(self):
        lamanites = {
            'name': 'lamanites',
            'stats': {
                "soldiers": 2100,
                "strength": 96,
                "defense": 30,
                "intelligence": 33,
                "agility": 84,
                "evasion": 19,
                "tactical_points": 0,
                "attack_points": 55,
                "armor_class": 50,
            },
        }
        battle_data = {
            'enemies': [
                {'name': 'leantum', 'level': 32},
                {'name': 'enoch', 'level': 30},
                {'name': 'jared', 'level': 30},
                {'name': 'antioni', 'level': 30},
                lamanites,
            ],
            'battle_type': 'story',
            'exit': "Please spare us! We surrender!",
        }
        enemies = []
        for enemy in battle_data['enemies']:
            if 'stats' in enemy:
                stats = enemy['stats']
            else:
                stats = load_stats(enemy['name'])
                stats['soldiers'] = get_max_soldiers(enemy['name'], enemy['level'], is_ally=False)
                stats['tactical_points'] = get_max_tactical_points(enemy['name'], enemy['level'])
                stats['attack_points'] = get_attack_points_by_level(enemy['level'])
                stats['armor_class'] = get_armor_class_by_level(enemy['level'])
                stats['tactics'] = get_tactics(enemy['name'], enemy['level'], pretty=False)
            enemies.append({
                'name': enemy['name'],
                'stats': stats,
            })
        self.current_map.start_battle_after_dialog(
            enemies, battle_data['battle_type'], exit=battle_data['exit'], battle_name="battle34",
            offguard=-1,
        )

    def handle_battle34_drunk(self):
        lamanites = {
            'name': 'lamanites',
            'stats': {
                "soldiers": 210,
                "strength": 96,
                "defense": 30,
                "intelligence": 33,
                "agility": 84,
                "evasion": 19,
                "tactical_points": 0,
                "attack_points": 55,
                "armor_class": 50,
            },
        }
        battle_data = {
            'enemies': [
                {'name': 'leantum', 'level': 32},
                {'name': 'enoch', 'level': 30},
                {'name': 'jared', 'level': 30},
                {'name': 'antioni', 'level': 30},
                lamanites,
            ],
            'battle_type': 'story',
            'exit': "Please spare us! We surrender!",
        }
        enemies = []
        for enemy in battle_data['enemies']:
            if 'stats' in enemy:
                stats = enemy['stats']
            else:
                stats = load_stats(enemy['name'])
                stats['soldiers'] = int(get_max_soldiers(enemy['name'], enemy['level'], is_ally=False) // 10)
                stats['tactical_points'] = get_max_tactical_points(enemy['name'], enemy['level'])
                stats['attack_points'] = get_attack_points_by_level(enemy['level'])
                stats['armor_class'] = get_armor_class_by_level(enemy['level'])
                stats['tactics'] = get_tactics(enemy['name'], enemy['level'], pretty=False)
            enemies.append({
                'name': enemy['name'],
                'stats': stats,
            })
        self.current_map.start_battle_after_dialog(
            enemies, battle_data['battle_type'], exit=battle_data['exit'], battle_name="battle34",
            offguard=1,
        )

    def handle_battle34(self):
        cities = copy.deepcopy(self.game_state['cities'])
        cities.append({
            'name': 'gid',
            'teleport': True,
        })
        self.update_game_state({
            'cities': cities,
        })

    def handle_corianton_joins(self):
        self.add_to_company(['corianton'])

    def handle_corianton_joins_again(self):
        self.add_to_company(['corianton'])

    def handle_corianton_runs_away(self):
        # if there is nobody alive left in the company, resurrect moroni or recruit him
        need_moroni = True
        for warlord in self.game_state['company']:
            if warlord['soldiers'] > 0 and warlord['name'] != 'corianton':
                need_moroni = False
                break
        if need_moroni:
            if 'moroni' in [warlord['name'] for warlord in self.game_state['company']]:
                self.heal('moroni', 100)
            else:
                reserve_index = self.get_reserve_index('moroni')
                self.recruit(reserve_index)

        self.remove_from_company_and_reserve('corianton')

    def handle_corianton_leaves(self):
        # if there is nobody alive left in the company, resurrect moronihah or recruit him
        need_moronihah = True
        for warlord in self.game_state['company']:
            if warlord['soldiers'] > 0 and warlord['name'] != 'corianton':
                need_moronihah = False
                break
        if need_moronihah:
            if 'moronihah' in [warlord['name'] for warlord in self.game_state['company']]:
                self.heal('moronihah', 100)
            else:
                reserve_index = self.get_reserve_index('moronihah')
                self.recruit(reserve_index)

        self.remove_from_company_and_reserve('corianton')

    def handle_battle37(self):
        cities = copy.deepcopy(self.game_state['cities'])
        cities.append({
            'name': 'nephihah',
            'teleport': True,
        })
        self.update_game_state({
            'cities': cities,
        })

    def handle_battle39(self):
        cities = copy.deepcopy(self.game_state['cities'])
        cities.append({
            'name': 'judea',
            'teleport': True,
        })
        self.update_game_state({
            'cities': cities,
        })

    def handle_helaman_joins(self):
        self.add_to_company(['helaman'])

    def handle_battle44(self):
        cities = copy.deepcopy(self.game_state['cities'])
        cities.append({
            'name': 'cumeni',
            'teleport': True,
        })
        self.update_game_state({
            'cities': cities,
        })

    def handle_cumeni_hq(self):
        self.update_game_state({
            'cities': [
                {
                    'name': 'zarahemla',
                    'teleport': False,
                },
                {
                    'name': 'manti',
                    'teleport': True,
                },
                {
                    'name': 'bountiful',
                    'teleport': True,
                },
                {
                    'name': 'gid',
                    'teleport': True,
                },
                {
                    'name': 'nephihah',
                    'teleport': False,
                },
                {
                    'name': 'judea',
                    'teleport': True,
                },
                {
                    'name': 'cumeni',
                    'teleport': True,
                },
            ]
        })

    def handle_showed_sign_to_seezoram(self):
        robbers = {
            'name': 'robbers',
            'stats': {
                "soldiers": 42000,
                "strength": 151,
                "defense": 88,
                "intelligence": 69,
                "agility": 128,
                "evasion": 31,
                "tactical_points": 0,
                "attack_points": 110,
                "armor_class": 90,
            },
        }
        battle_data = {
            'enemies': [
                {'name': 'seezoram', 'level': 60},
                robbers,
                robbers,
                robbers,
                robbers,
            ],
            'battle_type': 'story',
            'exit': "Please spare me! ~~~~~~~~ ~~~~~~~~ ~~~~~~~~ ~~~~~~~~ Seantum? What are you doing here?",
            'narration': 'Seantum suddenly appears and murders Seezoram!',
            'next_battle': {
                "name": "battle57",
                "intro": "Thank you for distracting my brother so that I could dispatch of him easily. Now his judgment seat will be mine, and I will gain more influence in the secret band of Gadianton.",
                "exit": "Let me go, and I will tell you where Gadianton is hiding. He is somewhere in the city Bountiful.",
                "enemies": [
                    {
                        "name": "seantum",
                        "level": 60
                    },
                    {
                        'name': 'robbers',
                        'stats': {
                            "soldiers": 42000,
                            "strength": 151,
                            "defense": 88,
                            "intelligence": 69,
                            "agility": 128,
                            "evasion": 31,
                            "tactical_points": 0,
                            "attack_points": 110,
                            "armor_class": 90,
                        },
                    },
                    {
                        'name': 'robbers',
                        'stats': {
                            "soldiers": 42000,
                            "strength": 151,
                            "defense": 88,
                            "intelligence": 69,
                            "agility": 128,
                            "evasion": 31,
                            "tactical_points": 0,
                            "attack_points": 110,
                            "armor_class": 90,
                        },
                    },
                    {
                        'name': 'robbers',
                        'stats': {
                            "soldiers": 42000,
                            "strength": 151,
                            "defense": 88,
                            "intelligence": 69,
                            "agility": 128,
                            "evasion": 31,
                            "tactical_points": 0,
                            "attack_points": 110,
                            "armor_class": 90,
                        },
                    },
                    {
                        'name': 'robbers',
                        'stats': {
                            "soldiers": 42000,
                            "strength": 151,
                            "defense": 88,
                            "intelligence": 69,
                            "agility": 128,
                            "evasion": 31,
                            "tactical_points": 0,
                            "attack_points": 110,
                            "armor_class": 90,
                        },
                    },
                ],
            },
        }
        enemies = []
        for enemy in battle_data['enemies']:
            if 'stats' in enemy:
                stats = enemy['stats']
            else:
                stats = load_stats(enemy['name'])
                stats['soldiers'] = get_max_soldiers(enemy['name'], enemy['level'], is_ally=False)
                stats['tactical_points'] = get_max_tactical_points(enemy['name'], enemy['level'])
                stats['attack_points'] = get_attack_points_by_level(enemy['level'])
                stats['armor_class'] = get_armor_class_by_level(enemy['level'])
                stats['tactics'] = get_tactics(enemy['name'], enemy['level'], pretty=False)
            enemies.append({
                'name': enemy['name'],
                'stats': stats,
            })
        self.current_map.start_battle_after_dialog(
            enemies, battle_data['battle_type'], exit=battle_data['exit'], battle_name="battle56",
            narration=battle_data['narration'], next_battle=battle_data['next_battle'],
        )

    def handle_talked_with_gadianton_in_bountiful(self):
        robbers = {
            'name': 'robbers',
            'stats': {
                "soldiers": 42000,
                "strength": 151,
                "defense": 88,
                "intelligence": 69,
                "agility": 128,
                "evasion": 31,
                "tactical_points": 0,
                "attack_points": 110,
                "armor_class": 90,
            },
        }
        battle_data = {
            'enemies': [
                {'name': 'gadianton', 'level': 60},
                {'name': 'kishkumen', 'level': 60},
                robbers,
                robbers,
                robbers,
            ],
            'battle_type': 'story',
            'exit': "You'll never be able to stop me! My secret band has infiltrated every level of government!",
            'narration': "Gadianton fled to the caves south of Zarahemla. ~~~~~~~~ ~~~~~~~~ ~~~~~~~~ ~~~~~~~~ Hey! He stole all our money and food!",
        }
        enemies = []
        for enemy in battle_data['enemies']:
            if 'stats' in enemy:
                stats = enemy['stats']
            else:
                stats = load_stats(enemy['name'])
                stats['soldiers'] = get_max_soldiers(enemy['name'], enemy['level'], is_ally=False)
                stats['tactical_points'] = get_max_tactical_points(enemy['name'], enemy['level'])
                stats['attack_points'] = get_attack_points_by_level(enemy['level'])
                stats['armor_class'] = get_armor_class_by_level(enemy['level'])
                stats['tactics'] = get_tactics(enemy['name'], enemy['level'], pretty=False)
            enemies.append({
                'name': enemy['name'],
                'stats': stats,
            })
        self.current_map.start_battle_after_dialog(
            enemies, battle_data['battle_type'], exit=battle_data['exit'], narration=battle_data['narration'], battle_name="battle58",
        )

    def handle_talked_with_robbers(self):
        robbers = {
            'name': 'robbers',
            'stats': {
                "soldiers": 1600000,
                "strength": 200,
                "defense": 130,
                "intelligence": 99,
                "agility": 128,
                "evasion": 35,
                "tactical_points": 0,
                "attack_points": 180,
                "armor_class": 180,
            },
        }
        battle_data = {
            'enemies': [
                robbers,
                robbers,
                robbers,
                robbers,
                robbers,
            ],
            'battle_type': 'story',
            'exit': "Alright! We surrender!",
        }
        enemies = []
        for enemy in battle_data['enemies']:
            if 'stats' in enemy:
                stats = enemy['stats']
            else:
                stats = load_stats(enemy['name'])
                stats['soldiers'] = get_max_soldiers(enemy['name'], enemy['level'], is_ally=False)
                stats['tactical_points'] = get_max_tactical_points(enemy['name'], enemy['level'])
                stats['attack_points'] = get_attack_points_by_level(enemy['level'])
                stats['armor_class'] = get_armor_class_by_level(enemy['level'])
                stats['tactics'] = get_tactics(enemy['name'], enemy['level'], pretty=False)
            enemies.append({
                'name': enemy['name'],
                'stats': stats,
            })
        self.current_map.start_battle_after_dialog(
            enemies, battle_data['battle_type'], exit=battle_data['exit'], battle_name="battle72",
        )

    def handle_moronihah_joins(self):
        self.add_to_company(['moronihah'])

    def handle_recruited_prisoners(self):
        level = self.game_state['level'] + 1
        experience = EXP_REQUIRED_BY_LEVEL.get(level, MAX_NUM)
        self.update_game_state({
            'level': level,
            'experience': experience,
        })
        pygame.mixer.music.load(os.path.join('data', 'audio', 'music', 'level.wav'))
        pygame.mixer.music.play()
        company = self.game_state['company']
        dialog = u"{}'s army has advanced one skill level. ".format(company[0]['name'].title())
        tactic_guys = []
        tactic = get_tactic_for_level(level)
        for warlord in company:
            if can_level_up(warlord['name']):
                dialog += u"{} now has {} soldiers. ".format(
                    warlord['name'].title(), get_max_soldiers(warlord['name'], level, is_ally=True),
                )
            if tactic and get_intelligence(warlord['name']) >= TACTICS[tactic]['min_intelligence']:
                tactic_guys.append(warlord)
        if len(tactic_guys) > 1:
            for warlord in tactic_guys[0:-1]:
                dialog += u"{}, ".format(warlord['name'].title())
        if len(tactic_guys) > 0:
            dialog += u"{} learned the {} tactic. ".format(tactic_guys[-1]['name'].title(), tactic.title())
        tactician = self.get_tactician()
        if tactician:
            new_tactical_points = get_max_tactical_points(tactician['name'], level)
            old_tactical_points = get_max_tactical_points(tactician['name'], level-1)
            if new_tactical_points > old_tactical_points:
                dialog += u"{}'s tactical ability increased to {}.".format(
                    tactician['name'].title(), new_tactical_points,
                )
        return dialog

    def handle_recruited_prisoners_again(self):
        return self.handle_recruited_prisoners()

    def handle_got_lost_and_found_item(self):
        lost_and_found = self.game_state['lost_and_found']
        item = lost_and_found.pop(0)
        self.add_to_inventory(item)
        self.update_game_state({'lost_and_found': lost_and_found})

    def handle_found_title_of_liberty(self):
        lost_and_found = self.game_state['lost_and_found']
        lost_and_found.remove('t~of~liberty')
        self.add_to_inventory('t~of~liberty')
        self.update_game_state({'lost_and_found': lost_and_found})

    def handle_gave_iron_ore_and_diamond(self):
        warlord, item_index = self._find_first_item_in_inventory('iron~ore')
        self.remove_item(warlord, item_index)
        warlord, item_index = self._find_first_item_in_inventory('diamond')
        self.remove_item(warlord, item_index)

    def handle_two_yuppies(self):
        self.two_yuppies_state = True

    def handle_one_yuppie(self):
        self.two_yuppies_state = False

    def handle_got_explosive(self):
        self.add_to_inventory('explosive')

    def handle_pahoran_joins(self):
        self.add_to_company(['pahoran'])

    def handle_battle48(self):
        self.update_game_state({
            'cities': [
                {
                    'name': 'zarahemla',
                    'teleport': True,
                },
                {
                    'name': 'manti',
                    'teleport': True,
                },
                {
                    'name': 'bountiful',
                    'teleport': True,
                },
                {
                    'name': 'gid',
                    'teleport': True,
                },
                {
                    'name': 'nephihah',
                    'teleport': False,
                },
                {
                    'name': 'judea',
                    'teleport': True,
                },
                {
                    'name': 'cumeni',
                    'teleport': True,
                },
            ]
        })

    def handle_battle49(self):
        self.update_game_state({
            'cities': [
                {
                    'name': 'zarahemla',
                    'teleport': True,
                },
                {
                    'name': 'manti',
                    'teleport': True,
                },
                {
                    'name': 'bountiful',
                    'teleport': True,
                },
                {
                    'name': 'gid',
                    'teleport': True,
                },
                {
                    'name': 'nephihah',
                    'teleport': True,
                },
                {
                    'name': 'judea',
                    'teleport': True,
                },
                {
                    'name': 'cumeni',
                    'teleport': True,
                },
            ],
        })

    def handle_battle55(self):
        self.update_game_state({
            'cities': [
                {
                    'name': 'zarahemla',
                    'teleport': True,
                },
                {
                    'name': 'manti',
                    'teleport': True,
                },
                {
                    'name': 'bountiful',
                    'teleport': True,
                },
                {
                    'name': 'gid',
                    'teleport': True,
                },
                {
                    'name': 'nephihah',
                    'teleport': True,
                },
                {
                    'name': 'judea',
                    'teleport': True,
                },
                {
                    'name': 'cumeni',
                    'teleport': True,
                },
                {
                    'name': 'moroni',
                    'teleport': True,
                },
            ],
        })

        # Just in case lehi never joined before
        if not self.conditions_are_met('lehi_and_aha_join'):
            self.set_game_state_condition('lehi_and_aha_join')
            self.delete_member(-1)
            self.delete_member(-1)

        # if there is nobody alive left in the company, resurrect lehi or recruit him
        need_lehi = True
        for warlord in self.game_state['company']:
            if warlord['soldiers'] > 0 and warlord['name'] not in ['moroni', 'pahoran', 'teancum']:
                need_lehi = False
                break
        if need_lehi:
            if 'lehi' in [warlord['name'] for warlord in self.game_state['company']]:
                self.heal('lehi', 100)
            else:
                reserve_index = self.get_reserve_index('lehi')
                self.recruit(reserve_index)

        # get rid of moroni, pahoran, and teancum
        self.remove_from_company_and_reserve('moroni')
        self.remove_from_company_and_reserve('pahoran')
        self.remove_from_company_and_reserve('teancum')

    def handle_got_gold_key(self):
        self.add_to_inventory('gold~key')

    def handle_nephi_joins(self):
        self.add_to_company(['nephi'])

    def handle_start_battle59(self):
        robbers = {
            'name': 'robbers',
            'stats': {
                "soldiers": 42000,
                "strength": 185,
                "defense": 210,
                "intelligence": 60,
                "agility": 101,
                "evasion": 135,
                "tactical_points": 0,
                "attack_points": 100,
                "armor_class": 80,
            },
        }
        battle_data = {
            'enemies': [
                {
                    "name": "gadianton",
                    "level": 60,
                },
                {
                    "name": "moriantum",
                    "level": 60,
                },
                {
                    "name": "zeezra",
                    "level": 60,
                },
                robbers,
                robbers,
            ],
            'battle_type': 'story',
            "intro": "You will never take me alive!",
            "narration": "Gadianton was slain in battle.",
        }
        enemies = []
        for enemy in battle_data['enemies']:
            if 'stats' in enemy:
                stats = enemy['stats']
            else:
                stats = load_stats(enemy['name'])
                stats['soldiers'] = get_max_soldiers(enemy['name'], enemy['level'], is_ally=False)
                stats['tactical_points'] = get_max_tactical_points(enemy['name'], enemy['level'])
                stats['attack_points'] = get_attack_points_by_level(enemy['level'])
                stats['armor_class'] = get_armor_class_by_level(enemy['level'])
                stats['tactics'] = get_tactics(enemy['name'], enemy['level'], pretty=False)
            enemies.append({
                'name': enemy['name'],
                'stats': stats,
            })
        self.current_map.start_battle_after_dialog(
            enemies, battle_data['battle_type'], intro=battle_data['intro'], narration=battle_data['narration'], 
            battle_name="battle59",
        )

    def handle_start_battle60(self):
        robbers = {
            'name': 'robbers',
            'stats': {
                "soldiers": 42000,
                "strength": 185,
                "defense": 210,
                "intelligence": 60,
                "agility": 101,
                "evasion": 135,
                "tactical_points": 0,
                "attack_points": 100,
                "armor_class": 80,
            },
        }
        battle_data = {
            'enemies': [
                {
                    "name": "kishkumen",
                    "level": 60,
                },
                {
                    "name": "moses",
                    "level": 60,
                },
                {
                    "name": "ramah",
                    "level": 60,
                },
                robbers,
                robbers,
            ],
            'battle_type': 'story',
            "intro": "Ha! You think just because you have found two of our hideouts that you have won against the band of Gadianton? We are in your cities, your wilderness, your government, your homes. We are everywhere!",
            "exit": "Until we meet again, Moronihah.",
        }
        enemies = []
        for enemy in battle_data['enemies']:
            if 'stats' in enemy:
                stats = enemy['stats']
            else:
                stats = load_stats(enemy['name'])
                stats['soldiers'] = get_max_soldiers(enemy['name'], enemy['level'], is_ally=False)
                stats['tactical_points'] = get_max_tactical_points(enemy['name'], enemy['level'])
                stats['attack_points'] = get_attack_points_by_level(enemy['level'])
                stats['armor_class'] = get_armor_class_by_level(enemy['level'])
                stats['tactics'] = get_tactics(enemy['name'], enemy['level'], pretty=False)
            enemies.append({
                'name': enemy['name'],
                'stats': stats,
            })
        self.current_map.start_battle_after_dialog(
            enemies, battle_data['battle_type'], intro=battle_data['intro'], exit=battle_data['exit'], 
            battle_name="battle60",
        )

    def handle_start_battle61(self):
        battle_data = {
            'enemies': [
                {
                    "name": "paanchi",
                    "level": 62,
                },
                {
                    "name": "sherem",
                    "level": 60,
                },
                {
                    "name": "zenehor",
                    "level": 60,
                },
                {
                    "name": "mulek",
                    "level": 60,
                },
                {
                    "name": "cumenihah",
                    "level": 60,
                },
            ],
            'battle_type': 'story',
            "intro": "I am the one who sent Kishkumen to murder my brother Pahoran. And once I have murdered Pacumeni too, the judgment seat will be mine. Too bad you won't be around to warn anyone.",
            "exit": "My life is forfeit! I spent my years plotting in the shadows, deceiving, and murdering. My punishment is just.",
            "narration": "The last known leaders of the Gadianton Robbers have been driven out of the land and gone into hiding. Hopefully the chief judge and the people are safe now from their secret combinations.",
        }
        enemies = []
        for enemy in battle_data['enemies']:
            if 'stats' in enemy:
                stats = enemy['stats']
            else:
                stats = load_stats(enemy['name'])
                stats['soldiers'] = get_max_soldiers(enemy['name'], enemy['level'], is_ally=False)
                stats['tactical_points'] = get_max_tactical_points(enemy['name'], enemy['level'])
                stats['attack_points'] = get_attack_points_by_level(enemy['level'])
                stats['armor_class'] = get_armor_class_by_level(enemy['level'])
                stats['tactics'] = get_tactics(enemy['name'], enemy['level'], pretty=False)
            enemies.append({
                'name': enemy['name'],
                'stats': stats,
            })
        self.current_map.start_battle_after_dialog(
            enemies, battle_data['battle_type'], intro=battle_data['intro'], exit=battle_data['exit'], 
            battle_name="battle61", narration=battle_data['narration'],
        )

    def handle_start_battle70(self):
        battle_data = {
            'enemies': [
                {
                    "name": "gidgiddoni",
                    "level": 70,
                },
            ],
            'battle_type': 'story',
            "intro": "Whoever you are, you do not want to mess with me right now.",
        }
        enemies = []
        for enemy in battle_data['enemies']:
            if 'stats' in enemy:
                stats = enemy['stats']
            else:
                stats = load_stats(enemy['name'])
                stats['soldiers'] = get_max_soldiers(enemy['name'], enemy['level'], is_ally=False)
                stats['tactical_points'] = get_max_tactical_points(enemy['name'], enemy['level'])
                stats['attack_points'] = get_attack_points_by_level(enemy['level'])
                stats['armor_class'] = get_armor_class_by_level(enemy['level'])
                stats['tactics'] = get_tactics(enemy['name'], enemy['level'], pretty=False)
            enemies.append({
                'name': enemy['name'],
                'stats': stats,
            })
        self.current_map.start_battle_after_dialog(
            enemies, battle_data['battle_type'], intro=battle_data['intro'], battle_name="battle70",
        )

    def handle_gidgiddoni_joins(self):
        self.add_to_company(['gidgiddoni'])

    def handle_lachoneus_joins(self):
        self.add_to_company(['lachoneus'])

    def handle_battle69(self):
        if self.game_complete(current_condition="battle69"):
            self._handle_game_complete()

    def handle_battle80(self):
        if self.game_complete(current_condition="battle80"):
            self._handle_game_complete()

    def handle_battle90(self):
        if self.game_complete(current_condition="battle90"):
            self._handle_game_complete()

    def _handle_game_complete(self):
        # if there is nobody alive left in the company, resurrect moronihah or recruit him
        need_moronihah = True
        for warlord in self.game_state['company']:
            if warlord['soldiers'] > 0 and warlord['name'] not in ['shiz', 'lachoneus']:
                need_moronihah = False
                break
        if need_moronihah:
            if 'moronihah' in [warlord['name'] for warlord in self.game_state['company']]:
                self.heal('moronihah', 100)
            else:
                reserve_index = self.get_reserve_index('moronihah')
                self.recruit(reserve_index)

        self.remove_from_company_and_reserve('lachoneus')
        self.remove_from_company_and_reserve('shiz')

    def handle_start_with_shiz(self):
        self.battle = None
        self.current_map = None
        self.current_music = 'repeat'
        self.continue_current_music = True
        pygame.mixer.music.load(VILLAGE_MUSIC['repeat'])
        pygame.mixer.music.play(-1)
        self.beginning_screen = Beginning(self, self.virtual_screen)
        self.set_screen_state('beginning')

    def handle_roll_credits(self):
        self.start_credits = True
