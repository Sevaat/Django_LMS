from django.http import HttpResponse, JsonResponse

def home(request):
    """Домашняя страница"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LMS - Learning Management System</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 600px;
                text-align: center;
            }
            h1 { color: #333; margin-bottom: 10px; }
            .status { color: #10b981; font-weight: bold; margin: 20px 0; padding: 10px; background: #d1fae5; border-radius: 10px; display: inline-block; }
            .endpoints { text-align: left; margin: 30px 0; padding: 20px; background: #f9fafb; border-radius: 10px; }
            .endpoints h3 { margin-top: 0; color: #555; }
            .endpoints ul { list-style: none; padding: 0; }
            .endpoints li { margin: 10px 0; padding: 8px; background: white; border-radius: 5px; border-left: 3px solid #667eea; }
            .endpoints a { color: #667eea; text-decoration: none; font-weight: 500; }
            .endpoints a:hover { text-decoration: underline; }
            .footer { margin-top: 30px; font-size: 12px; color: #888; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📚 LMS Platform</h1>
            <p>Learning Management System API</p>
            <div class="status">✅ Server is running</div>
            <div class="endpoints">
                <h3>📌 Available Endpoints:</h3>
                <ul>
                    <li>🔐 <a href="/admin/">Admin Panel</a></li>
                    <li>📖 <a href="/api/docs/">API Documentation</a></li>
                    <li>📚 <a href="/api/redoc/">API Reference</a></li>
                </ul>
            </div>
            <div class="footer">
                <p>LMS Project | Django REST Framework | Python 3.12</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)

def health(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'server': 'running'
    })