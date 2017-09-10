#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
import sys
import codecs
import os

from pygame.locals import *

SCR_RECT = Rect(0, 0, 640, 512)
GS = 64
UP,LEFT,DOWN,RIGHT= 0,1,2,3
STAND,DASH,ATUCK = 0,4,8 # state type
STATIC,MOVE = 0, 1 # moving type
PROB_MOVE = 0.005 #probability of moving




#キャラクタ描画用関数

def calc_offset(player):
    """calcurate offset"""
    offsetx = player.rect.topleft[0] - SCR_RECT.width/2
    offsety = player.rect.topleft[1] - SCR_RECT.height/2
    return offsetx, offsety

def load_image(filename, colorkey=None):
    filename = os.path.join("data", filename)
    
    try:
        image = pygame.image.load(filename)
    except pygame.error, message:
        print "Cannot load image:", filename
        raise SystemExit, message
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image
 
def split_image(image):
    """split 896x256 caractor image to 64x64 56 image
    and return the list contain splited image"""
    imageList = []
    for i in range(0, 256, GS):
        for j in range(0, 768, GS):
            surface = pygame.Surface((GS,GS)) #make 64x64 clear surface
            surface.blit(image, (0,0), (j,i,GS,GS))
            surface.set_colorkey(surface.get_at((0,0)), RLEACCEL)
            surface.convert()
            imageList.append(surface)
    return imageList




#ここからステートマシン用クラス


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

    images = [None] * 256 #マップチップを

    def __init__(self):

        self.map_name = "cave"

        self.row = -1
        self.col = -1
        self.map = []
        self.load()

        self.entities = {} #すべてのエンティティを格納する エンティティは
        self.entity_id = 0# 割り当てられた最後のエンティティid

    def add_entity(self, entity):

        #エンティティを格納し、現在のidを進める
        self.entities[self.entity_id] = entity
        entity.id = self.entity_id  
        self.entity_id += 1

    def get_close_entity(self, name , x, y, range = 5):

        for entity in self.entities.itervalues():

            if entity.name == name:

                lengthX = abs(entity.x - x)
                lengthY = abs(entity.y - y)

                distance = lengthX + lengthY

                if distance < range:

                    return entity

        return None
    

    def get_entity(self, x, y):

        for entity in self.entities.itervalues():

            if entity.x == x and entity.y == y:

                return entity


    def remove_entity(self,entity):

        del self.entities[entity.id]

    def get(self,entity_id):

        #エンティティを探し、IDを与える（見つからない場合はNone)
        if entity_id in self.entities:
            return self.entities[entity_id]
        else:
            return None


    def is_movable(self,x, y):

        if x < 0 or x > self.col-1 or y < 0 or y > self.row-1:
            return False
        if self.map[y][x] == 1 or self.map[y][x] == 4: # 水は移動できない
            return False

        for chara in self.entities.values():
            if chara.x == x and chara.y == y:
                return False
            return True
    


    def load(self):
        """Road the Map from Textfile"""
        file = os.path.join("data", self.map_name + ".map")
        # テキスト形式のマップを読み込む
        fp = open(file)
        lines = fp.readlines()  # ファイル全体を行単位で読み込む
        row_str, col_str = lines[0].split()  # 行数と列数
        self.row, self.col = int(row_str), int(col_str)  # int型に変換
        self.default = int(lines[1]) # default
        print self.default
        for line in lines[2:]:  # マップデータを読み込む
            line = line.rstrip()  # 改行除去
            self.map.append([int(x) for x in list(line)])
        fp.close()


    def render(self, screen, offset, flag):


        if flag == 1:
            
            """draw the map"""
            offsetx, offsety = offset
            #calcurate draw area of map
            startx = offsetx / GS
            endx = startx + SCR_RECT.width/GS + 1
            starty = offsety / GS
            endy = starty + SCR_RECT.height/GS + 1
            # draw a map
            for y in range(starty, endy):
                for x in range(startx, endx):
                    # Out area of map drawn by deffault image
                    # If nothing this method error coming in the edge of map
                    if x < 0 or y < 0 or x > self.col-1 or y > self.row-1:
                        screen.blit(self.images[self.default],(x*GS-offsetx, y*GS-offsety))
                    else:
                        screen.blit(self.images[self.map[y][x]],(x*GS-offsetx,y*GS-offsety))

            #draw a character on the map
            for chara in self.entities.values():   #エンティティの中のdraw関数を呼び出すにはこれでいいのか？　idは書く必要は？
                chara.draw(screen, offset)

        elif flag == 2:

            self.title_img = load_image('title.png', -1)
            screen.fill((0,0,128))
            screen.blit(self.title_img,(20,60))

        elif flag == 3:

            self.title_img = load_image('you_win.png', -1)
            screen.fill((255, 255, 255))
            screen.blit(self.title_img,(20,60))

        elif flag == 4:

            self.title_img = load_image('you_lost.png', -1)
            screen.fill((0, 0, 0))
            screen.blit(self.title_img,(20,60))
            


    def process(self, time_passed):

        # waワールド内の格エンティティを処理
        time_passed_seconds = time_passed / 1000.0 #ここ大丈夫？
        for entity in self.entities.values():
            entity.process(time_passed_seconds)



