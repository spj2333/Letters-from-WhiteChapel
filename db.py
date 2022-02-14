import redis
import os

class DB():
    def __init__(self, REDIS_URL, gameWaitingTime, gameMaxTime, gameEndTimes, serverMaxGame = 1):
        self.REDIS_URL = REDIS_URL
        self.gameWaitingTime = gameWaitingTime
        self.gameMaxTime = gameMaxTime
        self.gameEndTimes = gameEndTimes

        r = self.connect()
        r.set('test', int(1))

    def connect(self):
        return redis.from_url(self.REDIS_URL, decode_responses=True)

    def newGame(self, gameID, home):

        gamelist = self.loadList('gamelist')
        gamelist.append(gameID)

        self.saveList('gamelist',gamelist)
        self.saveInt(gameID, home)
        # return gameID

    def endGame(self, data):
        history = int(self.loadInt('history'))
        history += 1
        r = self.connect()
        r.set('history'+str(history), str(data))
        self.saveInt('history', history)

    def checkGameID(self, gameID):
        gameList = self.getGameList()
        return (int(gameID) in gameList)

    def checkGameIDHome(self, gameID, inoputhome):
        home = self.loadInt(gameID)
        if home == None or inoputhome != home:
            return False
        else:
            return True

    def setGemeTime(self, gameID, time):
        self.setExpire(gameID, time)

    def setState(self, n):
        r = self.connect()
        r.set('state', int(n))

    def getState(self):
        r = self.connect()
        return r.get('state')

    def getGameList(self):
        gamelist = self.loadList('gamelist')

        i = 0
        while i < len(gamelist):
            gameID = gamelist[i]

            if self.load(gameID) == None:
                del gamelist[i]
            else:
                i+=1

        self.saveList('gamelist', gamelist)
        return gamelist

    def getGameNumber(self):
        return self.loadInt('gamenumbermax')

    def historyGameList(self):
        r = self.connect()
        ans = []
        history = int(self.loadInt('history'))
        for i in range(1, history+1):
            data = r.get('history' + str(i))
            if data != None:
                data = eval(data)
                name1 = data['jackname']
                name2 = data['policename']
                date = data['date'] if 'date' in data else ''
                result = data['result'] if 'result' in data else ''


                ans.append(str(i)+'. ['+ str(date) + '] [' +str(name1)+' vs '+str(name2)+'] ['+str(result)+']')
        return ans

    def historyGameData(self, n):
        r = self.connect()
        data = r.get('history' + str(n))

        if data != None:
            return eval(data)
        else:
            return 0

    def historyGameData_fromgameID(self, gameID):
        r = self.connect()
        history = int(self.loadInt('history'))
        i = history
        while (i>0):
            data = eval(r.get('history' + str(i)))
            if 'gameID' in data and data['gameID'] == int(gameID):
                return data
            i -= 1

        return -1

    def historyClear(self):
        self.saveInt('history',0)

    def load(self, key):
        r = self.connect()
        return r.get(str(key))

    def saveInt(self, key, value):
        r = self.connect()
        r.set(str(key), int(value))

    def loadInt(self, key):
        r = self.connect()
        return int(r.get(str(key)))

    def saveList(self, key, value):
        r = self.connect()
        r.set(str(key), str(value))

    def loadList(self, key):
        r = self.connect()
        print ('---')
        print (r.get(str(key)))
        return eval(r.get(str(key)))

    def setExpire(self, key, time):
        r = self.connect()
        r.expire(str(key), time)

    def getTime(self, key):
        r = self.connect()
        return r.ttl(str(key))

    def delete(self, key):
        r = self.connect()
        r.delete(str(key))


    def clean(self):
        gamelist = self.getGameList()
        for gameID in gamelist:
            self.setExpire(gameID, 10)
        return 0

