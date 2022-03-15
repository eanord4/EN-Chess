"""
Intellectual property of Eric Nordstrom
https://github.com/eanord4/EN-Chess
"""


BOARDS = {
	"standard": {(file, rank) for file in "abcdefgh" for rank in range(1, 9)},
	"en": {(file, rank) for file in "abcdefgh" for rank in range(1, 9)}.union({("x", 0), ("x", 9)})
}

in_play = False





class Piece:

	def __init__(self, color, file, rank):
		self.color = color
		self.file = file
		self.rank = rank
		self.moved = False
		self._copy = None
		self._came_from = None

	def possible_moves(self, pieces="current", board="current"):
		"""(file, rank, interacting_pieces, *promote_cloass) of each move available to this piece"""

		if pieces == "current":
			pieces = globals()["pieces"]

		if board == "current":
			board = globals()["board"]

		# if any own kings in check, must make a move that decreases the number of own kings in check, or keep at zero if at zero

		# how many own kings in check prior to move?
		own_check_count = 0
		for king, check in _checks(pieces):
			if check and king.color == self.color:
				own_check_count += 1

		# how many own kings in check after each move?
		for file, rank, interacting_pieces, *promote_class in self._normally_possible_moves(pieces=pieces, board=board):

			hypothetical_own_check_count = 0

			for king, check in self._resulting_checks(file, rank, interacting_pieces, *promote_class, pieces=pieces, board=board):
				if check and king.color == self.color:
					hypothetical_own_check_count += 1

			if hypothetical_own_check_count < own_check_count or hypothetical_own_check_count == 0:
				yield file, rank, interacting_pieces, *promote_class

	def _resulting_checks(self, file, rank, interacting_pieces, *promote_class, pieces="current", board="current"):
		"""checks that would result from a hypothetical move"""

		if pieces == "current":
			pieces = globals()["pieces"]

		if board == "current":
			board = globals()["board"]

		# create hypothetical move scenario without changing actual scenario
		hypothetical_pieces = {piece.copy() for piece in pieces}
		hypothetical_board = {key: None for key in board}
		hypothetical_interacting_pieces = {piece._copy for piece in interacting_pieces}
		for piece in hypothetical_pieces:
			hypothetical_board[(piece.file, piece.rank)] = piece
		self._copy._move(file, rank, hypothetical_interacting_pieces, *promote_class, pieces=hypothetical_pieces, board=hypothetical_board)

		# get checks in hypothetical scenario
		for king, check in _checks(hypothetical_pieces):
			yield king._came_from, check

	def _move(self, file, rank, to_capture, *promote_class, pieces="current", board="current"):
		"""Apply the move under the assumption that it is legal. (Not to be applied unless legality has been assured.)"""

		if pieces == "current":
			pieces = globals()["pieces"]

		if board == "current":
			board = globals()["board"]

		# update location
		board[(self.file, self.rank)] = None
		self.file = file
		self.rank = rank
		board[(self.file, self.rank)] = self

		# remove captured pieces
		for piece in to_capture:
			pieces.remove(piece)

		# promoting
		if promote_class and promote_class[0]:
			pieces.remove(self)
			new_piece = promote_class(self.color, self.file, self.rank)
			new_piece._came_from = self
			new_piece.moved = True
			pieces.add(new_piece)

		# update state of having moved
		self.moved = True

	def copy(self):
		piece = type(self)(self.color, self.file, self.rank)
		piece.moved = self.moved
		piece._came_from = self
		self._copy = piece
		return piece

	def _abbrev(self):
		return type(self).__name__[0]

	def __repr__(self):
		return f"{self} @ {self.file}{self.rank}"