class GameState(object):

    def __init__(self, name):

        self.name = name
        

        self.brain = StateMachine()

    def process(self,time_passed):

        self.brain.think()

        #各ステートで表示する画面の選択


        
        



class GameEntity(object):

    speed = 4
    animcycle = 24
    frame = 0
    

    images = {}

    def __init__(self, world, name, pos, dirl, action ):

        self.world = world
        self.name = name
        self.image = self.images[name][0]
        self.x, self.y = pos[0],pos[1]
        self.vx, self.vy = 0, 0
        self.dex, self.dey = 0, 0 #  エンティティの目標地点の座標
        self.distx, self.disty = 0, 0 # エンティティの目標までの距離を示す
        self.rect = self.image.get_rect(topleft = (self.x*GS,self.y*GS))
        self.direction = dirl
        self.action = action
        self.moving = False
        self.HitPoint = 60
        self.magic = 10
        self.alive = True

        self.brain = StateMachine()

        self.id = 0

    def process(self, time_passed):  #時間が進む間常に実行

        #目標地点から自分の位置までの距離を計算
        self.disty = self.dey - self.y
        self.distx = self.dex - self.x

        """update the state of Player.
        map is necessary to jadge do you move"""
        #calc for move of Player
        if self.moving == True:
    
         # If you moving on Pixel, You have to move to you reach the any mass
         #   print "ugoke!", self.vx, self.vy
            self.rect.move_ip(self.vx, self.vy)
            if self.rect.left % GS == 0 and self.rect.top % GS == 0:                
                self.moving = False
                self.x = self.rect.left / GS
                self.y = self.rect.top / GS

        else:
               
                #self.vecty = self.disty / abs(self.disty)
                #self.vectx = self.distx / abs(self.distx)

                if self.distx == 0 and self.disty > 0:
                    if self.world.is_movable(self.x, self.y+1):
                        self.direction = DOWN
                        self.action = DASH
                        self.animcycle = 12
                        self.vx, self.vy = 0 ,self.speed
                        self.moving = True              
                    
                elif self.distx < 0 and self.disty == 0:
                    if self.world.is_movable(self.x-1, self.y):
                        self.direction = LEFT
                        self.action = DASH
                        self.animcycle = 12
                        self.vx, self.vy = -self.speed, 0
                        self.moving = True
                
                elif self.distx > 0 and self.disty == 0:
                    if self.world.is_movable(self.x+1, self.y):
                        self.direction = RIGHT
                        self.action = DASH
                        self.animcycle = 12
                        self.vx, self.vy = self.speed, 0
                        self.moving = True
                
                elif self.distx == 0 and self.disty < 0:
                    if self.world.is_movable(self.x, self.y-1):
                        self.direction = UP
                        self.action = DASH
                        self.animcycle = 12
                        self.vx, self.vy = 0 ,-self.speed
                        self.moving = True

                elif self.distx > 0 and self.disty < 0:
                    if self.world.is_movable(self.x-1, self.y):
                        self.direction = UP
                        self.action = DASH
                        self.animcycle = 12
                        self.vx, self.vy = 0.7 * self.speed ,-self.speed * 0.7
                        self.moving = True

                elif self.distx < 0 and self.disty < 0:
                    if self.world.is_movable(self.x-1, self.y-1):
                        self.direction = UP
                        self.action = DASH
                        self.animcycle = 12
                        self.vx, self.vy = -self.speed * 0.7 ,-self.speed * 0.7
                        self.moving = True

                elif self.distx > 0 and self.disty > 0:
                    if self.world.is_movable(self.x+1, self.y+1):
                        self.direction = DOWN
                        self.action = DASH
                        self.animcycle = 12
                        self.vx, self.vy = self.speed * 0.7 ,self.speed * 0.7
                        self.moving = True

                elif self.distx < 0 and self.disty > 0:
                    if self.world.is_movable(self.x-1, self.y+1):
                        self.direction = DOWN
                        self.action = DASH
                        self.animcycle = 12
                        self.vx, self.vy = -self.speed * 0.7 ,self.speed * 0.7
                        self.moving = True
                    
           
                else:
                    self.action = STAND
                    self.animcycle = 24


        self.brain.think()
        
            

         # characterAnimation
        self.frame += 1
        self.image = self.images[self.name][self.direction*12 + self.action + self.frame/self.animcycle % 4]


    def fire_at(self, world):
        nextx, nexty = self.x, self.y
        if self.direction == DOWN:
            nexty = self.y + 1
        elif self.direction == LEFT:
            nextx = self.x - 1
        elif self.direction == RIGHT:
            nextx = self.x + 1
        elif self.direction == UP:
            nexty = self.y - 1
        # another character is in that distance??
        entity = world.get_entity(nextx,nexty)
        if entity is not None:
            entity.HitPoint -= self.magic
            print "shit!" + str(entity.HitPoint)

            if entity.HitPoint <= 0:
                entity.alive = False
                self.hit(entity)
            

    def hit(self,entity):

        print "aieeee!"
        if entity.alive == False:
            
            self.world.remove_entity(entity)




    def draw(self,screen,offset):
        """draw a player"""
        offsetx, offsety = offset
        px = self.rect.topleft[0]
        py = self.rect.topleft[1]
        screen.blit(self.image, (px-offsetx,py-offsety))



