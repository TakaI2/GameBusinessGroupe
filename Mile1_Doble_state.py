#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
import sys
from pygame.locals import *

Light_COUNT = 3

class State(object):

    def __init__(self, name):
        self.name = name

    def do_actions(self):
        pass

    def check_conditions(self):
        pass

    def entry_actions(self):
        pass

    def exit_actions(self):
        pass



class StateMachine(object):

    def __init__(self):

        self.states = {} # ステートを格納する
        self.active_state = None #現在のアクティブなステート

    def add_states(self,state):

        #辞書の内部にステートを追加する
        self.states[state.name] = state

    def think(self):

        #アクティブなステートがあればただ続ける。
        if self.active_state is None:
            return

        #アクティブなステートのアクションを実行し、条件をチェックする
        self.active_state.do_actions()

        new_state_name = self.active_state.check_conditions()
        if new_state_name is not None:
            self.set_state(new_state_name)

    def set_state(self, new_state_name):

        # ステートを切り替えてexitアクションかentryアクションのいずれかを実行する。

        if self.active_state is not None:
            self.active_state.exit_actions()

        self.active_state = self.states[new_state_name]
        self.active_state.entry_actions()

class World(object):

    def __init__(self):

        self.entities = {} #すべてのエンティティを格納する
        self.entity_id = 0# 割り当てられた最後のエンティティid

    def add_entity(self, entity):

        #エンティティを格納し、現在のidを進める
        self.entities[self.entity_id] = entity
        entity.id = self.entity_id  
        self.entity_id += 1

    def remove_entity(self,entity):

        del self.entities[entity.id]

    def get(self,entity_id):

        #エンティティを探し、IDを与える（見つからない場合はNone)
        if entity_id in self.entities:
            return self.entities[entity_id]
        else:
            return None

    def process(self, time_passed):

        # waワールド内の各エンティティを処理
        time_passed_seconds = time_passed / 1000.0
        for entity in self.entities.values():
            entity.process(time_passed_seconds)

class GameEntity(object):

    def __init__(self, world, name):

        self.world = world
        self.name = name

        self.brain = StateMachine()

        self.id = 0

    def process(self, time_passed):

        self.brain.think()


class Light(GameEntity):

    def __init__(self,world):

        #基本クラスのコンストラクタを呼ぶ
        GameEntity.__init__(self,world, "light")

        #それぞれのステートのインスタンスを生成する
        Light_On_State = Light_turn_on(self)
        Light_Off_State = Light_turn_off(self)


        #ステートマシンのステートを追加する(self.brain)
        self.brain.add_states(Light_On_State)
        self.brain.add_states(Light_Off_State)

        self.stable = None
        self.timer = 0

        
class Light_turn_on(State):

    def __init__(self,light):

        # Stateを初期化するために基本クラスのコンストラクタを呼び出す
        State.__init__(self, "ON")
        # このStateが変更されるアリを設定する
        self.light = light

    def do_actions(self):

        self.light.timer += 1

        print 'ライト点いてます。'

    def check_conditions(self):

        if self.light.timer > 3:
            return "OFF"

        return None


    def entry_actions(self):

        print 'ライトが点灯しました'


    def exit_actions(self):

        print "明るくなってきたのでライトを消します。"
        self.light.timer = 0



class Light_turn_off(State):

    def __init__(self,light):

        # Stateを初期化するために基本クラスのコンストラクタを呼び出す
        State.__init__(self, "OFF")
        # このStateが変更されるアリを設定する
        self.light = light

    def do_actions(self):

        self.light.timer += 1

        print 'ライト消えてます。'

    def check_conditions(self):

        if self.light.timer > 3:
            return "ON"

        return None


    def entry_actions(self):

        print 'ライトが消灯しました'


    def exit_actions(self):

        print '暗くなってきたのでライトを点けます。'
        self.light.timer = 0


def run():

    pygame.init()

    world = World()

    clock = pygame.time.Clock()


    #全てのライトのエンティティを追加
    for Light_no in xrange(Light_COUNT):

        light = Light(world)
        light.brain.set_state("ON")
        world.add_entity(light)
    

    while True:

        for event in pygame.event.get():
            if event.type == QUIT:
                sys.exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                sys.exit()

        time_passed = clock.tick(30)


        world.process(time_passed)


if __name__ == "__main__":
    run()




        
        
            


        
        
    
