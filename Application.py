import random
import string
import boto3

from flask import Flask, request, render_template, redirect, session, url_for
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
        

application = Flask(__name__)

#https://www.javatpoint.com/python-program-to-generate-a-random-string#:~:text=ADVERTISEMENT-,The%20random.,choices()%20function.
application.secret_key = "".join(random.choices(string.ascii_uppercase + string.digits, k = 10))

@application.route("/", methods=["GET", "POST"])
def login():
    
    if 'loggedUser' in session:
        session.clear()
    
    error = None
    if request.method == 'POST':
        email = request.form['email']
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
    return render_template('admin.html', staffLevel = session['staffLevel'])



if __name__ == "__main__":
    #application.debug = True
    application.run()
    
    