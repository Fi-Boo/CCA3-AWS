from decimal import Decimal
import io
import random
import string
import boto3

from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime

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
cart = []
loginTable = dynamodb.Table("cca3-login")
productsTable = dynamodb.Table("cca3-products")
transactionTable = dynamodb.Table("cca3-transactions")

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
        'PLU': stockPLUSingle.upper(),
        'description': stockDesc,
        'price': stockPriceSingle,
        'qty' : "1",
        'SKU': SKU,
    }
    
    addEditProduct(item)
    
    if stockPLUMulti != "":
        item = {
            'PLU': stockPLUMulti.upper(),
            'description': stockDesc + " multipack",
            'price': stockPriceMulti,
            'qty' : stockMultiValue,
            'SKU': SKU,
        }
        addEditProduct(item)
        
    item = {
        'PLU': stockPLUCase.upper(),
        'description': stockDesc + " CASE",
        'price': stockPriceCase,
        'qty': "24",
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
            'qty' : item['qty'],
            'price': item['price']
        }  
        products.append(product)
    return products
    
def searchByCode(code):
    
    codeUpper = code.upper()
    response = productsTable.get_item(
        Key={
            'PLU': codeUpper
        }
    ) 
    products = []
    if 'Item' in response:
        item = response['Item']
        product = {
            'PLU': item['PLU'],
            'description': item['description'],
            'price': item['price'],
            'qty': item['qty'],
            'SKU': item['SKU']
        }
        products.append(product)
    return products


def searchByDesc(description):

    products = []
    response = productsTable.scan()
    
    if description != "":
    
        for item in response['Items']:
        
            itemDescription = item['description'].lower()
            
            if description.lower() in itemDescription:
                product = {
                    'PLU': item['PLU'],
                    'description': item['description'],
                    'price': item['price'],
                    'SKU': item['SKU'],
                    'qty': item['qty']
                }
                products.append(product)

    else:
        
        for item in response['Items']:
            product = {
                'PLU': item['PLU'],
                'description': item['description'],
                'price': item['price'],
                'SKU': item['SKU'],
                'qty': item['qty']
            }
            products.append(product)
            
    return products

def deletePLU(PLU):

    key = {'PLU': PLU}
    
    response = productsTable.delete_item(Key=key)

def updatePLU(PLU, description, qty, price):

    response = productsTable.get_item(
        Key={
            'PLU': PLU
        }
    ) 

    item = response['Item']
    product = {
        'PLU': item['PLU'],
        'SKU': item['SKU'],
        'description': description,
        'qty': qty,
        'price': price
    }
    
    productsTable.put_item(Item=product)   

def getTransactionID():
    response = transactionTable.scan()
    
    length = len(response.get('Items', []))
    
    id = "T" + '{:05d}'.format(length+1)

    return id
  
def getCartTotal():
    
    total = 0
    
    for item in cart:
        total += float(item['linetotal'])
        
    return format(total, ".2f")  


def updateTransRecord(transaction):
    
    transactionTable.put_item(Item=transaction)




        
application = Flask(__name__)

application.jinja_env.globals['float'] = float

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
        session['transID'] = getTransactionID()
        
        loggedUsername = getUsername(session['loggedUser'])
        
        cartTotal = getCartTotal()
        
        return render_template('main.html', navBanner = navBanner, cartTotal = cartTotal, cart = cart, loggedUser = loggedUsername)
    
    else:
        return redirect(url_for('login'))

@application.route('/admin', methods=["GET", "POST"])
def admin():
    
    if 'loggedUser' in session:
        
        error = request.args.get('m')
        
        users = getUsersList()
        
        loggedUser = getLoggedUser(session['loggedUser'])
        
        return render_template('admin.html', navBanner = navBanner, loggedUser = loggedUser, users = users, error = error)
    
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
        dataError = None
        resultMsg = None
        
        if 'm' in request.args: 
            message = request.args.get('m')
            
        if 'dataError' in request.args: 
            dataError = request.args.get('dataError')
            
        if 'resultMsg' in request.args: 
            resultMsg = request.args.get('resultMsg')
        
        return render_template("stock.html", navBanner = navBanner, message = message, dataError = dataError, resultMsg = resultMsg)

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
            resultMsg=None
            products = []
            searchSelection = request.form['searchPLUSKU']
            description = request.form['searchDesc']
            code = request.form['searchCode']
            searchType = request.form['searchBtn']
            
            if searchSelection == "SKU":
                m = "SKU search coming soon"
                return redirect(url_for('stock', m=m))

            if searchType == 'searchCode':
                
                if code != "":
                    products = searchByCode(code)
                else:
                    resultMsg = "must input code to use code search"
                    return redirect(url_for('stock', resultMsg = resultMsg))

            elif searchType == 'searchDesc':
                
                products = searchByDesc(description.lower())
            
            if len(products) == 0:
                resultMsg = "No match found"
                print("no match")
            
            return render_template("stock.html", navBanner = navBanner, products = products, resultMsg = resultMsg )
    
    return redirect(url_for('login'))

