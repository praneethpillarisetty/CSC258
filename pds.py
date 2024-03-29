from flask import Flask,render_template,flash, redirect,url_for,session,logging,request,send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
import flask_monitoringdashboard as dashboard
import authenticate as Auth
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import tempfile
import os,io
import random
import mimetypes

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'BAD_SECRET_KEY'
sn_host = '10.0.0.92'
sn_port = '5001'
pds_port = '5000'
sn_address = "http://"+sn_host+':'+sn_port
pds_address = "http://"+sn_host+':'+pds_port
login_users = {}

def remove_temp(path):
    try:
        os.remove(path)
        return True
    except:
        return False

def remove_temp_decrypt(usr,img):
    login = user.query.filter_by(username = usr).first()
    token = get_user_files(login.email)
    url = Auth.firebasedownload(login.email, img)
    Auth.decrypt(img, login.key)
    return_data = io.BytesIO()
    with open("static/temp/"+img, 'rb') as fo:
        return_data.write(fo.read())
    # (after writing, cursor will be at last byte, so move it to start)
    return_data.seek(0)
    os.remove("static/temp/"+img)
    return return_data


def get_user_files(email):
    files = list(user_data.query.filter_by(email = email))
    f = []
    if len(files) != 0:
        for i in files:
            f += [i.filename]
        return list(set(f))
    else:
        return 'None'
    
def get_user_friends(email):
    friends = list(user_friend.query.filter_by(email = email))
    f = []
    if len(friends) != 0:
        for i in friends:
            f += [i.friend]
        return list(set(f))
    else:
        return 'None'

def add_user_friends(email, friend):
    if friend is None:
        return 'None'
    friends = list(user.query.filter_by(username = friend))
    if len(friends) == 0:
        return 'None'
    else:
        friend_key = user.query.filter_by(username = friend).first().key
        register = user_friend(email = email, friend = friend, friend_key = friend_key)
        db.session.add(register)
        db.session.commit()
        return True
        
class login_user():
    fb_user_obj = None
    def set_fb_user(self, usr):
        self.fb_user_obj = usr
    def unset_fb_user(self):
        self.fb_user_obj = None
    def get_fb_user(self):
        return self.fb_user_obj

class user(db.Model):
    __tablename__ = "Users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    password = db.Column(db.String(80))
    key = db.Column(db.Integer())

class user_data(db.Model):
    __tablename__ = "Users_Data"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    filename = db.Column(db.String(500))

class user_friend(db.Model):
    __tablename__ = "Users_Friends"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    friend = db.Column(db.String(500))
    friend_key = db.Column(db.Integer())

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


def sn_login(inter_session):
    uname = inter_session["uname"]
    passw = inter_session["passw"]
    login = sn_user.query.filter_by(username = uname, password=passw).first()
    login_users[login.email] = current_user
    session["name"] = uname
    session["error"] = None
    return True

def sn_register(inter_session):
    error = session["error"]
    session["error"] = ""
    uname = inter_session["uname"]
    mail = inter_session["mail"]
    passw = inter_session["passw"]
    register = sn_user(username = uname, email = mail, password = passw)
    db.session.add(register)
    db.session.commit()
    session["error"] = "Registration sucessfull please login !"
    return True

current_user = login_user()   
@app.route("/")
def index():
    session["error"] = None
    return render_template("index.html")


@app.route("/login",methods=["GET", "POST"])
def login():
    error = session["error"]
    session["error"] = ""
    if request.method == "POST":
        uname = request.form["uname"]
        passw = request.form["passw"]
        login = user.query.filter_by(username = uname, password=passw).first()
        if login == None:
            error = "Failed to Login Try Again!"
            return render_template("login.html", error = error)
        token, usr = Auth.firebaselogin(login.email, passw)
        if login is not None and (token):
            #return redirect(url_for("index"))
            current_user.set_fb_user(usr)
            login_users[login.email] = current_user
            session["name"] = uname
            session["error"] = None
            inter_session={}
            inter_session["uname"] = uname
            inter_session["passw"] = passw
            sn_login(inter_session)
            return redirect(url_for("user_home", usr = uname))
        else:
            error = "Failed to Login Try Again!"
            session["error"] = error
            return render_template("login.html", error = error)
    return render_template("login.html", error = error)

