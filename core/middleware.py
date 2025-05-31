# core/middleware.py

class NgrokStaticMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Headers específicos para ngrok
        if 'ngrok' in request.get_host():
            response['ngrok-skip-browser-warning'] = 'true'
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response['Access-Control-Allow-Headers'] = '*'
            
            # Para arquivos estáticos
            if request.path.startswith('/static/'):
                response['Cache-Control'] = 'no-cache'
                response['X-Content-Type-Options'] = 'nosniff'
        
        return response
    