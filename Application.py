import random
import string
import boto3

from flask import Flask, request, render_template, redirect, url_for, session
from boto3.dynamodb.conditions import Key

#shouldn't be putting credentials in code! I'll have to search for alternative method (IAM) when I have more time.
dynamodb = boto3.resource('dynamodb', region_name='us-east-1', aws_access_key_id='AKIAW3MEABS7NBPKBZEW', aws_secret_access_key='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')

def validateLogin(email, password):
    
    table_name = "cca3-login"
    table = dynamodb.Table(table_name)
    
    response = table.get_item(
        Key={
            'email': email
        }
    )
    
    if 'Item' in response:
        if response['Item']['password'] == password:
            return True  
    return False 

def getUsername(email):
    
    table_name = "cca3-login"
    table = dynamodb.Table(table_name)
    
    response = table.get_item(
        Key={
            'email': email
        }
    )
    
    return response['Item']['user_name']

def getStaffLevel(email):
    
    table_name = "cca3-login"
    table = dynamodb.Table(table_name)
    
    response = table.get_item(
        Key={
            'email': email
        }
    )
    
    return response['Item']['staff_level']

def checkExists(email):
    
    table_name = "cca3-login"
    table = dynamodb.Table(table_name)
    
    response = table.get_item(
        Key={
            'email': email
        }
    )
    
    if 'Item' in response:
        return True
    return False
        
def addNewUser(email, username, password, staffLevel):
    
    table_name = "cca3-login"
    table = dynamodb.Table(table_name)
    
    item = {
        'email': email,
        'user_name': username,
        'password': password,
        'staff_level': staffLevel
    }
    
    table.put_item(Item=item)
    

def getUsersList():
    
    table_name = "cca3-login"
    table = dynamodb.Table(table_name)
    response = table.scan()
    users = []
    
    for item in response['Items']:
        user = {
            'email': item['email'],
            'name': item['user_name'],
            'password': item['password'],
            'staffLevel': item['staff_level']
        }
        users.append(user)
    
    return users

def editUser(email, name, staffLvl):
    
    table_name = "cca3-login"
    table = dynamodb.Table(table_name)
    
    response = table.get_item(
        Key={
            'email': email
        }
    )
    
    item = response['Item']
    user = {
        'email': item['email'],
        'user_name': name,
        'password': item['password'],
        'staff_level': staffLvl
    }
    
    table.put_item(Item=user)   
    
def deleteUser(email):

    table_name = "cca3-login"
    table = dynamodb.Table(table_name)
    key = {'email': email}
    
    response = table.delete_item(Key=key)


def getLoggedUser(email):
    
    table_name = "cca3-login"
    table = dynamodb.Table(table_name)
    
    response = table.get_item(
        Key={
            'email': email
        }
    )
    
    item = response['Item']
    user = {
        'email': item['email'],
        'user_name': item['user_name'],
        'password': item['password'],
        'staff_level': item['staff_level'],
        'password': item['password']
    }
    
    return user


application = Flask(__name__)

#https://www.javatpoint.com/python-program-to-generate-a-random-string#:~:text=ADVERTISEMENT-,The%20random.,choices()%20function.
application.secret_key = "".join(random.choices(string.ascii_uppercase + string.digits, k = 10))


@application.route("/", methods=["GET", "POST"])
def login():
    
    if 'loggedUser' in session:
        session.clear()
    
    error = None
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        
        if validateLogin(email, password) == True:
            
            session['loggedUser'] = email
            session['staffLevel'] = getStaffLevel(email)
        
            return redirect(url_for('main'))
        else:
            
            error = 'Invalid email or password. Please try again.'

    return render_template('login.html', error=error)


@application.route('/main', methods=["GET", "POST"])
def main():
    
    if 'loggedUser' in session:
        
        loggedUsername = getUsername(session['loggedUser'])
        
        return render_template('main.html', loggedUser = loggedUsername, staffLevel = session['staffLevel'])
    
    else:
        return redirect(url_for('login'))

@application.route('/admin', methods=["GET", "POST"])
def admin():
    
    if 'loggedUser' in session:
        
        error = request.args.get('m')
        
        users = getUsersList()
        
        loggedUser = getLoggedUser(session['loggedUser'])
        
        return render_template('admin.html', staffLevel = session['staffLevel'], loggedUser = loggedUser, users = users, error = error)
    
    else:
        return redirect(url_for('login'))
    
@application.route('/addUser', methods=["GET", "POST"])
def addUser():
    
    if 'loggedUser' in session:
        
        if request.method == 'POST':

            email = request.form['addUserEmail'].lower()
            username = request.form['addUserName']
            password = request.form['addUserPassword']
            passwordconf = request.form['addUserPasswordConfirm']
            staffLevel = request.form['addUserStaffLvl']
            
            if checkExists(email) == True:
                
                m = "Email already exists."

            elif password != passwordconf:
                
                m = "Password mismatch."

            else:
                
                addNewUser(email, username, password, staffLevel)
                m = "New user added"

            return redirect(url_for('admin', m = m))
                 
    else:
        return redirect(url_for('login'))


@application.route('/admin_process', methods=["GET", "POST"])
def adminProcess():
    
    loggedUser = getLoggedUser(session['loggedUser'])
    
    if 'loggedUser' in session:
        
        if request.method == 'POST':
            
            action = request.form['action']
            email = request.form['editUserEmail']
            name = request.form['editUserName']
            
            m = None

            
            if loggedUser['staff_level'] == "2":
                password = request.form['editUserPassword']
                passwordConfirm = request.form['editUserPasswordConfirm']
                staffLvl = "2"
                
                if password != passwordConfirm and password != "":
                    m = "Password Mismatch"
                
                else:
                    
                    if password == "":
                        password = loggedUser['password']
                    
                    addNewUser(email, name, password, staffLvl)
                    m = "User details changed"
                
                return redirect(url_for('admin', m = m))
            
            else:
                
                staffLvl = request.form['editUserLvl']
                
                if action == 'edit':
                
                    editUser(email, name, staffLvl)
                    m = "Changes to staff successful"
                
                elif action == 'delete':
                
                    deleteUser(email)
                    m = "Staff removed successful"

            return redirect(url_for('admin', m = m))
    else:
        return redirect(url_for('login'))


if __name__ == "__main__":
    #application.debug = True
    application.run()