class LongRangePiece(Piece):

	def _adjacent_aurors(self, pieces="current"):

		if pieces == "current":
			pieces = globals()["pieces"]

		if variant != "en":
			return 0, 0

		own_count = enemy_count = 0

		for piece in pieces:
			if isinstance(piece, Auror) and abs(ord(piece.file) - ord(self.file)) < 2 and abs(piece.rank - self.rank) < 2:
				if piece.color == self.color:
					own_count += 1
				else:
					enemy_count += 1

		return own_count, enemy_count

	def _iter_moves(self, direction, pieces="current", board="current"):
		"""moves that are possible in the given direction (file increment, rank increment) before considering check"""

		if board == "current":
			board = globals()["board"]

		if pieces == "current":
			pieces = globals()["pieces"]

		own_count, enemy_count = self._adjacent_aurors(pieces)
		max_captures = 1 + (variant == "en" and own_count > enemy_count)
		captures = set()

		# get next square
		if self.file == "x":
			if self.rank == 9:
				if direction == (-1, -1):
					file, rank = "d", 8
				elif direction == (1, -1):
					file, rank = "e", 8
				else:
					return
			elif self.rank == 0:
				if direction == (-1, 1):
					file, rank = "d", 1
				elif direction == (1, 1):
					file, rank = "e", 1
				else:
					return
		else:
			file = chr(ord(self.file) + direction[0])
			rank = self.rank + direction[1]

		# stunted mode (at least)
		if (file, rank) in board:
			
			if board[(file, rank)]:
				if board[(file, rank)].color == self.color:
					return
				else:
					captures = {board[(file, rank)]}
			
			yield file, rank, captures

		# standard & penetration modes
		if own_count >= enemy_count:

			file = chr(ord(file) + direction[0])
			rank += direction[1]

			while len(captures) < max_captures and (file, rank) in board:

				if board[(file, rank)]:
					if board[(file, rank)].color == self.color:
						return
					else:
						captures = captures.union({board[(file, rank)]})
				
				yield file, rank, captures

				file = chr(ord(file) + direction[0])
				rank += direction[1]

		# "x" squares
		if variant == "en" and len(captures) < max_captures and (file, rank) not in board:

			# revert to previous square
			file = chr(ord(self.file) - direction[0])
			rank = rank - direction[1]

			# availability of "x" squares based on location and direction
			if rank == 8 and (
				direction == (1, 1) and file == "d"
				or direction == (-1, 1) and file == "e"):

				if board[("x", 9)]:
					if board[("x", 9)].color == self.color:
						return
					else:
						captures = captures.union({board[("x", 9)]})

				yield "x", 9, captures

			elif rank == 1 and (
				direction == (1, -1) and file == "d"
				or direction == (-1, -1) and file == "e"):

				if board[("x", 0)]:
					if board[("x", 0)].color == self.color:
						return
					else:
						captures = captures.union({board[("x", 0)]})

				yield "x", 0, captures


