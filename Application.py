import random
import string
import boto3

from flask import Flask, request, render_template, redirect, session, url_for
from boto3.dynamodb.conditions import Key

#shouldn't be putting credentials in code! I'll have to search for alternative method (IAM) when I have more time.
dynamodb = boto3.resource('dynamodb', region_name='us-east-1', aws_access_key_id='AKIAW3MEABS7NBPKBZEW', aws_secret_access_key='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')

class DBController:
    
    def validateLogin(email, password):
        
        table_name = "login"
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
        
        table_name = "login"
        table = dynamodb.Table(table_name)
        
        response = table.get_item(
            Key={
                'email': email
            }
        )
        
        if 'Item' in response:
            return response['Item']['user_name']
        

application = Flask(__name__)

#https://www.javatpoint.com/python-program-to-generate-a-random-string#:~:text=ADVERTISEMENT-,The%20random.,choices()%20function.
application.secret_key = "".join(random.choices(string.ascii_uppercase + string.digits, k = 10))

@application.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if DBController.validateLogin(email, password) == True:
            
            print(application.secret_key)   
            
            session['loggedUser'] = email
        
            return redirect(url_for('main'))
        else:
            
            error = 'Invalid email or password. Please try again.'

    return render_template('login.html', error=error)

@application.route('/main', methods=["GET", "POST"])
def main():
    
    if 'loggedUser' in session:
        
        loggedUsername = DBController.getUsername(session['loggedUser'])
        
        return render_template('main.html', loggedUser = loggedUsername)
    
    else:
        return redirect(url_for('login'))
    


if __name__ == "__main__":
    #application.debug = True
    application.run()