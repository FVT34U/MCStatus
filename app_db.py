from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app import app as application

#app = Flask(__name__)
application.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:1234@localhost/mcstatus'
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(application)


class User(db.Model):
    __tablename__ = 'User'
    ID = db.Column(db.Integer(), primary_key=True, nullable=False)
    Login = db.Column(db.Text(), nullable=False)
    Email = db.Column(db.Text(), nullable=False)
    Password = db.Column(db.Text(), nullable=False)
    Bio = db.Column(db.Text())
    Role = db.Column(db.Text(), db.CheckConstraint('''"Role" = 'user'::text OR "Role" = 'admin'::text'''), server_default='user', nullable=False)
    Nickname = db.Column(db.Text(), nullable=False)
    servers = db.relationship('ServerPage', backref='user', cascade='all,delete-orphan')  # все сервера пользователя: user_name.servers
    comments = db.relationship('Comment', backref='user', cascade='all,delete-orphan')  # все комменты пользователя: user_name.comments
    server_rate = db.relationship('ServerRate', backref='user', cascade='all,delete-orphan')
    comment_rate = db.relationship('CommentRate', backref='user', cascade='all,delete-orphan')

    def __init__(self, login, email, password, bio, role, nickname):
        self.Login = login
        self.Email = email
        self.Password = password
        self.Bio = bio
        self.Role = role
        self.Nickname = nickname


class ServerPage(db.Model):
    __tablename__ = 'ServerPage'
    ID = db.Column(db.Integer(), primary_key=True, nullable=False)
    Name = db.Column(db.Text(), nullable=False)
    IP = db.Column(db.Text(), nullable=False)
    Version = db.Column(db.Text(), server_default='1.18', nullable=False)
    Description = db.Column(db.Text())
    Image = db.Column(db.Text())
    Rating = db.Column(db.Numeric(3, 2), db.CheckConstraint('''"Rating" >= 0 and "Rating" <= 5'''), server_default='0')
    Plugins = db.Column(db.ARRAY(db.Text()))
    Tags = db.Column(db.ARRAY(db.Text()))
    OwnerID = db.Column(db.Integer(), db.ForeignKey('User.ID'), nullable=False)  # найти пользователя: ServerPage_name.user
    comments = db.relationship('Comment', backref='server_page', cascade='all,delete-orphan')  # все комменты пользователя: user_name.comments
    server_rate = db.relationship('ServerRate', backref='server_page', cascade='all,delete-orphan')

    def __init__(self, name, ip, version, description, image, rating, plugins, tags, owner_id):
        self.Name = name
        self.IP = ip
        self.Version = version
        self.Description = description
        self.Image = image
        self.Rating = rating
        self.Plugins = plugins
        self.Tags = tags
        self.OwnerID = owner_id


class Comment(db.Model):
    __tablename__ = 'Comment'
    ID = db.Column(db.Integer(), primary_key=True, nullable=False)
    OwnerID = db.Column(db.Integer(), db.ForeignKey('User.ID'), nullable=False)
    ServerPageID = db.Column(db.Integer(), db.ForeignKey('ServerPage.ID'), nullable=False)
    CountLike = db.Column(db.Integer(), server_default='0', nullable=False)
    CountDislike = db.Column(db.Integer(), server_default='0', nullable=False)
    Text = db.Column(db.Text())
    comment_rate = db.relationship('CommentRate', backref='comment', cascade='all,delete-orphan')

    def __init__(self, owner_id, server_page_id, count_like, count_dislike, text):
        self.OwnerID = owner_id
        self.ServerPageID = server_page_id
        self.CountLike = count_like
        self.CountDislike = count_dislike
        self.Text = text


class CommentRate(db.Model):
    __tablename__ = 'CommentRate'
    RowID = db.Column(db.Integer(), primary_key=True, nullable=False)
    CommentID = db.Column(db.Integer(), db.ForeignKey('Comment.ID'), nullable=False)
    UserID = db.Column(db.Integer(), db.ForeignKey('User.ID'), nullable=False)
    RateNumber = db.Column(db.Integer(), db.CheckConstraint('''"RateNumber" >= -1 or "RateNumber" <= 1'''), server_default='0')

    def __init__(self, comment_id, user_id, rate_number):
        self.CommentID = comment_id
        self.UserID = user_id
        self.RateNumber = rate_number


class ServerRate(db.Model):
    __tablename__ = 'ServerRate'
    RowID = db.Column(db.Integer(), primary_key=True, nullable=False)
    ServerPageID = db.Column(db.Integer(), db.ForeignKey('ServerPage.ID'), nullable=False)
    UserID = db.Column(db.Integer(), db.ForeignKey('User.ID'), nullable=False)
    RateNumber = db.Column(db.Integer(), db.CheckConstraint('''"RateNumber" >= 0 and "RateNumber" <= 5'''), server_default='0')

    def __init__(self, server_page_id, user_id, rate_number):
        self.ServerPageID = server_page_id
        self.UserID = user_id
        self.RateNumber = rate_number


#db.drop_all()
#db.create_all() #создать/удалить сущности


if __name__ == '__main__':
    u1 = User('qwe', 'qwe@gmail.com', '1234', None, 'user', 'qwerty')
    u2 = User('ewq', 'ewq@gmail.com', '4321', None, 'user', 'ytrewq')
    a1 = User('admin', 'amd@gmail.com', 'admin1', 'yeah', 'admin', 'AdMiN')

    #db.session.add_all([u1, u2, a1])
    #db.session.commit()

    s1 = ServerPage('Server1', '127.56.28.111', '1.18.2', 'server by qwe', 'static/image.png', 4.5, ['authme', 'worldguard'], ['survival', 'anarchy', '1.18.2'], 7)

    #db.session.add_all([s1])
    #db.session.commit()

    bind1 = ServerRate(4, 7, 3)

    #db.session.add_all([bind1])
    #db.session.commit()

    com1 = Comment(7, 4, 0, 0, 'классный сервер, рекомендую')
    #db.session.add(com1)
    #db.session.commit()

    #del1 = User.query.filter_by(ID=10).first()
    #db.session.delete(del1)
    #db.session.commit()


