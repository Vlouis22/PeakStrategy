import os
from app import create_app

# Create application instance
app = create_app(os.getenv('FLASK_ENV', 'default'))

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(
        host=os.getenv('HOST', '0.0.0.0'),
        port=port,
        debug=app.config['DEBUG']
    )