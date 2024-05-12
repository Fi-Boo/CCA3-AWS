from decimal import Decimal
import random
import string
import boto3

from flask import Flask, request, render_template, redirect, url_for, session
from boto3.dynamodb.conditions import Key, Attr
from retailPOS import User, Product

#shouldn't be putting credentials in code! I'll have to search for alternative method (IAM) when I have more time.
awsKey = 'AKIAW3MEABS7NBPKBZEW'
awsSecretKey = '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'
region = 'us-east-1'
s3Bucket = 's2008156-cca3'
dynamodb = boto3.resource('dynamodb', region_name=region, aws_access_key_id=awsKey, aws_secret_access_key=awsSecretKey)
s3 = boto3.client('s3', aws_access_key_id=awsKey, aws_secret_access_key=awsSecretKey, region_name=region)
cloudFrontDomain ='https://d1yd7dukro94c1.cloudfront.net/'
navBanner = cloudFrontDomain + "navBanner.png"
products = []
loginTable = dynamodb.Table("cca3-login")
productsTable = dynamodb.Table("cca3-products")

def queryBy(email):
    
    response = loginTable.get_item(
        Key={
            'email': email
        }
    ) 
    return response


def validateLogin(email, password):
    
    response = queryBy(email)
    
    if 'Item' in response:
        if response['Item']['password'] == password:
            return True  
    return False 


def getUsername(email):
    
    return queryBy(email)['Item']['user_name']


def getStaffLevel(email):
  
    return queryBy(email)['Item']['staff_level']


def checkExists(email):

    if 'Item' in queryBy(email):
        return True
    return False
        
def addNewUser(email, username, password, staffLevel):
    
    item = {
        'email': email,
        'user_name': username,
        'password': password,
        'staff_level': staffLevel
    }
    
    loginTable.put_item(Item=item)
    

def getUsersList():
    
    response = loginTable.scan()
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
    
    response = queryBy(email)
    
    item = response['Item']
    user = {
        'email': item['email'],
        'user_name': name,
        'password': item['password'],
        'staff_level': staffLvl
    }
    
    loginTable.put_item(Item=user)   

    
def deleteUser(email):

    key = {'email': email}
    
    response = loginTable.delete_item(Key=key)


def getLoggedUser(email):

    response = queryBy(email)
    
    item = response['Item']
    user = {
        'email': item['email'],
        'user_name': item['user_name'],
        'password': item['password'],
        'staff_level': item['staff_level'],
        'password': item['password']
    }
    
    return user

def generateSKU(stockSKUClass):
    
    response = productsTable.scan(FilterExpression=Attr('SKU').begins_with(stockSKUClass))
    
    count = response['Count']+1
    
    return stockSKUClass + '{:03d}'.format(count)

def addNewSKU(stockDesc, stockPLUSingle, stockPriceSingle, stockPLUMulti, stockMultiValue, stockPriceMulti, stockPLUCase, stockPriceCase, SKU):
    
    item = {
        'PLU': stockPLUSingle,
        'description': stockDesc,
        'price': stockPriceSingle,
        'SKU': SKU,
    }
    addEditProduct(item)
    
    if stockPLUMulti != "":
        item = {
            'PLU': stockPLUMulti,
            'description': stockDesc + " (" + stockMultiValue + "PK)",
            'price': stockPriceMulti,
            'SKU': SKU,
        }
        addEditProduct(item)
        
    item = {
        'PLU': stockPLUCase,
        'description': stockDesc + " (CASE)",
        'price': stockPriceCase,
        'SKU': SKU,
    }
    addEditProduct(item)

    
def addEditProduct(item):
    response = productsTable.put_item(Item=item)

def getProducts():
    response = productsTable.scan()
    products = []
    for item in response["Items"]:  
        product = {
            'PLU': item['PLU'],
            'SKU': item['SKU'],
            'description': item['description'],
            'price': item['price']
        }  
        products.append(product)
    return products
    
