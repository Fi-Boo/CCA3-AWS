from flask import Flask, request, render_template


# EB looks for an 'application' callable by default.
application = Flask(__name__)

@application.route("/")
def index():
    return "Hello, welcome to my page!"


# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()