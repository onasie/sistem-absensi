from datetime import datetime
from flaskblog import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))

class User(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(20), unique=True, nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)
  image_file = db.Column(db.String(20), nullable=False)
  password = db.Column(db.String(60), nullable=False)
  posts = db.relationship('Post', backref='author', lazy=True)
  face = db.relationship('Photo', backref='facePhotos', lazy=True)
  presence = db.relationship('Presence', backref="presencing", lazy=True)

  def __repr__(self):
    return f"User('{self.id}','{self.username}', '{self.face}')"

class Post(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(100), nullable=False)
  date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
  content = db.Column(db.Text, nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

  def __repr__(self):
    return f"Post('{self.title}', '{self.date_posted}')"

class Photo(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  img_path = db.Column(db.String(120), nullable=False)
  emb_path = db.Column(db.String(120), nullable=False)

  def __repr__(self):
    return f"Photo('{self.id}','{self.user_id}', '{self.img_path}', '{self.emb_path}')"

class Presence(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

  def __repr__(self):
    return f"Presencing('{self.id}', '{self.user_id}', '{self.date}')"