from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True
    )

    return app