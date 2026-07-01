from flask import Flask

from app.database import init_db
from app.product import PRODUCT
from app.documentation.routes import documentation_bp

app = Flask(__name__)

init_db()

@app.context_processor
def inject_product():

    return {
        "product": PRODUCT
    }

app.register_blueprint(documentation_bp)

from app import routes
