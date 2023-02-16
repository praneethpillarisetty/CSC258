import pyrebase

config = {
    "apiKey": "AIzaSyDEwGq_NX1KPjgdGYtqcTwH3jSyK5ueBGU",
  "authDomain": "csc258-67d5d.firebaseapp.com",
  "projectId": "csc258-67d5d",
  "storageBucket": "csc258-67d5d.appspot.com",
  "messagingSenderId": "671548835336",
  "appId": "1:671548835336:web:48f40b52219cfc6b0d33bd",
  "measurementId": "G-NL8DMWZ8K1",
  "databaseURL": ""
}

firebase = pyrebase.initialize_app(config)

auth = firebase.auth()

#user = auth.create_user_with_email_and_password(email, password) #to create a user with help of email and password

def firebaselogin(email,password):
    try :
        user = auth.sign_in_with_email_and_password(email, password)
        auth.get_account_info(user['idToken'])
        return True, user
    except:
        return False, ''

def firebasesignup(email, password):
    try :
        user = auth.create_user_with_email_and_password(email, password)
        auth.get_account_info(user['idToken'])
        return True
    except:
        return False

def firebasesignout(user):
    try :
        user = auth.signOut()
        return True
    except:
        return False
