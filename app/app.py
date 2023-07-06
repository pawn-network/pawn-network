from flask import Flask, render_template, session, redirect, request
from itsdangerous import URLSafeTimedSerializer
from database import Database
from utils import security
from libs.PNet.pnpacket import PNPacket
from libs.PNet.pnclient import PNClient

from gmail import Email
import secrets
import time
import re

# Database application setup
database = Database('localhost', 'root', '', 'social')

# Application Instance
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
database.init(app)

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Application routes
## Index route
@app.route('/')
def index():
    database.connect()
    database.open_cursor()

    database.cursor.execute("SELECT posts.id, posts.title, users.username, posts.created_at, posts.content FROM posts JOIN users ON posts.user_id = users.id ORDER BY posts.created_at DESC")
    posts = database.cursor.fetchall()

    database.close_cursor()
    return render_template('index.html', posts=posts)

## Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'username' in session:

        database.connect()
        database.open_cursor()

        database.cursor.execute("SELECT posts.id, posts.title, users.username, posts.created_at, posts.content FROM posts JOIN users ON posts.user_id = users.id ORDER BY posts.created_at DESC")
        posts = database.cursor.fetchall()

        database.close_cursor()
        return render_template('dashboard.html', posts=posts)
    return redirect('/login')

## Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect('/dashboard')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        database.connect()
        database.open_cursor()
        database.cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, username))
        user = database.cursor.fetchone()

        if user:
            if user[4] == 0:
                database.close_cursor()
                return render_template('login.html', error='Você não verificou o seu e-mail ainda.')
    
            hashed_password = user[2]
            if security.check_password(password, hashed_password):
                session['username'] = username
                database.close_cursor()
                return redirect('/dashboard')
        
        database.close_cursor()
        return render_template('login.html', error='Usuário/email ou senha estão incorretos.')
    return render_template('login.html')

## Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect('/dashboard')
    
    if request.method == 'POST':
        email_template = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        email = request.form['email']
        if re.match(email_template, email) == False:
            error = 'O e-mail fornecido contém um padrão inválido.'
            return render_template('register.html', error=error)
        
        discord = request.form['discord']
        if security.discord_format(discord) == False:
            error = 'O discord fornecido contém um formato invalido.'
            return render_template('register.html', error=error)
        
        username = request.form['username']
        password = request.form['password']


        database.connect()
        database.open_cursor()

        database.cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = database.cursor.fetchone()

        if existing_user:
            error = 'Este nome de usuário ou e-mail já estão registrados.'
            return render_template('register.html', error=error)

        email_sender = Email()
        hashed_password = security.hash_password(password)
        temp_token = email_sender.generate_token()
        database.cursor.execute("INSERT INTO users (username, password, email, temp_token) VALUES (%s, %s, %s, %s)", (username, hashed_password, email, temp_token))
        database.connection.commit()
        database.close_cursor()
        
        email_sender.send_email('Confirmação de E-mail', f"""
            <h1>Bem-vindo à comunidade Pawn Network.</h1>
            <p>Confirme o seu e-mail clicando no botão abaixo:</p>
            <a href="http://127.0.0.1:5000/verify_email/{username}/{temp_token}" style="color: #fff; text-decoration: none; font-family: Verdana,'Helvetica Neue',HelveticaNeue,Helvetica,Arial,sans-serif; height: 48px; line-height: 48px; border-width: 0; border-radius: 24px; background-color: #303030; display: inline-block; font-size: 16px; margin: 0 auto; font-weight: bold; padding: 0 2rem;">Verificar conta</a>
            <p>Atenciosamente,</p>
            <p><strong>Pawn Network.</strong></p>""", email)
        
        error = 'Foi enviado um token de verificação em seu email.'
        return render_template('register.html', error=error)
    return render_template('register.html')

## Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

## New post route
@app.route('/new_post')
def new_post():
    if 'username' in session:
        return render_template('new_post.html')
    return render_template('register.html')

## Change password route
@app.route('/change_password')
def change_password():
    if 'username' in session:
        return render_template('change_password.html')
    return render_template('register.html')

