from flask import Flask
from flask import render_template
from flask import request
from flask import make_response
from flask import Flask, session, redirect, url_for, escape, request, abort
from flask_socketio import SocketIO, emit, join_room

from urllib.parse import urlparse
import redis
import os, time

from game import Game
from db import DB


ONLINE = True
# ONLINE = False


if ONLINE:
    import eventlet
    eventlet.monkey_patch()
    REDIS_URL = os.environ.get("REDIS_URL")
else:
    REDIS_URL = "redis://@127.0.0.1:6379/db"


TEAM_NAME = ['-','杰克','侦探']

app = Flask(__name__)
app.secret_key = ''
socketio = SocketIO(app, logger=True)
serverMaxGame = 1
gameWaitingTime = 60*3
gameMaxTime = 60*60*3
gameEndTime = 15

db = DB(REDIS_URL,gameWaitingTime, gameMaxTime, gameEndTime, serverMaxGame)
games = dict()

clients_jack = []
clients_police = []

def time2str(s):
    return str(s//3600)+'小时'+str((s%3600)//60)+'分'+str(s%60)+'秒'

@app.route('/')
def index():
    serverState = db.getState()
    if serverState == None or int(serverState) == 0:
        text = '0'
    else:
        text = '2'

    serverGameList = db.getGameList()
    gameIDs = list(games.keys())
    for gameID in gameIDs:
        game = games[gameID]

        if game.fin and (not game.saved):
            game.saved = True
            game.historyData['home'] = game.home.index
            game.historyData['jackname'] = game.jackPlayerName
            game.historyData['policename'] = game.policePlayerName
            game.historyData['gameID'] = game.gameID
            game.historyData['result'] = game.gameResult
            game.historyData['date'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            db.endGame(game.historyData)
            db.setGemeTime(gameID, gameEndTime)
            
        if not gameID in serverGameList:

            if (not game.saved) and (len(game.getPoliceplayerName())>0):
                print('储存耗尽时间的对局')
                game.saveDayData()
                game.historyData['home'] = game.home.index
                game.historyData['jackname'] = game.jackPlayerName
                game.historyData['policename'] = game.policePlayerName
                game.historyData['gameID'] = game.gameID
                game.historyData['result'] = game.gameResult
                game.historyData['date'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                db.endGame(game.historyData)

            games.pop(gameID)

    for gameID in serverGameList:
        if not gameID in gameIDs:
            db.delete(gameID)


    # 输出存活的游戏列表
    ans = []
    serverGameList = db.getGameList()
    for gameID in serverGameList:
        remain = db.getTime(gameID)
        remain = time2str(remain)

        game =  games[gameID]
        jack = game.getJackplayerName()
        police = game.getPoliceplayerName()

        phase = '第'+str(game.day)+'天'+str(game.round)+'回合'

        ans.append([jack, police, phase, remain])


    if len(ans) > 0:
        text = '1'

    return render_template('index.html', states = str(text), details = ans)


@app.route('/login_jack', methods = ['GET', 'POST'])
def login_jack():
    if request.method == 'POST':

        serverState = db.getState()
        if serverState == None or int(serverState) == 0:
            return '服务器维护中，无法进行游戏'

        result = request.form
        if len(result['playername'])<2 or len(result['playername'])>20:
            return '玩家名长度错误'
        if not result['roomid'].isdigit():
            return '房间号需要是整数'
        if int(result['roomid']) < 100 or int(result['roomid']) > 9999999:
            return '房间号长度错误'
        if not result['home'].isdigit():
            return '房间密码需要三位以上整数'
        if int(result['home'])<1 or int(result['home'])>195:
            return '家的位置在1-195之间'
        if int(result['home']) in [3,27,65,84,21,149,158,147]:
            return '家的位置不能选取在案发现场'

        gameID = int(result['roomid'])
        home = int(result['home'])
        jackname = str(result['playername'])


        if not db.checkGameID(gameID):
            if len(games) >= serverMaxGame:
                return '服务器已满，暂时无法创建新游戏。请等待服务器空闲。'


            db.newGame(gameID, home)
            db.setGemeTime(gameID, gameWaitingTime)

            game = Game(gameID)
            games[gameID] = game
            game.setHome(home)
            game.setJackplayerName(jackname)
            if 'AgentSwitch' in result:
                game.agent1_on = True


        else:
            if not db.checkGameIDHome(gameID, home):
                return '家不一致，无法中途加入'

            game = games[gameID]

        session['playername'] = result['playername']
        session['team'] = TEAM_NAME[1]
        session['name'] = result['playername'] + '('+TEAM_NAME[1]+ ')'
        session['gameid'] = gameID
        session['agent1'] = game.agent1_on


        return render_template('board.html',
                               roomid=result['roomid'],
                               playername=result['playername'],
                               teamname=TEAM_NAME[1],
                               agent1=game.agent1_on,
                               )


@app.route('/login_police', methods = ['GET', 'POST'])
def login_police():
    if request.method == 'POST':
        serverState = db.getState()
        if serverState == None or serverState == 0:
            return '服务器维护中，无法进行游戏'

        result = request.form
        if len(result['playername'])<2 or len(result['playername'])>20:
            return '玩家名长度错误'
        if not result['roomid'].isdigit():
            return '房间号需要是整数'   
        if int(result['roomid']) < 100 or int(result['roomid']) > 9999999:
            return '房间号长度错误'

        gameID = int(result['roomid'])
        policename = result['playername']

        if not db.checkGameID(gameID):
            return '房间号错误 或 杰克方没有创建房间'

        game = games[gameID]
        if not game.checkGameStart():
            game.setPoliceplayerName(policename)

        session['playername'] = result['playername']
        session['team'] = TEAM_NAME[2]
        session['name'] = result['playername'] + '(' + TEAM_NAME[2] + ')'
        session['gameid'] = gameID
        session['agent1'] = game.agent1_on


        return render_template('board.html',
                               roomid=result['roomid'],
                               playername=result['playername'],
                               teamname=TEAM_NAME[2],
                               policepower = result['policepower'],
                               agent1=game.agent1_on,
                               )


@app.route('/view_history', methods = ['GET', 'POST'])
def view_history():
    if request.method == 'POST':
        serverState = db.getState()
        if serverState == None or serverState == 0:
            return '服务器维护中，无法进行游戏'

        result = request.form
        if not result['roomid'].isdigit():
            return '房间号需要是整数'
        if int(result['roomid']) < 100 or int(result['roomid']) > 9999999:
            return '房间号长度错误'

        gameID = int(result['roomid'])
        data = db.historyGameData_fromgameID(gameID)
        if data == -1:
            return '找不到该房间号的游戏记录'

        name = data['jackname'] + ' vs ' + data['policename']
        home = data['home']
        roomid = data['gameID']
        result = data['result']
        ans = getHistoryData(data)
    return render_template('gamelog.html', home = home, roomid=roomid, playername=name, result=result, data=ans)


def sendSystemMessage(s, broadcast=True):
    if s != None and len(s)>0:
        emit('sysmessage', {'data': s}, namespace='/board', broadcast=broadcast)


def sendTime(game, broadcast=True):
    remain = db.getTime(game.gameID)
    remain = time2str(remain)
    emit('systime', {'data': remain}, namespace='/board', broadcast=broadcast)


def sendBoardState_broadcast(game, broadcast = True):
    if broadcast:
        for i in clients_jack:
            emit('boardstate', game.sumBoardInfo(True), namespace='/board', room = i)
        for i in clients_police:
            emit('boardstate', game.sumBoardInfo(False), namespace='/board', room = i)
    else:
        if session['team'] == TEAM_NAME[1] or session['team'] == 'admin':
            emit('boardstate', game.sumBoardInfo(True), namespace='/board', broadcast=False)
        else:
            emit('boardstate', game.sumBoardInfo(False), namespace='/board', broadcast=False)
            
def run2page(game, ans):
    subject = ans[0]
    message = ans[1]
    
    if subject == 0:
        broadcast = True
    else:
        broadcast = False
    
    sendSystemMessage(message, broadcast=broadcast)
    sendBoardState_broadcast(game, broadcast=broadcast)
    sendTime(game, broadcast=broadcast)


@socketio.on('joinmessage', namespace='/board')
def joinmessage(message):
    if session['team'] == TEAM_NAME[1] or session['team'] == 'admin':
        clients_jack.append(request.sid)
        room = session.get('room')
        join_room(room)
    else:
        clients_police.append(request.sid)
        room = session.get('room')
        join_room(room)
    
    if session['team'] != 'admin':
        s = '玩家' + session['name'] + '加入了房间'
        emit('sysmessage', {'data': s}, broadcast=True)

    gameID = int(message['gameid'])
    game = games[gameID]

    if (not game.checkGameStart()) and (session['team'] == TEAM_NAME[2]):
        db.setGemeTime(gameID, gameMaxTime)
        game.gameStart()
        run2page(game,[0,'游戏开始'])


@socketio.on('leavemessage', namespace='/board')
def leavemessage(message):
    if session['team'] != 'admin':
        s = '玩家' + session['name'] + '离开了房间'
        emit('sysmessage', {'data': s}, broadcast=True)
  

@socketio.on('refresh', namespace='/board')
def refresh(message):
    gameID = int(message['roomid'])
    if not gameID in list(games.keys()):
        return ('错误：找不到该游戏实例')
    game = games[gameID]

    sendBoardState_broadcast(game, broadcast=False)
    sendTime(game, broadcast=False)


@socketio.on('cmdmessage', namespace='/board')
def cmdmessage(message):
    gameID = int(message['roomid'])
    if not gameID in list(games.keys()):
        return ('错误：找不到该游戏实例')
    game = games[gameID]
    cmd = str(message['data'])

    turn = game.turn

    if session['team'] == game.cmdWaiting[min(1,game.round)][game.turn]:
        run2page(game, game.cmd(cmd))
    else:
        emit('sysmessage', {'data': '请等待对方行动'}, namespace='/board', broadcast=False)


@socketio.on('chatmessage', namespace='/board')
def chatmessage(message):
    s = '玩家' + session['name'] + '说：' + message['data']
    emit('chatmessage', {'data': s}, broadcast=True)



def getHistoryData(data):
    name = data['jackname'] + ' vs ' + data['policename']
    home = data['home']
    roomid = data['gameID']
    result = data['result']

    ans = []
    for i in [1, 2, 3, 4]:
        if i in data:
            ans.append(data[i][0])
            ans.append(data[i][1])
            ans.append(data[i][3] + data[i][5] + data[i][7] + data[i][9] + data[i][11])
            ans.append([data[i][2], data[i][4], data[i][6], data[i][8], data[i][10]])

        else:
            ans.append([])
            ans.append([])
            ans.append([])
            ans.append([])

    return ans



@socketio.on('agent1', namespace='/board')
def agent1(message):
    gameID = int(message['roomid'])

    if not gameID in list(games.keys()):
        return ('错误：找不到该游戏实例')
    if session['agent1']:
        game = games[gameID]
        data = game.agent1.run()
        emit('agent1_result', {'data': data}, namespace='/board', broadcast=False)



if __name__ == '__main__':
    socketio.run(app, debug=True)

    