class Player(GameEntity):

    def __init__(self,world,name, pos, dirl, action):

        #基本クラスのコンストラクタを呼ぶ
        GameEntity.__init__(self,world, name, pos, dirl, action) #このcharacterに名前を、imageに分割したimageを入れる。

        #それぞれのステートのインスタンスを生成する
     #   shot_State = Shooting(self)
     #   reload_State = Reloading(self)


        #ステートマシンのステートを追加する(self.brain)
    #    self.brain.add_states(shot_State)
    #    self.brain.add_states(reload_State)


    def process(self, time_passed):  #時間が進む間常に実行


        self.disty = self.dey - self.y
        self.distx = self.dex - self.x

        """update the state of Player.
        map is necessary to jadge do you move"""

        print self.vx + self.vy
        
        #calc for move of Player
        if self.moving == True:
    
         # If you moving on Pixel, You have to move to you reach the any mass
         #   print "ugoke!", self.vx, self.vy
            self.rect.move_ip(self.vx, self.vy)
            if self.rect.left % GS == 0 and self.rect.top % GS == 0:                
                self.moving = False
                self.x = self.rect.left / GS
                self.y = self.rect.top / GS

        else:

            pressed_keys = pygame.key.get_pressed()
            
            if pressed_keys[K_DOWN]:
                self.direction = DOWN
                if self.world.is_movable(self.x, self.y+1):
                    self.action = DASH
                    self.animcycle = 12
                    self.vx, self.vy = 0 ,self.speed
                    self.moving = True              
                    
            elif pressed_keys[K_LEFT]:
                self.direction = LEFT
                if self.world.is_movable(self.x-1, self.y):
                    self.action = DASH
                    self.animcycle = 12
                    self.vx, self.vy = -self.speed, 0
                    self.moving = True
                
            elif pressed_keys[K_RIGHT]:
                if self.world.is_movable(self.x+1, self.y):
                    self.direction = RIGHT
                    self.action = DASH
                    self.animcycle = 12
                    self.vx, self.vy = self.speed, 0
                    self.moving = True
                    
            elif pressed_keys[K_UP]:
                if self.world.is_movable(self.x, self.y-1):
                    self.direction = UP
                    self.action = DASH
                    self.animcycle = 12
                    self.vx, self.vy = 0 ,-self.speed
                    self.moving = True

            elif pressed_keys[K_UP] and pressed_keys[K_RIGHT]:
                if self.world.is_movable(self.x-1, self.y):
                    self.direction = UP
                    self.action = DASH
                    self.animcycle = 12
                    self.vx, self.vy = self.speed * 1.5 ,-self.speed * 1.5
                    self.moving = True

            elif pressed_keys[K_UP] and pressed_keys[K_LEFT]:
                if self.world.is_movable(self.x-1, self.y-1):
                    self.direction = UP
                    self.action = DASH
                    self.animcycle = 12
                    self.vx, self.vy = -self.speed * 1.5 ,-self.speed * 1.5
                    self.moving = True

            elif pressed_keys[K_DOWN] and pressed_keys[K_RIGHT]:
                if self.world.is_movable(self.x+1, self.y+1):
                    self.direction = DOWN
                    self.action = DASH
                    self.animcycle = 12
                    self.vx, self.vy = self.speed * 1.5 ,self.speed * 1.5
                    self.moving = True

            elif pressed_keys[K_DOWN] and pressed_keys[K_LEFT]:
                if self.world.is_movable(self.x-1, self.y+1):
                    self.direction = DOWN
                    self.action = DASH
                    self.animcycle = 12
                    self.vx, self.vy = -self.speed * 1.5 ,self.speed * 1.5
                    self.moving = True


            elif pressed_keys[K_SPACE]:
                self.action = ATUCK
                self.animcycle = 24

                self.fire_at(self.world)
           
            else:
                self.action = STAND
                self.animcycle = 24


       # self.brain.think()  #これが無いとやっぱり動かないのか？
        
            

         # characterAnimation
        self.frame += 1
        self.image = self.images[self.name][self.direction*12 + self.action + self.frame/self.animcycle % 4]

