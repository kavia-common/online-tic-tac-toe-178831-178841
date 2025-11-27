from flask import Flask
from flask_cors import CORS
from flask_smorest import Api
from .routes.health import blp as health_blp
from .routes.game import blp as game_blp

app = Flask(__name__)
app.url_map.strict_slashes = False
# Restrict CORS to frontend origin
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000"]}})

# OpenAPI / Swagger configuration
app.config["API_TITLE"] = "Tic Tac Toe API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/docs"
app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
app.config["OPENAPI_JSON_PATH"] = "openapi.json"

api = Api(app)

# Register blueprints
api.register_blueprint(health_blp)
api.register_blueprint(game_blp)
