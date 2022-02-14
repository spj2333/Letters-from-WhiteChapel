
import os
from board import Board
from agent1 import Agent1
import random

class Game():
    def __init__(self, gameID):
        self.init = True
        self.gameID = gameID
        self.fin = False
        self.saved = False

        path_map = os.path.join('static', 'mapdata', 'map.txt')
        path_alley = os.path.join('static', 'mapdata', 'alley.txt')
        self.board = Board(path_map, path_alley)

        self.jackPlayerName = ''
        self.policePlayerName = ''
        self.home = None # Point Class

        self.day = 0
        self.round = 0
        self.turn = 0
        self.round_wait = 0

        self.carriage = 0
        self.alley = 0

        self.tragedyNeedSelected = [0, 5, 4, 3, 1]
        self.tragedyAllNumber = [0, 8, 7, 6, 4]

        self.maxCarriage = [0, 3, 2, 2, 1]
        self.maxAlley = [0, 2, 2, 1, 1]

        self.moveLog = list()
        self.historyData = dict()

        # 游戏结果 + 杰克胜利  - 侦探胜利
        # +1 侦探投降 +2 杰克4天回家
        # -1 杰克投降 -2 杰克被抓 -3 杰克时间耗尽
        self.gameResult = 0 #

        self.cmdWaiting = [
            ['', '杰克', '侦探', '侦探', '杰克', '侦探', '杰克', ],
            ['', '杰克', '侦探', '侦探', '侦探', '侦探']
        ]

        # 辅助系统
        self.agent1 = Agent1(self)
        self.agent1_on = False


    def setJackplayerName(self, name):
        self.jackPlayerName = name

    def getJackplayerName(self):
        return self.jackPlayerName

    def setPoliceplayerName(self, name):
        self.policePlayerName = name

    def getPoliceplayerName(self):
        return self.policePlayerName

    def setHome(self, number):
        point_home = self.board.number2point(number)
        self.home = point_home

    def checkGameStart(self):
        return self.day>0

    #侦探加入 游戏开始
    def gameStart(self):
        # 进入第一天初始设置
        self.enterNewDay()

    
    def getgamettl(self):
        if self.db.exists('gameid') > 0:
            return self.db.ttl('gameid') 
        else:
            return 0
    

    # 游戏指令处理
    def cmd(self, cmd):
        # print ('CMD: '+cmd)
       

        day = self.day
        round = self.round
        turn = self.turn
        
        # print (day, round, turn)   
        if (self.gameResult != 0):
            textinfo = '游戏已结束。（请回到登录界面）'
            return self.zipMessage(0, textinfo)
        
        if cmd == 'GG':
            if turn in [1 ,4, 6]:
                textinfo = '杰克投降。游戏结束，侦探胜利。（请回到登录界面）'
                self.gameResult = -1
                self.turn = -2
                self.gameEnd()
            elif turn in [2 ,3, 5]:
                textinfo = '侦探投降，游戏结束，杰克胜利。（请回到登录界面）'
                self.gameResult = +1
                self.turn = -1
                self.gameEnd()
            else:
                 textinfo = '错误：自己回合才能投降'
              
            return self.zipMessage(0, textinfo)

            
        cmd = cmd.split('-')
        textinfo = '行动完毕'

        # 设置初始位置
        if round == 0:

            # 杰克初始
            if turn == 1:

                if len(list(set(cmd))) != self.tragedyNeedSelected[int(day)]:
                    return self.zipMessage(1, '错误：需要选择' + str(self.tragedyNeedSelected[int(day)]) + '个案发地点')
                
                for index in cmd:
                    # point = self.board.number2point(number)
                    point = self.board.index2point(index)
                    if not point.checkMurder():
                        return self.zipMessage(1, '错误：一个点不是案发现场')
                    if self.checkDuplicateMurderPoint(point):
                        return self.zipMessage(1, '错误：一个案发现场已经使用')
                        
                for index in cmd:
                    # index = self.board.number2index(number)
                    self.board.newTragedy(index)
                    # self.board.tragedySelectPoint.append(point)

                textinfo = '杰克调查目标完毕'

            # 补选2警局 只发生在第二天之后
            elif turn == 2:

                if len(list(set(cmd))) != 2:
                    return self.zipMessage(1, '错误：需要2个位置')


                point_list = [self.board.index2point(i) for i in cmd]
                for point in point_list:
                    if ((not point.checkStation()) or point.checkPawn()):
                        return self.zipMessage(1, '错误：只能选择空警局')

                self.board.changePoliceSelectPoint(point_list[0], point_list[1])
                textinfo = '侦探选择调回警局完毕'

            # 警察 7选5
            elif turn == 3:
                
                if len(list(set(cmd))) != 5:
                    return self.zipMessage(1, '错误：需要5个位置')

                indexlist = self.board.pointList2Index(self.board.policeSelectPoint)
                for index in cmd:
                    if not int(index) in indexlist:
                        return self.zipMessage(1, '错误：只能从7个预定位置中选')

                for i, index in enumerate(cmd):

                    point = self.board.index2point(index)
                    self.board.police[i].clearHistoryPoint()
                    self.board.police[i].forceMoveTo(point)

                textinfo = '侦探巡逻位置设置完毕'    


            # 杰克 击杀or等待
            elif turn == 4:
                if len(cmd[0])<1 or cmd[0] == 'PASS':
                    #杰克选择跳过

                    if self.round_wait >= 4:
                        return self.zipMessage(1, '错误：等待次数用尽，必须击杀')

                    self.board.clearTragedyAP()
                    self.round_wait += 1
                    newturn = 5
                    textinfo = '杰克选择等待'

                else:

                    # 非第三天
                    if self.day != 3:
                        if len(list(set(cmd))) != 1:
                            return self.zipMessage(1, '错误：需要1个位置击杀或等待')

                        # indexlist = self.board.pawnList2Index(self.board.tragedySelectPawn)
                        index = int(cmd[0])
                        # index = self.board.number2index(number)

                        targetTragedy = None
                        for tragedy in self.board.tragedySelectPawn:
                            # print (tragedy.getIndex())
                            # print (index)
                            if tragedy.getIndex() == index:
                                targetTragedy = tragedy
                                break

                        if targetTragedy == None:
                            return self.zipMessage(1, '错误：只能选无辜的人击杀')

                        # 记录原始击杀红点
                        self.board.killedPoint.append(targetTragedy.bornPoint)
                        # 杰克移动至无辜的人地点
                        self.board.jackMove(targetTragedy.point)
                        # 给线索
                        self.board.police[0].addClue(targetTragedy.point)
                        #
                        for i in range(4 - int(self.round_wait)):
                            self.moveLog.append('-')
                        self.moveLog.append(targetTragedy.point.number)

                        # 移除悲剧的人
                        self.board.removeTragedy()



                        newturn = 7
                        textinfo = '杰克选择击杀'

                    # 第三天
                    else:
                        if len(list(set(cmd))) != 2:
                            return self.zipMessage(1, '错误：需要2个位置击杀或等待')

                        # indexlist = self.board.pawnList2Index(self.board.tragedySelectPawn)

                        # index1 = self.board.number2index(cmd[0])
                        index1 = int(cmd[0])
                        # index2 = self.board.number2index(cmd[1])
                        index2 = int(cmd[1])

                        targetTragedy1 = None
                        targetTragedy2 = None
                        for tragedy in self.board.tragedySelectPawn:
                            if tragedy.getIndex() == index1:
                                targetTragedy1 = tragedy
                            if tragedy.getIndex() == index2:
                                targetTragedy2 = tragedy

                        if targetTragedy1 == None or targetTragedy2 == None :
                            return self.zipMessage(1, '错误：只能选无辜的人击杀')

                        # 记录原始击杀红点
                        self.board.killedPoint.append(targetTragedy1.bornPoint)
                        self.board.killedPoint.append(targetTragedy2.bornPoint)
                        # 杰克移动至无辜的人地点
                        self.board.jackMove(targetTragedy1.point)
                        self.board.jackMove(targetTragedy2.point)
                        # 给线索
                        self.board.police[0].addClue(targetTragedy1.point)
                        self.board.police[0].addClue(targetTragedy2.point)
                        #
                        for i in range(4 - int(self.round_wait)):
                            self.moveLog.append('-')

                        number1 = min(targetTragedy1.point.number, targetTragedy2.point.number)
                        number2 = max(targetTragedy1.point.number, targetTragedy2.point.number)
                        self.moveLog.append(str(number1)+'/'+str(number2))
                        self.moveLog.append(str(number1)+'/'+str(number2))

                        # 移除悲剧的人
                        self.board.removeTragedy()

                        newturn = 7
                        textinfo = '杰克选择双杀'

            # 侦探 操作无辜的人
            elif turn == 5:
                if len(cmd)<1 or cmd[0] == 'PASS':
                    #侦探结束移动
                    textinfo = '侦探结束移动受害者'
                else:
                    if len(list(set(cmd))) != 2:
                        return self.zipMessage(1, '错误：需要2个位置')
                    # print(cmd)
                    point0 = self.board.index2point(cmd[0])
                    point1 = self.board.index2point(cmd[1])
                    # print(point0, point1)
                    target_tragedy = None
                    for tragedy in self.board.tragedySelectPawn:
                        # print(tragedy)
                        if point0 == tragedy.point:
                            target_tragedy = tragedy
                    if target_tragedy == None:
                        return self.zipMessage(1, '错误：需要选择受害者')

                    #已经移动
                    if target_tragedy.AP > 0:
                        return self.zipMessage(1, '错误：该受害者已经移动过')
                    if point1.pawn != None:
                        return self.zipMessage(1, '错误：目标点已被占')
                    # 警察阻挡
                    if not self.board.checkJackNotBlock(point0, point1):
                        return self.zipMessage(1, '错误：受害者不能穿越侦探')
                    # 相邻判断
                    if not (point1 in point0.adjacentWhite):
                        return self.zipMessage(1, '错误：受害者移动目标不相邻')
                    # 已使用现场
                    if point1 in self.board.killedPoint:
                        return self.zipMessage(1, '错误：受害者不能移动到已使用现场')
                    # 相邻判断
                    for police in self.board.police:
                        if point1 in police.point.adjacent:
                            return self.zipMessage(1, '错误：受害者不能移动到侦探相邻点')

                    target_tragedy.AP = 2
                    target_tragedy.forceMoveTo(point1)
                    textinfo = '侦探移动受害者'
                    return self.zipMessage(0, textinfo)

            # 杰克 查看警察
            elif turn == 6:
                if len(list(set(cmd))) != 1:
                    return self.zipMessage(1, '错误：需要1个位置')

                targetPoint = self.board.index2point(cmd[0])
                flag = 0
                for point in self.board.policeSelectPoint:
                    if targetPoint == point:
                        flag = 1

                        break

                if flag == 0:
                    return self.zipMessage(1, '错误：需要选择一个侦探位置')
                else:

                    for police in self.board.police:
                        if police.point == targetPoint:
                            police.visible = True

                    self.board.deleteAPoliceSelectPoint(targetPoint)
                textinfo = '杰克探查侦探位置'

        else:
            # 杰克行动
            if turn == 1:
                #杰克行动
                now_point = self.board.jack.point

                #特殊移动小巷
                if cmd[0] == 'A':

                    # 小巷数量检查
                    if int(self.alley) <= 0:
                        return self.zipMessage(1, '错误：杰克小巷数量不足')
                    #回家检查
                    if 'H' in cmd:
                        return self.zipMessage(1, '错误：杰克使用特殊移动时不能回家')

                    #小巷
                    # target_point = self.board.number2point(cmd[1])
                    target_point = self.board.index2point(cmd[1])

                    #小巷移动规则检查
                    if not target_point in now_point.alley:
                        return self.zipMessage(1, '错误：无法使用小巷到目标点')
                        
                    self.alley -= 1

                    #杰克移动
                    self.board.jackMove(target_point)
                    self.moveLog.append('小巷')

                    textinfo = '杰克使用小巷移动一步'
                    # 传数据到辅助系统
                    if self.agent1 != None:
                        self.agent1.addMoveData('A')

                # 特殊移动马车
                elif cmd[0] == 'C':
                    # 马车数量检查
                    if int(self.carriage) <= 0:
                        return self.zipMessage(1, '错误：杰克马车数量不足')
                    # 马车步数检查
                    if len(list(set(cmd))) < 3:
                        return self.zipMessage(1, '错误：杰克使用马车应移动两步')
                    # 回家检查
                    if 'H' in cmd:
                        return self.zipMessage(1, '错误：杰克使用特殊移动时不能回家')
                        
                    #马车
                    # target_point1 = self.board.number2point(cmd[1])
                    # target_point2 = self.board.number2point(cmd[2])
                    target_point1 = self.board.index2point(cmd[1])
                    target_point2 = self.board.index2point(cmd[2])

                    
                    # 马车调头检查
                    if now_point == target_point2:
                        return self.zipMessage(1, '错误：杰克使用马车不能回头')
                        
                    # 相邻判断
                    if not (target_point1 in now_point.adjacentWhite):
                        return self.zipMessage(1, '错误：杰克马车第一步使用位置不相邻')
                    if not (target_point2 in target_point1.adjacentWhite):
                        return self.zipMessage(1, '错误：杰克马车第二步使用位置不相邻')
                        
                    # 成功使用马车
                    self.carriage -= 1
                    self.board.jackMove(target_point1)
                    self.moveLog.append('马车--')

                    self.round += 1
                    self.board.jackMove(target_point2)
                    self.moveLog.append('--马车')

                    textinfo = '杰克使用马车移动两步'
                    # 传数据到辅助系统
                    if self.agent1 != None:
                        self.agent1.addMoveData('C')

                # 普通移动
                else:
                    if cmd[0] == 'H':
                        returnHome = True
                        target_point = self.board.index2point(cmd[1])
                    else:
                        returnHome = False
                        target_point = self.board.index2point(cmd[0])

                    # print (now_point)
                    # print (now_point.adjacent)
                    # print (target_point)
                    # 相邻判断
                    if not (target_point in now_point.adjacentWhite):
                        return self.zipMessage(1, '错误：杰克移动目标不相邻')
                    # 警察阻挡
                    if not self.board.checkJackNotBlock(now_point, target_point):
                        return self.zipMessage(1, '错误：杰克不能穿越侦探')
                    
                    # 成功移动一步    
                    self.board.jackMove(target_point)
                    self.moveLog.append('移动')

                    textinfo = '杰克移动一步'
                    # 传数据到辅助系统
                    if self.agent1 != None:
                        self.agent1.addMoveData('N')
                    
                    # 普通移动 宣布回家
                    if returnHome:
                        # print (str(target_index), self.db.load('home'))
                        if target_point == self.home:
                            
                            self.turn = 5
                            textinfo = '杰克移动一步，并宣告回家'
                            
                            # 杰克胜利
                            if self.day == 4:
                                textinfo = '杰克移动一步，并宣告回家。游戏结束，杰克胜利。（请回到登录界面）'
                                self.gameResult = +2
                                self.turn = -1
                                self.gameEnd()

                            return self.zipMessage(0, textinfo)
                   
                   
                # 15回合到
                if self.round >= 15+self.round_wait:
                    textinfo = '杰克没有在规定回合内回家。游戏结束，侦探胜利。（请回到登录界面）'
                    self.gameResult = -3
                    self.turn = -2
                    self.gameEnd()
                    return self.zipMessage(0, textinfo)

            # 侦探移动
            elif turn == 2:

                if len(cmd)<1 or cmd[0] == 'PASS':
                    #侦探结束移动
                    textinfo = '侦探结束移动阶段'

                elif len(cmd) == 1:
                    return self.zipMessage(1, '错误：未选择目标')

                else:
                    #侦探移动
                    policeid = cmd[0]
                    if not policeid in ['A','B','C','D','E']:
                        return self.zipMessage(1, '错误：侦探编号错误')

                    police = self.board.id2Police[policeid]

                    if int(police.AP) >=2 :
                        return self.zipMessage(1, '错误：侦探移动达到上限')
                    
                    now_point = police.point
                    
                    if len(cmd) == 2:  
                        target_point = self.board.index2point(cmd[1])
                        
                        # print ('侦探当前：' + str(now_index))
                        # print ('侦探移动目标：' + str(target_index))
                        
                        # 侦探移动到白点
                        if target_point.checkWhite():
                            return self.zipMessage(1, '错误：侦探无法移动到白点')
                        # 相邻判断
                        if not target_point in now_point.adjacentBlack:
                            return self.zipMessage(1, '错误：侦探移动目标不相邻')
                        # 相撞
                        if target_point.checkPawn():
                            return self.zipMessage(1, '错误：目标位置有另一个侦探')
                        
                        # 侦探正常移动
                        self.board.policeMove(police, target_point)
                        police.AP += 1

                        textinfo = police.name+'移动一步'
                        return self.zipMessage(0, textinfo)
                        
                    elif len(cmd) == 3:
                        target_point1 = self.board.index2point(cmd[1])
                        target_point2 = self.board.index2point(cmd[2])
                        
                        #侦探行动力检查

                        if police.AP >= 1 :
                            return self.zipMessage(1, '错误：该侦探仅剩余一步')
                        # 侦探移动到白点
                        if target_point1.checkWhite() or target_point2.checkWhite():
                            return self.zipMessage(1, '错误：侦探无法移动到白点')
                        # 相邻判断
                        if not target_point1 in now_point.adjacentBlack:
                            return self.zipMessage(1, '错误：侦探移动第一步不相邻')
                        if not target_point2 in target_point1.adjacentBlack:
                            return self.zipMessage(1, '错误：侦探移动第二步不相邻')
                        # 相撞
                        if target_point2.checkPawn():
                            return self.zipMessage(1, '错误：目标位置有另一个侦探')
                                
                        # 侦探正常移动
                        self.board.policeMove(police, target_point2)
                        police.AP += 2
                        # self.updatePoliceIndex(policeid, target_index2)
                        # self.db.save('policeaction'+policeid, int(self.db.load('policeaction'+policeid))+2)
                        textinfo = police.name+'移动两步'
                        return self.zipMessage(0, textinfo)

            # 侦探调差抓捕
            elif turn == 3:

                # print (cmd)

                if len(cmd)<1 or cmd[0] == 'PASS':
                    #侦探结束调查
                    textinfo = '侦探结束调查阶段'


                elif len(cmd) == 1 or cmd[0] == 'SA':
                    #快搜

                    # 已有的线索列表
                    clues = list()
                    for police in self.board.police:
                        clues += police.clues

                    for police in self.board.police:
                        if police.AP >= 2:
                            continue

                        police.AP = 2

                        # 侦探相邻点
                        now_point = police.point
                        target_points = [i for i in now_point.adjacent if (i.checkWhite() and not (i in clues))]

                        # print (target_points)
                        # 检查是否有线索

                        flag = False
                        getClue = list()
                        for i in target_points:
                            if i in self.board.jack.getHistoryPoint():
                                flag = True
                                getClue.append(i)

                        if flag:
                            # 有线索，随机显示一个
                            ranPoint = random.choice(getClue)
                            police.addClue(ranPoint)
                            self.board.addTodayCluePoint(ranPoint)

                        else:
                            # 无线索，显示所有
                            for i in target_points:
                                self.board.addTodayNoCluePoint(i)

                    # 结束回合
                    textinfo = '侦探使用快速搜索结束调查阶段'


                elif len(cmd) == 1:
                    return self.zipMessage(1, '错误：未选择目标')

                else:
                    #侦探调查线索
                    policeid = cmd[0]
                    if not policeid in ['A', 'B', 'C', 'D', 'E']:
                        return self.zipMessage(1, '错误：侦探编号错误')

                    police = self.board.id2Police[policeid]

                    if int(police.AP) >= 2:
                        return self.zipMessage(1, '错误：侦探行动达到上限')

                    now_point = police.point

                    if len(cmd) == 3 and cmd[-1] == 'R':  
                        #抓捕 
                        if int(police.AP) == 1:
                            return self.zipMessage(1, '错误：侦探已经搜查，不能抓捕')

                        target_point = self.board.index2point(cmd[1])

                        # 相邻判断
                        if not target_point in now_point.adjacent:
                            return self.zipMessage(1, '错误：抓捕目标不相邻')

                                      
                        if self.board.jack.point == target_point:
                            #抓到
                            textinfo = police.name+'成功抓捕杰克。游戏结束，侦探胜利。（请回到登录界面）'
                            self.gameResult = -2
                            self.turn = -2
                            self.gameEnd()
                            return self.zipMessage(0, textinfo)
                            
                        else:
                            #未抓到
                            police.AP = 2
                            textinfo = police.name+'抓捕失败:'+ str(target_point.number)
                            return self.zipMessage(0, textinfo)
                        
                    else:
                        #调查
                        target_point_list = [self.board.index2point(i) for i in cmd[1:]]
                        # print (target_point_list)
                        for target_point in target_point_list:
                            if not target_point in now_point.adjacent:
                                return self.zipMessage(1, '错误：搜查目标不相邻')


                        for target_point in target_point_list:
                            if target_point in self.board.jack.getHistoryPoint():
                                #查到
                                police.AP = 2
                                police.addClue(target_point)
                                self.board.addTodayCluePoint(target_point)
                                textinfo = police.name+'查到线索:'+ str(target_point.number)
                                return self.zipMessage(0, textinfo)
                                
                            else:    
                                #未查到
                                self.board.addTodayNoCluePoint(target_point)
                                police.AP = 1
                                
                        textinfo = police.name+'未查到线索:'+', '.join([ str(target_point.number) for target_point in target_point_list ])

                        
                        return self.zipMessage(0, textinfo)

            # 杰克已经回家，进入新一天
            elif turn == 5:

                #self.saveDay()
                self.enterNewDay()
                self.board.clearTodayNoCluePoint()
                self.board.clearTodayCluePoint()
                textinfo = '进入新的一天'
                return self.zipMessage(0, textinfo)

            # 游戏已经结束
            elif turn in [-1, -2]:

                textinfo = '游戏已结束'
                return self.zipMessage(0, textinfo)


        # 下一步准备
        if round == 0:
            #布置
            if turn == 1:
                if day == 1:
                    # self.police_hide_index = self.policestation[:]
                    self.board.policeSelectPoint = self.board.policeStationPoint
                    self.turn = 3
                else:
                    self.turn = 2
            elif turn == 2:
                self.turn = 3
            elif turn == 3:
                self.turn = 4
            elif self.turn == 4:
                if newturn == 5:
                    self.turn = 5
                else:
                    self.round += 1
                    if self.day != 3:
                        self.turn = 1
                    else:
                        self.turn = 2
                        # 传数据到辅助系统
                        if self.agent1 != None:
                            self.agent1.addMoveData('K')

            elif self.turn == 5:
                self.turn = 6

            elif self.turn == 6:
                self.turn = 4
        else:
            #行动
            self.board.clearPoliceAP()
            if turn == 1:
                self.turn = 2
                self.board.clearTodayNoCluePoint()
                self.board.clearTodayCluePoint()
            elif turn == 2:
                self.turn = 3
            else:
                # 传数据到辅助系统
                if self.agent1 != None:
                    self.agent1.addclueData()

                self.turn = 1
                self.round += 1
        
        return self.zipMessage(0, textinfo)


    # 打包发给前台消息
    # subject: 0 所有 1 当前玩家（错误警告）
    def zipMessage(self, subject=0, message=''):
        return [subject, message]



    # 检查点是否在killed列表
    def checkDuplicateMurderPoint(self, point):
        # path = self.db.loadlist('killedpos')
        return point in self.board.killedPoint

    #保存一天数据
    def saveDayData(self):
        ans = []
        ans.append(self.moveLog)
        ans.append(self.board.jack.getHistoryIndex())
        for police in self.board.police:
            ans.append(police.getHistoryIndex())
            ans.append(police.getHistoryClue())
        
        self.historyData[self.day] = ans

    #进入新的一天
    def enterNewDay(self):

        # 保存这一天的数据
        if self.day > 0:
            self.saveDayData()

        self.day += 1
        self.round = 0
        self.turn = 1
        self.round_wait = 0

        self.carriage = self.maxCarriage[self.day]
        self.alley = self.maxAlley[self.day]

        self.moveLog = list()

        if self.day >= 2:
            policePoint_list = [i.point for i in self.board.police]
            self.board.newDay(policePoint_list)
        else:
            self.board.newDay()

        # 传数据到辅助系统
        if self.agent1 != None:
            self.agent1.newDay()


    #游戏面板数据打包，发送前台
    def sumBoardInfo(self, jack = True):
        ans = dict()
        ans['day'] = self.day
        ans['round'] =  self.round
        ans['turn'] =  self.turn


        ans['carriage'] = self.carriage
        ans['alley'] = self.alley

        if self.day<1:
            return ans

        # 受害者
        if self.round == 0 and self.turn > 3:
            ans['tragedySelectPoint'] = []
            for tragedy in self.board.tragedySelectPawn:
                ans['tragedySelectPoint'].append(tragedy.getIndex())

        # 警察幻影
        if self.round == 0 and self.turn > 2:
            ans['policeSelectPoint'] = self.board.pointList2Index(self.board.policeSelectPoint)


        # 杰克玩家信息
        if jack or self.turn < 0:
            ans['home'] =  self.home.index
            ans['jackpos'] =  self.board.jack.getHistoryIndex()
            ans['jacknowpos'] = self.board.jack.getIndex()


        for policePawn in self.board.police:
            if self.round > 0 or self.turn <= 2 or policePawn.visible:
                policeID = policePawn.id
                # ans['policepos'+policeID] =  policePawn.getHistoryIndex()
                ans['clue'+policeID] =  self.board.pointList2Index(policePawn.clues)
                ans['policeposition'+policeID] =  policePawn.getIndex()
                ans['policeaction'+policeID] =  policePawn.AP
            
        # ans['police_hide_index'] = self.police_hide_index

        # 今夜无线索位置
        ans['noCluePoint'] = self.board.pointList2Index(self.board.policeTodayNoCluePoint)

        # 历史击杀位置
        ans['killedPoint'] = self.board.pointList2Index(self.board.killedPoint)

        # 游戏底部记录条
        ans['moveLog'] = self.moveLog

        return ans

        # 游戏结束

    def gameEnd(self):
        self.saveDayData()
        self.fin = True

        pass
        # self.saveDay()
        # self.db.save('history' + str(self.gamenumber).zfill(5), self.history)
        # self.setExpire(self.gameEndTime)

    #-----------------------

    def startAgent1(self):
        pass




if __name__ == '__main__':
    game = Game(None)
    d = {}
    for index in game.board.map:
        point = game.board.map[index]
        if point.checkWhite():
            number = point.number
            level = len(point.adjacentWhite)
            if not level in d:
                d[level] = [number]
            else:
                d[level].append(number)
            # print (number, level)
    for i in range(20):
        if i in d.keys():

            print (i)
            print (sorted(d[i]))
    # print (d)