'''
    def  #ここに攻撃処理を書く予定

'''


        
# キャラクタを作る為の枠組み
class Enemy(GameEntity):

    def __init__(self,world,name, pos, dirl, action):

        #基本クラスのコンストラクタを呼ぶ
        GameEntity.__init__(self,world, name, pos, dirl, action) #このcharacterに名前を、imageに分割したimageを入れる。

        #それぞれのステートのインスタンスを生成する
        patroll_State = Patroll(self)
        return_State = Return(self)
        seek_State = Seeking(self)


        #ステートマシンのステートを追加する(self.brain)
        self.brain.add_states(patroll_State)
        self.brain.add_states(return_State)
        self.brain.add_states(seek_State)



#ステート
        
class Patroll(State):

    def __init__(self, enemy):

        # Stateを初期化するために基本クラスのコンストラクタを呼び出す
        State.__init__(self, "patroll")
        # このStateが変更されるenemyを設定する
        self.enemy = enemy

    def do_actions(self):


        self.enemy.dex = 1
        self.enemy.dey = 9
       # print 'shoot', self.soldier.x, self.soldier.y, self.soldier.px, self.soldier.py, self.soldier.vectx, self.soldier.vecty, self.soldier.moving


    def check_conditions(self):



        player = self.enemy.world.get_close_entity("Player",self.enemy.x, self.enemy.y)
        if player is not None:                             
            self.enemy.player_id = player.id

            print 'みつけたぞ！'
            return "seek"

        if self.enemy.x == self.enemy.dex and self.enemy.y == self.enemy.dey:
            
            print str(self.enemy.name) + str(self.enemy.id) + ':' + 'かえるぞ'
            
            return "return"

        return None


    def entry_actions(self):

        print str(self.enemy.name) + str(self.enemy.id) + ':' + 'やれやれ！'
  #      print 'shoot', self.soldier.x, self.soldier.y, self.soldier.dex, self.soldier.dey, self.soldier.moving


    def exit_actions(self):

        print str(self.enemy.name) + str(self.enemy.id) + ':' + 'いくぞ！！'