class Pawn(Piece):

	def _normally_possible_moves(self, pieces="current", board="current"):
		"""moves that are possible before considering check"""

		if pieces == "current":
			pieces = globals()["pieces"]

		if board == "current":
			board = globals()["board"]

		if self.rank in {1, 8}:  # EN only - promoting options only
			for move in self._move_with_promote_options(self.file, self.rank, set()):
				yield move

		if self.color == "White":

			# can move forward unless piece in the way (or promoted)
			forward_1 = self.rank < 8  # in EN variant, can choose not to promote D and E pawns; therefore, it is possible for a pawn not to have a forward move even if no piece is in the way
			forward_2 = self.rank == 2  # 2-square jump at start

			for piece in pieces:

				# capture diagonally
				if piece.color == "Black"\
					and abs(ord(piece.file) - ord(self.file)) == 1\
					and piece.rank == self.rank + 1:

					for move in self._move_with_promote_options(self.file, self.rank, {piece}):
						yield move

				# piece in the way
				if piece.file == self.file:
					if piece.rank == self.rank + 1:
						forward_1 = forward_2 = False
					elif piece.rank == self.rank + 2:
						forward_2 = False

				# EN only
				if piece.rank == 9 and self.rank == 8 and self.file in {"d", "e"}:
					for move in self._move_with_promote_options("x", 9, {piece}):
						yield move

			if forward_1:
				for move in self._move_with_promote_options(self.file, self.rank + 1, set()):
					yield move

			if forward_2:
				yield self.file, self.rank + 2, set(), None

		else:

			# can move forward unless piece in the way or at end of board
			forward_1 = self.rank > 1  # in EN variant, can choose not to promote D and E pawns; therefore, it is possible for a pawn not to have a forward move even if no piece is in the way
			forward_2 = self.rank == 7  # 2-square jump at start

			for piece in pieces:

				# capture diagonally
				if piece.color == "White"\
					and abs(ord(piece.file) - ord(self.file)) == 1\
					and piece.rank == self.rank - 1:

					for move in self._move_with_promote_options(piece.file, piece.rank, {piece}):
						yield move

				# piece in the way
				if piece.file == self.file:
					if piece.rank == self.rank - 1:
						forward_1 = forward_2 = False
					elif piece.rank == self.rank - 2:
						forward_2 = False

				# EN only
				if piece.rank == 0 and self.rank == 1 and self.file in {"d", "e"}:
					for move in self._move_with_promote_options("x", 0, {piece}):
						yield move

			if forward_1:
				for move in self._move_with_promote_options(self.file, self.rank - 1, set()):
					yield move

			if forward_2:
				yield self.file, self.rank - 2, set(), None

	def _move_with_promote_options(self, file, rank, to_capture):
		"""yield all versions of the move with promote options where necessary (otherwise keep as the same single move)"""

		if rank in {1, 8}:

			# EN options
			if variant == "en":

				yield file, rank, to_capture, King

				if self.rank == rank:
					yield file, rank, to_capture, Auror
				else:
					yield file, rank, to_capture, None
			
			# standard options
			if variant == "standard" or self.rank == rank:
				for promote_class in (Queen, Rook, Knight, Bishop):
					yield file, rank, to_capture, promote_class

		elif file == "x":
			for promote_class in (King, Auror, Queen, Knight, Bishop):
				yield file, rank, to_capture, promote_class

		else:
			yield file, rank, to_capture, None

	def __str__(self):
		if self.color == "Black":
			return "𝖕" 
		return "ρ"


class Rook(LongRangePiece):

	def _normally_possible_moves(self, pieces="current", board="current"):
		"""moves that are possible before considering check"""

		if pieces == "current":
			pieces = globals()["pieces"]

		if board == "current":
			board = globals()["board"]

		for direction in ((0, -1), (0, 1), (-1, 0), (1, 0)):
			for move in self._iter_moves(direction, pieces, board):
				yield move

	def __str__(self):
		if self.color == "Black":
			return "𝑹"
		return "ᖇ"


class Knight(Piece):

	def _normally_possible_moves(self, pieces="current", board="current"):
		"""moves that are possible before considering check"""

		if pieces == "current":
			pieces = globals()["pieces"]

		if board == "current":
			board = globals()["board"]

		x_accessible_squares = {
			0: [("c", 1), ("d", 2), ("e", 2), ("f", 1)],
			9: [("c", 8), ("d", 7), ("e", 7), ("f", 8)]
		}

		if self.file == "x":
			for file, rank in x_accessible_squares[self.rank]:

				piece = board[(file, rank)]

				if piece:
					if piece.color != self.color:
						yield file, rank, {piece}
				else:
					yield file, rank, set()

		else:

			available_squares = BOARDS[variant].copy()

			for piece in pieces:
				if abs((piece.rank - self.rank) * (ord(piece.file) - ord(self.file))) == 2\
					or piece.file == "x" and (self.file, self.rank) in x_accessible_squares[piece.rank]:

					if piece.color != self.color:
						yield piece.file, piece.rank, {piece}

					available_squares.remove((piece.file, piece.rank))

			for square in available_squares:
				if abs((square[1] - self.rank) * (ord(square[0]) - ord(self.file))) == 2\
					or square[0] == "x" and (self.file, self.rank) in x_accessible_squares[square[1]]:
					yield *square, set()

	def __str__(self):
		if self.color == "Black":
			return "𝑵"
		return "Ɲ"


