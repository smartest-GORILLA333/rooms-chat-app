from flask import Flask, render_template, request, url_for, redirect, session
from flask_socketio import SocketIO, join_room, leave_room, send
import random
from string import ascii_uppercase

rooms={}

app = Flask(__name__,template_folder="templates")
app.config['SECRET_KEY'] = 'BB22FC74363463D7967F5BAF156A2'
socketio= SocketIO(app)

def generateRoomCode():
    code = ""
    while True:
        for _ in range(4):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            break
    return code



@app.route("/",methods=["GET","POST"])
def index():
    return render_template("index.html" , rooms=rooms.keys())

@app.route("/userform" , methods=["POST","GET"])
def handleForm():

    username= request.form.get("username")
    roomCode= request.form.get("roomId")
    joinBtn= request.form.get("join" , False)
    creatBtn= request.form.get("create" , False)


    if creatBtn != False:
        if not username:
            return redirect(url_for("index"))

        newRoom=generateRoomCode()
        rooms[newRoom]={"members":0 , "messages":[]}
        session['room']=newRoom
        session['username'] = username
        return redirect(url_for("room"))




    if joinBtn != False:
        if not username or not roomCode:
            return redirect(url_for("index"))
        if roomCode not in rooms:
            return redirect(url_for("index", error="Room does not exist"))

        session['username'] = username
        session['room'] = roomCode
        return redirect(url_for("room"))




@app.route("/room")
def room():
    room=session.get("room")
    if room is None or session.get("username") is None or room not in rooms:
        redirect(url_for("index"))
    return render_template("room.html" , room=room ,rooms=rooms,username=session.get("username"))


@socketio.on("join")
def on_join(data):
    name=data['username']
    roomId=data['room']

    join_room(roomId)
    rooms[roomId]["members"] +=1
    socketio.emit("update_room", {"room": roomId, "members": rooms[roomId]["members"]}, room=roomId)
    socketio.emit("message",f"{name} joined the room:{roomId}." , to=roomId)
    print(f"{name} joined the room:{roomId}.")

@socketio.on("disconnect")
def on_disconnect():
    name = session.get("username")
    roomId = session.get("room")
    leave_room(roomId)
    rooms[roomId]["members"] -= 1
    socketio.emit("update_room", {"room": roomId, "members": rooms[roomId]["members"]}, room=roomId)
    socketio.emit("message", f"{name} left the room {roomId}.", to=roomId)
    print(f"{name} left the room:{roomId}.")

@socketio.on("send")
def on_send_msg(data):
    name=data['username']
    roomId=data['room']
    text=data["txt"]

    rooms[roomId]["messages"].append(text)
    print(f"{name} : {text}")
    socketio.emit("message",f"{name} : {text}",to=roomId)







if __name__ == "__main__":
    socketio.run(app, debug=True , allow_unsafe_werkzeug=True)