class Return(State):

    def __init__(self, enemy):

        # Stateを初期化するために基本クラスのコンストラクタを呼び出す
        State.__init__(self, "return")
        # このStateが変更されるenemyを設定する
        self.enemy = enemy

    def do_actions(self):

        self.enemy.dex = 10
        self.enemy.dey = 10

    def check_conditions(self):

        if self.enemy.x == self.enemy.dex and self.enemy.y == self.enemy.dey:

            return "patroll"

        return None


    def entry_actions(self):

        print str(self.enemy.name) + str(self.enemy.id) + ':' + '敵を見失った'


    def exit_actions(self):

        print str(self.enemy.name) + str(self.enemy.id) + ':' + '補給はOKだ！！'



class Seeking(State):

    def __init__(self, enemy):

        # Stateを初期化するために基本クラスのコンストラクタを呼び出す
        State.__init__(self, "seek")
        # このStateが変更されるキャラを設定する
        self.enemy = enemy
        self.player_id = None

    def do_actions(self):

        #プレイヤーを発見したら、
        player = self.enemy.world.get(self.enemy.player_id)

        if player is not None:
            self.enemy.dex = player.x
            self.enemy.dey = player.y

            if abs(self.enemy.dex - self.enemy.x) <= 1 or abs(self.enemy.dey - self.enemy.y) <= 1:

                self.enemy.fire_at(self.enemy.world)


        
       
       # print 'shoot', self.soldier.x, self.soldier.y, self.soldier.px, self.soldier.py, self.soldier.vectx, self.soldier.vecty, self.soldier.moving


    def check_conditions(self):

        if self.enemy.x == self.enemy.dex and self.enemy.y == self.enemy.dey:
            
            print str(self.enemy.name) + str(self.enemy.id) + ':' + '殲滅完了！'
            
            return "return"

        return None


    def entry_actions(self):

        print str(self.enemy.name) + str(self.enemy.id) + ':' + 'まて！'

  #      print 'shoot', self.soldier.x, self.soldier.y, self.soldier.dex, self.soldier.dey, self.soldier.moving


    def exit_actions(self):

        print str(self.enemy.name) + str(self.enemy.id) + ':' + '任務にもどる！！'






#ゲームの状態管理



class GameState(object):

    def __init__(self, name):

        self.name = name
        

        self.brain = StateMachine()

    def process(self,time_passed):

        self.brain.think()
        



class Mode(GameState):

    def __init__(self):

        #基本クラスのコンストラクタを呼ぶ
        GameState.__init__(self, "mode")

        #それぞれのステートのインスタンスを生成する
        Title_State = TITLE(self)
        Field_State = FIELD(self)
        Win_State = WIN(self)
        Lose_State = LOSE(self)


        #ステートマシンのステートを追加する(self.brain)
        self.brain.add_states(Title_State)
        self.brain.add_states(Field_State)
        self.brain.add_states(Win_State)
        self.brain.add_states(Lose_State)

        self.stable = None
        self.timer = 0




class TITLE(State):

    def __init__(self,mode):

        State.__init__(self, "title")
        self.mode = mode

        self.world = World()

        self.screen = pygame.display.set_mode(SCR_RECT.size) #画面を描画する
        pygame.display.set_caption(u"testbase") #ディスプレイのキャプションをセット


    def do_actions(self):


        self.world.render(self.screen, (0,0) , 2)

        print "Title"


    def check_conditions(self):

        pressed_keys = pygame.key.get_pressed()

        if pressed_keys[K_x]:
            return "field"

        return None

    def entry_actions(self):

        print "welcome"

    def exit_actions(self):

        print "Now Loading"



