import logging
import sys
from flask import Flask

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def home():
    logging.info('Home endpoint was accessed')
    return "Hello, World!"

