from flask import Flask 
import requests
import os, sys

display = False
app = Flask(__name__)

@app.route("/")
def index():
    return "gogo is running"

@app.route("/restart")
def restart():
    requests.get("http://localhost:6060/hdc")
    os.execv(sys.executable, ['python'] + sys.argv)

try:
    requests.get("http://localhost:6060/hc")
except:
    pass

def run():
    app.run(host="0.0.0.0", port=9191)