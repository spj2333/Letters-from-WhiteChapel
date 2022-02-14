import os
import random
import copy

from board import Board
from pawn import Pawn
from point import Point

class Node():
    def __init__(self, point: Point, round, path = 0):
        self.point = point

        self.previous = []
        self.next = []

        self.round = round
        self.check = 0


    def addNext(self, node):
        if not node in self.next:
            self.next.append(node)

    def addPrevious(self, node):
        if not node in self.previous:
            self.previous.append(node)


    def __repr__(self):
        return 'Node:【' + str(self.point.number) + '】 R' + str(self.round) + ', [P:' + str([j.point.number for j in self.previous])  + ' N:' + str([j.point.number for j in self.next])+']'


class Agent1():
    def __init__(self, game):
        self.game = game
        self.data = dict()

        self.day = 0
        self.searchedRound = 0

        self.searchedRound_Path = 0
        self.searchedRound_Safe = 0
        self.searchedRound_Clue = 0


    def newDay(self):
        self.day = self.game.day
        self.searchedRound = 0
        self.searchedRound_Path = 0
        self.searchedRound_Safe = 0
        self.searchedRound_Clue = 0

    def addMoveData(self, jackMoveType):

        round = self.game.round

        if not self.day in self.data.keys():
            self.data[self.day] = dict()
            self.data[self.day]['startPoint'] = [self.game.board.jack.getHistoryPoint()[0]]

        if jackMoveType == 'K':
            self.data[self.day]['startPoint'].append(self.game.board.jack.getHistoryPoint()[1])


        # print (self.data)

        # 侦探位置
        policePointList = []
        for police in self.game.board.police:
            policePointList.append(police.getPoint())


        if jackMoveType == 'C':
            # 使用马车，跳过一回合，特殊处理
            round_record = [round-1, round]
            movetype_list = ['','2']
        else:
            round_record = [round]
            movetype_list = ['']



        for index, round in enumerate(round_record):
            # print (index)
            # print (round)
            # round = round_record[index]
            movetype = jackMoveType + movetype_list[index]

            # 开新字典
            if not round in self.data[self.day].keys():
                self.data[self.day][round] = dict()

            # 记录 杰克移动方式
            self.data[self.day][round]['jackMoveType'] = movetype
            # 记录 侦探位置
            self.data[self.day][round]['policePointList'] = policePointList

            # print (self.data)

    def addclueData(self):

        round = self.game.round
        # 侦探本回合结束安全点
        if round > 0:
            self.data[self.day][round]['safePointList'] = self.game.board.policeTodayNoCluePoint

        # 侦探上回合线索点
        if round > 0:
            self.data[self.day][round]['cluePointList'] = self.game.board.policeTodayCluePoint

    def run(self):
        # print(self.data)

        if not self.day in self.data.keys():
            return []

        # 基础 构建possibleNodeList
        # step 1 排除阻挡、安全点，构建轨迹树
        for round in range(self.searchedRound+1, self.game.round+1):
            # print (round)
            # print (self.data[self.day].keys())

            # 没有本轮数据，跳过
            if not round in self.data[self.day].keys():
                continue

            # 搜索一步可达范围，并添加进数据
            if self.searchedRound_Path < round:
                self.oneStep(round)
                # 保存状态
                self.searchedRound_Path = round


            # 遍历所有安全点，在轨迹树中根据本轮的安全点进行减
            if self.searchedRound_Safe < round and 'safePointList' in self.data[self.day][round]:
                # 第round轮的安全点汇总
                safePointList = list()
                if ('safePointList' in self.data[self.day][round].keys()):
                    for j in self.data[self.day][round]['safePointList']:
                        if not j in safePointList:
                            safePointList.append(j)

                # 利用第round轮的安全点，删除路径树上的节点
                for i in range (1, round+1):
                    for node in self.data[self.day][i]['possibleNodeList']:
                        if node.point in safePointList:
                            self.deleteNone(node)

                # 保存状态
                self.searchedRound_Safe = round


            # 根据线索点 删除非法路径
            if self.searchedRound_Clue < round and 'cluePointList' in self.data[self.day][round]:

                # 枝
                # 遍历所有路径，根据线索与安全点排除
                for i in self.data[self.day]['startnodeList']:
                    for path in self.searchPath(i, None, round):
                        # print('检查路径', path)
                        flag = self.checkClue(path, round)
                        # print('线索检查结果', flag)

                        # 如果路径合法，给路径每个节点做标签check = 当前round
                        if flag:
                            for j in path:
                                j.check = round

                # 遍历所有点，删除check没有达到本轮的点
                for r in range(1, round + 1):
                    for node in self.data[self.day][r]['possibleNodeList']:
                        if node.check < r:
                            self.deleteNone(node)

                # 保存状态
                self.searchedRound_Clue = round

        if self.searchedRound_Path == round and self.searchedRound_Safe == round and self.searchedRound_Clue == round:
            self.searchedRound = round

        # print (self.data)

        # 返回每轮结果
        ans = list()
        for round in range(1, self.game.round + 1):
            if (round in self.data[self.day].keys()):
                nodes = self.data[self.day][round]['possibleNodeList']
                points = [node.point for node in nodes]
                ans.append(self.game.board.pointList2Index(points))
        return ans


    # 一步范围，排除警察阻挡，和安全点
    def oneStep(self, round):
        # print (round)
        # print(self.data)

        # 获得起点列表
        if round == 1:
            # 初始，从起点出发
            nodeList = [Node(j, round=0, path=1) for j in self.data[self.day]['startPoint']]
            self.data[self.day]['startnodeList'] = nodeList
        else:
            # 后续，获取前一回合的possibleNodeList
            nodeList = self.data[self.day][round-1]['possibleNodeList']

        # print (nodeList)
        newNodeList = list()
        newNodeList_2 = list()
        # 遍历每个可能的起点列表
        for startNode in nodeList:
            startPoint = startNode.point
            # print('起点', startPoint)

            # 转换为point，搜索合法相邻点

            # 第三天双杀
            if self.data[self.day][round]['jackMoveType'] == 'K':
                # 遍历targetPoint列表

                newNode = Node(startPoint, round=round, path=0)
                newNodeList.append(newNode)

                # 起点节点添加next
                startNode.addNext(newNode)
                newNode.addPrevious(startNode)

                self.data[self.day][round]['possibleNodeList'] = newNodeList



            elif self.data[self.day][round]['jackMoveType'] == 'N':
                # 一层相邻白点
                resultList = startPoint.adjacentWhite
                # 挡路
                resultList = [j for j in resultList if self.checkBlock(startPoint, j, self.data[self.day][round]['policePointList'])]
                # 去重
                targetPoint = list()
                targetPoint = [j for j in resultList if not j in targetPoint]

                # 遍历targetPoint列表
                for newPoint in targetPoint:
                    #如果该层没有这个点，新建；有的话找到直接索引
                    if not newPoint in [j.point for j in newNodeList]:
                        newNode = Node(newPoint, round=round, path=0)
                        newNodeList.append(newNode)
                    else:
                        newNode = [j for j in newNodeList if j.point == newPoint][0]

                    # 起点节点添加next
                    startNode.addNext(newNode)
                    newNode.addPrevious(startNode)

                self.data[self.day][round]['possibleNodeList'] = newNodeList



            elif self.data[self.day][round]['jackMoveType'] == 'A':
                # 小巷相邻
                resultList = startPoint.alley
                # 去重
                targetPoint = list()
                targetPoint = [j for j in resultList if not j in targetPoint]

                # 遍历targetPoint列表
                for newPoint in targetPoint:
                    # 如果该层没有这个点，新建；有的话找到直接索引
                    if not newPoint in [j.point for j in newNodeList]:
                        newNode = Node(newPoint, round=round, path=0)
                        newNodeList.append(newNode)
                    else:
                        newNode = [j for j in newNodeList if j.point == newPoint][0]

                    # 起点节点添加next
                    startNode.addNext(newNode)
                    newNode.addPrevious(startNode)

                self.data[self.day][round]['possibleNodeList'] = newNodeList



            elif self.data[self.day][round]['jackMoveType'] == 'C':
                # 马车第二部 C2直接忽略
                # 一层相邻白点
                resultList = startPoint.adjacentWhite
                # 去重
                targetPoint = list()
                targetPoint = [j for j in resultList if not j in targetPoint]

                # 遍历targetPoint列表
                node_temp = []
                for newPoint in targetPoint:
                    # 如果该层没有这个点，新建；有的话找到直接索引
                    if not newPoint in [j.point for j in newNodeList]:
                        newNode = Node(newPoint, round=round, path=0)
                        newNodeList.append(newNode)
                    else:
                        newNode = [j for j in newNodeList if j.point == newPoint][0]

                    if not newNode in node_temp:
                        node_temp.append(newNode)

                    # 起点节点添加next
                    startNode.addNext(newNode)
                    newNode.addPrevious(startNode)


                # 马车 还要考虑第二步
                for startNode_2 in node_temp:
                    # 第二层层相邻白点
                    resultList = startNode_2.point.adjacentWhite
                    # 去重
                    targetPoint_2 = list()
                    targetPoint_2 = [j for j in resultList if not j in targetPoint_2]
                    # 与起点一致，删除
                    targetPoint_2 = [j for j in targetPoint_2 if j != startNode.point]

                    # 遍历targetPoint列表
                    for newPoint in targetPoint_2:
                        # 如果该层没有这个点，新建；有的话找到直接索引
                        if not newPoint in [j.point for j in newNodeList_2]:
                            newNode = Node(newPoint, round=round+1, path=0)
                            newNodeList_2.append(newNode)
                        else:
                            newNode = [j for j in newNodeList_2 if j.point == newPoint][0]

                        # 起点节点添加next
                        startNode_2.addNext(newNode)
                        newNode.addPrevious(startNode_2)


                self.data[self.day][round+1]['possibleNodeList'] = newNodeList_2
                self.data[self.day][round]['possibleNodeList'] = newNodeList





    # 判断单点是否在安全线索中
    '''
    def checkPointSafe(self, roundNow, targetPoint):

        # 汇总安全点，从今天之后的安全线索
        safePointList = list()
        for round in range(roundNow, self.game.round+1):
            if (round in self.data[self.day].keys()) and ('safePointList' in self.data[self.day][round].keys()):
                for j in self.data[self.day][round]['safePointList']:
                    if not j in safePointList:
                        safePointList.append(j)

        # print('汇总安全点', safePointList)
        # 排除
        targetPoint = [j for j in targetPoint if not j in safePointList]
        # print('排除安全点', targetPoint)

        return targetPoint
    '''

    # 删除节点
    def deleteNone(self, node):
        # print('删除节点', node)
        for nextNode in node.next:
            # print('删除next循环', nextNode)

            nextNode.previous = [j for j in nextNode.previous if j != node]
            # print('处理完毕', nextNode)
            # print('处理完毕', nextNode.previous)
            if len(nextNode.previous) == 0:
                self.deleteNone(nextNode)

        for previousNode in node.previous:
            previousNode.next = [j for j in previousNode.next if j != node]
            if len(previousNode.next) == 0:
                self.deleteNone(previousNode)

        round = node.round
        if round > 0 :
            self.data[self.day][round]['possibleNodeList'] = [j for j in self.data[self.day][round]['possibleNodeList'] if j != node]
        self.previous = []
        self.next = []
        del self

    # 查询每天的线索，根据线索排除路径
    def checkClue(self, path, round):
        if not round in self.data[self.day].keys():
            return True

        # 第round轮的线索汇总
        if 'cluePointList' in self.data[self.day][round]:
            culePointList = self.data[self.day][round]['cluePointList']
            # print('线索汇总', culePointList)

            # 第round轮搜出来的线索，需要在1-round轮踩到
            pathPoints = [j.point for j in path[:round+1]]
            # print ('截取路径', pathPoints)

            #有一个线索不在，则返回F
            for clue in culePointList:
                if not clue in pathPoints:
                    return False

        return True

    #DFS搜索所有路径
    def searchPath(self, nowNode, base, round):

        nextList = nowNode.next
        if base == None:
            newbase = [nowNode]
        else:
            newbase = base + [nowNode]

        if (len(nextList) > 0) and (len(newbase)-1<round):
            for i in nextList:
                yield from self.searchPath(i, newbase, round)

        else:
            yield newbase

    def deletePath(self, path):
        node = path[-1]


    '''
    def deletePath(self, path):
        print('删除路径', path)

        # 向后遍历，都是单入
        s = len(path) - 1
        for i in range(len(path)):
            if len(path[i].previous) > 1:
                s = i - 1
                break

        # 向前遍历，都是单出
        t = 0
        for j in range(len(path))[::-1]:
            if len(path[j].next) > 1:
                t = j + 1
                break

        print(t, s)
        # 删除中间的t--s
        if s>=t:

            print('断链')
            if t > 0:
                path[t - 1].next = [j for j in path[t - 1].next if j != path[t]]
            if s < len(path) - 1:
                path[s + 1].previous = [j for j in path[s + 1].previous if j != path[s]]


            for i in range(t,s+1):
                print (i)
                nowNode = path[i]
                print ('删除', nowNode)

                #取消这个节点从possibleNodeList
                print ('删除前', self.data[self.day][i]['possibleNodeList'])
                self.data[self.day][i]['possibleNodeList'] = [j for j in self.data[self.day][i]['possibleNodeList'] if j != nowNode]
                print ('删除后', self.data[self.day][i]['possibleNodeList'])
                # 删除节点

                print ('节点实例删除')
                del nowNode

    '''


    '''
    # 一步范围，排除警察阻挡
    def oneStep(self, round):
        if round == 1:
            nowPointList = [self.data[self.day]['startPoint']]
        else:
            nowPointList = self.data[self.day][round-1]['possiblePointList']

        #遍历前一天所有可能位置作为起点，走一步的位置
        # print ('起点', nowPointList)

        ans = list()
        for i in nowPointList:
            # print('起点', i)
            resultList = i.adjacentWhite #一层相邻白点
            # print('一层相邻白点', resultList)
            resultList = [j for j in resultList if self.checkBlock(i, j, self.data[self.day][round]['policePointList'])]
            # print('过滤警察挡路', resultList)
            resultList = [j for j in resultList if not j in ans]
            # print('去重', resultList)
            ans += resultList

        #从今天之后的安全线索，删掉排除的位置
        # 汇总安全点
        if 'safePointList' in self.data[self.day][round].keys():
            safePointList = list()
            for round in range(round, self.game.round):
                for j in self.data[self.day][round]['safePointList']:
                    if not j in safePointList:
                        safePointList.append(j)

            # print('汇总安全点', safePointList)
            # 排除
            ans = [j for j in ans if not j in safePointList]
            # print('排除安全点', ans)

        return ans
    '''

    # 查询警察堵路 能通：True
    def checkBlock(self, point1:Point, point2:Point, policePointList):
        adj = point1.adjacent
        if point2 in adj:
            return True

        done = []
        new = [i for i in adj if ( (i.checkBlack()) and (not i in policePointList) and (not i in done))]
        while len(new) > 0:
            this = new[0]
            adj = this.adjacent
            if point2 in adj:
                return True
            new += [i for i in adj if (
                        (i.checkBlack()) and (not i in policePointList) and (not i in done) and (
                    not i in new))]

            done.append(this)
            del new[0]

        return False


if __name__ == '__main__':
    agent1 = Agent1(None)

    n1 = Node(Point(1))
    n2 = Node(Point(2))
    n3 = Node(Point(3))
    n4 = Node(Point(4))
    n5 = Node(Point(5))
    n6 = Node(Point(6))
    n1.next = [n2, n3]
    n2.next = [n4, n5]
    n3.next = [n5, n6]


    for i in agent1.searchPath(n1, None):
        print (i)