@app.route("/<usr>/signout",methods=["GET", "POST"])
def signout(usr):
    if not session.get("name") or usr != session.get("name"):
        return redirect("/login")
    error = session["error"]
    session["error"] = ""
    if usr == 'None':
        error = "Please login First"
        return redirect(url_for("login", error = error))
    else:
        login = user.query.filter_by(username = usr).first()
        session["error"] = "Signout Sucessfull!"
        try:
            #del login_users[login.email]
            session["name"] = None
            return redirect(url_for("login"))
        except:
            return redirect(url_for("login"))
    return render_template("login.html", error = error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = session["error"]
    session["error"] = ""
    if request.method == "POST":
        uname = request.form['uname']
        mail = request.form['mail']
        passw = request.form['passw']
        if Auth.firebasesignup(mail, passw):
            key=random.randint(0,256)
            register = user(username = uname, email = mail, password = passw, key = key)
            db.session.add(register)
            db.session.commit()
            inter_session={}
            inter_session["uname"] = uname
            inter_session["passw"] = passw
            inter_session["mail"] = mail
            sn_register(inter_session)
            session["error"] = "Registration sucessfull please login !"
            return redirect(url_for("login"))
        else:
            error = "Failed to Register Try Again!"
            return render_template("register.html", error = error)
    return render_template("register.html", error = error)

@app.route("/<usr>/home", methods = ["GET", "POST"])
def user_home(usr):
    if not session.get("name") or usr != session.get("name"):
        return redirect("/login")
    return render_template("home.html", name = usr, sn_address = sn_address, pds_address = pds_address)

@app.route("/<usr>/upload_dec", methods = ["POST"])
def upload_dec(usr):
    data = request.get_json()
    fname = data['name']
    encrypted_data = base64.b64decode(data['data'])
    key = base64.b64decode(data['key'])
    login = user.query.filter_by(username = usr).first()
    # Decrypt the image data
    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)
    #fname = 'static/temp/'+ fname
    #app.logger.info(data['name'])
    with open(fname, 'wb') as f:
            f.write(decrypted_data)
    session['fname'] = fname
    if len(fname) == 0:
        return render_template("empty.html", name = usr, error = "Please select File first!", sn_address = sn_address, pds_address = pds_address)
    temp = fname[::-1]
    x = len(fname) - temp.index(".")
    filenamenew = fname[:x]+"png"
    #file.save(fname)
    #app.logger.info(data['name'])
    nfname = Auth.encrypt(fname, login.key, text = "Owned by "+usr )
    token = Auth.firebaseupload(login.email, filenamenew, nfname)
    if token:
        uploaded_data = user_data(email = login.email, filename = filenamenew)
        db.session.add(uploaded_data)
        db.session.commit()
        uploaded_data = sn_user_data(email = login.email, filename = filenamenew)
        db.session.add(uploaded_data)
        db.session.commit()
        error = "Upload Sucessfull"
        session["error"] = error
        remove_temp(fname)
        remove_temp(nfname)
        return jsonify({'status': 'success'})
    else:
        session["error"] = "Session Expired! Please login Again"
        return jsonify({'status': 'failure'})

@app.route("/<usr>/upload", methods = ["GET", "POST"])
def user_upload(usr):
    if not session.get("name") or usr != session.get("name"):
        return redirect("/login")
    error = session["error"]
    session["error"] = ""
    return render_template("upload.html", name = usr, error = error, sn_address = sn_address, pds_address = pds_address)


@app.route("/<usr>/view_download/<img>", methods = ["GET", "POST"])
def user_view_download(usr,img):
    if not session.get("name") or usr != session.get("name"):
        return redirect("/login")
    return_data = remove_temp_decrypt(usr,img)

    return send_file(return_data, mimetype= mimetypes.guess_type(img, strict=True)[0], download_name=img)

@app.route("/<usr>/delete", methods = ["GET", "POST"])
def user_delete(usr):
    if not session.get("name") or usr != session.get("name"):
        return redirect("/login")
    login = user.query.filter_by(username = usr).first()
    login_sn = sn_user.query.filter_by(username = usr).first()
    token = get_user_files(login.email)
    if token == 'None':
        return render_template("empty.html", name = usr, error = "Please add a file First!", sn_address = sn_address, pds_address = pds_address)
    data = [i for i in token]
    error = None
    if request.method == "POST":
        img = request.form.getlist("images")
        if len(img)==0:
            error = "Nothing is Selected Please Try Again!"
            return render_template("delete.html", name = usr, data = data, error = error, sn_address = sn_address, pds_address = pds_address)
        else:
            session["error"] = "Delete Not Sucessfull!"
            for i in img:
                Token = Auth.firebasedelete(login.email, i)
                if Token == True:
                    deleted_data = user_data.query.filter_by(email = login.email, filename = i).first()
                    db.session.delete(deleted_data)
                    db.session.commit()
                    deleted_data2 = sn_user_data.query.filter_by(email = login_sn.email, filename = i).first()
                    db.session.delete(deleted_data2)
                    db.session.commit()
                    session["error"] = "Delete Sucessfull!"
            return redirect(url_for("user_upload", usr = usr))
        
    return render_template("delete.html", name = usr, data = data, error = error, sn_address = sn_address, pds_address = pds_address)

