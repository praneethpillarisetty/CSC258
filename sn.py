from flask import Flask,render_template,flash, redirect,url_for,session,logging,request,send_file
from flask_sqlalchemy import SQLAlchemy
import flask_monitoringdashboard as dashboard
import authenticate as Auth
import tempfile
import os,io
import random
import mimetypes

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'BAD_SECRET_KEY'
login_users = {}

sn_host = '10.117.50.233'
sn_port = '5001'
pds_port = '5000'
sn_address = "http://"+sn_host+':'+sn_port
pds_address = "http://"+sn_host+':'+pds_port


def get_user_files(email):
    files = list(sn_user_data.query.filter_by(email = email))
    f = []
    if len(files) != 0:
        for i in files:
            f += [i.filename]
        return list(set(f))
    else:
        return 'None'

class sn_user(db.Model):
    __tablename__ = "SN_Users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    password = db.Column(db.String(80))

class sn_user_data(db.Model):
    __tablename__ = "SN_Users_Data"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    filename = db.Column(db.String(500))

@app.route("/<usr>/view", methods = ["GET", "POST"])
def user_view(usr):
    if not session.get("name") or usr != session.get("name"):
        return redirect("/login")
    login = sn_user.query.filter_by(username = usr).first()
    token = get_user_files(login.email)
    data = []
    if token == 'None':
        return render_template("view.html", name = usr, data = [], sn_address = sn_address, pds_address = pds_address)
    else:
        for i in token:
            url = Auth.firebasegeturl(login.email, i)
            if url != 'None':
                data +=[[str(i), url]]
        return render_template("view.html", name = usr, data = data, sn_address = sn_address, pds_address = pds_address)
        
    return render_template("view.html", name = usr, sn_address = sn_address, pds_address = pds_address)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.config['UPLOAD_FOLDER'] = 'static/temp'
    dashboard.bind(app)
    app.run( host = sn_host, port = '5001',threaded=True) # host = '10.0.0.92' or '10.117.50.233', add it if you want the server to run on the private network 
