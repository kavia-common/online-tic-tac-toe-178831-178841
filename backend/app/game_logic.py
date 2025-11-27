from typing import List, Optional, Tuple


# PUBLIC_INTERFACE
def check_winner(board: List[List[Optional[str]]]) -> Optional[str]:
    """Check the board for a winner. Returns 'X', 'O', or None."""
    lines = []

    # Rows and columns
    for i in range(3):
        lines.append(board[i])  # row
        lines.append([board[0][i], board[1][i], board[2][i]])  # column

    # Diagonals
    lines.append([board[0][0], board[1][1], board[2][2]])
    lines.append([board[0][2], board[1][1], board[2][0]])

    for line in lines:
        if line[0] is not None and line.count(line[0]) == 3:
            return line[0]
    return None


# PUBLIC_INTERFACE
def is_draw(board: List[List[Optional[str]]]) -> bool:
    """Return True if the board is full and there is no winner."""
    for row in board:
        for cell in row:
            if cell is None:
                return False
    return check_winner(board) is None


# PUBLIC_INTERFACE
def parse_board(board_str: str) -> List[List[Optional[str]]]:
    """
    Convert board string of length 9 (chars in [X,O,_]) into 3x3 matrix with Optional[str].
    '_' or ' ' will be interpreted as None.
    """
    normalized = board_str.replace(" ", "_")
    if len(normalized) != 9:
        # Pad or truncate to 9 for safety
        normalized = (normalized + "_________")[:9]
    result: List[List[Optional[str]]] = []
    for r in range(3):
        row = []
        for c in range(3):
            ch = normalized[r * 3 + c]
            if ch in ("X", "O"):
                row.append(ch)
            else:
                row.append(None)
        result.append(row)
    return result


# PUBLIC_INTERFACE
def serialize_board(board: List[List[Optional[str]]]) -> str:
    """Convert 3x3 matrix back to 9-char string with '_' for empty."""
    chars: List[str] = []
    for r in range(3):
        for c in range(3):
            val = board[r][c]
            chars.append(val if val in ("X", "O") else "_")
    return "".join(chars)


# PUBLIC_INTERFACE
def apply_move(board: List[List[Optional[str]]], row: int, col: int, symbol: str) -> Tuple[bool, str]:
    """
    Attempt to place symbol at row,col.
    Returns (success, message). Does not modify board on invalid move.
    """
    if symbol not in ("X", "O"):
        return False, "Invalid symbol"
    if not (0 <= row < 3 and 0 <= col < 3):
        return False, "Invalid move position"
    if board[row][col] is not None:
        return False, "Cell already occupied"
    board[row][col] = symbol
    return True, "Move applied"
