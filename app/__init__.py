from flask import Flask

from app.database import init_db
from app.product import PRODUCT

app = Flask(__name__)

init_db()

@app.context_processor
def inject_product():

    return {
        "product": PRODUCT
    }

from app import routes
