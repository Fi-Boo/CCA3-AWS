import boto3
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
    

    
        

