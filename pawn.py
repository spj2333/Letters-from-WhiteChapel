from point import Point

JOB2NAME = ['杰克','红侦探','蓝侦探','黄侦探','绿侦探','紫侦探','无辜的人','藏匿点','绿','红','黄']

class Pawn():

    def __init__(self, job):

        self.job = job # 棋子类型：
        #0杰克；1-5侦探；6虚假侦探；7无辜的人；8房子；9绿色点；10红色点；11黄色点

        self.id = ''
        self.name = JOB2NAME[self.job] # 显示名字

        self.point = None # 棋盘位置：
        # -1不出现

        self.visible = False


        #移动规则
        if self.job in [0,7]:
            self.moveRule = 0 # 白格
        elif self.job in [1,2,3,4,5]:
            self.moveRule = 1  # 黑格
        else:
            self.moveRule = -1 # 不能移动

        #历史位置
        self.historyPoint = list()
        #行动力
        self.AP = 0
        # 线索
        self.clues = list()

        # 无辜的人 出生位置
        self.bornPoint = None


    def __repr__(self):
        return "{}->({},{})".format(self.__class__.__name__,self.point,JOB2NAME[self.job])

    def addClue(self,point:Point):
        self.clues.append(point)

    def getIndex(self):
        return self.point

    def forceMoveTo(self, targetPoint:Point):
        if self.point != None:
            self.point.clearPawn()
        self.point = targetPoint
        targetPoint.setPawn(self)
        self.historyPoint.append(targetPoint)

    def clearHistoryPoint(self):
        self.historyPoint = list()

    def remove(self):
        if self.point != None:
            self.point.clearPawn()
        self.point = None

    def getHistoryIndex(self):
        return [i.index for i in self.historyPoint]

    def getHistoryClue(self):
        return [i.index for i in self.clues]

    def getHistoryPoint(self):
        return self.historyPoint

    def getIndex(self):
        if self.point != None:
            return self.point.index
        else:
            return -1

    def getPoint(self):
        return self.point