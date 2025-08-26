from datetime import datetime
from flask import Flask, jsonify, redirect, request
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# Import configuration, database, and models
try:
    from .config import Config
    from .database import Base, SessionLocal, engine
    from .models import Transcript, User
except ImportError:  # Running as a script
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent))
    from config import Config
    from database import Base, SessionLocal, engine
    from models import Transcript, User


def create_app() -> Flask:
    """Create Flask application"""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.debug = Config.DEBUG

    # Enable CORS for frontend requests
    CORS(app, resources={r"/api/*": {"origins": Config.FRONTEND_ORIGIN}})

    # Initialize database tables
    with app.app_context():
        Base.metadata.create_all(bind=engine)

    # ------------------ ROUTES ------------------

    @app.get("/")
    def index():
        """Redirect to frontend"""
        return redirect(Config.FRONTEND_URL, code=302)

    @app.get("/api/health")
    def health() -> tuple:
        """Health check endpoint"""
        return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()}), 200

    # ------------------ TRANSCRIPTS ------------------

    @app.post("/api/transcripts")
    def create_transcript():
        """Create a new transcript"""
        payload = request.get_json(force=True) or {}
        text = (payload.get("text") or "").strip()
        language = payload.get("language")
        if not text:
            return jsonify({"error": "text is required"}), 400

        db = SessionLocal()
        try:
            item = Transcript(text=text, language=language)
            db.add(item)
            db.commit()
            db.refresh(item)
            return jsonify({
                "id": item.id,
                "text": item.text,
                "language": item.language,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }), 201
        finally:
            db.close()

    @app.get("/api/transcripts")
    def list_transcripts():
        """List latest transcripts"""
        db = SessionLocal()
        try:
            items = db.query(Transcript).order_by(Transcript.id.desc()).limit(100).all()
            return jsonify([
                {
                    "id": i.id,
                    "text": i.text,
                    "language": i.language,
                    "created_at": i.created_at.isoformat() if i.created_at else None,
                } for i in items
            ]), 200
        finally:
            db.close()

    @app.get("/api/transcripts/<int:item_id>")
    def get_transcript(item_id: int):
        """Fetch a specific transcript"""
        db = SessionLocal()
        try:
            item = db.get(Transcript, item_id)
            if not item:
                return jsonify({"error": "not found"}), 404
            return jsonify({
                "id": item.id,
                "text": item.text,
                "language": item.language,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }), 200
        finally:
            db.close()

    # ------------------ USER AUTH ------------------

    @app.post("/api/register")
    def register_user():
        """Register a new user"""
        payload = request.get_json(force=True) or {}
        first_name = (payload.get("first_name") or "").strip()
        last_name = (payload.get("last_name") or "").strip()
        email = (payload.get("email") or "").strip().lower()
        password = (payload.get("password") or "").strip()

        if not first_name or not last_name or not email or not password:
            return jsonify({"error": "All fields are required"}), 400

        db = SessionLocal()
        try:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                return jsonify({"error": "Email already registered"}), 409

            password_hash = generate_password_hash(password)
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password_hash=password_hash,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            return jsonify({
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }), 201
        finally:
            db.close()

    @app.post("/api/login")
    def login_user():
        """User login"""
        payload = request.get_json(force=True) or {}
        email = (payload.get("email") or "").strip().lower()
        password = (payload.get("password") or "").strip()

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user or not check_password_hash(user.password_hash, password):
                return jsonify({"error": "Invalid credentials"}), 401

            return jsonify({
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }), 200
        finally:
            db.close()

    return app


# ------------------ APP ENTRY POINT ------------------
# For local development and Render deployment
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
else:
    app = create_app()
