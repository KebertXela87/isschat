import psycopg2
import psycopg2.extras
import os
import uuid
from flask import Flask, session, render_template, request, redirect, url_for
from flask.ext.socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'secret!'
app.secret_key = os.urandom(24).encode('hex')

socketio = SocketIO(app)

messages = [{'text': 'Booting system', 'name': 'Bot'}, {'text': 'ISS Chat now live!', 'name': 'Bot'}]
            
users = {}

searchResults = []

rooms = []

def connectToDB():
    connectionString = 'dbname=isschat user=isschatcontroller password=issisfun host=localhost'
    print connectionString
    try:
        return psycopg2.connect(connectionString)
    except:
        print("Can't connect to database")

@socketio.on('connect', namespace='/iss')
def makeConnection():
    db = connectToDB()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    global messages
    
    messages = [] #reset the message array on a reconnect
    rooms = []
    
    messages = [{'text': 'Booting system', 'name': 'Bot'}, {'text': 'ISS Chat now live!', 'name': 'Bot'}]
    
    session['uuid'] = uuid.uuid1()
    session['username'] = 'New user'
    print('connected')
    users[session['uuid']] = {'username': 'New user', 'room': 'General'}
    
    join_room(users[session['uuid']]['room'])
    emit('joinedGeneral')
    print users[session['uuid']]['username'] + ' joined room ' + users[session['uuid']]['room']

    cur.execute("SELECT roomname FROM rooms;")
    roomList = cur.fetchall()
    for room in roomList:
        rooms.append(room)
        emit('createRoom', room)
    
    cur.execute("select * from issmessages where room = %s;", (users[session['uuid']]['room'],))
    results = cur.fetchall()
    if(len(results) > 0):
        for result in results:
            tmp = {'text': result[2], 'name': result[1]}
            messages.append(tmp)
    
    for message in messages:
        print(message)
        emit('message', message)

@socketio.on('identify', namespace='/iss')
def on_identify(name):
    print('identify ' + name)
    users[session['uuid']] = {'username': name, 'room': users[session['uuid']]['room']}

@socketio.on('on_join', namespace='/iss')
def on_join(room):
    db = connectToDB()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    global messages
    
    subbedRooms = []
    cur.execute("SELECT rooms.roomname FROM rooms JOIN subscriptions ON rooms.id = subscriptions.room_id JOIN users ON subscriptions.user_id = users.id WHERE users.username = %s;", (users[session['uuid']]['username'],))
    subbedRooms = cur.fetchall()
    print subbedRooms
    if room in subbedRooms:
        leave_room(users[session['uuid']]['room'])
        print 'Leaving room ' + users[session['uuid']]['room']
        for message in messages:
            emit('refreshMessages')
        
        messages = []
        
        users[session['uuid']]['room'] = room[0]
        join_room(users[session['uuid']]['room'])
        print users[session['uuid']]['username'] + ' joined room ' + users[session['uuid']]['room']
        cur.execute("select * from issmessages where room = %s;", (users[session['uuid']]['room'],))
        results = cur.fetchall()
        if(len(results) > 0):
            for result in results:
                tmp = {'text': result[2], 'name': result[1]}
                messages.append(tmp)
                emit('message', tmp, room=users[session['uuid']]['room'])
        emit('joined', users[session['uuid']]['room'])
        
    else:
        print 'You are not subscribed to that chatroom'

@socketio.on('createRoom', namespace='/iss')
def create_room(room):
    db = connectToDB()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    print "This is a test - Username: " + users[session['uuid']]['username']
    print "This is a test - Room: " + users[session['uuid']]['room']
    
    #add room to the room table.
    cur.execute('INSERT INTO rooms (roomname) VALUES (%s);', (room,))
    db.commit()
    
    rooms.append(room)
    emit('createRoom', room)

