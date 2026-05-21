from flask import render_template
from app import app
from app.system_info import get_system_info
from app.inventory import load_servers

@app.route("/")
def home():
    system_info = get_system_info()
    servers = load_servers()

    return render_template(
        "index.html", 
        system_info=system_info,
        servers=servers
    )