class Bishop(LongRangePiece):

	def _normally_possible_moves(self, pieces="current", board="current"):
		"""moves that are possible before considering check"""

		if pieces == "current":
			pieces = globals()["pieces"]

		if board == "current":
			board = globals()["board"]

		for direction in ((-1, -1), (1, 1), (-1, 1), (1, -1)):
			for move in self._iter_moves(direction, pieces, board):
				yield move

	def __str__(self):
		if self.color == "Black":
			return "𝑩"
		return "ẞ"


class Queen(LongRangePiece):

	def _normally_possible_moves(self, pieces="current", board="currrent"):
		"""moves that are possible before considering check"""

		if pieces == "current":
			pieces = globals()["pieces"]

		if board == "current":
			board = globals()["board"]
		
		# orthogonal movement
		for move in Rook(self.color, self.file, self.rank)._normally_possible_moves(pieces=pieces, board=board):
			yield move

		# diagonal movement
		for move in Bishop(self.color, self.file, self.rank)._normally_possible_moves(pieces=pieces, board=board):
			yield move

	def __str__(self):
		if self.color == "Black":
			return "𝑸"
		return "𝚀"


class King(Piece):

	def _move(self, file, rank, interacting_pieces, pieces="current", board="current"):

		if pieces == "current":
			pieces = globals()["pieces"]

		if board == "current":
			board = globals()["board"]

		# special moves
		to_capture = interacting_pieces.copy()
		for piece in interacting_pieces:
			if piece.color == self.color:

				# castling
				if isinstance(piece, Rook):
					if piece.file == "a":
						piece._move("d", self.rank, set(), pieces=pieces, board=board)
					else:
						piece._move("f", self.rank, set(), pieces=pieces, board=board)

				# auror swaps
				if isinstance(piece, Auror):
					piece._move(self.file, self.rank, set(), pieces=pieces, board=board)

				to_capture.remove(piece)

		Piece._move(self, file, rank, to_capture, pieces=pieces, board=board)
		self.moved = True

	def _normally_possible_moves(self, pieces="current", board="current"):
		"""moves that are possible before considering resulting checks"""

		if pieces == "current":
			pieces = globals()["pieces"]

		if board == "current":
			board = globals()["board"]
		
		available_squares = BOARDS[variant].copy()  # for normal king movement

		if self.file == "x":

			queenside_clear_for_castle = kingside_clear_for_castle = False

			if self.rank == 0:

				for piece in pieces:
					if piece.rank == 1 and piece.file in "de":
						if piece.color != self.color:
							yield piece.file, piece.rank, {piece}
						available_squares.remove((piece.file, piece.rank))

				for square in available_squares:
					if square[1] == 1 and square[0] in "de":
						yield *square, set()

			elif self.rank == 9:

				for piece in pieces:
					if piece.rank == 8 and piece.file in "de":
						if piece.color != self.color:
							yield piece.file, piece.rank, {piece}
						available_squares.remove((piece.file, piece.rank))

				for square in available_squares:
					if square[1] == 8 and square[0] in "de":
						yield *square, set()

		else:

			queenside_clear_for_castle = kingside_clear_for_castle = True

			for piece in pieces:

				if abs(piece.rank - self.rank) < 2\
					and abs(ord(piece.file) - ord(self.file)) < 2\
					or piece.file == "x" and self.file in "de" and (
						piece.rank == 0 and self.rank == 1
						or piece.rank == 9 and self.rank == 8):

					if piece.color != self.color:
						yield piece.file, piece.rank, {piece}

					available_squares.remove((piece.file, piece.rank))

				if piece.rank == self.rank and not(piece.color == self.color and piece.file in "ah"):
					if piece.file < self.file:
						queenside_clear_for_castle = False
					elif piece.file > self.file:
						kingside_clear_for_castle = False

			for square in available_squares:
				if abs(square[1] - self.rank) < 2\
					and abs(ord(square[0]) - ord(self.file)) < 2\
					or square[0] == "x" and (
						square[1] == 0 and self.rank == 1 and self.file in "de"
						or square[1] == 9 and self.rank == 8 and self.file in "de"):

					yield *square, set()

		# special moves
		for piece in pieces:

			# auror swaps
			if isinstance(piece, Auror) and piece.color == self.color:
				yield piece.file, piece.rank, {piece}

			# castling
			elif not self.moved and (queenside_clear_for_castle or kingside_clear_for_castle)\
				and isinstance(piece, Rook) and piece.color == self.color and not piece.moved:
				# must rule out checks that do not result from the final state of the move (namely passing through check or castling out of check)
				
				# currently in check?
				for king, check in _checks(pieces):
					if check and king is self:
						break

				# also cannot pass through check	
				else:

					if piece.file == "a" and queenside_clear_for_castle:
						for king, check in self._resulting_checks("d", self.rank, set(), pieces=pieces):
							if check and king is self:
								break
						else:
							yield "c", self.rank, {piece}

					elif piece.file == "h" and kingside_clear_for_castle:
						for king, check in self._resulting_checks("f", self.rank, set(), pieces=pieces):
							if check and king is self:
								break
						else:
							yield "g", self.rank, {piece}

	def __str__(self):
		if self.color == "Black":
			return "𝑲"
		return "𐌊"


