# from mailbox import Message
import os
from mailjet_rest import Client
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
import mysql.connector
import MySQLdb.cursors
import re
from itsdangerous import URLSafeTimedSerializer
import time
import random

app = Flask(__name__)

app.secret_key = 'tomaszogrodnikjestgruby'

mysql = mysql.connector.connect(
    host="34.159.139.65",
    user='kuba',
    password='zabki62a',
    db = 'twitter',
)

mailjet = Client(auth=('d4a0e56cd58e2eb358753e75b3152d38', '0c6be36828e9b20a85888c19f17c1101'))

@app.route('/')
def directtologin():
    if 'loggedin' in session:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))
            

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if 'loggedin' in session:
        return redirect(url_for('home'))
    else:
        msg = ''
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
            username = request.form['username']
            password = request.form['password']
            cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s AND verification = 1', (username, password,))
            account = cursor.fetchone()
            # account = str(account)
            if account:
                session['loggedin'] = True
                # session["id"] = account['id']
                session["username"] = username
                session["password"] = password
                return redirect(url_for('home'))
            else:
                msg = 'Incorrect username/password or check inbox to verification account'
        return render_template('index.html', msg=msg)

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if 'loggedin' in session:
        return redirect(url_for('home'))
    else:
        msg = ''
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists!'
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address!'
            elif not re.match(r'[A-Za-z0-9]+', username):
                msg = 'Username must contain only characters and numbers!'
            elif not username or not password or not email:
                msg = 'Please fill out the form!'
            else:
                session["email"] = email
                session["confirmemail"] = True
                cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, 0, 0, 0)', (username, password, email,))
                mysql.commit()
                msg = 'You have successfully registered, now only confirm your email in inbox'
                data = {
                'FromEmail': 'twitter.technischools@gmail.com',
                'FromName': 'Twitter Technischools',
                'Subject': 'Twitter Technischools verification!',
                'Text-part': 'Hello, Thank you for register, confirm your account clicking link down!',
                'Html-part': '127.0.0.1:5000/confirm',
                'Recipients': [{'Email':(email)}]
                    }
            result = mailjet.send.create(data=data)
            return "Mail with verification link has sent, check your inbox"
        elif request.method == 'POST':
            msg = 'Please fill out the form!'
        return render_template('register.html', msg=msg)
    
@app.route('/confirm/')
def confirm():
    if 'confirmemail' in session:
        mail = session["email"]
        mail = str(mail)
        cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE accounts SET verification = 1 where email = %s', (mail,))
        mysql.commit()
        session.clear()
        return render_template('verification-confirm.html')
    else:
        return "You not have active session to confirm mail"


@app.route('/home/', methods=['GET', 'POST'])
def home():
    if 'loggedin' in session:
        if request.method == "POST":
            data = dict(request.form)
            users = getusers(data["search"])
        else:
            users = []
        cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT username, body, "created-at", likes  FROM posts order by "created-at"')
        post = cursor.fetchall()
        print(post)

        

        for _post in post:
            print (_post)
        # username = post
        return render_template('home.html', username=session['username'], post=post, usr=users)
    else:
        return redirect(url_for('login'))

@app.route('/create-post/', methods=['GET', 'POST'])
def posting():
        if 'loggedin' in session:
            msg = ''
            if request.method == 'POST' and 'body' in request.form:
                username=session['username']
                body = request.form['body']
                cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('INSERT INTO posts VALUES (NULL, %s, %s, CURRENT_TIMESTAMP, 0)', (username, body))
                mysql.commit()
                return render_template('createpost.html', username=username, body=body)
            elif request.method == 'POST':
                msg = 'Please fill out the form!'
            return render_template('createpost.html', msg=msg)
        else:
            return redirect(url_for('login'))

@app.route('/profile/')
def profile():
    if 'loggedin' in session:
        username=session['username']
        password=session['password']
        cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT email FROM accounts WHERE username = %s and password = %s', (username,password,))
        email = cursor.fetchall()
        for x in range(2):
            email = email[-1]
        return render_template('profile.html', username=username, password=password, email=email,)
    else:
        return redirect(url_for('login'))

@app.route('/logout/')
def logout():
    session['loggedin'] = False
    session.clear()
    return redirect(url_for('login'))

