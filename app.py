from flask import Flask, render_template, url_for, request, redirect, abort, session, flash
from flask_sqlalchemy import SQLAlchemy
from mcstatus import JavaServer
import minestat
import os

app = Flask(__name__, template_folder='templates')

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:1234@localhost/mcstatus'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

UPLOAD_FOLDER = 'static/user_images/'
ALLOWED_EXTENSIONS = {'png', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    """ Функция проверки расширения файла """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    servers = ServerPage.query.order_by(ServerPage.Rating.desc()).all()
    if 'loggedIn' in session:
        if session['loggedIn']:
            if User.query.filter_by(ID=session['userID']).first().Role == 'admin':
                session['isAdmin'] = True
            else:
                session['isAdmin'] = False
            return render_template('Main_page.html', session=session, servers=servers)
    else:
        session['loggedIn'] = False
        session['isAdmin'] = False
        session.modified = True
    return render_template('Main_page.html', session=session, servers=servers)


@app.route('/about')
def about_page():
    return render_template('About.html', session=session)


@app.route('/login', methods=['POST', 'GET'])
def login_page():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        get_data = User.query.filter_by(Login=login).first()
        if User.query.filter_by(Login=login).first() is not None:
            if login == get_data.Login and password == get_data.Password:
                print('Logged In!!!')
                session['loggedIn'] = True
                session['userID'] = get_data.ID
                if User.query.filter_by(ID=session['userID']).first().Role == 'admin':
                    session['isAdmin'] = True
                else:
                    session['isAdmin'] = False
                session.modified = True
                return redirect('/')
        flash('Вы ввели неверный логин или пароль, попробуйте ещё раз')
        return redirect('/login')
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
        if User.query.filter_by(Login=login).first() is not None:
            flash("Такой логин уже занят, попробуйте другой")
            return redirect('/reg')
        if User.query.filter_by(Email=email).first() is not None:
            flash("На этот адрес электронной почты уже зарегистрирован аккаунт, попробуйте другой")
            return redirect('/reg')
        if User.query.filter_by(Nickname=nickname).first() is not None:
            flash("Такой никнейм уже занят, попробуйте другой")
            return redirect('/reg')
        user1 = User(login=login, email=email, password=password, bio=bio, role=role, nickname=nickname)
        try:
            db.session.add(user1)
            db.session.commit()
            session['loggedIn'] = True
            session['userID'] = User.query.filter_by(Login=login, Password=password).first().ID
            session.modified = True  # инфа о том, что сессия была модифицирована
            return redirect('/')
        except:
            flash('Ошибка при занесении данных в базу, обратитесь к администратору')
            return redirect('/reg')
    else:
        return render_template('Sign_up_page.html')


@app.route('/server/<int:server_id>', methods=['POST', 'GET'])
def server_page(server_id):
    if request.method == 'POST':
        if request.form['new_comment'] != '' and request.form['score'] != '':
            comment = request.form['new_comment']
            score = request.form['score']
            if Comment.query.filter_by(ServerPageID=server_id, OwnerID=session['userID']).first() is None:
                c1 = Comment(owner_id=session['userID'], server_page_id=session['curServerID'], count_like=0, count_dislike=0, text=comment)
                sc1 = ServerRate(server_page_id=server_id, user_id=session['userID'], rate_number=score)
                try:
                    db.session.add_all([c1, sc1])
                    db.session.commit()
                except:
                    flash('Ошибка при занесении данных в базу, обратитесь к администратору')
            else:
                flash('Вы уже оставляли комментарий с оценкой')
        else:
            flash('Пожалуйста, напишите текст комментария и оценку')
        return redirect('/server/' + str(session['curServerID']))
    else:
        server = ServerPage.query.filter_by(ID=server_id).first()
        session['curServerID'] = server_id
        ms = minestat.MineStat(server.IP, 25565, 1)
        online = 0
        if ms.online:
            online = ms.current_players
        return render_template('Server_page.html', session=session, server=server, ServerRate=ServerRate, online=online)


@app.route('/createserver', methods=['POST', 'GET'])
def create_server_page():
    if 'loggedIn' not in session or 'userID' not in session:
        return redirect('/login')
    if not session['loggedIn'] or session['userID'] is None:
        return redirect('login')
    if request.method == 'POST':
        server_name = request.form['serverName']
        ip = request.form['IP']
        version = request.form['version']
        description = request.form['description']
        tags = request.form['tags'].split(', ')
        plugins = request.form['plugins'].split(', ')
        server_image = request.files['imgServer']
        if server_image is None:
            flash('Нет изображения')
            return redirect('/createserver')
        if server_image.filename == '':
            flash('Нет изображения')
            return redirect('/createserver')
        if server_image and allowed_file(server_image.filename):
            server_image.save(os.path.join(app.config['UPLOAD_FOLDER'], server_image.filename))
        else:
            flash('Ошибка в загрузке изображения')
            return redirect('/createserver')
        if ServerPage.query.filter_by(IP=ip).first() is not None:
            flash('Сервер с таким IP-адресом уже находится в системе!')
            return redirect('/createserver')
        server1 = ServerPage(name=server_name, ip=ip, version=version, description=description, image='../static/user_images/' + server_image.filename, rating=0.,
                             plugins=plugins, tags=tags, owner_id=session['userID'])
        try:
            db.session.add(server1)
            db.session.commit()
            return redirect('/server/' + str(ServerPage.query.filter_by(IP=ip).first().ID))
        except:
            flash('Ошибка при занесении данных в базу, обратитесь к администратору')
            return redirect('/createserver')
    else:
        return render_template('Create_server_page.html', session=session)


@app.route('/editprofile', methods=['POST', 'GET'])
def edit_profile():
    if request.method == 'POST':
        if 'loggedIn' not in session or 'userID' not in session:
            return redirect('/login')
        if not session['loggedIn'] or session['userID'] is None:
            return redirect('/login')
        nickname = request.form['nickName']
        email = request.form['email']
        password = request.form['password']
        new_password = request.form['newPassword']
        description = request.form['description']
        if User.query.filter_by(Email=email).first() is not None:
            flash("На этот адрес электронной почты уже зарегистрирован аккаунт, попробуйте другой")
            return redirect('/editprofile')
        if User.query.filter_by(Nickname=nickname).first() is not None:
            flash("Такой никнейм уже занят, попробуйте другой")
            return redirect('/editprofile')
        if password != new_password:
            flash("Введенные пароли не совпадают")
            return redirect('/editprofile')
        if password == User.query.filter_by(ID=session['userID']).first().Password:
            flash("Новый пароль не должен совпадать со старым")
            return redirect('/editprofile')
        user1 = User.query.filter_by(ID=session['userID']).first()
        if nickname != '':
            user1.Nickname = nickname
        if email != '':
            user1.Email = email
        if password != '' and new_password != '':
            user1.Password = password
        if description != '':
            user1.Bio = description
        db.session.add(user1)
        db.session.commit()
        return redirect('/profile/' + str(session['userID']))
    else:
        if 'loggedIn' in session and 'userID' in session:
            if session['loggedIn'] and session['userID'] is not None:
                user = User.query.filter_by(ID=session['userID']).first()
                return render_template('Edit_profile.html', session=session, user=user)
        return redirect('/')


@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.filter_by(ID=user_id).first()
    return render_template('Profile.html', session=session, user=user)


@app.route('/editserver', methods=['POST', 'GET'])
def edit_server():
    if request.method == 'POST':
        if 'loggedIn' not in session or 'userID' not in session:
            return redirect('/login')
        if not session['loggedIn'] or session['userID'] is None:
            return redirect('/login')
        if session['userID'] != ServerPage.query.filter_by(ID=session['curServerID']).first().OwnerID:
            return redirect('/')
        server_name = request.form['serverName']
        version = request.form['version']
        ip = request.form['IP']
        description = request.form['description']
        tags = request.form['tags']
        plugins = request.form['plugins']
        server_image = request.files['imgServer']
        if server_name != '' and ServerPage.query.filter_by(Name=server_name).first() is not None:
            flash("Такое название сервера уже занято, попробуйте другое")
            return redirect('/editserver')
        if server_image and allowed_file(server_image.filename):
            server_image.save(os.path.join(app.config['UPLOAD_FOLDER'], server_image.filename))
        else:
            flash('Ошибка в загрузке изображения')
            return redirect('/createserver')
        if ServerPage.query.filter_by(IP=ip).first() is not None:
            flash('Сервер с таким IP-адресом уже находится в системе!')
            return redirect('/createserver')
        server1 = ServerPage.query.filter_by(ID=session['curServerID']).first()
        if server_name != '':
            server1.Name = server_name
        if version != '':
            server1.Version = version
        if ip != '':
            server1.IP = ip
        if description != '':
            server1.Description = description
        if tags != '':
            server1.Tags = tags.split(', ')
        if plugins != '':
            server1.Plugins = plugins.split(', ')
        if server_image.filename != '':
            server1.Image = '../static/user_images/' + server_image.filename
        db.session.add(server1)
        db.session.commit()
        return redirect('/server/' + str(session['curServerID']))
    else:
        if session['userID'] != ServerPage.query.filter_by(ID=session['curServerID']).first().OwnerID:
            return redirect('/')
        server = ServerPage.query.filter_by(ID=session['curServerID']).first()
        return render_template('Edit_Server_page.html', session=session, server=server)


@app.route('/comment/<int:comment_id>/del')
def del_comment(comment_id):
    if session['isAdmin'] == False and session['userID'] != Comment.query.filter_by(ID=comment_id).first().OwnerID:
        return redirect('/')
    del1 = Comment.query.filter_by(ID=comment_id).first()
    del2 = ServerRate.query.filter_by(ServerPageID=session['curServerID'], UserID=session['userID']).first()
    try:
        db.session.delete(del1)
        db.session.delete(del2)
        db.session.commit()
        return redirect('/server/' + str(session['curServerID']))
    except:
        return redirect('/')


@app.route('/server/<int:server_id>/del')
def del_server(server_id):
    if session['isAdmin'] == False and session['userID'] != ServerPage.query.filter_by(ID=server_id).first().OwnerID:
        return redirect('/')
    del1 = ServerPage.query.filter_by(ID=server_id).first()
    try:
        db.session.delete(del1)
        db.session.commit()
        return redirect('/')
    except:
        flash('Ошибка при занесении данных в базу, обратитесь к администратору')
        return redirect('/server/' + str(session['curServerID']))


@app.route('/comment/<int:comment_id>/like')
def dislike_comment(comment_id):
    if 'loggedIn' in session:
        if session['loggedIn']:
            if CommentRate.query.filter_by(CommentID=comment_id, UserID=session['userID']).first() is None:
                cr1 = CommentRate(comment_id=comment_id, user_id=session['userID'], rate_number=1)
                try:
                    db.session.add(cr1)
                    db.session.commit()
                except:
                    flash('Ошибка при занесении данных в базу, обратитесь к администратору')
            elif CommentRate.query.filter_by(CommentID=comment_id, UserID=session['userID']).first().RateNumber == 0:
                cr1 = CommentRate.query.filter_by(CommentID=comment_id, UserID=session['userID']).first()
                cr1.RateNumber = 1
                try:
                    db.session.add(cr1)
                    db.session.commit()
                except:
                    flash('Ошибка при занесении данных в базу, обратитесь к администратору')
            elif CommentRate.query.filter_by(CommentID=comment_id, UserID=session['userID']).first().RateNumber == 1:
                cr1 = CommentRate.query.filter_by(CommentID=comment_id, UserID=session['userID']).first()
                cr1.RateNumber = 0
                try:
                    db.session.add(cr1)
                    db.session.commit()
                except:
                    flash('Ошибка при занесении данных в базу, обратитесь к администратору')
            else:
                cr1 = CommentRate.query.filter_by(CommentID=comment_id, UserID=session['userID']).first()
                cr1.RateNumber = 1
                try:
                    db.session.add(cr1)
                    db.session.commit()
                except:
                    flash('Ошибка при занесении данных в базу, обратитесь к администратору')
        else:
            return redirect('/login')
    else:
        return redirect('/login')
    return redirect('/server/' + str(session['curServerID']))


@app.route('/comment/<int:comment_id>/dislike')
def like_comment(comment_id):
    if 'loggedIn' in session:
        if session['loggedIn']:
            if CommentRate.query.filter_by(CommentID=comment_id, UserID=session['userID']).first() is None:
                cr1 = CommentRate(comment_id=comment_id, user_id=session['userID'], rate_number=-1)
                try:
                    db.session.add(cr1)
                    db.session.commit()
                except:
                    flash('Ошибка при занесении данных в базу, обратитесь к администратору')
            elif CommentRate.query.filter_by(CommentID=comment_id, UserID=session['userID']).first().RateNumber == 0:
                cr1 = CommentRate.query.filter_by(CommentID=comment_id, UserID=session['userID']).first()
                cr1.RateNumber = -1
                try:
                    db.session.add(cr1)
                    db.session.commit()
                except:
                    flash('Ошибка при занесении данных в базу, обратитесь к администратору')
            elif CommentRate.query.filter_by(CommentID=comment_id, UserID=session['userID']).first().RateNumber == 1:
                cr1 = CommentRate.query.filter_by(CommentID=comment_id, UserID=session['userID']).first()
                cr1.RateNumber = -1
                try:
                    db.session.add(cr1)
                    db.session.commit()
                except:
                    flash('Ошибка при занесении данных в базу, обратитесь к администратору')
            else:
                cr1 = CommentRate.query.filter_by(CommentID=comment_id, UserID=session['userID']).first()
                cr1.RateNumber = 0
                try:
                    db.session.add(cr1)
                    db.session.commit()
                except:
                    flash('Ошибка при занесении данных в базу, обратитесь к администратору')
        else:
            return redirect('/login')
    else:
        return redirect('/login')
    return redirect('/server/' + str(session['curServerID']))


@app.route('/search')
def search():
    ip = request.args['ip']
    if ServerPage.query.filter_by(IP=ip).first() is not None:
        return redirect('/server/' + str(ServerPage.query.filter_by(IP=ip).first().ID))
    ms = minestat.MineStat(ip, 25565, 1)
    server = {}
    if ms.online:
        server = {
            'online': ms.current_players,
            'ping': ms.latency,
            'motd': ms.stripped_motd,
            'version': ms.version,
            'ip': ip,
        }
    else:
        return redirect('/')
    return render_template('Search.html', server=server)



@app.route('/exit')
def _exit():
    session.pop('isAdmin', None)
    session.pop('userID', None)
    session.pop('curServerID', None)
    session['loggedIn'] = False
    return redirect('/')


@app.errorhandler(404)
def http_404_handler(error):
    return render_template('404.html')


@app.errorhandler(505)
def http_404_handler(error):
    return "<p>HTTP 505 Error Encountered</p>", 505


if __name__ == '__main__':
    app.secret_key = 'i hate jinners, sorry'
    app.run(debug=True)
