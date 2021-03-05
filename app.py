from flask import Flask, redirect, url_for, render_template, request, session
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

EntryQueue = []
entryPosn = 2
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)

client = gspread.authorize(creds)

file = client.open("testsheet")

sheetoptions = {'1': "Sheet1",
                '2': "Sheet2",
                '3': "Sheet3",
                '4': "Sheet4",
                '5': "Sheet5"}

app = Flask(__name__)
app.secret_key = "wh4t1nTh3w0rld15th15?"

def job_function():
    if (EntryQueue):
        q = EntryQueue[0]
        print('running on', q[1])
        values = []
        for x in q[2]:
            exRow = [q[1], x['Q'], x['O'], x['A'].lower(), q[3]]
            values.append(exRow)
        file.values_append(q[0], {'valueInputOption': 'USER_ENTERED', 'insertDataOption': 'INSERT_ROWS'}, {'values': values})
        EntryQueue.pop(0)

scheduler = BackgroundScheduler()
scheduler.add_job(func=job_function, trigger="interval", seconds=30)
scheduler.start()

@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        user = request.form["n"]
        pd = request.form['p']
        session["user"] = user
        session['period'] = pd
        return redirect(url_for('quiz'))
    else:
        if "user" in session:
            return redirect(url_for('quiz'))
        else:
            return render_template('index.html')


@app.route("/quiz/", methods=["POST", "GET"])
def quiz():
    if "user" in session and "period" in session:
        if session['user'] != '' and session['period'].isnumeric():
            if 1 <= int(session["period"]) <=5:
                usr = session['user']
                pd = session['period']
                return render_template('quiz.html', user=usr, per=pd)
    return redirect(url_for('logout'))

@app.route('/logout/')
def logout():
    session.pop("user", None)
    return redirect(url_for('home'))

@app.route('/postmethod', methods = ['POST'])
def get_post_javascript_data():
    jsdata = json.loads(request.form['javascript_data'])
    period = session['period']
    user = session['user']
    sheet = sheetoptions[period]
    logtime = str(datetime.datetime.now().replace(microsecond=0))
    queueRow = [sheet, user, jsdata, logtime]
    EntryQueue.append(queueRow)
    session.pop("user", None)#logout after values stored in quue
    return ""

# Shutdown your cron thread if the web process is stopped
atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    app.run()


