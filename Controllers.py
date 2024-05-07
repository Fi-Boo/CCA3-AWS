dummy_user = {
    'email': 'example@example.com',
    'password': 'password123'
    }


class DBController:
      
    def validateEmail(email):
        if email == dummy_user["email"]:
            return True
        else:
            return False
        
    
    def validatePassword(password):
        if password == dummy_user["password"]:
            return True
        else:
            return False
        
