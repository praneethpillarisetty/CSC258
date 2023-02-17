from flask import Flask,render_template,flash, redirect,url_for,session,logging,request
from flask_sqlalchemy import SQLAlchemy
import authenticate as Auth

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
login_users = {}

class login_user():
    fb_user_obj = None
    def set_fb_user(self, usr):
        self.fb_user_obj = usr
    def unset_fb_user(self):
        self.fb_user_obj = None

class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    password = db.Column(db.String(80))
    
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
            current_user = login_user()
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
        return render_template("login.html", error = error)
    else:
        login = user.query.filter_by(username = usr).first()
        del login_users[login.email]
        error = "Signout Sucessfull!"
        return render_template("login.html", error = error)
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
            return redirect(url_for("login"))
        else:
            error = "Failed to Register Try Again!"
            return render_template("register.html", error = error)
    return render_template("register.html", error = error)

@app.route("/<usr>/home", methods = ["GET", "POST"])
def user_home(usr):
    return render_template("home.html", name = usr)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True) # host = '10.117.50.233', add it if you want the server to run on the private network 