class FIELD(State):

    def __init__(self, mode):

        State.__init__(self,"field")
        self.mode = mode

        self.world = World()



    def do_actions(self):
        

        for event in pygame.event.get():
            if event.type == QUIT:
                sys.exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                sys.exit()

        time_passed = self.clock.tick(60)

        self.world.process(time_passed)
        offset = calc_offset(self.prisoner)
        self.world.render(self.screen, offset, 1)
    

    def check_conditions(self):

        pressed_keys = pygame.key.get_pressed()

        if self.prisoner.x >= 26 and self.prisoner.y == 1 :
            return "win"

        elif self.prisoner.alive == False:
            return "lose"

        else:

            return None

    def entry_actions(self):

        self.prisoner = Player(self.world,"Player",(2,2),DOWN, 0) #Playerクラスからエンティティ'Arisa'を派生
        self.bot1 = Enemy(self.world,"Enemy", (8,2), DOWN, 0)  #Witchクラスからエンティティ"Rose"を派生
        self.bot2 = Enemy(self.world,"Enemy", (15,10), LEFT, 0)
        self.bot1.brain.set_state("patroll")
        self.bot2.brain.set_state("patroll")

        self.world.add_entity(self.prisoner)
        self.world.add_entity(self.bot1)
        self.world.add_entity(self.bot2)

        self.screen = pygame.display.set_mode(SCR_RECT.size) #画面を描画する
        pygame.display.set_caption(u"testbase") #ディスプレイのキャプションをセット



        #全てのライトのエンティティを追加
        #敵を複数呼び出すのとかに使えるかも
        """
        for Light_no in xrange(Light_COUNT):

            light = Light(self.world)
            light.brain.set_state("ON")
            self.world.add_entity(light) """

        self.clock = pygame.time.Clock()

        print "Game Start"

    def exit_actions(self):

        self.prisoner.alive = True

        #エンティティを全てリセットする処理を作る。

        self.world.entities.clear()
        
        print "Game Over"

class WIN(State):
    
    def __init__(self, mode):

        State.__init__(self,"win")
        self.mode = mode

        self.world = World()

        self.screen = pygame.display.set_mode(SCR_RECT.size) #画面を描画する

    def do_actions(self):

        self.world.render(self.screen, (0,0) , 3)
        
        print "You Win"

    def check_conditions(self):  

        pressed_keys = pygame.key.get_pressed()

        if pressed_keys[K_SPACE]:
            return "title"

        return None

    def entry_actions(self):

        print "Congraturation"

    def exit_actions(self):

        print "fin"


class LOSE(State):
    
    def __init__(self, mode):

        State.__init__(self,"lose")
        self.mode = mode

        self.world = World()

        self.screen = pygame.display.set_mode(SCR_RECT.size) #画面を描画する

    def do_actions(self):

        self.world.render(self.screen, (0,0) , 4)

        print "You Lost"

    def check_conditions(self):

        pressed_keys = pygame.key.get_pressed()

        if pressed_keys[K_SPACE]:
            return "title"

        return None

    def entry_actions(self):

        print "Dont Mind"

    def exit_actions(self):

        print "fin"
   






def run():

    pygame.init()  #pygameをイニシャライズ

    screen = pygame.display.set_mode(SCR_RECT.size) #画面を描画する
    pygame.display.set_caption(u"testbase") #ディスプレイのキャプションをセット
    # load a characterImage
    Player.images["Player"] = split_image(load_image("prisoner.png"))
    Enemy.images["Enemy"] = split_image(load_image("GURD_BOT.png")) #RoseDot2.bmpを分割し、GameEntityから派生したWitchの中のイメージの辞書に格納する。それをcharacterクラスの辞書imagesに"Rose"という名前で保存
    # load a map tip
    World.images[0] = load_image("plate.png")  # 地形用のイメージを読み込む
    World.images[1] = load_image("block.png")  # 壁のイメージを読み込む
    World.images[3] = load_image("door.png")   #ドアのイメージを読み込む

    mode = Mode()
    mode.brain.set_state("title")

    w = 640
    h = 512

    clock = pygame.time.Clock()

 

    while True:


        for event in pygame.event.get():
            if event.type == QUIT:
                sys.exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                sys.exit()

        time_passed = clock.tick(60)

        mode.process(time_passed)

        pygame.display.update()


if __name__ == "__main__":
    run()




        
        
            


        
        
    
