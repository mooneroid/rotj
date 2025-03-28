# -*- coding: UTF-8 -*-

import copy
import math
import os
import time

import pygame
from pygame.locals import *
import pyscroll
from pytmx.util_pygame import load_pygame

from constants import CAVE_NAMES, ITEMS
from helpers import get_map_filename
from hero import Hero
from report import Report
from shop import create_shop
from text import create_prompt, MenuBox, TextBox


class MapMenu(object):
    def __init__(self, screen, tiled_map):
        self.screen = screen
        self.main_menu = MenuBox(['TALK', 'CHECK', 'FORMATION', 'GENERAL', 'ITEM'], title='Command')
        self.main_menu.focus()
        self.select_sound = pygame.mixer.Sound(os.path.join('data', 'audio', 'select.wav'))
        self.select_sound.play()
        self.resurrect_sound = pygame.mixer.Sound(os.path.join('data', 'audio', 'resurrect.wav'))
        self.state = 'main'
        self.prompt = None
        self.map = tiled_map
        self.game = self.map.game
        self.formation_menu = None
        self.order_menu = None
        self.new_order = None
        self.order_indices = []
        self.strat_menu = None
        self.general_menu = None
        self.report = None
        self.items_menu = None
        self.item_selected_menu = None
        self.recipient_menu = None
        self.city_menu = None
        self.dialog_choice = None
        self.dialog_choice_menu = None
        self.shop = None
        self.save_menu = None
        self.game = self.map.game
        self.spoils_box = None

    def update(self, dt):
        if self.state == 'main':
            self.main_menu.update(dt)
        if self.prompt:
            self.prompt.update(dt)
        if self.state in ['talk', 'check', 'confirm_strat', 'empty', 'item_prompt']:
            if self.dialog_choice and not self.prompt.has_more_stuff_to_show():
                self.handle_dialog_choice()
        if self.state == 'formation':
            self.formation_menu.update(dt)
        if self.state == 'order':
            self.order_menu.update(dt)
            self.new_order.update(dt)
        if self.state in ['strat', 'confirm_strat', 'item']:
            self.strat_menu.update(dt)
        if self.state == 'general':
            self.general_menu.update(dt)
        if self.state == 'items':
            self.items_menu.update(dt)
        if self.state == 'item_selected':
            self.item_selected_menu.update(dt)
        if self.state == 'recipient':
            self.recipient_menu.update(dt)
        if self.state == 'city':
            self.city_menu.update(dt)
        if self.state == 'choice':
            self.dialog_choice_menu.update(dt)
        if self.state == 'shop':
            self.shop.update(dt)
        if self.state == 'save':
            if not self.save_menu:
                if not self.prompt.has_more_stuff_to_show():
                    self.save_menu = MenuBox(['YES', 'NO'])
                    self.save_menu.focus()
                    self.prompt.shutdown()
                    self.item_selected_menu = None
            else:
                self.save_menu.update(dt)
        if self.state in ['talk', 'choice']:
            if not self.spoils_box and self.show_spoils_box and not self.prompt.has_more_stuff_to_show():
                self.create_spoils_box()

    def create_spoils_box(self):
        money = self.game.game_state['money']
        food = int(math.ceil(self.game.game_state['food']))
        text = u"MONEY\n{:~>9}\nFOOD\n{:~>9}".format(money, food)
        self.spoils_box = TextBox(text, border=True, indent=1)

    def handle_dialog_choice(self):
        self.state = 'choice'
        if self.dialog_choice and len(self.dialog_choice) and self.dialog_choice[0]['choice'] == 'Share password':
            width = 96
        else:
            width = None
        self.dialog_choice_menu = MenuBox([choice['choice'] for choice in self.dialog_choice], width=width)
        self.dialog_choice_menu.focus()

    def draw(self):
        if self.main_menu:
            self.screen.blit(self.main_menu.surface, (160, 0))
        if self.prompt:
            self.screen.blit(self.prompt.surface, (0, 160))
        if self.formation_menu:
            self.screen.blit(self.formation_menu.surface, (160, 128))
        if self.order_menu:
            self.screen.blit(self.order_menu.surface, (0, 0))
        if self.new_order:
            self.screen.blit(self.new_order.surface, (128, 0))
        if self.strat_menu:
            self.screen.blit(self.strat_menu.surface, (0, 0))
        if self.general_menu:
            self.screen.blit(self.general_menu.surface, (0, 0))
        if self.report:
            self.screen.blit(self.report.surface, (0, 0))
        if self.items_menu:
            self.screen.blit(self.items_menu.surface, (64, 0))
        if self.item_selected_menu:
            self.screen.blit(self.item_selected_menu.surface, (176, 128))
        if self.recipient_menu:
            self.screen.blit(self.recipient_menu.surface, (144, 0))
        if self.city_menu:
            self.screen.blit(self.city_menu.surface, (160, 0))
        if self.dialog_choice_menu:
            self.screen.blit(self.dialog_choice_menu.surface, (160, 128))
        if self.shop:
            self.shop.update_surface()
            self.screen.blit(self.shop.surface, (0, 0))
        if self.save_menu:
            self.screen.blit(self.save_menu.surface, (176, 128))
        if self.spoils_box:
            self.screen.blit(self.spoils_box.surface, (160, 184))

    def handle_input_main(self, pressed):
        self.main_menu.handle_input(pressed)
        if pressed[K_z]:
            return self.exit()
        elif pressed[K_x]:
            self.select_sound.play()
            choice = self.main_menu.get_choice()
            if choice == 'TALK':
                self.handle_talk()
            elif choice == 'CHECK':
                self.handle_check()
            elif choice == 'FORMATION':
                self.handle_formation()
            elif choice == 'GENERAL':
                self.handle_general()
            elif choice == 'ITEM':
                self.handle_item()

    def handle_item(self):
        self.state = 'item'
        self.main_menu.unfocus()
        self.strat_menu = MenuBox(self.map.get_company_names())
        self.strat_menu.focus()    

    def handle_general(self):
        self.general_menu = MenuBox(self.map.get_company_names())
        self.main_menu.unfocus()
        self.general_menu.focus()
        self.state = 'general'

    def exit(self):
        if self.prompt:
            self.prompt.shutdown()
            self.prompt = None
            self.spoils_box = None
        return 'exit'

    def handle_input(self, pressed):
        if pressed[K_RETURN] and (not self.prompt or not self.prompt.has_more_stuff_to_show()):
            self.game.open_pause_menu()
        elif self.state == 'main':
            return self.handle_input_main(pressed)
        elif self.state in ['talk', 'check', 'confirm_strat', 'item_prompt']:
            self.prompt.handle_input(pressed)
            if (pressed[K_x] or pressed[K_z]) and not self.prompt.has_more_stuff_to_show():
                return self.exit()
        elif self.state == 'save':
            if self.save_menu:
                self.save_menu.handle_input(pressed)
                if pressed[K_x] and self.save_menu.get_choice() == 'YES':
                    self.game.save()
                    self.game.start_sleep(os.path.join('data', 'audio', 'save.wav'), "Your game is saved.")
                if pressed[K_x] or pressed[K_z]:
                    return self.exit()
            else:
                self.prompt.handle_input(pressed)
        elif self.state == 'formation':
            return self.handle_input_formation(pressed)
        elif self.state == 'order':
            return self.handle_input_order(pressed)
        elif self.state == 'strat':
            return self.handle_input_strat(pressed)
        elif self.state == 'general':
            return self.handle_input_general(pressed)
        elif self.state == 'report':
            if pressed[K_x] or pressed[K_z]:
                self.state = 'general'
                self.report = None
                return
        elif self.state == 'item':
            return self.handle_input_item(pressed)
        elif self.state == 'empty':
            return self.handle_input_empty(pressed)
        elif self.state == 'items':
            return self.handle_input_items(pressed)
        elif self.state == 'item_selected':
            return self.handle_input_item_selected(pressed)
        elif self.state == 'recipient':
            return self.handle_input_recipient(pressed)
        elif self.state == 'city':
            return self.handle_input_city(pressed)
        elif self.state == 'choice':
            return self.handle_input_choice(pressed)
        elif self.state == 'shop':
            return self.shop.handle_input(pressed)

    def handle_input_choice(self, pressed):
        self.dialog_choice_menu.handle_input(pressed)
        if pressed[K_x]:
            self.select_sound.play()
            for choice in self.dialog_choice:
                if choice['choice'] == self.dialog_choice_menu.get_choice():
                    selected_choice = choice
                    break
            action_dialog = None
            if 'game_state_action' in selected_choice:
                action_dialog = self.map.set_game_state_condition(selected_choice['game_state_action'])
            self.show_spoils_box = selected_choice.get('show_spoils_box', False)
            self.spoils_box = None
            self.state = 'talk'
            self.dialog_choice_menu = None
            next_dialog = action_dialog or selected_choice.get('next_dialog', 'OK')
            if isinstance(next_dialog, str):
                self.prompt = create_prompt(next_dialog)
                self.dialog_choice = None
            else: # it's a list
                for conditional_dialog in next_dialog:
                    if self.game.conditions_are_met(conditional_dialog.get('condition')):
                        break
                self.prompt = create_prompt(conditional_dialog['text'])
                self.dialog_choice = conditional_dialog.get('prompt')
                self.show_spoils_box = selected_choice.get('show_spoils_box', False)

    def handle_input_city(self, pressed):
        self.city_menu.handle_input(pressed)
        if pressed[K_z]:
            self.city_menu = None
            self.state = 'item_selected'
            self.item_selected_menu.focus()
        elif pressed[K_x]:
            self.select_sound.play()
            self.map.teleport(self.city_menu.get_choice().lower())
            item_index = self.items_menu.current_choice
            user = self.strat_menu.get_choice().lower()
            self.map.remove_item(user, item_index)
            return self.exit()

    def handle_input_recipient(self, pressed):
        self.recipient_menu.handle_input(pressed)
        if pressed[K_z]:
            self.recipient_menu = None
            self.state = 'item_selected'
            self.item_selected_menu.focus()
        elif pressed[K_x]:
            self.select_sound.play()
            action_choice = self.item_selected_menu.get_choice()
            item_name = self.items_menu.get_choice().lower()
            user = self.strat_menu.get_choice().lower()
            recipient = self.recipient_menu.get_choice().lower()
            recipient_is_dead = '*' in self.recipient_menu.get_choice(strip_star=False)
            if action_choice == 'USE':
                healing_points = ITEMS[item_name].get('healing_points')
                if healing_points:
                    if recipient_is_dead:
                        self.state = 'item_prompt'
                        text = "{} used {}. But nothing happened.".format(user.title(), item_name.title())
                        self.prompt = create_prompt(text)
                    else:
                        self.map.remove_item(user, self.items_menu.current_choice)
                        self.map.heal(recipient, healing_points)
                        text = "{} used {}. {}'s soldiers recovered their strength.".format(
                            user.title(), item_name.title(), recipient.title(),
                        )
                        self.prompt = create_prompt(text)
                        self.state = 'item_prompt'
                elif item_name == 'resurrect':
                    if recipient == 'shiz' and self.game.shiz_is_headless() and not recipient_is_dead:
                        self.state = 'item_prompt'
                        self.resurrect_sound.play()
                        time.sleep(1.5)
                        text = "{} used {}. {} has recovered from his wounds.".format(
                            user.title(), item_name.title(), recipient.title(),
                        )
                        self.prompt = create_prompt(text)
                        self.map.remove_item(user, self.items_menu.current_choice)
                        self.map.restore_head_of_shiz()
                    elif not recipient_is_dead:
                        self.state = 'item_prompt'
                        text = "{} used {}. But nothing happened.".format(user.title(), item_name.title())
                        self.prompt = create_prompt(text)
                    else:
                        self.map.remove_item(user, self.items_menu.current_choice)
                        self.map.heal(recipient, 1)
                        self.resurrect_sound.play()
                        time.sleep(1.5)
                        text = "{} used {}. {} has recovered from his wounds.".format(
                            user.title(), item_name.title(), recipient.title(),
                        )
                        self.prompt = create_prompt(text)
                        self.state = 'item_prompt'
            elif action_choice == 'PASS':
                self.map.pass_item(user, recipient, self.items_menu.current_choice)
                self.items_menu = self.create_items_menu()
                if self.items_menu:
                    self.state = 'items'
                    self.items_menu.focus()
                else:
                    self.state = 'item'
                    self.strat_menu.focus()
                self.recipient_menu = None
                self.item_selected_menu = None

    def handle_input_item_selected(self, pressed):
        self.item_selected_menu.handle_input(pressed)
        if pressed[K_z]:
            self.item_selected_menu = None
            self.items_menu.focus()
            self.state = 'items'
        elif pressed[K_x]:
            self.select_sound.play()
            choice = self.item_selected_menu.get_choice()
            if choice == 'USE':
                self.handle_use()
            elif choice == 'PASS':
                self.handle_pass()
            elif choice == 'EQUIP':
                self.handle_equip()
            elif choice == 'DROP':
                self.handle_drop()

    def handle_drop(self):
        item_index = self.items_menu.current_choice
        item = self.items_menu.get_choice().lower()
        user = self.strat_menu.get_choice().lower()
        self.map.remove_item(user, item_index)
        if ITEMS[item].get('rare'):
            self.map.add_to_lost_and_found(item)
        self.items_menu = self.create_items_menu()
        self.item_selected_menu = None
        if self.items_menu:
            self.items_menu.focus()
            self.state = 'items'
        else:
            self.state = 'item'
            self.strat_menu.focus()

    def handle_equip(self):
        item_index = self.items_menu.current_choice
        user = self.strat_menu.get_choice().lower()
        self.map.try_toggle_equip_on_item(user, item_index)
        self.items_menu = self.create_items_menu()
        self.item_selected_menu = None
        self.items_menu.focus()
        self.state = 'items'

    def handle_pass(self):
        self.item_selected_menu.unfocus()
        self.state = 'recipient'
        user = self.strat_menu.get_choice().lower()
        self.recipient_menu = MenuBox(self.map.get_company_names(with_empty_item_slots=True, omit=user))
        self.recipient_menu.focus()

    def handle_use(self):
        self.item_selected_menu.unfocus()
        item_name = self.items_menu.get_choice().lower()
        map_usage = ITEMS[item_name].get('map_usage')
        user = self.strat_menu.get_choice()
        user_is_dead = '*' in self.strat_menu.get_choice(strip_star=False)
        if user_is_dead:
            self.state = 'item_prompt'
            self.prompt = create_prompt("{} has been injured and can't move.".format(user.title()))
        elif map_usage == 'company':
            self.state = 'recipient'
            self.recipient_menu = MenuBox(self.map.get_company_names())
            self.recipient_menu.focus()
        elif map_usage == 'city':
            if self.map.game.conditions_are_met({
                'battle59': True,
                'battle60': True,
                'battle61': False,
            }):
                self.state = 'item_prompt'
                self.prompt = create_prompt("Strange. It's not working right now.")
            else:
                self.state = 'city'
                self.city_menu = MenuBox(self.map.get_teleport_cities())
                self.city_menu.focus()
        elif map_usage == 'map':
            self.state = 'item_prompt'
            self.prompt = create_prompt("{} used {}. But nothing happened.".format(user, item_name.title()))
        elif map_usage == 'cloak':
            self.state = 'item_prompt'
            if self.map.name in ['onidah', 'tunnels_of_the_north']:
                self.prompt = create_prompt("That doesn't seem to work in here.")
            else:
                self.prompt = create_prompt("{} used {}. Our movements are hidden from the enemy.".format(
                    user, item_name.title(),
                ))
                self.map.game.cloak_steps_remaining = 1000 if item_name == 's.~cloak' else 100
                self.map.remove_item(user, self.items_menu.current_choice)
        elif map_usage == 'scout':
            self.state = 'item_prompt'
            self.prompt = create_prompt("{} deployed a scout ahead of our army. Auto-Train and On-Guard enabled.".format(user))
            self.map.game.scout_steps_remaining = 400
            self.map.remove_item(user, self.items_menu.current_choice)
        elif map_usage == 'save':
            if self.map.name in CAVE_NAMES:
                self.state = 'item_prompt'
                self.prompt = create_prompt("It's too dark to record here.")
            else:
                self.prompt = create_prompt("Are you sure you want to save your game?")
                self.state = 'save'
        elif map_usage == 'unlock':
            result_text = self.map.check_for_item(unlocker=item_name)
            text = "{} used {}. {}".format(self.map.hero.name.title(), item_name.title(), result_text)
            self.prompt = create_prompt(text)
            self.state = 'item_prompt'
            warlord, item_index = self.game._find_first_item_in_inventory(item_name)
            self.game.remove_item(warlord, item_index)
        elif map_usage == 'explosive':
            status = self.map.attempt_explosive()
            if status == 'success':
                text = "{} used Explosive.".format(self.map.hero.name.title())
                self.map.remove_item(user, self.items_menu.current_choice)
            elif status == 'watch_it':
                text = "Hey, watch it! You want us to all go up in flames?"
            else:
                text = "We shouldn't use that here."
            self.prompt = create_prompt(text)
            self.state = 'item_prompt'
        else:
            self.state = 'item_prompt'
            self.prompt = create_prompt("That can't be used here.")

    def handle_input_empty(self, pressed):
        if pressed[K_x]:
            return self.exit()
        elif pressed[K_z]:
            self.prompt.shutdown()
            self.prompt = None
            self.strat_menu.focus()
            self.state = 'item'

    def handle_input_item(self, pressed):
        self.strat_menu.handle_input(pressed)
        if pressed[K_z]:
            self.strat_menu = None
            self.main_menu.focus()
            self.state = 'main'
        elif pressed[K_x]:
            self.select_sound.play()
            warlord = self.strat_menu.get_choice()
            self.items_menu = self.create_items_menu()
            if not self.items_menu:
                self.state = 'empty'
                self.strat_menu.unfocus()
                self.prompt = create_prompt(u"{} doesn't have anything.".format(warlord))
            else:
                self.state = 'items'
                self.strat_menu.unfocus()
                self.items_menu.focus()

    def create_items_menu(self):
        warlord = self.strat_menu.get_choice()
        items = self.map.get_items(warlord)
        return MenuBox(
            [u"{}{}".format(('*' if item.get('equipped') else ''), item['name'].title()) for item in items]
        ) if items else None

    def handle_input_items(self, pressed):
        self.items_menu.handle_input(pressed)
        if pressed[K_z]:
            self.items_menu = None
            self.strat_menu.focus()
            self.state = 'item'
        elif pressed[K_x]:
            self.select_sound.play()
            self.item_selected_menu = MenuBox(['USE', 'PASS', 'EQUIP', 'DROP'])
            self.state = 'item_selected'
            self.items_menu.unfocus()
            self.item_selected_menu.focus()

    def handle_input_general(self, pressed):
        self.general_menu.handle_input(pressed)
        if pressed[K_z]:
            self.general_menu = None
            self.main_menu.focus()
            self.state = 'main'
        elif pressed[K_x]:
            self.select_sound.play()
            choice = self.general_menu.get_choice().lower()
            self.state = 'report'
            self.report = Report(choice, self.map.get_level(), self.map.get_equips(choice), headless=self.map.get_headless(choice))

    def handle_input_strat(self, pressed):
        self.strat_menu.handle_input(pressed)
        if pressed[K_z]:
            self.strat_menu = None
            self.formation_menu.focus()
            self.state = 'formation'
        elif pressed[K_x]:
            self.select_sound.play()
            choice = self.strat_menu.get_choice(strip_star=False)
            if choice.startswith(u'★'):
                choice = choice[1:]
                already_tactician = True
            else:
                already_tactician = False
            if already_tactician:
                self.map.retire_tactician(choice)
                self.strat_menu.remove_stars()
                text = "{} resigned as tactician.".format(choice.title())
            else:
                success = self.map.try_set_tactician(choice)
                if success:
                    self.strat_menu.remove_stars()
                    self.strat_menu.choices[self.strat_menu.current_choice] = u"★" + self.strat_menu.get_choice()
                    text = "{} is the acting tactician.".format(choice.title())
                else:
                    text = "{} can't be a tactician.".format(choice.title())
            self.prompt = create_prompt(text)
            self.state = 'confirm_strat'
            self.strat_menu.create_text_box(None, None, None)
            self.strat_menu.unfocus()

    def handle_input_formation(self, pressed):
        self.formation_menu.handle_input(pressed)
        if pressed[K_z]:
            self.formation_menu = None
            self.state = 'main'
            self.main_menu.focus()
        elif pressed[K_x]:
            self.select_sound.play()
            choice = self.formation_menu.get_choice()
            if choice == 'ORDER':
                self.handle_order()
            elif choice == 'STRAT.':
                self.handle_strat()

    def handle_input_order(self, pressed):
        self.order_menu.handle_input(pressed)
        if pressed[K_z]:
            if len(self.new_order.choices) == 0:
                self.state = 'formation'
                self.formation_menu.focus()
                self.order_menu = None
                self.new_order = None
            else:
                warlord = self.new_order.choices.pop()
                self.order_menu.choices.insert(self.order_indices.pop(), warlord)
        elif pressed[K_x]:
            self.select_sound.play()
            choice_with_star = self.order_menu.get_choice(strip_star=False)
            index = self.order_menu.current_choice
            if choice_with_star:
                self.order_menu.choices.remove(choice_with_star)
                if self.order_menu.current_choice == len(self.order_menu.choices):
                    self.order_menu.current_choice = max(0, self.order_menu.current_choice-1)
                self.new_order.choices.append(choice_with_star)
                self.order_indices.append(index)
            else:
                self.map.update_company_order([choice.lower() for choice in self.new_order.get_choices()])
                return self.exit()

    def handle_order(self):
        self.state = 'order'
        self.formation_menu.unfocus()
        self.order_menu = MenuBox(self.map.get_company_names())
        self.order_menu.focus()
        self.new_order = MenuBox([], width=self.order_menu.get_width(), height=self.order_menu.get_height())

    def handle_strat(self):
        self.state = 'strat'
        self.formation_menu.unfocus()
        self.strat_menu = MenuBox(self.map.get_company_names())
        self.strat_menu.focus()

    def handle_talk(self):
        shop = self.map.get_shop()
        if shop:
            self.state = 'shop'
            self.shop = create_shop(shop, self.map.game)
            self.main_menu.unfocus()
        else:
            lost_and_found = self.game.game_state.get('lost_and_found', [])
            formatters = {
                'lost_and_found': len(lost_and_found) and lost_and_found[0].title(),
            }
            dialog = self.map.get_dialog()
            text = dialog if isinstance(dialog, str) else dialog['text']
            text = text.format(**formatters)
            self.prompt = create_prompt(text)
            self.state = 'talk'
            self.main_menu.unfocus()
            if isinstance(dialog, dict) and 'prompt' in dialog:
                self.dialog_choice = dialog['prompt']
            if isinstance(dialog, dict) and 'show_spoils_box' in dialog:
                self.show_spoils_box = True
            else:
                self.show_spoils_box = False

    def handle_check(self):
        result_text = self.map.check_for_item()
        text = u"{} searched. {}".format(self.map.hero.name.title(), result_text)
        self.prompt = create_prompt(text)
        self.state = 'check'
        self.main_menu.unfocus()

    def handle_formation(self):
        self.formation_menu = MenuBox(['ORDER', 'STRAT.'])
        self.formation_menu.focus()
        self.main_menu.unfocus()
        self.state = 'formation'


