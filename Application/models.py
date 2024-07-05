from Application import db, login_mang, app
from datetime import datetime
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as ser

@login_mang.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    elections = db.relationship('Election', backref='admin', lazy=True)
    votes = db.relationship('Votes', backref='admin', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = ser(app.config['SECRET_KEY'], expires_sec)
        return s.dump({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = ser(app.config['SECRET_KEY'])
        try:
            user_id = s.load(token)['user_id']
        except:
            return None
        return User.query.get(user_id)





    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.today())
    end_date = db.Column(db.DateTime, nullable=False, default=datetime.today())
    candidates = db.relationship('Candidate', backref='candidates', lazy=True)
    votes = db.relationship('Votes', backref='candidates', lazy=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    @classmethod
    def get_next_valid_id(clss):
        all_ids = Election.query.with_entities(Election.id).order_by(Election.id).all()
        if len(all_ids) == 0:
            return 1
        if len(all_ids) == all_ids[-1][0]:
            return len(all_ids) + 1
        current_valid_id = 1
        while current_valid_id < len(all_ids) and current_valid_id == all_ids[current_valid_id-1][0]:
            current_valid_id += 1
        return current_valid_id

    def too_early(self):
        if self.start_date > datetime.today():
            return True
        else:
            return False

    def too_late(self):
        if self.end_date < datetime.today():
            return True
        else:
            return False


    def already_voted(self, user_id, election_id):
        print(Votes.query.filter_by(user_id=user_id, election_id=election_id).first())
        if Votes.query.filter_by(user_id=user_id, election_id=election_id).all():
            return True
        else:
            return False


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    votes = db.Column(db.Integer, nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)


class Votes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)


