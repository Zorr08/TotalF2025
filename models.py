import os
import logging
import json
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SQLAlchemy()

class CachedPlayer(db.Model):
    __tablename__ = 'cached_players'
    
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, nullable=False)
    data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_cached_data(player_id):
        cache = CachedPlayer.query.filter_by(player_id=player_id).first()
        if cache and cache.updated_at > datetime.utcnow() - timedelta(minutes=5):
            return json.loads(cache.data)
        return None
    
    @staticmethod
    def update_cache(player_id, data):
        cache = CachedPlayer.query.filter_by(player_id=player_id).first()
        if cache:
            cache.data = json.dumps(data)
            cache.updated_at = datetime.utcnow()
        else:
            cache = CachedPlayer(player_id=player_id, data=json.dumps(data))
            db.session.add(cache)
        db.session.commit()

class AppSettings(db.Model):
    __tablename__ = 'app_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), nullable=False, unique=True)
    value = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Player(db.Model):
    __tablename__ = 'players'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    photo_url = db.Column(db.String(255))
    team_logo = db.Column(db.String(255))
    price = db.Column(db.Float)
    form = db.Column(db.Float)
    points_per_match = db.Column(db.Float)
    total_points = db.Column(db.Integer)
    total_bonus = db.Column(db.Integer)
    ict_index = db.Column(db.Float)
    selected_by_percent = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'photo_url': self.photo_url,
            'team_logo': self.team_logo,
            'price': self.price,
            'form': self.form,
            'points_per_match': self.points_per_match,
            'total_points': self.total_points,
            'total_bonus': self.total_bonus,
            'ict_index': self.ict_index,
            'selected_by_percent': self.selected_by_percent,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class SerieAPlayer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    team = db.Column(db.String(255))
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<SerieAPlayer {self.name}>"