## Email validation to change  route
@app.route('/verify_code', methods=['POST'])
def verify_code():
    if 'username' in session:
        if request.method == 'POST':
            username = session['username']
            email = request.form['email']
            database.connect()
            database.open_cursor()
            database.cursor.execute("SELECT email FROM users WHERE username = %s", (username))
            result = database.cursor.fetchone() 

            if result is not None:
                user_email = result[0]
                if user_email == email:
                    email_sender = Email()
                    temp_code = email_sender.generate_code()
                    database.cursor.execute("UPDATE users SET temp_code = %s, time_code = %s WHERE username = %s", (temp_code, time.time(), username))
                    database.connection.commit()
                    database.close_cursor()

                    email_sender.send_email('Código de verificação', f"""
                        <h1>Uma solicitação de mudança de senha foi requisitada.</h1>
                        <p>Se não foi você que requisitou a mudança, ignore o e-mail e proteja sua conta.</p>
                        <h2><stronger>Código de verificação:</stronger></h2>
                        <h2 style="color: #00d7fd;">{temp_code}</h2>
                        <p>Atenciosamente,</p>
                        <p><strong>Pawn Network.</strong></p>""", user_email)
                    return render_template('verify_code.html')
                else:
                    database.close_cursor()
                    error = 'O e-mail fornecido não está vinculado a sua conta.'
                    return render_template('change_password.html', error=error)
            else:
                database.close_cursor()
                error = 'Não foi encontrado nenhum e-mail vinculado a sua conta.'
                return render_template('change_password.html', error=error)
            
    return render_template('register.html')

## Confirm code and change password route
@app.route('/confirm_code', methods=['POST'])
def confirm_code():
    if 'username' in session:
        if request.method == 'POST':
            username = session['username']
            code = request.form['code']
            password = request.form['password']

            database.connect()
            database.open_cursor()
            database.cursor.execute("SELECT * FROM users WHERE username = %s", (username))
            result = database.cursor.fetchone()

            if result[6] == code and result[7] < time.time()+300:
                hashed_password = security.hash_password(password)
                database.cursor.execute("UPDATE users SET password = %s, temp_code = 'Null', time_code = '0' WHERE username = %s", (hashed_password, username))
                database.connection.commit()
                database.close_cursor()
                session.pop('username', None)
                msg = 'Senha alterada com sucesso, logue novamente.'
                return render_template('login.html', error=msg)
            else:
                database.close_cursor()
                error = 'Código inválido ou expirado.'
                return render_template('verify_code.html', error=error)
    return render_template('login.html')

## Verify email route
@app.route('/verify_email/<username>/<token>')
def verify_email(username, token):
    email = Email()

    database.connect()
    database.open_cursor()
    database.cursor.execute("SELECT * FROM users WHERE username = %s", (username))
    result = database.cursor.fetchone()

    if result[4] == 1:
        return redirect('/dashboard')
    
    if email.is_token_valid(token, result[5]):
        session['username'] = username
        database.cursor.execute("UPDATE users SET temp_token = 'Null', verified = 1 WHERE username = %s", (username))
        database.connection.commit()
        database.close_cursor()
        email.send_email('Bem-vindo à Pawn Network', f"""
            <h1>Olá <strong>{username}</strong>,</h1>
            <p>Parabéns por verificar o seu e-mail.</p>
            <p>Estamos muito felizes pelo seu interesse em fazer parte da nossa comunidade.</p>
            <p>Esperamos que você adquira e partilhe muito conhecimento e, a partir disso, ajude novos usuários.</p>
            <p>Caso deseje, clique no botão abaixo para conhecer a nossa dashboard.</p>
            <<a href=http://127.0.0.1:5000/dashboard style="line-height:23px;font-family:'Poppins',sans-serif;text-align:left;padding:12px;margin:0px 0px 0px 100px;background-color:#ccc;color:#212121;text-decoration:none">Dashboard</a>
            <p>Atenciosamente,</p>
            <p><strong>Pawn Network.</strong></p>""", result[3])
        return redirect('/dashboard')
    else:
        database.close_cursor()
        return 'O token de confirmação é inválido ou expirou.'

## Create post route
@app.route('/create_post', methods=['POST'])
def create_post():
    if 'username' in session:
        username = session['username']
        content = request.form['content']
        title = request.form['title']

        database.connect()
        database.open_cursor()

        database.cursor.execute("SELECT id FROM users WHERE username = %s", (username))
        user_id = database.cursor.fetchone()[0]

        database.cursor.execute("INSERT INTO posts (user_id, title, content, created_at) VALUES (%s, %s, %s, NOW())", (user_id, title, content))
        database.connection.commit()
        database.close_cursor()

    return redirect('/dashboard')
