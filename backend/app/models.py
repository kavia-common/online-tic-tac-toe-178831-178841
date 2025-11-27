from typing import Optional, Dict, Any, List
from .db import fetch_one, fetch_all, execute


def _row_to_room(row: tuple) -> Dict[str, Any]:
    # Expected order: id, code, player_x, player_o, board, next_turn, status, created_at, updated_at
    return {
        "id": row[0],
        "code": row[1],
        "player_x": row[2],
        "player_o": row[3],
        "board": row[4],
        "next_turn": row[5],
        "status": row[6],
        "created_at": row[7],
        "updated_at": row[8],
    }


def _row_to_move(row: tuple) -> Dict[str, Any]:
    # Expected order: id, room_id, move_number, player, row, col, created_at
    return {
        "id": row[0],
        "room_id": row[1],
        "move_number": row[2],
        "player": row[3],
        "row": row[4],
        "col": row[5],
        "created_at": row[6],
    }


def find_room_by_code(code: str) -> Optional[Dict[str, Any]]:
    row = fetch_one(
        """
        SELECT id, code, player_x, player_o, board, next_turn, status, created_at, updated_at
        FROM rooms
        WHERE code = %s
        """,
        (code,),
    )
    if not row:
        return None
    return _row_to_room(row)


def create_room(code: str, player_id: str) -> Dict[str, Any]:
    # Create new room with empty board and player_x assigned
    execute(
        """
        INSERT INTO rooms (code, player_x, player_o, board, next_turn, status)
        VALUES (%s, %s, NULL, %s, %s, %s)
        """,
        (code, player_id, "_________", "X", "ongoing"),
    )
    # initial move_number at 0 possible; no move history yet
    return find_room_by_code(code)  # type: ignore[return-value]


def join_room(code: str, player_id: str) -> Optional[Dict[str, Any]]:
    # Assign player_o only if available and room ongoing
    updated = execute(
        """
        UPDATE rooms
        SET player_o = %s
        WHERE code = %s AND player_o IS NULL AND status = 'ongoing'
        """,
        (player_id, code),
    )
    if updated == 0:
        return None
    return find_room_by_code(code)


def get_room_id(code: str) -> Optional[int]:
    row = fetch_one("SELECT id FROM rooms WHERE code = %s", (code,))
    return row[0] if row else None


def list_moves(room_id: int) -> List[Dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT id, room_id, move_number, player, row, col, created_at
        FROM moves
        WHERE room_id = %s
        ORDER BY move_number ASC
        """,
        (room_id,),
    )
    return [_row_to_move(r) for r in rows]


def next_move_number(room_id: int) -> int:
    row = fetch_one("SELECT COALESCE(MAX(move_number), 0) FROM moves WHERE room_id = %s", (room_id,))
    return (row[0] or 0) + 1


def add_move(room_id: int, move_number: int, player: str, row: int, col: int) -> None:
    execute(
        """
        INSERT INTO moves (room_id, move_number, player, row, col)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (room_id, move_number, player, row, col),
    )


def update_room_state(code: str, board: str, next_turn: Optional[str], status: str) -> None:
    execute(
        """
        UPDATE rooms
        SET board = %s, next_turn = %s, status = %s
        WHERE code = %s
        """,
        (board, next_turn, status, code),
    )


def reset_room(code: str) -> Optional[Dict[str, Any]]:
    room_id = get_room_id(code)
    if room_id is None:
        return None
    # clear moves, reset board
    execute("DELETE FROM moves WHERE room_id = %s", (room_id,))
    execute(
        """
        UPDATE rooms
        SET board = '_________', next_turn = 'X', status = 'ongoing'
        WHERE code = %s
        """,
        (code,),
    )
    return find_room_by_code(code)
