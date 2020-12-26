import os, hashlib
import csv
import psycopg2
from datetime import datetime
from flask import Flask, jsonify, render_template, request, g, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, current_user, logout_user
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

UPLOAD_FOLDER = 'static/images/'

app = Flask(__name__, static_url_path='/static/')
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:postgres@localhost:5432/insta"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "secret"

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String())
    password = db.Column(db.String())

class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500))
    image_url = db.Column(db.String())
    upload_date = db.Column(db.DateTime())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"))

class Follower(db.Model):
    __tablename__ = 'followers'

    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"))
    follower = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"))

class Topic(db.Model):
    __tablename__ = 'topics'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def home():
    total_posts = Post.query.all()
    total_posts_dict = {}
    # total_posts_list = []
    for p in total_posts:
        total_posts_dict[p.id] = {
        "text":p.text,
        "image_url":p.image_url,
        "upload_date":p.upload_date,
        "username": User.query.filter_by(id=p.user_id).first().username
        }
    favourite_posts = []
    favourite_people = []
    favourites = Follower.query.filter_by(follower=current_user.get_id()).all()
    for fav in favourites:
        favourite_people.append(User.query.filter_by(id=fav.user).first().username)
        posts = Post.query.filter_by(user_id=fav.user).all()
        for p in posts:
            favourite_posts.append(p.id)

    sorted_posts = []
    for p in favourite_posts:
        sorted_posts.append(total_posts_dict[p])
    
    for k, v in total_posts_dict.items():
        if k not in favourite_posts:
            sorted_posts.append(v)
    
    return render_template('index.html', total_posts=sorted_posts, favourite_people=favourite_people)


@app.route('/profile')
@login_required
def profile():
    total_posts = Post.query.filter_by(user_id=current_user.get_id()).all()
    return render_template('profile.html', total_posts=total_posts)


@app.route('/dump_data')
@login_required
def dump_data():
    users_query = """
            SELECT * from users
        """

    posts_query = """
            SELECT * from posts
        """

    followers_query = """
            SELECT * from followers
        """

    topics_query = """
            SELECT * from topics
        """

    conn = psycopg2.connect(database="insta", user="postgres", host="localhost", password="postgres")

    cur = conn.cursor()
    cur.execute(users_query)

    with open('dump_data/users.csv', 'w') as f:
        writer = csv.writer(f, delimiter=',')
        for row in cur.fetchall():
            writer.writerow(row)

    cur.close()

    cur = conn.cursor()
    cur.execute(posts_query)

    with open('dump_data/posts.csv', 'w') as f:
        writer = csv.writer(f, delimiter=',')
        for row in cur.fetchall():
            writer.writerow(row)

    cur.close()

    cur = conn.cursor()
    cur.execute(followers_query)

    with open('dump_data/followers.csv', 'w') as f:
        writer = csv.writer(f, delimiter=',')
        for row in cur.fetchall():
            writer.writerow(row)

    cur.close()

    cur = conn.cursor()
    cur.execute(topics_query)

    with open('dump_data/topics.csv', 'w') as f:
        writer = csv.writer(f, delimiter=',')
        for row in cur.fetchall():
            writer.writerow(row)

    cur.close()

    conn.close()
    return jsonify(message=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template('login.html')
    elif request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        # check if user actually exists
        # take the user supplied password, hash it, and compare it to the hashed password in database
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return render_template('login.html')
        print("Logged in")
        # if the above check passes, then we know the user has the right credentials
        login_user(user, remember=remember)
        return redirect('/')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('login')


@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == "GET":
        return render_template('signup.html')
    elif request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

    with app.app_context():
        user = User.query.filter_by(username=username).first()

        if user: 
            print("User already exists.")
            return redirect('/signup')

        new_user = User(username=username, password=generate_password_hash(password, method='sha256'))
        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()
        print("User has been registered.")
        return redirect('/login')

@app.route('/create_post', methods=['GET','POST'])
@login_required
def create_post():
    if request.method == "GET":
        return render_template('create-post.html')
    if request.method == "POST":
        text = request.form.get('text')
        upload_date = datetime.now()
        f = request.files['image']
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) 
        image_url = app.config['UPLOAD_FOLDER'] + f.filename
        user_id = current_user.get_id()
        
        post = Post(text=text, upload_date=upload_date, image_url=image_url, user_id=user_id)
        db.session.add(post)
        db.session.commit()

        print("Post has been created.")
        return redirect('/')


@app.route('/update_post/<post_id>', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    value = Post.query.filter_by(id=int(post_id)).first()
    if request.method == "GET":
        return render_template('edit_post.html', value=value)
    if request.method == "POST":
        text = request.form.get('text')
        value.text = text
        f = request.files['image']
        filename = secure_filename(f.filename)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) 
        image_url = app.config['UPLOAD_FOLDER'] + f.filename
        value.image_url = image_url
        db.session.commit()
        print("Post has been updated.")
        return redirect('/profile')

@app.route('/delete_post/<post_id>', methods=['GET'])
@login_required
def delete_post(post_id):
        Post.query.filter_by(id=post_id).delete()
        db.session.commit()
        print("Post has been deleted.")
        return redirect('/')


@app.route('/follow/<username>', methods=['GET'])
def follow(username):
    user_id = User.query.filter_by(username=username).first().id
    follower = current_user.get_id()
    f = Follower(user=user_id, follower=follower)
    db.session.add(f)
    db.session.commit()
    return jsonify(message=True)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
