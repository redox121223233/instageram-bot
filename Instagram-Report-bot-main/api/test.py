"""
Simple test file to verify Vercel deployment
"""
import json

def handler(event, context):
    """Simple test handler"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'message': 'Test endpoint is working!',
            'event': str(event)[:100]
        })
    }

# For Flask-style deployment
def handler_flask(environ, start_response):
    """Flask-style handler"""
    status = '200 OK'
    headers = [('Content-Type', 'application/json')]
    start_response(status, headers)
    
    response_data = {
        'message': 'Test endpoint is working!',
        'method': environ.get('REQUEST_METHOD', 'GET'),
        'path': environ.get('PATH_INFO', '/')
    }
    
    return [json.dumps(response_data).encode()]