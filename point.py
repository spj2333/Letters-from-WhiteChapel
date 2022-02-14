TYPE2NAME = ['白','黑']

class Point():

    def __init__(self, index, type = 0, number = -1):

        self.index = index
        self.type = type # 0 白点 1 黑点
        self.number = number

        # 直接临近点（黑白，调查）
        self.adjacent = list()
        # 纯白临近店（只看白，杰克移动）
        self.adjacentWhite = list()
        # 纯黑临近店（只看白，警察移动）
        self.adjacentBlack = list()
        self.alley = list()

        self.station = 0
        self.murder = 0
        # self.killed = 0


        self.pawn = None
        self.x = 0.0
        self.y = 0.0

    def __repr__(self):
        if self.checkWhite():
            return "{}->({},{}{})".format(self.__class__.__name__,self.index,TYPE2NAME[self.type],self.number)
        else:
            return "{}->({},{})".format(self.__class__.__name__,self.index,TYPE2NAME[self.type])

    def checkBlack(self):
        return self.type==1

    def checkWhite(self):
        return self.type == 0

    def checkStation(self):
        return self.station == 1

    def checkMurder(self):
        return self.murder == 1

    def checkPawn(self):
        if self.pawn == None:
            return False
        else:
            return True

    def clearPawn(self):
        self.pawn = None

    def setPawn(self, pawn):
        self.pawn = pawn

    def setXY(self,x,y):
        self.x = x
        self.y = y
