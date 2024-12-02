import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# Set the SQLALCHEMY_DATABASE_URI in the app config
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'app/database/app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Optional, to suppress warnings

# Initialize the database
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Initialize database (this creates the database file if it doesn't exist)
with app.app_context():
    db.create_all()

# Functions for managing users
def list_users():
    """List all users."""
    users = User.query.all()
    if not users:
        print("No users found.")
    else:
        for user in users:
            print(f"ID: {user.id}, Username: {user.username}, Created At: {user.created_at}")

def add_user(username, password):
    """Add a new user."""
    if User.query.filter_by(username=username).first():
        print(f"User '{username}' already exists.")
        return
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"User '{username}' added successfully.")

def delete_user(username, password=None):
    """Delete a user with password verification."""
    user = User.query.filter_by(username=username).first()
    if not user:
        print(f"User '{username}' not found.")
        return
    
    # If password is provided, check it before deletion
    if password:
        if not user.check_password(password):
            print(f"Incorrect password for user '{username}'. Deletion aborted.")
            return

    confirmation = input(f"Are you sure you want to delete user '{username}'? (yes/no): ")
    if confirmation.lower() == "yes":
        db.session.delete(user)
        db.session.commit()
        print(f"User '{username}' deleted successfully.")
    else:
        print("Deletion cancelled.")

def edit_user(username, new_username=None, new_password=None):
    """Edit a user's username or password."""
    user = User.query.filter_by(username=username).first()
    if not user:
        print(f"User '{username}' not found.")
        return

    # Validate and set the new username
    if new_username:
        if User.query.filter_by(username=new_username).first():
            print(f"Username '{new_username}' already exists.")
            return
        user.username = new_username

    # Set new password if provided
    if new_password:
        user.set_password(new_password)

    db.session.commit()
    print(f"User '{username}' updated successfully.")

# Main logic for handling command-line arguments
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python app.py [list|add|delete|edit]")
        sys.exit(1)

    command = sys.argv[1].lower()

    with app.app_context():
        if command == "list":
            list_users()
        elif command == "add":
            if len(sys.argv) != 4:
                print("Usage: python app.py add <username> <password>")
                sys.exit(1)
            username = sys.argv[2]
            password = sys.argv[3]
            add_user(username, password)
        elif command == "delete":
            if len(sys.argv) < 3:
                print("Usage: python app.py delete <username> [--password <password>]")
                sys.exit(1)
            username = sys.argv[2]
            password = None
            if "--password" in sys.argv:
                password = sys.argv[sys.argv.index("--password") + 1]
            delete_user(username, password)
        elif command == "edit":
            if len(sys.argv) < 3:
                print("Usage: python app.py edit <username> [--username <new_username>] [--password <new_password>]")
                sys.exit(1)

            # Ensure there are no more than 4 arguments for the 'edit' command
            if len(sys.argv) > 5:
                print("Too many arguments. Usage: python app.py edit <username> [--username <new_username>] [--password <new_password>]")
                sys.exit(1)

            username = sys.argv[2]
            new_username = None
            new_password = None

            # Extract new username and password if provided
            if "--username" in sys.argv:
                new_username = sys.argv[sys.argv.index("--username") + 1]
            if "--password" in sys.argv:
                new_password = sys.argv[sys.argv.index("--password") + 1]

            # Ensure only one new username and/or password is provided
            if (new_username and new_password) and len(sys.argv) != 5:
                print("Usage: python app.py edit <username> --username <new_username> [--password <new_password>]")
                sys.exit(1)

            edit_user(username, new_username, new_password)
        else:
            print(f"Unknown command: {command}")
            print("Usage: python app.py [list|add|delete|edit]")
            sys.exit(1)
