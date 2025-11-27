from flask_smorest import Blueprint
from flask.views import MethodView
from marshmallow import Schema, fields
from typing import Optional

from ..models import (
    find_room_by_code,
    create_room,
    join_room,
    get_room_id,
    list_moves,
    next_move_number,
    add_move,
    update_room_state,
    reset_room,
)
from ..game_logic import parse_board, serialize_board, apply_move, check_winner, is_draw

blp = Blueprint(
    "Game",
    "game",
    url_prefix="/api",
    description="Tic Tac Toe game endpoints"
)


class CreateRoomSchema(Schema):
    code = fields.String(required=True, description="Room join code")
    player_id = fields.String(required=True, description="Unique ID of creating player (becomes X)")


class JoinRoomSchema(Schema):
    code = fields.String(required=True, description="Room join code")
    player_id = fields.String(required=True, description="Unique ID of joining player (becomes O)")


class RoomResponseSchema(Schema):
    code = fields.String()
    player_x = fields.String(allow_none=True)
    player_o = fields.String(allow_none=True)
    board = fields.String()
    next_turn = fields.String(allow_none=True)
    status = fields.String()


class MoveSchema(Schema):
    row = fields.Integer(required=True, description="Row index 0..2")
    col = fields.Integer(required=True, description="Col index 0..2")
    player_id = fields.String(required=True, description="Player making the move")


class StateResponseSchema(Schema):
    board = fields.String()
    next_turn = fields.String(allow_none=True)
    status = fields.String()
    winner = fields.String(allow_none=True)


class HistoryResponseSchema(Schema):
    moves = fields.List(fields.Dict())


@blp.route("/rooms")
class RoomsCreate(MethodView):
    @blp.arguments(CreateRoomSchema)
    @blp.response(201, RoomResponseSchema)
    def post(self, args):
        """
        Create a new room.
        """
        code = args["code"]
        player_id = args["player_id"]
        # Ensure not exists
        existing = find_room_by_code(code)
        if existing:
            return existing
        room = create_room(code, player_id)
        return {
            "code": room["code"],
            "player_x": room["player_x"],
            "player_o": room["player_o"],
            "board": room["board"],
            "next_turn": room["next_turn"],
            "status": room["status"],
        }


@blp.route("/rooms/join")
class RoomsJoin(MethodView):
    @blp.arguments(JoinRoomSchema)
    @blp.response(200, RoomResponseSchema)
    def post(self, args):
        """
        Join an existing room as O if slot available.
        """
        code = args["code"]
        player_id = args["player_id"]
        room = join_room(code, player_id)
        if not room:
            return {"message": "Unable to join room"}, 400
        return {
            "code": room["code"],
            "player_x": room["player_x"],
            "player_o": room["player_o"],
            "board": room["board"],
            "next_turn": room["next_turn"],
            "status": room["status"],
        }


@blp.route("/rooms/<string:code>")
class RoomsGet(MethodView):
    @blp.response(200, RoomResponseSchema)
    def get(self, code: str):
        """
        Get room info by code.
        """
        room = find_room_by_code(code)
        if not room:
            return {"message": "Room not found"}, 404
        return {
            "code": room["code"],
            "player_x": room["player_x"],
            "player_o": room["player_o"],
            "board": room["board"],
            "next_turn": room["next_turn"],
            "status": room["status"],
        }


@blp.route("/game/<string:code>/state")
class GameState(MethodView):
    @blp.response(200, StateResponseSchema)
    def get(self, code: str):
        """
        Get current game state for room.
        """
        room = find_room_by_code(code)
        if not room:
            return {"message": "Room not found"}, 404
        board = parse_board(room["board"])
        winner: Optional[str] = check_winner(board)
        status = room["status"]
        if winner:
            status = "finished"
        elif is_draw(board):
            status = "draw"
        return {
            "board": serialize_board(board),
            "next_turn": room["next_turn"],
            "status": status,
            "winner": winner,
        }


@blp.route("/game/<string:code>/move")
class GameMove(MethodView):
    @blp.arguments(MoveSchema)
    def post(self, args, code: str):
        """
        Post a move for the given room code.
        """
        row = int(args["row"])
        col = int(args["col"])
        player_id = args["player_id"]

        room = find_room_by_code(code)
        if not room:
            return {"message": "Room not found"}, 404

        if room["status"] != "ongoing":
            return {"message": "Game is not active"}, 400

        # Determine player's symbol
        symbol: Optional[str] = None
        if room["player_x"] == player_id:
            symbol = "X"
        elif room["player_o"] == player_id:
            symbol = "O"
        else:
            return {"message": "Player not part of this room"}, 403

        if room["next_turn"] != symbol:
            return {"message": "Not your turn"}, 400

        board = parse_board(room["board"])
        success, msg = apply_move(board, row, col, symbol)
        if not success:
            return {"message": msg}, 400

        winner = check_winner(board)
        status = room["status"]
        next_turn: Optional[str] = "O" if symbol == "X" else "X"

        if winner:
            status = "finished"
            next_turn = None
        elif is_draw(board):
            status = "draw"
            next_turn = None

        # Persist
        s_board = serialize_board(board)
        update_room_state(code, s_board, next_turn, status)

        room_id = get_room_id(code)
        if room_id is None:
            return {"message": "Internal error: room missing"}, 500
        mv_no = next_move_number(room_id)
        add_move(room_id, mv_no, symbol, row, col)

        return {
            "board": s_board,
            "next_turn": next_turn,
            "status": status,
            "winner": winner,
            "move_number": mv_no,
        }, 201


@blp.route("/game/<string:code>/history")
class GameHistory(MethodView):
    @blp.response(200, HistoryResponseSchema)
    def get(self, code: str):
        """
        Retrieve move history for the room.
        """
        room_id = get_room_id(code)
        if room_id is None:
            return {"message": "Room not found"}, 404
        moves = list_moves(room_id)
        return {"moves": moves}


@blp.route("/game/<string:code>/reset")
class GameReset(MethodView):
    @blp.response(200, RoomResponseSchema)
    def post(self, code: str):
        """
        Reset a room to initial state and clear history.
        """
        room = reset_room(code)
        if not room:
            return {"message": "Room not found"}, 404
        return {
            "code": room["code"],
            "player_x": room["player_x"],
            "player_o": room["player_o"],
            "board": room["board"],
            "next_turn": room["next_turn"],
            "status": room["status"],
        }