class Auror(Piece):

	def _normally_possible_moves(self, pieces="current", board="current"):
		"""moves that are possible before considering check"""

		if pieces == "current":
			pieces = globals()["pieces"]

		if board == "current":
			board = globals()["board"]

		own_auror_locations = {(piece.file, piece.rank) for piece in pieces
			if isinstance(piece, Auror)
			and piece.color == self.color}
		
		# king-like movement without capturing or auror swaps
		hypothetical_king = King(self.color, self.file, self.rank)
		hypothetical_king.moved = True
		for move in hypothetical_king._normally_possible_moves(pieces=pieces, board=board):
			if not move[2] and move[:2] not in own_auror_locations:
				yield move

		# knight-like movement without capturing
		for move in Knight(self.color, self.file, self.rank)._normally_possible_moves(pieces=pieces, board=board):
			if not move[2]:
				yield move

		# king swaps
		for piece in pieces:
			if isinstance(piece, King) and piece.color == self.color:
				yield piece.file, piece.rank, {piece}

	def _move(self, file, rank, king_to_swap, pieces="current", board="current"):

		if pieces == "current":
			pieces = globals()["pieces"]

		if board == "current":
			board = globals()["board"]		

		if king_to_swap:
			king_to_swap.pop()._move(self.file, self.rank, set(), pieces=pieces, board=board)

		Piece._move(self, file, rank, set(), pieces=pieces, board=board)

	def __str__(self):
		if self.color == "Black":
			return "𝕬"
		return "ᗩ"







def _init_pieces(variant="standard"):

	if variant == "en":
		return _init_pieces("standard").union({Auror("White", "x", 0), Auror("Black", "x", 9)})

	return {Pawn("White", file, 2) for file in "abcdefgh"}\
			.union({Pawn("Black", file, 7) for file in "abcdefgh"})\
			.union({
				Rook("White", "a", 1), Rook("White", "h", 1), Rook("Black", "a", 8), Rook("Black", "h", 8),
				Knight("White", "b", 1), Knight("White", "g", 1), Knight("Black", "b", 8), Knight("Black", "g", 8),
				Bishop("White", "c", 1), Bishop("White", "f", 1), Bishop("Black", "c", 8), Bishop("Black", "f", 8),
				Queen("White", "d", 1), Queen("Black", "d", 8),
				King("White", "e", 1), King("Black", "e", 8)})


def _init_board(variant="standard"):
	
	board = {loc: None for loc in BOARDS[variant]}

	for piece in pieces:
		board[(piece.file, piece.rank)] = piece

	return board


