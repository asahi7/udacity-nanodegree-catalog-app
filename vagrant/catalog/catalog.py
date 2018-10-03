from flask import Flask, request, session, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)


@app.route("/cities")
@app.route("/")
def hello():
    return "Hello world!"


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
