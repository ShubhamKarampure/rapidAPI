from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import wikipediaapi
from datetime import timedelta
import os

app = Flask(__name__)

# Database Configuration (NeonDB)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://neondb_owner:npg_daRS61CNBKbH@ep-shy-term-a8jcan7o-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "your_secret_key"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Wikipedia API Setup
wiki_api = wikipediaapi.Wikipedia(
    language='en',
    user_agent='RapidAPI/1.0 (shubhamkarampure@gmail.com)'  )

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Educational Resource Model
class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)

# Create Database Tables
with app.app_context():
    db.create_all()

# User Registration
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"message": "User already exists"}), 400
    user = User(username=data["username"], password=data["password"])
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

# User Login
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(username=data["username"], password=data["password"]).first()
    if not user:
        return jsonify({"message": "Invalid credentials"}), 401
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200

# Add a Resource (Protected Route)
@app.route("/resource", methods=["POST"])
@jwt_required()
def add_resource():
    data = request.json
    resource = Resource(**data)
    db.session.add(resource)
    db.session.commit()
    return jsonify({"message": "Resource added successfully"}), 201

# Get All Resources
@app.route("/resources", methods=["GET"])
def get_resources():
    resources = Resource.query.all()
    return jsonify([{
        "id": r.id, "title": r.title, "subject": r.subject,
        "difficulty": r.difficulty, "content_type": r.content_type,
        "description": r.description
    } for r in resources])

# Wikipedia API - Fetch Educational Content
@app.route("/wiki/<topic>", methods=["GET"])
def get_wikipedia_content(topic):
    page = wiki_api.page(topic)
    if not page.exists():
        return jsonify({"error": "Topic not found"}), 404
    return jsonify({"title": page.title, "summary": page.summary[:500]})

# Run the App
if __name__ == "__main__":
    app.run(debug=True)
