from flask import Flask, render_template, url_for


app = Flask(__name__, template_folder='templates')


@app.route('/')
def main_page():
    return render_template('Main_page.html')


@app.route('/about')
def about_page():
    return render_template('Main_page.html')


@app.route('/login')
def login_page():
    return render_template('Login_page.html')


@app.route('/reg')
def reg_page():
    return render_template('Sign_up_page.html')


@app.route('/server/<int:server_id>')
def server_page(server_id):
    return render_template('Server_page.html')


@app.errorhandler(404)
def http_404_handler(error):
    return "<p>HTTP 404 Error Encountered</p>", 404


if __name__ == '__main__':
    app.run(debug=True)
