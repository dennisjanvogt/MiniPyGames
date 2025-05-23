import tkinter as tk
from tkinter import simpledialog, messagebox
import copy
import time  # Für AI-Denkpause und Performance-Messung (optional)

# --- Konstanten und globale Spielzustandsvariablen ---
BOARD_SIZE = 6
SQUARE_SIZE = 80
PIECE_FONT = ("Arial", 40)
STATUS_FONT = ("Arial", 14)

AI_PLAYER_COLOR = "black"  # KI spielt Schwarz
HUMAN_PLAYER_COLOR = "white"
AI_SEARCH_DEPTH = 2  # Suchtiefe für Minimax (Anzahl Halbzüge)

PIECES_UNICODE = {
    "wP": "♙",
    "wR": "♖",
    "wN": "♘",
    "wB": "♗",
    "wQ": "♕",
    "wK": "♔",
    "bP": "♟",
    "bR": "♜",
    "bN": "♞",
    "bB": "♝",
    "bQ": "♛",
    "bK": "♚",
}

PIECE_VALUES = {
    "P": 10,
    "N": 30,
    "B": 35,
    "R": 50,
    "Q": 90,
    "K": 0,  # Königswert wird durch Schachmatt behandelt
}
CHECKMATE_SCORE = 10000
STALEMATE_SCORE = 0
MOBILITY_WEIGHT = 0.1  # Kleiner Faktor für Mobilitätsbonus

INITIAL_BOARD_SETUP = [
    ["bR", "bN", "bB", "bK", "bQ", "bR"],
    ["bP", "bP", "bP", "bP", "bP", "bP"],
    [None, None, None, None, None, None],
    [None, None, None, None, None, None],
    ["wP", "wP", "wP", "wP", "wP", "wP"],
    ["wR", "wN", "wB", "wQ", "wK", "wR"],
]

# Globale Variablen für den aktuellen Spielzustand
board = []
current_player = HUMAN_PLAYER_COLOR  # Mensch beginnt
king_positions = {}
castling_rights = {}
en_passant_target = None
game_over = False
selected_piece_pos = None
highlighted_square_ids = []
possible_move_dots = []


# --- Hilfsfunktionen für Figuren und Brett (bleiben meist gleich) ---
def get_piece_color(piece_char):
    if piece_char is None:
        return None
    return "white" if piece_char.startswith("w") else "black"


def get_piece_type(piece_char):
    if piece_char is None:
        return None
    return piece_char[1]