@app.route("/<usr>/friends", methods = ["GET", "POST"])
def user_friends(usr):
    if not session.get("name") or usr != session.get("name"):
        return redirect("/login")
    login = user.query.filter_by(username = usr).first()
    token = get_user_friends(login.email)
    data = []
    if token == 'None':
        return render_template("empty.html", name = usr , error = "Please add a friend First!", sn_address = sn_address, pds_address = pds_address)
    else:
        for i in token:
            url = Auth.firebasegeturl(login.email, i)
            if url != 'None':
                data +=[str(i)]
        return render_template("friends.html", name = usr, data = data, sn_address = sn_address, pds_address = pds_address)
        
    return render_template("friends.html", name = usr, sn_address = sn_address, pds_address = pds_address)

@app.route("/<usr>/add_friend", methods = ["GET", "POST"])
def add_friend(usr):
    error = session["error"]
    session["error"] = ""
    if not session.get("name") or usr != session.get("name"):
        return redirect("/login")
    login = user.query.filter_by(username = usr).first()
    if request.method == "POST":
        uname = request.form["uname"]
        if len(uname) == 0:
            return render_template("add_friends.html", name = usr, error = "Enter a value first!", sn_address = sn_address, pds_address = pds_address)
        if usr == uname:
            return render_template("add_friends.html", name = usr, error = "Cannot add yourself as a friend", sn_address = sn_address, pds_address = pds_address)
        friends = get_user_friends(login.email)
        if uname in friends:
            return render_template("add_friends.html", name = usr, error = "Already a friend", sn_address = sn_address, pds_address = pds_address)
        token = add_user_friends(login.email,uname)
        if token == 'None':
            return render_template("add_friends.html", name = usr, error = "Please Enter a Valid Username", sn_address = sn_address, pds_address = pds_address)
        return redirect(url_for("user_home", usr = usr))
    return render_template("add_friends.html", name = usr, sn_address = sn_address, pds_address = pds_address)

@app.route("/<usr>/view_friends", methods = ["GET", "POST"])
def user_view_friends(usr):
    if not session.get("name"):
        return redirect("/login")
    login = user.query.filter_by(username = usr).first()
    token = get_user_files(login.email)
    data = []
    if token == 'None':
        return render_template("view_friends.html", name = usr, data = [])
    else:
        for i in token:
            url = Auth.firebasegeturl(login.email, i)
            if url != 'None':
                data +=[[str(i), url]]
        return render_template("view_friends.html", name = usr, data = data)
        
    return render_template("view_friends.html", name = usr)

@app.route("/<usr>/view_friend_download/<img>", methods = ["GET", "POST"])
def user_view_friend_download(usr,img):
    if not session.get("name"):
        return redirect("/login")
    return_data = remove_temp_decrypt(usr,img)

    return send_file(return_data, mimetype= mimetypes.guess_type(img, strict=True)[0], download_name=img)

@app.route("/<usr>/delete_friend", methods = ["GET", "POST"])
def user_delete_friend(usr):
    if not session.get("name") or usr != session.get("name"):
        return redirect("/login")
    login = user.query.filter_by(username = usr).first()
    token = get_user_friends(login.email)
    if token == 'None':
        return render_template("empty.html", name = usr , error = "Please add a friend First!", sn_address = sn_address, pds_address = pds_address)
    data = [i for i in token]
    mesg = "Select Files to delete"
    if request.method == "POST":
        img = request.form.getlist("friends")
        if len(img)==0:
            error = "Nothing is Selected Please Try Again!"
            return render_template("delete_friends.html", name = usr, data = data, error = error, sn_address = sn_address, pds_address = pds_address)
        else:
            session["error"] = "Delete Sucessfull!"
            for i in img:
                #Token = Auth.firebasedelete(login.email, i)
                deleted_data = user_friend.query.filter_by(email = login.email, friend = i).first()
                db.session.delete(deleted_data)
                db.session.commit()
            return redirect(url_for("add_friend", usr = usr))
        
    return render_template("delete_friends.html", name = usr, data = data, mesg = mesg, sn_address = sn_address, pds_address = pds_address)

@app.route("/<usr>/check_owner", methods = ["GET", "POST"])
def check_ownership(usr):
    if not session.get("name") or usr != session.get("name"):
        return redirect("/login")
    error = session["error"]
    session["error"] = ""
    if request.method == "POST":
        login = user.query.filter_by(username = usr).first()
        file = request.files['file']
        fname = file.filename
        if len(fname) == 0:
            return render_template("check_owner.html", name = usr, error = "Please select File first!", sn_address = sn_address, pds_address = pds_address)
        fname = 'static/temp/'+ fname
        file.save(fname)
        owner = Auth.owner(fname)
        owner = file.filename + " is " + owner 
        return render_template("empty.html", name = usr , error = owner, sn_address = sn_address, pds_address = pds_address)
    return render_template("check_owner.html", name = usr, error = error, sn_address = sn_address, pds_address = pds_address)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.config['UPLOAD_FOLDER'] = 'static/temp'
    dashboard.bind(app)
    app.run( host = sn_host,port='5000',threaded=True) # host = '10.0.0.92' or '10.117.50.233', add it if you want the server to run on the private network 
