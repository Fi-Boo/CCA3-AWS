from flask import Flask, request, render_template, redirect, url_for
from Controllers import DBController

application = Flask(__name__)

@application.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if DBController.validateLogin(email, password) == True:
    
            return redirect(url_for('success'))
        else:
            
            error = 'Invalid email or password. Please try again.'

    return render_template('login.html', error=error)

@application.route('/success')
def success():
    return "Login successful!"


if __name__ == "__main__":
    #application.debug = True
    application.run()