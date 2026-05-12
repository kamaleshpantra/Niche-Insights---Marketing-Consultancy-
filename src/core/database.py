from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

# Define database path (SQLite)
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "niche_insights.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    body = Column(Text)
    url = Column(String)
    score = Column(Integer)
    num_comments = Column(Integer)
    topic = Column(String)
    ai_response = Column(Text)
    sentiment = Column(String)
    impact_score = Column(Float)
    conversion_potential = Column(Float)
    reach = Column(Integer)
    slack_status = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_post_to_db(post_data):
    db = SessionLocal()
    try:
        # Check if post already exists
        existing_post = db.query(Post).filter(Post.id == post_data["id"]).first()
        if existing_post:
            # Update existing post
            for key, value in post_data.items():
                setattr(existing_post, key, value)
        else:
            # Create new post
            new_post = Post(**post_data)
            db.add(new_post)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_all_posts():
    db = SessionLocal()
    try:
        return db.query(Post).order_by(Post.created_at.desc()).all()
    finally:
        db.close()

def update_post_status(post_id, status):
    db = SessionLocal()
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            post.slack_status = status
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