def start_game(game_variant="en"):
	global pieces, board, turn, variant, in_play, turn_count  ### future: change into a list of moves; add value counts (auror?)
	variant = game_variant.lower()
	pieces = _init_pieces(variant)
	board = _init_board(variant)
	turn = "White"
	in_play = True
	turn_count = 0
	display_board()
	print("White to move.")


def move(piece_loc, destination_loc, *promote_class):
	global in_play, turn

	if not in_play:
		raise RuntimeError("You haven't started a game yet!")

	piece = board[(piece_loc[0], int(piece_loc[1]))]
	if not piece:
		raise ValueError("There's no piece there!")

	if piece.color != turn:
		raise ValueError(f"It's {turn}'s turn!")

	for file, rank, interacting_pieces, *move_promote_class in piece.possible_moves():
		if file == destination_loc[0] and rank == int(destination_loc[1]) and (
			promote_class in {(None,), tuple()} and tuple(move_promote_class) in {(None,), tuple()}
			or promote_class and move_promote_class and promote_class[0].title() == move_promote_class[0].__name__):

			piece._move(file, rank, interacting_pieces, *move_promote_class)
			print(f"{type(piece).__name__} moved to {destination_loc}.")

			for interacting_piece in interacting_pieces:
				if interacting_piece.color != piece.color:
					print(f"{type(interacting_piece).__name__} captured.")

			if promote_class and promote_class[0]:
				print(f"{type(piece).__name__} promoted to {promote_class[0].__name__}!")

			### future: announce checks?

			break

	else:
		raise ValueError("Move not allowed!")

	print()

	turn = ["White", "Black"][turn == "White"]

	for move in _all_possible_moves():
		display_board(perspective=turn)
		print(f"{turn} to move.")
		break

	else:
		# no possible moves; differentiate between checkmate, stalemate, and partial checkmate

		king_count = check_count = 0
		for king, check in _checks():
			if king.color == turn:

				king_count += 1

				if check:
					check_count += 1
				
		if check_count == 0:
			print("Draw by stalemate!!!")
			display_board(perspective=turn)
			print("Draw by stalemate!!!")
			in_play = False
		elif check_count < king_count:
			print(f"{check_count}/{king_count} partial checkmate; {turn} loses a turn.")
			turn = ["White", "Black"][turn == "White"]
			display_board(perspective=turn)
			print(f"{turn} to move.")
		else:
			print(f"{turn} wins by checkmate!!!")
			display_board(perspective=turn)
			print(f"{turn} wins by checkmate!!!")
			in_play = False


def _checks(pieces="current", board="current"):
	"""yields (king, true/false) for each king, indicating whether that king is in check"""

	if pieces == "current":
		pieces = globals()["pieces"]

	if board == "current":
		board = globals()["board"]

	for king in pieces:
		if isinstance(king, King):

			for piece in pieces:
				if piece.color != king.color:

					# prevent endless loop for uncastled kings (which must examine checks even before the transition from _normally_possible_moves to possible_moves) in hypothetical scenarios (real scenarios can never have kings checking other kings)
					if isinstance(piece, King):
						if abs(ord(piece.file) - ord(king.file)) < 2 and abs(piece.rank - king.rank) < 2:
							yield king, True
							break

					else:

						# note that `interacting_pieces` can only be for capture if the moving and interacting pieces are of different players, as there are no cross-player special moves
						for _, _, interacting_pieces, *_ in piece._normally_possible_moves(pieces=pieces, board=board):
							if king in interacting_pieces:
								yield king, True
								break
						else:
							continue

						break

			else:
				yield king, False


def _all_possible_moves():

	to_skip = []

	for piece in pieces:
		if piece.color == turn:
			for file, rank, interacting_pieces, *promote_class in piece.possible_moves():
				for interacting_piece in interacting_pieces:
					if interacting_piece.color == piece.color and {piece, interacting_piece} not in to_skip:
						yield piece, file, rank, interacting_pieces, *promote_class
						to_skip.append({piece, interacting_piece})
						break
				else:
					yield piece, file, rank, interacting_pieces, *promote_class


