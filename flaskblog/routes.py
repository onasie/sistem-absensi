import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort, Response, send_from_directory
from flaskblog import app, db, bcrypt
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from flaskblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flaskblog.capture import capture_and_save
from flaskblog.camera import Camera
from pathlib import Path
from flaskblog.recogCamera import recogCamera

camera = Camera()
recog_Camera = recogCamera()

@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.all()
    users = User.query.all()
    return render_template('home.html', posts=posts, users=users)

@app.route("/about")
@login_required
def about():
    return render_template('face_recognition.html', title='About')

@app.route("/register", methods=['GET', 'POST'])
@login_required
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        picture_file = save_picture(form.picture.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, image_file=picture_file)
        db.session.add(user)
        db.session.commit()
        flash('New account has been created! ' + form.username.data +  ' now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
          picture_file = save_picture(form.picture.data)
          current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('settings'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('settings.html', title='Account Settings',
                           image_file=image_file, form=form)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

@app.route("/r", methods=['POST'])
def capture():
    user = request.form.get('userSelect')
    im, gray = camera.capture_frame()
    capture_and_save(str(user), im, gray)
    return render_template("send_to_init.html")

@app.route("/images/last")
def last_image():
    p = Path("images/last.png")
    if p.exists():
        r = "last.png"
    else:
        r = "not_found.jpeg"
    return send_from_directory("../images", r)

def gen(cam):
    while True:
        frame = cam.get_frame()
        if cam is recog_Camera:
            name = cam.get_name()
            print("name", name)

        yield (b'--frame\r\n'
               b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')
        # yield(name)

@app.route("/stream", methods=['GET'])
def stream():
  recog_Camera.stop()
  camera.run()
  users = User.query.all()
  return render_template('stream.html', title='Stream', users=users)

@app.route("/recognition")
def recognition():
  # posts = Post.query.filter_by(id)
  camera.stop()
  recog_Camera.run()
  return render_template('recognition.html', title='Recognition')

@app.route("/video_feed/<int:video_id>/")
def video_feed(video_id):
    if video_id is 1:
      cam = camera
    else:
      cam = recog_Camera
    return Response(gen(cam),
        mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/content")
def content():
    def inner():
        while True:
            name = recog_Camera.get_name()
            print("name in route", name)
            yield (name)
    return Response(inner(), mimetype='text/html')