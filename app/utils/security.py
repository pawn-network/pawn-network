import bcrypt

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def discord_format(texto):
    if "#" in texto:
        index = texto.index("#")
        if len(texto[index+1:]) == 4 and texto[index+1:].isdigit():
            return True
    return False