def list_checks():
	for king, check in _checks():
		print(f"{repr(king)}: {check}")
				

def list_all_possible_moves():
	"""List all of the current player's possible moves."""

	for piece, file, rank, interacting_pieces, *promote_class in _all_possible_moves():

		print(f"{piece} --> {file}{rank}")

		for interacting_piece in interacting_pieces:

			if interacting_piece.color == piece.color:

				if isinstance(interacting_piece, Rook):
					if interacting_piece.file < piece.file:
						print("\t(castle queenside)")
					else:
						print("\t(castle kingside)")
				else:
					print(f"\t(swap with {type(interacting_piece).__name__})")

			else:
				print(f"\tcapture {interacting_piece}")

		if promote_class and promote_class[0]:
			print(f"\tpromote to {promote_class.__name__}")


def list_piece_possible_moves(piece_loc):
	"""List all possible moves for the piece at the specified location."""

	piece = board[(piece_loc[0], int(piece_loc[1]))]

	for file, rank, interacting_pieces, *promote_class in pieces.possible_moves():

		print(file + str(rank))

		list_captures = True
		for piece in interacting_pieces:
			if piece.color == piece.color:
				if isinstance(piece, Rook):
					print("\t(castle)")
				elif isinstance(piece, King):
					print("\t(swap with King)")
				elif isinstance(piece, Auror):
					print("\t(swap with Auror)")
			elif list_captures:
				print(f"\t(capture {', '.join((p for p in interacting_pieces if p.color != piece.color))})")
				list_captures = False  # only list once and include all captured pieces on this line

		if promote_class and promote_class[0]:
			print(f"\t(promote to {promote_class.__name__})")


def display_board(perspective="White"):

	if perspective[0].upper() == "W":
		rank_order = range(8, 0, -1)
		file_order = "abcdefgh"
	else:
		rank_order = range(1, 9)
		file_order = "hgfedcba"

	# top X square
	if variant == "en":
		rank = 9 if perspective == "White" else 0
		occupant = board[("x", rank)]
		occupant = str(occupant) if occupant else " "
		print(" " * 34, rank)
		print(" " * 33 + "// \\\\")
		print(" " * 31 + "///   \\\\\\")
		print(" " * 29 + f"///  {occupant} {occupant}  \\\\\\")
		print(" " * 29 + f"\\\\\\  {occupant} {occupant}  ///")
		print(" " * 31 + "\\\\\\   ///")
		print(" " * 33 + "\\\\ //")
		print(" " * 35 + "x")

	# top line
	if variant == "en":
		print("    " + " ".join(["-------"] * 3) + " -----// \\\\----- " + " ".join(["-------"] * 3))
	else:
		print("    " + " ".join(["-------"] * 8))

	# standard squares
	for rank in rank_order:

		# 1st of 3 rows
		print("   |", end="")
		for file in file_order:
			if (ord(file) - ord("a")) % 2 == (rank - 1) % 2:
				print("///" + (" " if board[(file, rank)] else "|") + "\\\\\\|", end="")
			else:
				print("       |", end="")

		# 2nd of 3 rows
		print(f"\n{rank}  |", end="")
		for file in file_order:

			occupant = board[(file, rank)]

			if (ord(file) - ord("a")) % 2 == (rank - 1) % 2:
				occupant = f"  {occupant}  " if occupant else "|||||"
				print(f"|{occupant}||", end="")
			else:
				occupant = str(occupant) if occupant else " "
				print(f"   {occupant}   |", end="")

		# 3rd of 3 rows
		print("\n   |", end="")
		for file in file_order:
			if (ord(file) - ord("a")) % 2 == (rank - 1) % 2:
				print("\\\\\\" + (" " if board[(file, rank)] else "|") + "///|", end="")
			else:
				print("       |", end="")

		# rank separator
		if rank != rank_order[-1]:
			print("\n    " + "+".join(["-------"] * 8))

	# bottom line
	if variant == "en":
		print("\n    " + " ".join(["-------"] * 3) + " -----\\\\ //----- " + " ".join(["-------"] * 3))
	else:
		print("\n    " + " ".join(["-------"] * 8))

	# file labels
	if variant == "en":
		print("       " + "       ".join(file_order[:4]) + "   x   " + "       ".join(file_order[4:]))
	else:
		print("       " + "       ".join(file_order))

	# bottom X square
	if variant == "en":
		rank = 0 if perspective == "White" else 9
		occupant = board[("x", rank)]
		occupant = str(occupant) if occupant else " "
		print(" " * 33 + "// \\\\")
		print(" " * 31 + "///   \\\\\\")
		print(" " * 29 + f"///  {occupant} {occupant}  \\\\\\")
		print(" " * 29 + f"\\\\\\  {occupant} {occupant}  ///")
		print(" " * 31 + "\\\\\\   ///")
		print(" " * 33 + "\\\\ //")
		print(" " * 34, rank)


