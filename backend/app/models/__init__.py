from backend.app.extensions import db
from datetime import datetime, timezone
from sqlalchemy.sql import func
from sqlalchemy import Enum

# Many-to-Many Relationship Table Between Photos & Faces
photo_faces = db.Table(
    'photo_faces',
    db.Column('photo_id', db.Integer, db.ForeignKey('photos.id'), primary_key=True, index=True),
    db.Column('face_id', db.Integer, db.ForeignKey('faces.id'), primary_key=True, index=True)
)

# Users Table
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    token_hash = db.Column(db.String(255), nullable=True, default=None)
    photo_count = db.Column(db.Integer, nullable=False, default=0)
    max_photos = db.Column(db.Integer, nullable=False, default=5000)
    last_otp = db.Column(db.String(200), nullable=True, default=None)
    login_attempt = db.Column(db.Integer, default=0)
    login_at = db.Column(db.TIMESTAMP(timezone=True), server_default=func.now())
    created_at = db.Column(db.TIMESTAMP(timezone=True), server_default=func.now())
    account_status = db.Column(Enum('pending','active', 'suspended', 'deleted', name='account_status_enum'),nullable=False, default='pending')

# Photos Table
class Photo(db.Model):
    __tablename__ = 'photos'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    photo_url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # Many-to-Many Relationship with Faces
    faces = db.relationship('Face', secondary=photo_faces, backref='photos')

    def to_dict(self):
        return {
            'id': self.id,
            'photo_url': self.photo_url,
        }

#  Faces Table
class Face(db.Model):
    __tablename__ = 'faces'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=True)
    face_url = db.Column(db.String(255))
    face_count = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'face_url': self.face_url,
            'face_count': self.face_count,
        }
