
class User:
    
    def __init__(self, email, name, password, staff_level):
        self.email = email
        self.user_name = name
        self.password = password
        self.staff_level = staff_level
        
    def setPW(self, password):
        self.password = password
        
    def setName(self, name):
        self.user_name = name
        
    def setStaffLvl(self, stafflvl):
        self.staff_level = stafflvl
        
        
class Product:
    
    def __init__(self, PLU, SKU, description, price, quantity, category):
        self.PLU = PLU
        self.SKU = SKU
        self.description = description
        self.price = price
        self.quantity = quantity
        self.category = category 
        
    
    
class SKUstock:
    
    def __init__(self, stockDesc, stockPLUSingle, stockPriceSingle, stockPLUMulti, stockMultiValue, stockPriceMulti, SKU):
        self.stockDesc = stockDesc
        self.stockPLUSingle = stockPLUSingle  
        self.stockPriceSingle = stockPriceSingle 
        self.stockPLUMulti = stockPLUMulti
        self.stockMultiValue = stockMultiValue
        self.stockPriceMulti = stockPriceMulti
        self.stockSKU = SKU


