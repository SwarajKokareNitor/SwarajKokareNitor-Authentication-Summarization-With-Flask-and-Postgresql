# db.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base

# Initialize SQLAlchemy
db = SQLAlchemy()

# User model
class User(db.Model):  # Inherit from db.Model to integrate with Flask-SQLAlchemy
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)


class PDFDocument(db.Model):
    __tablename__ = 'pdf_documents'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)  # Store the PDF as binary data
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    summary = db.Column(db.Text, nullable=True) 