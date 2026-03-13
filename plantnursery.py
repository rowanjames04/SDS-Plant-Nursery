from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template('Home.html')

@app.route("/login")
def login():
    return render_template('Login.html')

@app.route("/register")
def register():
    return render_template('Register.html')