@socketio.on('message', namespace='/iss')
def new_message(message):
    db = connectToDB()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    tmp = {'text': message, 'name': users[session['uuid']]['username'], 'room': users[session['uuid']]['room']}
    #tmp = {'text': message['text'], 'room': message['room'], 'name': users[session['uuid']]['username']}
    print(tmp)
    print("INSERT INTO issmessages (name, message, room) VALUES ('%s', '%s', '%s')" % (tmp['name'], tmp['text'], tmp['room']))
    cur.execute("INSERT INTO issmessages (name, message, room) VALUES (%s, %s, %s)", (tmp['name'], tmp['text'], tmp['room']))
    db.commit()
    
    messages.append(tmp)
    emit('message', tmp, room=tmp['room'])
    
@socketio.on('search', namespace='/iss')
def new_search(sTerm):
    db = connectToDB()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    searchResults = []
    
    cur.execute("SELECT name, message FROM issmessages WHERE (UPPER(name) LIKE UPPER(%s) OR UPPER(message) LIKE UPPER(%s)) AND room = %s;", ("%%" + sTerm + "%%", "%%" + sTerm + "%%", users[session['uuid']]['room']))
    print("SELECT name, message FROM issmessages WHERE (UPPER(name) LIKE UPPER('%%%s%%') OR UPPER(message) LIKE UPPER('%%%s%%')) AND room = '%s';" % (sTerm, sTerm, users[session['uuid']]['room']))
    results = cur.fetchall()
    if(len(results) > 0):
        for result in results:
            tmp = {'text': result[1], 'name': result[0]}
            searchResults.append(tmp)
    
        for searchResult in searchResults:
            print(searchResult)
            emit('searchResult', searchResult)
            emit('showResults')
    else:
        emit('showNoResults')
    
@socketio.on('login', namespace='/iss')
def on_login(pw):
    db = connectToDB()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = "select * from users WHERE username = '%s' AND password = crypt('%s', password);" % (users[session['uuid']]['username'], pw)
    print query
    cur.execute(query)
    if cur.fetchone():
        emit('goodlogin')
    else:
        emit('badlogin')

@app.route('/')
def hello_world():
    print 'in hello world'
    return app.send_static_file('index.html')
    
@app.route('/register', methods=['GET', 'POST'])
def new_user():
    db = connectToDB()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    rooms = []
    cur.execute("SELECT roomname FROM rooms;")
    roomList = cur.fetchall()
    for room in roomList:
        rooms.append(room[0])
        
    print rooms
    
    if request.method == 'POST':
        print "Hello"
        checkUser = "SELECT * from users WHERE username = '%s'" % (request.form['username'])
        print checkUser
        cur.execute(checkUser)
        if cur.fetchone():
            print 'That user already exists!'
            return render_template('register.html', baduser='true', checkboxes=rooms)
        else:
            query = "INSERT INTO users (username, password) VALUES ('%s', crypt('%s', gen_salt('bf')));" % (request.form['username'], request.form['password'])
            print(query)
            try:
                cur.execute("INSERT INTO users (username, password) VALUES (%s, crypt(%s, gen_salt('bf')));", (request.form['username'], request.form['password']))
                db.commit()
                for room in rooms:
                    if room in request.form:
                        print room
                        cur.execute("SELECT * FROM users WHERE username = %s", (request.form['username'],))
                        userID = cur.fetchone()
                        cur.execute("SELECT * FROM rooms WHERE roomname = %s", (room,))
                        roomID = cur.fetchone()
                        cur.execute("INSERT INTO subscriptions (user_id, room_id) VALUES (%s, %s);", (userID[0], roomID[0]))
            except:
                print("Error Creating user...")
                db.rollback()
            db.commit()
            
            return redirect(url_for('hello_world'))
    
    return render_template('register.html', checkboxes=rooms)

# start the server
if __name__ == '__main__':
        socketio.run(app, host=os.getenv('IP', '0.0.0.0'), port =int(os.getenv('PORT', 8080)), debug=True)