def display_piece_possible_moves(piece_loc, perspective="White"):
	"""Annotate the board with all possible moves for the piece at the specified location."""

	from io import StringIO
	import sys

	orig_stdout = sys.stdout
	sys.stdout = markup = StringIO()
	display_board(perspective)
	markup = markup.getvalue()
	sys.stdout = orig_stdout

	piece = board[(piece_loc[0], int(piece_loc[1]))]

	if not piece:
		raise ValueError("There's no piece there!")

	for file, rank, interacting_pieces, *promote_class in piece.possible_moves():

		if file == "x":

			chars = " ※ ※ "

			for interacting_piece in interacting_pieces:
				if interacting_piece.color == piece.color:
					if type(interacting_piece) in {King, Auror}:
						chars = f" ({str(interacting_piece)} {str(interacting_piece)}) "
				else:
					chars = f" x{str(interacting_piece)} {str(interacting_piece)}x "

			if rank == 9 and perspective[0].upper() == "W" or rank == 0 and perspective[0].upper() == "B":
				markup = markup[:150] + chars + markup[155:193] + chars + markup[198:]
			else:
				markup = markup[:2766] + chars + markup[2771:2809] + chars + markup[2814:]

		else:

			chars = "  ፠  "

			for interacting_piece in interacting_pieces:
				if interacting_piece.color == piece.color:
					if type(interacting_piece) in {King, Auror}:
						chars = f" ({str(interacting_piece)}) "
				else:
					chars = f" x{str(interacting_piece)}x "

			start = 462
			file_adjustment = 8 * (ord(file) - ord("a"))
			rank_adjustment = 275 * (8 - rank if perspective[0].upper() == "W" else rank - 1)
			chars_loc = start + rank_adjustment + file_adjustment
			markup = markup[:chars_loc] + chars + markup[chars_loc + 5:]

	print(markup)


def display_possible_moves_by_piece(perspective="White"):
	"""For each of the current player's pieces, display the board, annoted with all possible moves of that piece."""

	for piece in pieces:
		print(repr(piece))
		display_piece_possible_moves(piece.file + str(piece.rank))
		list_piece_possible_moves(piece.file + str(piece.rank))
		print()






if __name__ == "__main__":
	while True:

		variant = "x"
		while variant not in {"en", "standard"}:
			variant = input("Choose variant ('en' or 'standard'): ").lower()

		print("The game begins!")
		start_game(variant)

		while True:

			func, *args = input().split()

			if len(func) == 2:  # there are no functions with name of length 2, so assume this is a piece position
				args = (func, *args)
				func = "move"

			try:
				eval(func)(*args)
			except Exception as e:
				print(repr(e))

		play_again = "x"
		while play_again not in {"y", "n"}:
			play_again = input("Play again? (y/n): ").lower()

		if play_again != "y":
			print("Thanks for playing!")
			break
