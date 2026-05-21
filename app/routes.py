from app import app

@app.route("/")
def home():
    return "Linux Patch & Compliance Dashboard"
