######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
# Author: Yanzheng Wu(U89934368)
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
from datetime import datetime as dt
import flask_login

#for image uploading
import os, base64
import sys

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '123'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		first_name = request.form.get('first_name')
		last_name = request.form.get('last_name')
		email = request.form.get('email')
		dob = request.form.get('birth_date')
		hometown = request.form.get('hometown')
		gender = request.form.get('gender')
		psd = request.form.get('password')
		
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	
	if test:
		print(cursor.execute("INSERT INTO Users (first_name, last_name, email, birth_date, hometown, gender, password) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(first_name, last_name, email, dob, hometown, gender, psd)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]


def getUsersAlbumPhotos(uid, albumid):
	cursor = conn.cursor()
	cursor.execute('''SELECT P.imgdata, P.picture_id, P.caption FROM Users AS U, Albums as A, Pictures AS P WHERE A.user_id = %s AND A.album_id = %s AND A.user_id = P.user_id AND P.album_id = A.album_id"''', (uid, albumid))
	return cursor.fetchall()


def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", photos=getUsersPhotos(uid), base64=base64)



#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# part 2 of photo uploading code
@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		album_id = request.form.get('album_id')
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		photo_data =imgfile.read()
		#print(str(imgfile))
		caption = request.form.get('caption')
		tag = request.form.get('tag').strip()
		res = tuple(map(str, tag.split(',')))
		cursor1 = conn.cursor()
		cursor1.execute('''INSERT INTO Pictures (album_id, user_id, imgdata, caption) VALUES (%s, %s, %s, %s)''', (album_id, uid, photo_data, caption))
		cursor1.execute('''SELECT COUNT(*) FROM Pictures''')
		lenc = cursor.fetchall()[0][0]
		#print(str(lenc))
		cursor2 = conn.cursor()
		for t in res:
			cursor2.execute('''INSERT INTO Tags (tag, picture_id) VALUES (%s, %s)''', (t, lenc))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		cursor = conn.cursor()
		cursor.execute('SELECT album_id, album_name FROM Albums')
		data = cursor.fetchall()
		return render_template("upload.html", data = data)
#end photo uploading code


#start like photo
@app.route('/like_photo',methods = ['GET','POST'])
def like_photo():

	if request.method == 'POST':
		picture_id = request.form.get('picture_id')
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor1 = conn.cursor()
		cursor2 = conn.cursor()
		cursor1.execute('''INSERT INTO Likes (picture_id, user_id) VALUES (%s,%s)''',( picture_id, uid))
		cursor2.execute('''UPDATE Pictures AS P SET P.num_like = P.num_like + 1 WHERE P.picture_id = %s''',(picture_id)) 
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='You have liked the photo!')
	else:
		return render_template('like_photo.html')
#end of like


#Friendlist button
@app.route('/friendlist', methods = ['GET'])
def friendlist():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute('''SELECT U1.first_name, U1.last_name, U1.email FROM Friends F, Users U1, Users U2 WHERE (F.user_id1 = %s AND F.user_id1 = U2.user_id AND F.user_id2 = U1.user_id) OR (F.user_id2 = %s AND F.user_id2 = U2.user_id AND F.user_id1 = U1.user_id)''',(uid, uid))
	data = cursor.fetchall()
	conn.commit()
	return render_template('friendlist.html', data = data)
#End of friendlist button


#Add Friend Function
@app.route('/add_friend', methods = ['GET', 'POST'])
@flask_login.login_required
def add_Friend():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		message = request.form.get('message')
		recipient_email = request.form.get('recipient_email')
		cursor = conn.cursor()
		cursor.execute('''SELECT user_id FROM Users WHERE email = %s''',(recipient_email))
		recipient_id = cursor.fetchall()
		
		cursor.execute('''SELECT * FROM Friends WHERE (Friends.user_id1 = %s AND Friends.user_id2 = %s) OR (Friends.user_id1 = %s AND Friends.user_id2 = %s)''', (uid, recipient_id, recipient_id, uid))
		temp = cursor.fetchall()
		if len(temp) > 0:
			return render_template('hello.html', name=flask_login.current_user.id, message='It is a match, gratz!')
			
		if uid == recipient_id[0][0]:
			return render_template('hello.html', name=flask_login.current_user.id, message='Sorry, you cannot add yourself!')
		
		cursor.execute('''SELECT * FROM FriendRequest WHERE sender_id = %s AND recipient_id = %s''', (recipient_id, uid))
		ret = cursor.fetchall()
		if len(ret) == 0: 
			cursor.execute('''INSERT INTO FriendRequest (sender_id, recipient_id, message) VALUES (%s, %s, %s)''', (uid, recipient_id[0][0], message))
			conn.commit()
			cursor.close()
			return render_template('hello.html', name=flask_login.current_user.id, message='You have sent the request!')
		else: 
			cursor.execute('''DELETE FROM FriendRequest WHERE sender_id = %s AND recipient_id = %s''', (recipient_id, uid))
			cursor.execute('''INSERT INTO Friends (user_id1, user_id2) VALUES (%s, %s)''', (recipient_id, uid))
			conn.commit()
			cursor.close()
			return render_template('hello.html', name=flask_login.current_user.id, message='Friend Added!')
	
	else:
		return render_template('add_friend.html')
#End of adding friend


#Receive Friend Request Function
@app.route('/receive_friend_request', methods = ['GET', 'POST'])
@flask_login.login_required
def receive_request():
	if request.method == 'POST':
		return render_template('hello.html', name=flask_login.current_user.id, message='Holding the place for ya!')
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute('''SELECT F.sender_id, U.first_name, U.last_name, F.message, U.email FROM FriendRequest F, Users U WHERE (F.recipient_id = %s AND F.sender_id = U.user_id)''', (uid))
		data = cursor.fetchall()
		cursor.close()
		return render_template('receive_friend_request.html', data = data)
# End of friend request


#album button
@app.route('/album')
def album():
	return render_template('album.html')
#end of album button


#Create an album
@app.route('/create_album',methods = ['GET','POST'])
@flask_login.login_required
def create_album():
	if request.method == 'POST':
		albumN = request.form.get('album_name')
		now = dt.now()#Server time???
		creation_time = now.strftime("%Y/%m/%d")#Year/Month/Day
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Albums (album_name, date, user_id) VALUES (%s, %s, %s)''',(albumN, creation_time, uid))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Album created!')
	else:
		return render_template('create_album.html')
#end of create album


#View all albums
@app.route('/view_album', methods = ['GET'])
def view_album():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute('''SELECT album_id, album_name, date FROM Albums WHERE user_id = %s ORDER BY album_id''', (uid))
		album_data = cursor.fetchall()
		albums = []
		for i in range(len(album_data)):
			temp = []
			temp.append(album_data[i][1])
			cursor.execute('''SELECT P.imgdata, P.caption FROM Pictures P, Albums A WHERE A.album_id = %s AND P.album_id = A.album_id''', (album_data[i][0]))
			data = cursor.fetchall()
			temp.append(data)
			albums.append(tuple(temp))
		albums = tuple(albums)
		return render_template('view_album.html', album_data=album_data, albums = albums, base64=base64)
#end of view albums


#Add Comment and like button
@app.route('/likeandcomment')
def likeandcomment():
	return render_template('likeandcomment.html')
#End of comment button


#Create a comment
@app.route('/create_comment',methods = ['GET','POST'])
def create_comment():
	
	if request.method == 'POST':
		comment_text = request.form.get('comment_text')
		picture_id = request.form.get('picture_id')
		uid = getUserIdFromEmail(flask_login.current_user.id)
		now = dt.now()
		comment_date = now.strftime("%Y/%m/%d")#Year/Month/Day
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Comments (comment_text, comment_date, picture_id, user_id) VALUES (%s,%s,%s,%s)''',(comment_text, comment_date, picture_id, uid))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Comment posted!')
	else:
		return render_template('create_comment.html')
#end of create a comment


#default page
@app.route("/", methods=['GET'])
def hello():
	try: 
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('hello.html', name=flask_login.current_user.id, message='Your Profile', photos=getUsersPhotos(uid), base64=base64)
	except: 
		return render_template('hello.html', message = 'Welcome to Photoshare :)')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
