"""
Routes package initializer.

Exposes blueprints for easy import and registration.
"""

from .health import blp as health_blp  # Health check blueprint
from .game import blp as game_blp      # Game endpoints blueprint

__all__ = ["health_blp", "game_blp"]