@app.route('/reset/', methods=['GET', 'POST'])
def reset():
    if 'loggedin' in session:
        return redirect(url_for('home'))
    else:
        if request.method == 'POST' and 'email' in request.form:
            email = request.form['email']
            session["email"] = email
            code = random.randint(1000,9999)
            code = str(code)
            session["code"] = code
            
            data = {
                'FromEmail': 'twitter.technischools@gmail.com',
                'FromName': 'Twitter Technischools',
                'Subject': 'Twitter Technischools Reset Password!',
                'Text-part': 'Hello, here your code to reset password!',
                'Html-part': (code),
                'Recipients': [{'Email':(email)}]
                    }
            result = mailjet.send.create(data=data)
            return redirect(url_for('reset2'))
        return render_template('reset.html')
        
@app.route('/reset2/', methods=['GET', 'POST'])
def reset2():
    if 'loggedin' in session:
        return redirect(url_for('home'))
    else:
        if request.method == 'POST' and 'code' in request.form:
            code2 = request.form['code']
            code = session["code"]
            if code == code2:
                return redirect(url_for('reset3'))
            else:
                msg = "Incorrent code"
                return render_template('resetcode.html', msg=msg)
        return render_template('resetcode.html')
    
@app.route('/reset3/', methods=['GET', 'POST'])
def reset3():
    if 'loggedin' in session:
        return redirect(url_for('home'))
    else:
        if request.method == 'POST' and 'password' in request.form:
            email = session["email"]
            password = request.form['password']
            cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE accounts SET password = %s where email = %s', (password,email))
            mysql.commit()
            return render_template('password-confirm.html')
    return render_template('resetpassword.html')

@app.route('/likeadd/')
def likeadd():
    cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE posts SET likes = likes + 1')
    mysql.commit()
    return redirect(url_for('home'))


def getusers(search):
        cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT username FROM `accounts` WHERE `username` like %s OR `email` like %s LIMIT 1",("%"+search+"%", "%"+search+"%",))
        results = cursor.fetchall()
        session['results'] = results[0]
        return results

@app.route('/user/')
def profilesearch():
    if 'loggedin' in session:
            username2 = session['results']
            comma_delim = ','
            username4 = comma_delim.join(username2)
            cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT username FROM accounts WHERE username = %s', (username2))
            user = cursor.fetchall()
            cursor.execute('SELECT following FROM accounts WHERE username = %s', (username2))
            following = cursor.fetchall()
            cursor.execute('SELECT followers FROM accounts WHERE username = %s', (username2))
            followers = cursor.fetchall()
            username = session['username']
            comma_delim = ','
            username3 = comma_delim.join(username2)
            cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT `from` from followers where `from` = %s and `to` = %s', (username, username3))
            fromuser = cursor.fetchall()
            fromuser2 = str(fromuser)
            fromuser2 = fromuser2.replace("[('", "").replace("',)]", "")
            if username4 == username:
                return render_template('profileuserself.html', username=username2, following=following, followers=followers)
            else:
                if fromuser2 == username:
                    return render_template('profileusersunfollow.html', username=username2, following=following, followers=followers)
                else:
                    return render_template('profileusersfollow.html', username=username2, following=following, followers=followers)
    else:
        return redirect(url_for('login'))
    
@app.route('/follow/')
def followadd():
    username = session['username']
    username2 = session['results']
    comma_delim = ','
    username3 = comma_delim.join(username2)
    cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE `accounts` SET `followers` = CASE WHEN followers IS NULL THEN 1 ELSE followers + 1 END WHERE `username` = %s', (username2))
    cursor.execute('INSERT INTO followers VALUES (NULL, %s, %s)', (username, username3))
    mysql.commit()
    return redirect(url_for('profilesearch'))

@app.route('/unfollow/')
def unfollow():
    username = session['username']
    username2 = session['results']
    comma_delim = ','
    username3 = comma_delim.join(username2)
    cursor = mysql.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE `accounts` SET `followers` = `followers` - 1 WHERE `username` = %s', (username2))
    mysql.commit()
    cursor.execute('DELETE FROM followers WHERE `from` = %s AND `to` = %s', (username, username3))
    mysql.commit()
    return redirect(url_for('profilesearch'))