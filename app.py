from flask import Flask,render_template,flash, redirect,url_for,session,logging,request
from flask_sqlalchemy import SQLAlchemy
import authenticate as Auth
import tempfile
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
login_users = {}

def remove_temp(path):
    try:
        os.remove(path)
        return True
    except:
        return False

def get_user_files(email):
    files = list(user_data.query.filter_by(email = email))
    f = []
    if len(files) != 0:
        for i in files:
            f += [i.filename]
        return list(set(f))
    else:
        return 'None'
    
        
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

class user_data(db.Model):
    __tablename__ = "Users_Data"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    filename = db.Column(db.String(500))

current_user = login_user()   
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login",methods=["GET", "POST"])
def login():
    error = None
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
            return redirect(url_for("user_home", usr = uname))
        else:
            error = "Failed to Login Try Again!"
            return render_template("login.html", error = error)
    return render_template("login.html", error = error)

@app.route("/<usr>/signout",methods=["GET", "POST"])
def signout(usr):
    error = None
    if usr == 'None':
        error = "Please login First"
        return redirect(url_for("login", error = error))
    else:
        login = user.query.filter_by(username = usr).first()
        try:
            del login_users[login.email]
            error = "Signout Sucessfull!"
            return redirect(url_for("login", error = error))
        except:
            error = "Signout Sucessfull!"
            return redirect(url_for("login", error = error))
    return render_template("login.html", error = error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        uname = request.form['uname']
        mail = request.form['mail']
        passw = request.form['passw']
        if Auth.firebasesignup(mail, passw):
            register = user(username = uname, email = mail, password = passw)
            db.session.add(register)
            db.session.commit()
            error = "Registration sucessfull please login !"
            return redirect(url_for("login", error = error))
        else:
            error = "Failed to Register Try Again!"
            return render_template("register.html", error = error)
    return render_template("register.html", error = error)

@app.route("/<usr>/home", methods = ["GET", "POST"])
def user_home(usr):
    return render_template("home.html", name = usr)

@app.route("/<usr>/upload", methods = ["GET", "POST"])
def user_upload(usr):
    error = None
    if request.method == "POST":
        login = user.query.filter_by(username = usr).first()
        file = request.files['file']
        fname = file.filename
        fname = 'static/temp/'+ fname
        file.save(fname)
        if current_user.get_fb_user == None:
            error = "Session experied please login again!"
            return render_template("login.html", error = error)
        else:
            token = Auth.firebaseupload(login.email, file.filename, fname)
            if token:
                uploaded_data = user_data(email = login.email, filename = file.filename)
                db.session.add(uploaded_data)
                db.session.commit()
                error = "Upload Sucessfull"
                remove_temp(fname)
                return render_template("upload.html", name = usr, error = error)
            else:
                #error = "Not Authorised to Upload! Please Contact Adminstrator"
                error = (file.filename, login.email, fname)
                return render_template("upload.html", name = usr, error = error)
    return render_template("upload.html", name = usr)

@app.route("/<usr>/view", methods = ["GET", "POST"])
def user_view(usr):
    login = user.query.filter_by(username = usr).first()
    token = get_user_files(login.email)
    data = []
    if token == 'None':
        return render_template("view.html", name = usr, data = [])
    else:
        for i in token:
            url = Auth.firebasegeturl(login.email, i)
            if url != 'None':
                data +=[[str(i), url]]
        return render_template("view.html", name = usr, data = data)
        
    return render_template("view.html", name = usr)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.config['UPLOAD_FOLDER'] = 'static/temp'
    app.run(host = '10.117.50.233', debug=True) # host = '10.117.50.233', add it if you want the server to run on the private network 
