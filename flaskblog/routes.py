import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, Response, send_from_directory
from flaskblog import app, db, bcrypt
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm
from flaskblog.models import User, Presence
from flask_login import login_user, current_user, logout_user, login_required
from flaskblog.capture import capture_and_save
from flaskblog.camera import Camera
from pathlib import Path
from flaskblog.cameraRecog import cameraRecog
import pytz
from datetime import datetime

camera = Camera()
recog_Camera = cameraRecog()

@app.route("/")
@app.route("/home")
def home():
    recog_Camera.stop()
    camera.stop()
    presences = []
    try:
        if current_user.username == "admin":
            presences = Presence.query.all()
        else:
            presences = current_user.presence
    except:
        pass
    return render_template('home.html', presences=presences)

@app.route("/user")
def user():
    recog_Camera.stop()
    camera.stop()
    users = User.query.all()
    return render_template('user.html', users=users)

@app.route("/register", methods=['GET', 'POST'])
@login_required
def register():
    recog_Camera.stop()
    camera.stop()
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
    recog_Camera.stop()
    camera.stop()
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
    recog_Camera.stop()
    camera.stop()
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
    recog_Camera.stop()
    camera.stop()
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

@app.route("/r", methods=['POST'])
def capture():
    user = request.form.get('userSelect')
    im, gray = camera.capture_frame()
    capture_and_save(str(user), im, gray)
    user = User.query.get_or_404(str(user))
    flash('Berhasil mengambil wajah ' + user.username + '! Perhatikan ulang nama yang dipilih jika ingin melakukan pendaftaran lagi!', 'success')
    return redirect(url_for('stream'))

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

        yield (b'--frame\r\n'
               b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')

@app.route("/stream", methods=['GET'])
def stream():
  recog_Camera.stop()
  camera.run()
  users = User.query.all()
  return render_template('stream.html', title='Stream', users=users)

@app.route("/recognition")
def recognition():
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

@app.route("/presence", methods=['GET', 'POST'])
@login_required
def new_presencing():
    id = recog_Camera.get_name()

    if id != "Unknown":
        user = User.query.get_or_404(id)
        userPresence = user.presence
        lastPresence = userPresence.order_by(None).order_by(Presence.id.desc()).first()
        if user == current_user or current_user.username == "admin":
            now_utc = datetime.utcnow()
            tz = pytz.timezone('Asia/Jakarta')
            now_kl = now_utc.replace(tzinfo=pytz.utc).astimezone(tz)
            if lastPresence:
                if lastPresence.status == "Masuk" and lastPresence.dateIn.strftime("%d-%m-%Y") == now_kl.strftime("%d-%m-%Y"):
                    presence = Presence.query.get_or_404(lastPresence.id)
                    presence.dateOut = now_kl
                    presence.status = 'Keluar'
                    db.session.commit()
                    flash('Selamat! ' + user.username + ' berhasil absen keluar!', 'success')
                else:
                    presence = Presence(user_id=id, dateIn=now_kl)
                    db.session.add(presence)
                    db.session.commit()
                    flash('Selamat! ' + user.username + ' berhasil absen masuk!', 'success')
            else:
                presence = Presence(user_id=id, dateIn=now_kl)
                db.session.add(presence)
                db.session.commit()
                flash('Selamat! ' + user.username + ' berhasil absen masuk!', 'success')
        else:
            flash(user.username + ' absen dengan Akun yang salah!', 'danger')
        return redirect(url_for('home'))
    flash('Absensi Gagal! Silahkan Ulangi Absensi!', 'danger')
    return redirect(url_for('recognition'))