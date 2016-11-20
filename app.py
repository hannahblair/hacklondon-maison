import flask
from flask import Flask, send_from_directory, request, render_template
from pymongo import MongoClient, ReturnDocument
from pusher import Pusher

REMINDER_CHANNEL = 'reminder_channel'

app = Flask(__name__)
app.debug = True
db = MongoClient("52.17.26.163")['test']
pusher = Pusher(
  app_id='183632',
  key='fdbd6c7bb85a1f20e56d',
  secret='467d650bec35aeb85fc7',
  ssl=True,
  port=443
)

def log(msg):
    print(msg)
    return msg

def set_db(new_db):
    global db
    db = new_db

def strip_mongoid(document):
    document.pop("_id")
    return document

def create_new_id(id_name):
    counter_doc = db.counters.find_one_and_update({"id":id_name},
                                                  {"$inc":{"seq":1}},
                                                  return_document=ReturnDocument.AFTER,
                                                  upsert=True)
    return counter_doc['seq']

def create_new_task(task_name, date, persons):
    id = create_new_id('taskId')
    return {"id": id, "name": task_name, "date": date, "persons": persons}

@app.route("/")
def hello():
    return send_from_directory("","index.html")

@app.route("/login/<user>")
def login(user):
    return render_template('login.html', user=user)

@app.route("/logout")
def logout():
    return send_from_directory("", 'logout.html')

@app.route("/<filename>")
def serve_file(filename):
    return send_from_directory("", filename)

@app.route("/somethingForTest")
def test():
    return "Testing"

@app.route("/getAllUsers")
def getAllUsers():
    all = db['users'].find()
    all_list = [strip_mongoid(x) for x in all]
    return flask.jsonify(users=all_list)

@app.route("/getAllTasks")
def getAllTasks():
    all = db['tasks'].find()
    all_list = [strip_mongoid(x) for x in all]
    return flask.jsonify(tasks=all_list)

@app.route("/addTask", methods = ['POST'])
def addTask():
    print("Received POST: "+str(request.form))
    task = create_new_task(request.form['taskName'],
                           request.form['date'],
                           request.form.getlist('users[]'))
    db['tasks'].insert(task)
    logmsg = "Inserted "+str(task['id'])
    print(logmsg)
    return logmsg

@app.route("/removeTask", methods = ['POST'])
def removeTask():
    print("Received POST: "+str(request.form))
    if 'taskName' not in request.form:
        return log("POST did not contain taskName")
    taskName = request.form['taskName']
    result = db['tasks'].delete_one({'name':taskName})
    if result.deleted_count == 0:
        return log("Did not find specified taskName: "+ taskName)
    return log("Deleted task: " + taskName)

@app.route("/testPusher")
def testPusher():
    pusher.trigger('reminder_channel', 'alice', {'message': 'hello world'})
    return "Sent successfully"

@app.route("/sendTaskReminders/<taskName>")
def sendTaskReminders(taskName):
    task = db['tasks'].find_one({"name": taskName})
    persons = task['persons']
    for p in persons:
        pusher.trigger(REMINDER_CHANNEL, p, {'taskName': taskName })
    return "Sent reminders to " + ", ".join(persons)

@app.route("/addTestTask", methods = ['GET'])
def addTestTask():
    task = create_new_task("testname", "testdate", ['someone'])
    db['tasks'].insert(task)
    return "Inserted "+str(task['id'])

if __name__ == "__main__":
    app.run()