def is_valid_square(r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


# --- PARAMETERISIERTE Logik für Figurenbewegungen ---
def _get_pawn_moves(r, c, color, current_board, current_en_passant_target):
    moves = []
    direction = -1 if color == "white" else 1
    start_row = BOARD_SIZE - 2 if color == "white" else 1

    if is_valid_square(r + direction, c) and current_board[r + direction][c] is None:
        moves.append((r + direction, c))
        if (
            r == start_row
            and is_valid_square(r + 2 * direction, c)
            and current_board[r + 2 * direction][c] is None
        ):
            moves.append((r + 2 * direction, c))

    for dc in [-1, 1]:
        if is_valid_square(r + direction, c + dc):
            target_piece = current_board[r + direction][c + dc]
            if target_piece and get_piece_color(target_piece) != color:
                moves.append((r + direction, c + dc))
            if (r + direction, c + dc) == current_en_passant_target:
                moves.append((r + direction, c + dc))
    return moves


def _get_linear_moves(r, c, color, current_board, directions):  # Für Turm & Läufer
    moves = []
    for dr, dc in directions:
        for i in range(1, BOARD_SIZE):
            nr, nc = r + dr * i, c + dc * i
            if not is_valid_square(nr, nc):
                break
            target_piece = current_board[nr][nc]
            if target_piece is None:
                moves.append((nr, nc))
            else:
                if get_piece_color(target_piece) != color:
                    moves.append((nr, nc))
                break
    return moves


def _get_rook_moves(r, c, color, current_board):
    return _get_linear_moves(
        r, c, color, current_board, [(0, 1), (0, -1), (1, 0), (-1, 0)]
    )


def _get_bishop_moves(r, c, color, current_board):
    return _get_linear_moves(
        r, c, color, current_board, [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    )


def _get_knight_moves(r, c, color, current_board):
    moves = []
    for dr, dc in [
        (1, 2),
        (1, -2),
        (-1, 2),
        (-1, -2),
        (2, 1),
        (2, -1),
        (-2, 1),
        (-2, -1),
    ]:
        nr, nc = r + dr, c + dc
        if is_valid_square(nr, nc):
            target_piece = current_board[nr][nc]
            if target_piece is None or get_piece_color(target_piece) != color:
                moves.append((nr, nc))
    return moves


def _get_queen_moves(r, c, color, current_board):
    return _get_rook_moves(r, c, color, current_board) + _get_bishop_moves(
        r, c, color, current_board
    )


def _get_king_moves(
    r,
    c,
    color,
    current_board,
    current_castling_rights,
    current_king_positions,
    current_en_passant_target,
):
    moves = []
    for dr_king in [-1, 0, 1]:
        for dc_king in [-1, 0, 1]:
            if dr_king == 0 and dc_king == 0:
                continue
            nr_king, nc_king = r + dr_king, c + dc_king
            if is_valid_square(nr_king, nc_king):
                target_piece_king = current_board[nr_king][nc_king]
                if (
                    target_piece_king is None
                    or get_piece_color(target_piece_king) != color
                ):
                    moves.append((nr_king, nc_king))

    opponent_color = "black" if color == "white" else "white"
    # Rochaderechte des Königs, dessen Züge generiert werden (color)
    # Die Rochaderechte für _is_square_attacked_from_state beziehen sich auf den Kontext von 'color'
    # (d.h. die Rochaderechte von 'color', nicht die des 'opponent_color')
    if color == "white" and r == 5 and c == 4:
        if (
            current_castling_rights.get("white_kingside")
            and current_board[5][5] == "wR"
            and not _is_square_attacked_from_state(
                5,
                4,
                opponent_color,
                current_board,
                current_king_positions,
                current_en_passant_target,
                current_castling_rights,
            )
            and not _is_square_attacked_from_state(
                5,
                5,
                opponent_color,
                current_board,
                current_king_positions,
                current_en_passant_target,
                current_castling_rights,
            )
        ):
            moves.append((5, 5, "O-O"))
        if (
            current_castling_rights.get("white_queenside")
            and current_board[5][0] == "wR"
            and current_board[5][1] is None
            and current_board[5][2] is None
            and current_board[5][3] is None
            and not _is_square_attacked_from_state(
                5,
                4,
                opponent_color,
                current_board,
                current_king_positions,
                current_en_passant_target,
                current_castling_rights,
            )
            and not _is_square_attacked_from_state(
                5,
                3,
                opponent_color,
                current_board,
                current_king_positions,
                current_en_passant_target,
                current_castling_rights,
            )
            and not _is_square_attacked_from_state(
                5,
                2,
                opponent_color,
                current_board,
                current_king_positions,
                current_en_passant_target,
                current_castling_rights,
            )
        ):
            moves.append((5, 2, "O-O-O"))
    elif color == "black" and r == 0 and c == 3:
        if (
            current_castling_rights.get("black_kingside")
            and current_board[0][5] == "bR"
            and current_board[0][4] is None
            and not _is_square_attacked_from_state(
                0,
                3,
                opponent_color,
                current_board,
                current_king_positions,
                current_en_passant_target,
                current_castling_rights,
            )
            and not _is_square_attacked_from_state(
                0,
                4,
                opponent_color,
                current_board,
                current_king_positions,
                current_en_passant_target,
                current_castling_rights,
            )
            and not _is_square_attacked_from_state(
                0,
                5,
                opponent_color,
                current_board,
                current_king_positions,
                current_en_passant_target,
                current_castling_rights,
            )
        ):
            moves.append((0, 5, "O-O"))
        if (
            current_castling_rights.get("black_queenside")
            and current_board[0][0] == "bR"
            and current_board[0][1] is None
            and current_board[0][2] is None
            and not _is_square_attacked_from_state(
                0,
                3,
                opponent_color,
                current_board,
                current_king_positions,
                current_en_passant_target,
                current_castling_rights,
            )
            and not _is_square_attacked_from_state(
                0,
                2,
                opponent_color,
                current_board,
                current_king_positions,
                current_en_passant_target,
                current_castling_rights,
            )
            and not _is_square_attacked_from_state(
                0,
                1,
                opponent_color,
                current_board,
                current_king_positions,
                current_en_passant_target,
                current_castling_rights,
            )
        ):
            moves.append((0, 1, "O-O-O"))
    return moves


# --- PARAMETERISIERTE Kern Spiellogik ---


def _get_all_pseudo_legal_moves_for_piece(
    r_piece,
    c_piece,
    piece_char,
    current_board,
    current_en_passant_target,
    current_castling_rights_for_own_king,
    current_king_positions,
):
    if not piece_char:
        return []
    color_of_piece = get_piece_color(piece_char)
    ptype_of_piece = get_piece_type(piece_char)

    if ptype_of_piece == "P":
        return _get_pawn_moves(
            r_piece, c_piece, color_of_piece, current_board, current_en_passant_target
        )
    if ptype_of_piece == "R":
        return _get_rook_moves(r_piece, c_piece, color_of_piece, current_board)
    if ptype_of_piece == "N":
        return _get_knight_moves(r_piece, c_piece, color_of_piece, current_board)
    if ptype_of_piece == "B":
        return _get_bishop_moves(r_piece, c_piece, color_of_piece, current_board)
    if ptype_of_piece == "Q":
        return _get_queen_moves(r_piece, c_piece, color_of_piece, current_board)
    if ptype_of_piece == "K":
        return _get_king_moves(
            r_piece,
            c_piece,
            color_of_piece,
            current_board,
            current_castling_rights_for_own_king,
            current_king_positions,
            current_en_passant_target,
        )
    return []


def _is_square_attacked_from_state(
    r_attacked,
    c_attacked,
    attacker_color,
    current_board,
    current_king_positions,
    current_en_passant_target,
    relevant_castling_rights,
):
    # relevant_castling_rights sind die Rochaderechte des Spielers, dessen Königspfad/Feld geprüft wird,
    # NICHT die des Angreifers. Für die Angriffszuggenerierung der meisten Figuren sind sie irrelevant.
    for R_attacker in range(BOARD_SIZE):
        for C_attacker in range(BOARD_SIZE):
            piece_attacker = current_board[R_attacker][C_attacker]
            if piece_attacker and get_piece_color(piece_attacker) == attacker_color:
                p_type_attacker = get_piece_type(piece_attacker)

                if p_type_attacker == "P":
                    direction_attacker = -1 if attacker_color == "white" else 1
                    for dc_capture_attacker in [-1, 1]:
                        if (
                            R_attacker + direction_attacker == r_attacked
                            and C_attacker + dc_capture_attacker == c_attacked
                        ):
                            return True
                elif p_type_attacker == "K":
                    # König greift seine 8 Nachbarfelder an.
                    if (
                        max(abs(R_attacker - r_attacked), abs(C_attacker - c_attacked))
                        == 1
                    ):
                        return True
                else:  # R, N, B, Q
                    # Für diese Figuren sind ihre eigenen Rochaderechte irrelevant für Angriffszüge.
                    # Daher leere Rochaderechte an _get_all_pseudo_legal_moves_for_piece übergeben.
                    pseudo_moves_attacker = _get_all_pseudo_legal_moves_for_piece(
                        R_attacker,
                        C_attacker,
                        piece_attacker,
                        current_board,
                        current_en_passant_target,  # EP-Ziel ist relevant für Bauernangriffe
                        {},  # Leere Rochaderechte für Angreifer R,N,B,Q
                        current_king_positions,
                    )
                    for move_attacker in pseudo_moves_attacker:
                        if (
                            move_attacker[0] == r_attacked
                            and move_attacker[1] == c_attacked
                        ):
                            if len(move_attacker) == 3 and move_attacker[2].startswith(
                                "O-O"
                            ):
                                continue  # Rochade ist kein Angriff
                            return True
    return False


def _is_in_check_from_state(
    player_color_in_check,
    current_board,
    current_king_positions,
    current_en_passant_target,
    current_castling_rights,
):
    if player_color_in_check not in current_king_positions:
        return False
    kr_in_check, kc_in_check = current_king_positions[player_color_in_check]
    opponent_color_attacker = "black" if player_color_in_check == "white" else "white"
    # Die Rochaderechte, die hier übergeben werden, sind die von player_color_in_check (relevant, falls _get_king_moves des Angreifers aufgerufen würde, was wir aber für K vermeiden)
    return _is_square_attacked_from_state(
        kr_in_check,
        kc_in_check,
        opponent_color_attacker,
        current_board,
        current_king_positions,
        current_en_passant_target,
        current_castling_rights,
    )


def _get_all_legal_moves_from_state(
    player_color_moving,
    p_board,
    p_king_positions,
    p_en_passant_target,
    p_castling_rights,
):
    legal_moves = []
    for r_start in range(BOARD_SIZE):
        for c_start in range(BOARD_SIZE):
            piece = p_board[r_start][c_start]
            if piece and get_piece_color(piece) == player_color_moving:
                pseudo_moves = _get_all_pseudo_legal_moves_for_piece(
                    r_start,
                    c_start,
                    piece,
                    p_board,
                    p_en_passant_target,
                    p_castling_rights,
                    p_king_positions,
                )
                for move_tuple in pseudo_moves:
                    next_s_board, next_s_king_pos, next_s_ep, next_s_castling = (
                        _simulate_move_on_state(
                            p_board,
                            p_king_positions,
                            p_en_passant_target,
                            p_castling_rights,
                            player_color_moving,
                            (r_start, c_start),
                            move_tuple,
                        )
                    )
                    if not _is_in_check_from_state(
                        player_color_moving,
                        next_s_board,
                        next_s_king_pos,
                        next_s_ep,
                        next_s_castling,
                    ):
                        legal_moves.append(((r_start, c_start), move_tuple))
    return legal_moves


def get_all_legal_moves_for_player(player_color_moving):
    return _get_all_legal_moves_from_state(
        player_color_moving,
        copy.deepcopy(board),
        copy.deepcopy(king_positions),
        en_passant_target,
        copy.deepcopy(castling_rights),
    )


def is_in_check(player_color_in_check):
    return _is_in_check_from_state(
        player_color_in_check, board, king_positions, en_passant_target, castling_rights
    )


def _simulate_move_on_state(
    prev_board,
    prev_king_pos,
    prev_ep_target,
    prev_castling_rights,
    player_making_move,
    start_pos_sim,
    end_tuple_sim,
    promotion_piece_sim=None,
):
    sim_board = copy.deepcopy(prev_board)
    sim_king_pos = copy.deepcopy(prev_king_pos)
    sim_castling_rights = copy.deepcopy(prev_castling_rights)
    sim_ep_target = None

    r_start, c_start = start_pos_sim
    r_end, c_end = end_tuple_sim[0], end_tuple_sim[1]
    is_castling = len(end_tuple_sim) == 3 and end_tuple_sim[2].startswith("O-O")

    moved_piece = sim_board[r_start][c_start]
    moved_piece_type = get_piece_type(moved_piece)

    sim_board[r_end][c_end] = moved_piece
    sim_board[r_start][c_start] = None

    if moved_piece_type == "P" and (r_end, c_end) == prev_ep_target:
        if player_making_move == "white":
            sim_board[r_end + 1][c_end] = None
        else:
            sim_board[r_end - 1][c_end] = None

    if moved_piece_type == "P" and abs(r_start - r_end) == 2:
        sim_ep_target = ((r_start + r_end) // 2, c_start)

    if moved_piece_type == "K":
        sim_king_pos[player_making_move] = (r_end, c_end)

    if is_castling:
        castle_type = end_tuple_sim[2]
        # Wichtig: sim_board wird hier direkt modifiziert
        if castle_type == "O-O" and player_making_move == "white":  # K(5,4)R(5,5) swap
            sim_board[5][4], sim_board[5][5] = "wR", "wK"
        elif (
            castle_type == "O-O-O" and player_making_move == "white"
        ):  # K E1(5,4)->C1(5,2), R A1(5,0)->D1(5,3)
            sim_board[5][3], sim_board[5][0] = "wR", None
        elif (
            castle_type == "O-O" and player_making_move == "black"
        ):  # K D6(0,3)->F6(0,5), R F6(0,5)->E6(0,4)
            # König ist schon auf (0,5) durch Hauptzug. Turm von (0,5) nach (0,4).
            sim_board[0][4] = "bR"
            # sim_board[0][5] bleibt bK
        elif (
            castle_type == "O-O-O" and player_making_move == "black"
        ):  # K D6(0,3)->B6(0,1), R A6(0,0)->C6(0,2)
            sim_board[0][2], sim_board[0][0] = "bR", None

    if moved_piece_type == "K":
        sim_castling_rights[player_making_move + "_kingside"] = False
        sim_castling_rights[player_making_move + "_queenside"] = False
    elif moved_piece_type == "R":
        original_rook_pos_map = {
            "white_queenside": (5, 0),
            "white_kingside": (5, BOARD_SIZE - 1),
            "black_queenside": (0, 0),
            "black_kingside": (0, BOARD_SIZE - 1),
        }
        for side_key, pos_key in original_rook_pos_map.items():
            if (
                player_making_move == side_key.split("_")[0]
                and (r_start, c_start) == pos_key
            ):
                sim_castling_rights[side_key] = False
                break

    promo_rank = 0 if player_making_move == "white" else BOARD_SIZE - 1
    if moved_piece_type == "P" and r_end == promo_rank:
        promo_char = promotion_piece_sim if promotion_piece_sim else "Q"
        sim_board[r_end][c_end] = player_making_move[0] + promo_char

    return sim_board, sim_king_pos, sim_ep_target, sim_castling_rights


def initialize_game_state():
    global board, current_player, king_positions, castling_rights, en_passant_target, game_over
    board = copy.deepcopy(INITIAL_BOARD_SETUP)
    current_player = HUMAN_PLAYER_COLOR
    king_positions = {"white": (5, 4), "black": (0, 3)}
    castling_rights = {
        "white_kingside": True,
        "white_queenside": True,
        "black_kingside": True,
        "black_queenside": True,
    }
    en_passant_target = None
    game_over = False


def make_move(start_pos_make, end_move_tuple_make, promotion_piece_type_make=None):
    global board, current_player, king_positions, castling_rights, en_passant_target

    new_board, new_king_pos, new_ep_target, new_castling_rights = (
        _simulate_move_on_state(
            board,
            king_positions,
            en_passant_target,
            castling_rights,
            current_player,
            start_pos_make,
            end_move_tuple_make,
            promotion_piece_type_make,
        )
    )

    board = new_board
    king_positions = new_king_pos
    en_passant_target = new_ep_target
    castling_rights = new_castling_rights

    current_player = (
        AI_PLAYER_COLOR if current_player == HUMAN_PLAYER_COLOR else HUMAN_PLAYER_COLOR
    )


def check_game_status():
    global game_over
    legal_moves_for_current = get_all_legal_moves_for_player(current_player)

    if not legal_moves_for_current:
        opponent = (
            HUMAN_PLAYER_COLOR if current_player == AI_PLAYER_COLOR else AI_PLAYER_COLOR
        )
        if is_in_check(current_player):
            messagebox.showinfo(
                "Spielende", f"Schachmatt! {opponent.capitalize()} gewinnt."
            )
            game_over = True
        else:
            messagebox.showinfo("Spielende", "Patt! Unentschieden.")
            game_over = True
        return True
    elif is_in_check(current_player):
        if gui:
            gui.update_status_label(f"{current_player.capitalize()} ist im Schach!")
    return False


# --- KI Logik ---
def evaluate_board_state(
    e_board, e_king_pos, e_ep_target, e_castling_rights, player_turn_on_this_board
):
    score = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece = e_board[r][c]
            if piece:
                p_color = get_piece_color(piece)
                p_type = get_piece_type(piece)
                value = PIECE_VALUES.get(p_type, 0)
                if p_color == AI_PLAYER_COLOR:
                    score += value
                else:
                    score -= value

    # Mobilitätsbonus (optional, kann performance-intensiv sein)
    # ai_moves = len(_get_all_legal_moves_from_state(AI_PLAYER_COLOR, e_board, e_king_pos, e_ep_target, e_castling_rights))
    # human_moves = len(_get_all_legal_moves_from_state(HUMAN_PLAYER_COLOR, e_board, e_king_pos, e_ep_target, e_castling_rights))
    # score += (ai_moves - human_moves) * MOBILITY_WEIGHT
    return score


def _minimax_recursive(
    m_board,
    m_king_pos,
    m_ep_target,
    m_castling_rights,
    m_player_turn,
    depth,
    alpha,
    beta,
    maximizing_player,
):
    possible_moves = _get_all_legal_moves_from_state(
        m_player_turn, m_board, m_king_pos, m_ep_target, m_castling_rights
    )

    if depth == 0 or not possible_moves:
        if not possible_moves:
            if _is_in_check_from_state(
                m_player_turn, m_board, m_king_pos, m_ep_target, m_castling_rights
            ):
                return (
                    -CHECKMATE_SCORE if maximizing_player else CHECKMATE_SCORE
                ), None  # Note: Score relative to current player in minimax node
            else:
                return STALEMATE_SCORE, None
        # Bewertung ist immer aus Sicht der KI (AI_PLAYER_COLOR), unabhängig von maximizing_player
        # Korrektur: Die Bewertungsfunktion sollte den Score für den aktuellen maximierenden Spieler zurückgeben.
        # Einfacher ist es, wenn evaluate_board_state immer aus Sicht von AI_PLAYER_COLOR bewertet
        # und Minimax das Vorzeichen bei Bedarf anpasst.
        # Für den Moment: evaluate_board_state gibt Score aus Sicht der KI.
        # Wenn maximizer = KI, ist das ok. Wenn minimizer = KI (also Mensch ist maximizer), dann -score.
        # Die aktuelle Struktur: maximizing_player ist True, wenn AI_PLAYER_COLOR am Zug ist (in diesem Ast)
        base_eval_score = evaluate_board_state(
            m_board, m_king_pos, m_ep_target, m_castling_rights, m_player_turn
        )
        return base_eval_score, None

    best_move_at_this_depth = None
    next_player = (
        HUMAN_PLAYER_COLOR if m_player_turn == AI_PLAYER_COLOR else AI_PLAYER_COLOR
    )

    if maximizing_player:
        max_eval = -float("inf")
        for start_pos, move_tuple in possible_moves:
            next_board, next_king_pos, next_ep, next_castling = _simulate_move_on_state(
                m_board,
                m_king_pos,
                m_ep_target,
                m_castling_rights,
                m_player_turn,
                start_pos,
                move_tuple,
                "Q",
            )
            eval_score, _ = _minimax_recursive(
                next_board,
                next_king_pos,
                next_ep,
                next_castling,
                next_player,
                depth - 1,
                alpha,
                beta,
                False,
            )

            if eval_score > max_eval:
                max_eval = eval_score
                best_move_at_this_depth = (start_pos, move_tuple)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move_at_this_depth
    else:
        min_eval = float("inf")
        for start_pos, move_tuple in possible_moves:
            next_board, next_king_pos, next_ep, next_castling = _simulate_move_on_state(
                m_board,
                m_king_pos,
                m_ep_target,
                m_castling_rights,
                m_player_turn,
                start_pos,
                move_tuple,
                "Q",
            )
            eval_score, _ = _minimax_recursive(
                next_board,
                next_king_pos,
                next_ep,
                next_castling,
                next_player,
                depth - 1,
                alpha,
                beta,
                True,
            )

            if eval_score < min_eval:
                min_eval = eval_score
                best_move_at_this_depth = (start_pos, move_tuple)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move_at_this_depth


def find_best_move_ai():
    score, best_move = _minimax_recursive(
        copy.deepcopy(board),
        copy.deepcopy(king_positions),
        en_passant_target,
        copy.deepcopy(castling_rights),
        AI_PLAYER_COLOR,
        AI_SEARCH_DEPTH,
        -float("inf"),
        float("inf"),
        True,  # True, da KI (AI_PLAYER_COLOR) maximiert
    )
    # print(f"AI ({AI_PLAYER_COLOR}) wählt Zug: {best_move} mit Score: {score}")
    return best_move


# --- GUI Klasse --- (weitgehend unverändert, Anpassungen in Zugbehandlung)
class ChessGUI:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("6x6 Schach mit KI")
        self.canvas = tk.Canvas(
            root_window, width=BOARD_SIZE * SQUARE_SIZE, height=BOARD_SIZE * SQUARE_SIZE
        )
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self.on_square_click)
        self.status_label = tk.Label(
            root_window, text="Weiß ist am Zug.", font=STATUS_FONT
        )
        self.status_label.pack(pady=5)
        reset_button = tk.Button(
            root_window, text="Neues Spiel", command=self.reset_game_ui
        )
        reset_button.pack(pady=5)
        self.reset_game_ui()

    def reset_game_ui(self):
        global selected_piece_pos, possible_move_dots, highlighted_square_ids, current_player, game_over
        initialize_game_state()
        selected_piece_pos = None
        self.clear_highlights()
        self.clear_possible_move_dots()
        self.draw_board()
        self.draw_pieces()
        self.update_status_label(f"{current_player.capitalize()} (Mensch) ist am Zug.")

    def draw_board(self):
        self.canvas.delete("board_squares")
        for r_draw in range(BOARD_SIZE):
            for c_draw in range(BOARD_SIZE):
                x1, y1 = c_draw * SQUARE_SIZE, r_draw * SQUARE_SIZE
                x2, y2 = x1 + SQUARE_SIZE, y1 + SQUARE_SIZE
                color_square = (
                    "saddlebrown" if (r_draw + c_draw) % 2 != 0 else "blanchedalmond"
                )
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color_square, tags="board_squares"
                )

    def draw_pieces(self):
        self.canvas.delete("pieces")
        for r_draw_p in range(BOARD_SIZE):
            for c_draw_p in range(BOARD_SIZE):
                piece_draw = board[r_draw_p][c_draw_p]
                if piece_draw:
                    x_draw_p = c_draw_p * SQUARE_SIZE + SQUARE_SIZE // 2
                    y_draw_p = r_draw_p * SQUARE_SIZE + SQUARE_SIZE // 2
                    fill_color_p = (
                        "black" if get_piece_color(piece_draw) == "black" else "dimgray"
                    )
                    self.canvas.create_text(
                        x_draw_p,
                        y_draw_p,
                        text=PIECES_UNICODE[piece_draw],
                        font=PIECE_FONT,
                        tags="pieces",
                        fill=fill_color_p,
                    )

    def clear_highlights(self):
        global highlighted_square_ids
        for item_id_clear in highlighted_square_ids:
            self.canvas.delete(item_id_clear)
        highlighted_square_ids = []

    def highlight_selected_square(self, r_highlight, c_highlight):
        self.clear_highlights()
        x1_hl, y1_hl = c_highlight * SQUARE_SIZE, r_highlight * SQUARE_SIZE
        x2_hl, y2_hl = x1_hl + SQUARE_SIZE, y1_hl + SQUARE_SIZE
        rect_id_hl = self.canvas.create_rectangle(
            x1_hl, y1_hl, x2_hl, y2_hl, outline="blue", width=3
        )
        highlighted_square_ids.append(rect_id_hl)

    def clear_possible_move_dots(self):
        global possible_move_dots
        for dot_id_clear in possible_move_dots:
            self.canvas.delete(dot_id_clear)
        possible_move_dots = []

    def show_possible_moves(self, moves_tuples_list_show):
        self.clear_possible_move_dots()
        for move_tuple_show in moves_tuples_list_show:
            r_end_show, c_end_show = move_tuple_show[0], move_tuple_show[1]
            x_show = c_end_show * SQUARE_SIZE + SQUARE_SIZE // 2
            y_show = r_end_show * SQUARE_SIZE + SQUARE_SIZE // 2
            radius_show = SQUARE_SIZE // 8
            fill_color_dot = (
                "darkolivegreen1"
                if board[r_end_show][c_end_show] is None
                else "orangered"
            )
            dot_id_show = self.canvas.create_oval(
                x_show - radius_show,
                y_show - radius_show,
                x_show + radius_show,
                y_show + radius_show,
                fill=fill_color_dot,
                outline="",
                tags="possible_move_dot",
            )
            possible_move_dots.append(dot_id_show)

    def on_square_click(self, event_click):
        global selected_piece_pos, current_player, game_over

        if game_over or current_player == AI_PLAYER_COLOR:
            return

        c_click = event_click.x // SQUARE_SIZE
        r_click = event_click.y // SQUARE_SIZE

        if not is_valid_square(r_click, c_click):
            return
        clicked_piece_on_board = board[r_click][c_click]

        if selected_piece_pos:
            start_r_click, start_c_click = selected_piece_pos
            potential_moves_for_selected_click = []
            all_player_moves_click = get_all_legal_moves_for_player(current_player)
            for move_pair_click in all_player_moves_click:
                if move_pair_click[0] == selected_piece_pos:
                    potential_moves_for_selected_click.append(move_pair_click[1])

            target_move_tuple_click = None
            for move_tuple_click_item in potential_moves_for_selected_click:
                if (
                    move_tuple_click_item[0] == r_click
                    and move_tuple_click_item[1] == c_click
                ):
                    target_move_tuple_click = move_tuple_click_item
                    break

            if target_move_tuple_click:
                self.handle_human_move(selected_piece_pos, target_move_tuple_click)
                selected_piece_pos = None
                self.clear_highlights()
                self.clear_possible_move_dots()
            elif (
                clicked_piece_on_board
                and get_piece_color(clicked_piece_on_board) == current_player
            ):
                selected_piece_pos = (r_click, c_click)
                self.highlight_selected_square(r_click, c_click)
                self.show_legal_moves_for_selected_piece(r_click, c_click)
            else:
                selected_piece_pos = None
                self.clear_highlights()
                self.clear_possible_move_dots()

        elif (
            clicked_piece_on_board
            and get_piece_color(clicked_piece_on_board) == current_player
        ):
            selected_piece_pos = (r_click, c_click)
            self.highlight_selected_square(r_click, c_click)
            self.show_legal_moves_for_selected_piece(r_click, c_click)

    def show_legal_moves_for_selected_piece(self, r_selected_show, c_selected_show):
        legal_moves_for_this_piece_show = []
        all_player_moves_show = get_all_legal_moves_for_player(current_player)
        for move_pair_show in all_player_moves_show:
            if move_pair_show[0] == (r_selected_show, c_selected_show):
                legal_moves_for_this_piece_show.append(move_pair_show[1])
        self.show_possible_moves(legal_moves_for_this_piece_show)

    def handle_human_move(self, start_pos_handle, end_move_tuple_handle):
        global game_over, current_player

        piece_char_handle = board[start_pos_handle[0]][start_pos_handle[1]]
        ptype_handle = get_piece_type(piece_char_handle)
        color_handle = get_piece_color(piece_char_handle)
        promotion_piece_choice_handle = None

        promotion_rank_handle = 0 if color_handle == "white" else BOARD_SIZE - 1
        if ptype_handle == "P" and end_move_tuple_handle[0] == promotion_rank_handle:
            promotion_piece_choice_handle = self.prompt_pawn_promotion()
            if not promotion_piece_choice_handle:
                return

        make_move(
            start_pos_handle, end_move_tuple_handle, promotion_piece_choice_handle
        )
        self.draw_board()
        self.draw_pieces()

        if not game_over:
            is_game_now_over = check_game_status()
            if not is_game_now_over:
                if current_player == AI_PLAYER_COLOR:
                    self.trigger_ai_turn()
            # Statuslabel wird in trigger_ai_turn oder check_game_status gesetzt

    def trigger_ai_turn(self):
        if game_over or current_player != AI_PLAYER_COLOR:
            return
        self.update_status_label(f"{AI_PLAYER_COLOR.capitalize()} (KI) denkt nach...")
        self.root.update_idletasks()
        self.root.after(50, self.execute_ai_move)

    def execute_ai_move(self):
        global game_over, current_player
        if game_over or current_player != AI_PLAYER_COLOR:
            return

        ai_move = find_best_move_ai()

        if ai_move:
            start_pos_ai, end_tuple_ai = ai_move
            promotion_choice_ai = None
            piece_char_ai = board[start_pos_ai[0]][start_pos_ai[1]]
            ptype_ai = get_piece_type(piece_char_ai)
            promo_rank_ai = 0 if AI_PLAYER_COLOR == "white" else BOARD_SIZE - 1
            if ptype_ai == "P" and end_tuple_ai[0] == promo_rank_ai:
                promotion_choice_ai = "Q"

            make_move(start_pos_ai, end_tuple_ai, promotion_choice_ai)
            self.draw_board()
            self.draw_pieces()

            if not game_over:
                is_game_now_over_after_ai = check_game_status()
                if not is_game_now_over_after_ai:
                    if not is_in_check(
                        current_player
                    ):  # current_player ist jetzt HUMAN
                        self.update_status_label(
                            f"{current_player.capitalize()} (Mensch) ist am Zug."
                        )
                    # Falls Schach, hat check_game_status das Label aktualisiert
        else:  # KI findet keinen Zug mehr (sollte durch check_game_status vorher abgefangen werden)
            if not game_over:
                check_game_status()

    def prompt_pawn_promotion(self):
        choice_promo = simpledialog.askstring(
            "Bauernumwandlung", "Wähle Figur (Q, R, B, N):", parent=self.root
        )
        if choice_promo and choice_promo.upper() in ["Q", "R", "B", "N"]:
            return choice_promo.upper()
        return "Q"

    def update_status_label(self, text_status):
        self.status_label.config(text=text_status)


# --- Hauptprogramm ---
gui = None
if __name__ == "__main__":
    root = tk.Tk()
    gui = ChessGUI(root)
    root.mainloop()