@application.route('/fileProcess', methods=['GET', 'POST'])
def fileProcess():
    
    if 'loggedUser' in session:
        
        if request.method == 'POST':
            
            dataError = None
            
            processType = request.form['dataBtn']
            
            if processType == 'import':
                
                try:
                
                    file = request.files['importFile']
                    
                    if file.filename == '':
                        dataError = 'No File selected'
                        return redirect(url_for('stock', dataError = dataError))
        
                    if file:
                        
                        fileData = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                        csv_reader = csv.DictReader(fileData, delimiter='\t')
                        items = []
                        for row in csv_reader:
                            items.append(row)
                        
                        for item in items:
                            productsTable.put_item(Item=item)
                        
                        dataError = "Data imported successfully"
                    else:
                        dataError = "Error with data import"
                        
                    return redirect(url_for('stock', dataError = dataError))
                
                except Exception as e:
                    return str(e)

    return redirect(url_for('login'))


@application.route('/editStock', methods=['GET','POST'])
def editStock():
    
    if 'loggedUser' in session:
        
        if request.method == 'POST':
            
            resultMsg = None
            PLU = request.form['PLU']
            description = request.form['description']
            qty = request.form['qty']
            price = request.form['price']
            action = request.form['Btn']
            
            if action == "delete":
                
                deletePLU(PLU)
                resultMsg = "Product deleted successfully"
            
            elif action == "edit":
                
                updatePLU(PLU, description, qty, price)
                resultMsg = "Product edited successfully"
                
            
            return redirect(url_for('stock', resultMsg = resultMsg))  

    return redirect(url_for('login'))


@application.route('/cart', methods=['GET','POST'])
def viewCart():
    
    if 'loggedUser' in session:
        
        m = None
        
        if request.method == 'POST':
            
            PLU = request.form['PLUsearch']
            
            if PLU != '':
                results = searchByCode(PLU)
                
                if results:
                    for result in results:
                        cartItem = {
                            "product": result,
                            "qty": 1,
                            "linetotal" : format(float(result['price']), ".2f")
                        }
                        cart.append(cartItem)
                        
                else:
                    m="No product found"

        return render_template('main.html', navBanner = navBanner, cartTotal = getCartTotal(), cart = cart, error = m)
    
    return redirect(url_for('login'))


@application.route('/removeCartItem', methods=['GET', 'POST'])
def removeCartItem():
    
    if 'loggedUser' in session:
        
        m = None
        
        if request.method == 'POST':
            
            index = int(request.form['index'])-1 
            
            del cart[index]
            
            return render_template('main.html', navBanner = navBanner, cartTotal = getCartTotal(), cart = cart, error = m)
    
    return redirect(url_for('login'))
    
@application.route('/updateCart', methods=['POST'])
def updateCart():
    
    if 'loggedUser' in session:
        
        m=None
        index = int(request.form['productLine'])-1
        newQty = int(request.form['qty'])
        
        linetotal = newQty * float(cart[index]['product']['price'])
        
        cart[index]['qty'] = newQty
        cart[index]['linetotal'] = format(linetotal, ".2f")
        
        updatedCartTotal = format(sum(float(item['linetotal']) for item in cart), ".2f")

        return jsonify({'updatedLineTotal': cart[index]['linetotal'], 'updatedCartTotal': updatedCartTotal})
    
    return redirect(url_for('login'))


@application.route('/checkout', methods=['POST'])
def checkout():

    if 'loggedUser' in session:
        
        transactionID = session['transID']
        cartTotal = request.form['cartTotal']
        
        if float(cartTotal) == 0:
            
            return redirect(url_for('main'))
        
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        transaction = {
            'id': transactionID,
            'cart': cart,
            'total': cartTotal,
            'staff': session['loggedUser'],
            'date_time': timestamp
        }
        
        updateTransRecord(transaction)
        cart.clear()
        session['transID'] = getTransactionID()
        
        return redirect(url_for('main'))
        
    return redirect(url_for('login'))
  


@application.route('/logout')
def logout():
    
    session.clear()
    cart.clear()
    return redirect(url_for('login'))
    

if __name__ == "__main__":
    #application.debug = True
    application.run()