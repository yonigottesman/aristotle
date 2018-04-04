from app import db
from flask_login import UserMixin
from app import login
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    runs = db.relationship('Run', backref='owner', lazy='dynamic'
                           , cascade='delete')
    experiments = db.relationship('Experiment', backref='owner', lazy='dynamic'
                                  , cascade='delete')

    
    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Experiment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(150))
    columns = db.Column(db.String(400))
    runs = db.relationship('Run', backref='experiment', lazy='dynamic'
                           , cascade='delete')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    column_extract_code = db.Column(db.String(600))
    def __repr__(self):
        return '<Experiment {}>'.format(self.description)    

    
class Run(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(50))
    run_result = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    experiment_id = db.Column(db.Integer, db.ForeignKey('experiment.id'))
    columns = db.Column(db.String(400))
    
    def __repr__(self):
        return '<Run {}>'.format(self.description)    


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
