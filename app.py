from flask import Flask, render_template, url_for, request, redirect, abort, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, template_folder='templates')

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:1234@localhost/mcstatus'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


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


@app.route('/')
def main_page():
    if 'loggedIn' in session:
        if session['loggedIn']:
            return render_template('Main_page.html')  # Подгрузить новую шапку
    else:
        session['loggedIn'] = False
        session.modified = True
    return render_template('Main_page.html')


@app.route('/about')
def about_page():
    return render_template('About.html')


@app.route('/login', methods=['POST', 'GET'])
def login_page():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        get_data = User.query.filter_by(Login=login).all()
        for i in get_data:
            if login in i.Login:
                if password in i.Password:
                    #print('Logged In!!!' + str(i.ID) + login + ' ' + password)
                    print('Logged In!!!')
                    session['loggedIn'] = True
                    session['userID'] = i.ID
                    session.modified = True
                    return redirect('/')
        else:
            print('Invalid login or password!!!')
            abort(404)
    else:
        if 'loggedIn' in session:
            if session['loggedIn']:
                return redirect('/')
        else:
            session['loggedIn'] = False
            session.modified = True
        return render_template('Login_page.html')


@app.route('/reg', methods=['POST', 'GET'])
def reg_page():
    if request.method == 'POST':
        login = request.form['login']
        email = request.form['email']
        password = request.form['password']
        bio = ''
        role = 'user'
        nickname = request.form['nickName']
        user1 = User(login=login, email=email, password=password, bio=bio, role=role, nickname=nickname)
        try:
            db.session.add(user1)
            db.session.commit()
            session['loggedIn'] = True
            session['userID'] = User.query.filter_by(Login=login, Password=password).first().ID
            session.modified = True  # инфа о том, что сессия была модифицирована
            return redirect('/')
        except:
            print('DB ERROR!!!')
            return redirect('/reg')
    else:
        return render_template('Sign_up_page.html')


@app.route('/server/<int:server_id>')
def server_page(server_id):
    return render_template('Server_page.html')


@app.route('/createserver')
def creat_server_page():
    return render_template('Create_server_page.html')


@app.route('/editprofile')
def edit_profile():
    return render_template('Edit_profile.html')


@app.route('/profile')
def profile():
    session['loggedIn'] = True
    return render_template('Profile.html')


@app.errorhandler(404)
def http_404_handler(error):
    return "<p>HTTP 404 Error Encountered</p>", 404


@app.errorhandler(505)
def http_404_handler(error):
    return "<p>HTTP 505 Error Encountered</p>", 505


if __name__ == '__main__':
    app.secret_key = 'i hate jinners, sorry'
    app.run(debug=True)