def searchByCode(code):
    response = productsTable.get_item(
        Key={
            'PLU': code
        }
    ) 
    products = []
    item = response['Item']
    product = {
        'PLU': item['PLU'],
        'description': item['description'],
        'price': item['price'],
        'SKU': item['SKU'],
    }
    products.append(product)
    return products


def searchByDesc(description):
    
    if description != "":
        response = productsTable.scan(
            FilterExpression='contains(description, :search)',
            ExpressionAttributeValues={':search': description}
        )
    else:
        response = productsTable.scan()
        
    products = []
    for item in response['Items']:
        product = {
            'PLU': item['PLU'],
            'description': item['description'],
            'price': item['price'],
            'SKU': item['SKU'],
        }
        products.append(product)
    return products
        
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
        
        products = getProducts()
        
        loggedUsername = getUsername(session['loggedUser'])
        
        return render_template('main.html', navBanner = navBanner, loggedUser = loggedUsername, staffLevel = session['staffLevel'])
    
    else:
        return redirect(url_for('login'))

@application.route('/admin', methods=["GET", "POST"])
def admin():
    
    if 'loggedUser' in session:
        
        error = request.args.get('m')
        
        users = getUsersList()
        
        loggedUser = getLoggedUser(session['loggedUser'])
        
        return render_template('admin.html', navBanner = navBanner, staffLevel = session['staffLevel'], loggedUser = loggedUser, users = users, error = error)
    
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


@application.route('/stock', methods=["GET", "POST"])
def stock():
    
    if 'loggedUser' in session:
        
        message = None
        
        if 'm' in request.args: 
            message = request.args.get('m')
        
        return render_template("stock.html", navBanner = navBanner, message = message)

    return redirect(url_for('login'))



@application.route('/addStock', methods=['GET', 'POST'])
def addStockItem():
    
    if 'loggedUser' in session:
        
        if request.method == 'POST':
            
            m= None
            
            stockDesc = request.form['stockDesc']
            stockPLUSingle = request.form['stockPLUSingle']
            stockPriceSingle = request.form['stockPriceSingle']
            stockPLUMulti = request.form['stockPLUMulti']
            stockMultiValue = request.form['stockMultiValue']
            stockPriceMulti = request.form['stockPriceMulti']
            stockPLUCase = request.form['stockPLUCase']
            stockPriceCase = request.form['stockPriceCase']
            stockSKUClass = request.form['stockSKUClass']

            count = sum(bool(value) for value in [stockPLUMulti, stockMultiValue, stockPriceMulti])
            if count == 1 or count == 2:
                m = "All multipack values must be empty or populated."
                return redirect(url_for('stock', m = m))
             
            SKU = generateSKU(stockSKUClass)
            addNewSKU(stockDesc, stockPLUSingle, stockPriceSingle, stockPLUMulti, stockMultiValue, stockPriceMulti, stockPLUCase, stockPriceCase, SKU)  
            
            try:       
                file = request.files["stockSKUImage"]
                
                if file.filename != "":
                    
                    fileType = file.filename.rsplit('.', 1)[-1]
                    filename = SKU + "." + fileType
                    s3.upload_fileobj(file, s3Bucket, filename)
                
                m="Product added successfully"
                return redirect(url_for('stock', m = m))
            
            except Exception as e:
                print("Error:", e)
    
    return redirect(url_for('login'))

@application.route('/search', methods=['GET', 'POST'])
def searchProduct():
    
    if 'loggedUser' in session:
        
        if request.method == 'POST':
            m=None
            products = []
            searchSelection = request.form['searchPLUSKU']
            description = request.form['searchDesc']
            code = request.form['searchCode']
            searchType = request.form['searchBtn']
            
            if searchSelection == "SKU":
                m = "SKU search coming soon"
                return redirect(url_for('stock', m=m))

            if searchType == 'searchCode':
                products = searchByCode(code)

            else:
                products = searchByDesc(description)
            
            return render_template("stock.html", navBanner = navBanner, products = products )
    
    return redirect(url_for('login'))


if __name__ == "__main__":
    #application.debug = True
    application.run()