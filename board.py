
from pawn import Pawn
from point import Point
import random

BLACK = 1
WHITE = 0

class Board():

    def __init__(self, mapPath, alleyPath):

        #加载棋盘点
        self.map, self.map_number2index, self.policeStationPoint = self.initMapData(mapPath)
        self.initAlleyData(alleyPath)
        self.initAdjacentBlack()

        # 已经击杀位置
        self.killedPoint = []

        #杰克选择目标
        self.tragedySelectPawn = []

        #侦探所有选择位置 7个
        self.policeSelectPoint = []

        #今夜无线索位置
        self.policeTodayNoCluePoint = []

        #今夜线索位置
        self.policeTodayCluePoint = []

    def clearPoliceAP(self):
        for police in self.police:
            police.AP = 0

    def clearTragedyAP(self):
        for tragedy in self.tragedySelectPawn:
            tragedy.AP = 0

    def changePoliceSelectPoint(self, point1:Point, point2:Point):
        self.policeSelectPoint = []
        for police in self.police:
            self.policeSelectPoint.append(police.point)
        self.policeSelectPoint.append(point1)
        self.policeSelectPoint.append(point2)
        # print(self.policeSelectPoint)
        random.shuffle(self.policeSelectPoint)
        # print(self.policeSelectPoint)

    def deleteAPoliceSelectPoint(self, point:Point):
        if point in self.policeSelectPoint:
            self.policeSelectPoint.remove(point)


    def addTodayNoCluePoint(self, point):
        if not point in self.policeTodayNoCluePoint:
            self.policeTodayNoCluePoint.append(point)

    def clearTodayNoCluePoint(self):
        self.policeTodayNoCluePoint = []

    def addTodayCluePoint(self, point):
        if not point in self.policeTodayCluePoint:
            self.policeTodayCluePoint.append(point)

    def clearTodayCluePoint(self):
        self.policeTodayCluePoint = []

    # 加载新棋子
    def newDay(self, policeStartPoint = None):
        self.jack = Pawn(0)
        self.police = list()
        self.id2Police = dict()
        policename = ['-','A','B','C','D','E']
        for i in [1, 2, 3, 4, 5]:
            p = Pawn(i)
            self.police.append(p)
            self.id2Police[policename[i]] = p
            p.id = policename[i]

        # 第二天之后，警察有初始位置
        if policeStartPoint != None:
            for i, police in enumerate(self.police):
                police.forceMoveTo(policeStartPoint[i])


        self.moveLog = list()

    def newTragedy(self, index):
        pawn = Pawn(6)
        point = self.index2point(index)
        pawn.forceMoveTo(point)
        pawn.bornPoint = point
        self.tragedySelectPawn.append(pawn)
        self.bornPoint = point

    def jackMove(self, point):
        self.jack.forceMoveTo(point)

    def policeMove(self, police, point):
        police.forceMoveTo(point)

    # def getJackIndex

    def removeTragedy(self):
        for pawn in self.tragedySelectPawn:
            pawn.remove()
        self.tragedySelectPawn = []


    def pointList2Index(self, pointList):
        return [i.index for i in pointList]

    def pawnList2Index(self, pawnList):
        return [i.getindex() for i in pawnList]

    def number2index(self,n):
        return self.map_number2index[int(n)]

    def index2point(self,index):
        return self.map[int(index)]

    def number2point(self,n):
        index = self.number2index(int(n))
        return self.map[index]

    # 查询警察堵路
    def checkJackNotBlock(self, point1:Point, point2:Point):
        adj = point1.adjacent
        if point2 in adj:
            return True

        done = []
        new = [i for i in adj if ( (i.checkBlack()) and (not i.checkPawn()) and (not i in done))]
        while len(new) > 0:
            this = new[0]
            adj = this.adjacent
            if point2 in adj:
                return True
            new += [i for i in adj if (
                        (i.checkBlack()) and (not i.checkPawn()) and (not i in done) and (
                    not i in new))]

            done.append(this)
            del new[0]

        return False


    # 初始化棋盘信息
    def initMapData(self, mapPath):
        mapdata = dict()
        mapdata_number2index = dict()
        adjacent = dict()
        adjacentWhite = dict()
        datafile_path = mapPath
        policestation = list()

        with open(datafile_path) as f:
            line = f.readline()
            while line:
                info = line.strip().split('-')
                id = int(info[0])
                key = info[1]
                data = info[2]

                # Find point
                if not id in mapdata:
                    point = Point(id, BLACK)
                    mapdata[id] = point
                else:
                    point = mapdata[id]

                # Add attribute
                if key == 'position':
                    data = eval(data)
                    point.setXY(float(data[0]),float(data[1]))
                elif key == 'adjacent':
                    adjacent[id] = data
                elif key == 'adjacentNumber':
                    adjacentWhite[id] = data
                    # data = eval(data)
                    # print (data)
                    # point.adjacentWhite = [self.index2point(int(i)) for i in data]
                elif key == 'number':
                    point.type = WHITE
                    point.number = int(data)
                    # 外部编号转换内部编号字典
                    if key == 'number':
                        mapdata_number2index[int(data)] = id

                elif key == 'murder':
                    point.murder = 1
                elif key == 'station':
                    point.station = 1
                    policestation.append(point)


                line = f.readline()

        # 临近点
        for index in adjacent:
            for j in eval(adjacent[index]):
                mapdata[index].adjacent.append(mapdata[j])
        for index in adjacentWhite:
            for j in eval(adjacentWhite[index]):
                mapdata[index].adjacentWhite.append(mapdata[j])

        return mapdata, mapdata_number2index, policestation

    # 初始化小巷链接信息
    def initAlleyData(self, path):
        with open(path) as f:
            line = f.readline()
            while line:
                info = line.strip().split('-')

                number = int(info[0])

                if len(info) > 1:
                    data = [self.number2point(int(i)) for i in info[1].split(';')]
                else:
                    data = []

                for j in data:
                    self.number2point(number).alley = data

                line = f.readline()

    def initAdjacentBlack(self):

        for i in self.map:

            p = self.map[i]
            if p.checkWhite():
                p.adjacentBlack = []
                continue

            adj = [j for j in p.adjacent if j.checkBlack()]
            adj_white = [j for j in p.adjacent if j.checkWhite()]
            adj_white_2level = []

            #在一层白色点循环
            for k in adj_white:
                # 寻找k的直接相连白点
                adj_white_2level += [j for j in k.adjacent if j.checkWhite()]


            for j in adj_white + adj_white_2level:
                adj += [k for k in j.adjacent if (k.checkBlack() and k != p)]

            adj = list(set(adj))
            p.adjacentBlack = adj