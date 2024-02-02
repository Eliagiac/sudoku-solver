from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

max_tries = 1000

extra_spaces = 1

window_size = 600
margin_size = [58, 87]

time_between_steps = 1


class GridBackgroundWidget(QWidget):
	box_size = 3
	grid_size = 9

	def __init__(self, box_size, grid_size):
		self.box_size = box_size
		self.grid_size = grid_size
		super().__init__()

	def paintEvent(self, event):
		painter = QPainter(self)
		pen = QPen()

		# Draw square boundaries.
		pen.setWidth(1)
		pen.setColor(Qt.gray)
		painter.setPen(pen)

		square_width = window_size / self.grid_size
		for i in range(self.grid_size):
			position = round(square_width*i)
			painter.drawLine(position, 0, position, window_size)
			painter.drawLine(0, position, window_size, position)

		# Draw box boundaries.
		pen.setWidth(2)
		pen.setColor(Qt.black)
		painter.setPen(pen)

		box_width = window_size / self.box_size
		for i in range(self.box_size):
			position = round(box_width*i)
			painter.drawLine(position, 0, position, window_size)
			painter.drawLine(0, position, window_size, position)

		# Draw grid boundaries.
		pen.setWidth(6)
		pen.setColor(Qt.black)
		painter.setPen(pen)

		corners = [
			QPoint(0, 0),
			QPoint(0, window_size),
			QPoint(window_size, 0),
			QPoint(window_size, window_size)
		]

		painter.drawLine(corners[0], corners[1])
		painter.drawLine(corners[1], corners[3])
		painter.drawLine(corners[3], corners[2])
		painter.drawLine(corners[2], corners[0])


# Each square also stores its position in the squares array (indexed by [row][column])
class Square:
	pos = []
	n = 0

	def __init__(self, pos, n):
		self.pos = pos
		self.n = n

	def __str__(self):
		return str(self.n)

	# For simplicity, equality between a square and an int is supported
	def __eq__(self, other):
		if type(other) is int:
			return other == self.n
		if type(other) is Square:
			return other.n == self.n

		return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def __gt__(self, other):
		return self.n > other.n

	def is_empty(self):
		return self.n == 0


class Sudoku:
	box_size = 0
	grid_size = 0
	
	all_possible_numbers = []

	initial_rows = []

	# 2D arrays indexed by [row][column].
	grid = []
	candidates = []

	total_tries = 0
	max_difficulty = 0

	def __init__(self, rows, box_size):
		self.box_size = box_size
		self.grid_size = box_size ** 2
		
		self.all_possible_numbers = range(1, self.grid_size + 1)

		self.initial_rows = rows

		for row_index, row in enumerate(rows):
			self.grid.append([Square([row_index, square_index], n) for square_index, n in enumerate(row)])

	def set_square(self, row_index, column_index, n):
		self.grid[row_index][column_index] = Square([row_index, column_index], n)

	# Returns a list of coordinates for all squares in the row.
	# Indexed by [X; Y]
	# X: row index; Y: column index
	def get_coordinates_by_row(self, i):
		return [[i, j] for j in range(self.grid_size)]

	def get_coordinates_by_column(self, i):
		return [[j, i] for j in range(self.grid_size)]

	def get_coordinates_by_box(self, i):
		size = self.box_size
		first_row_index = (i // size) * size
		first_column_index = (i % size) * size

		return [[first_row_index + j, first_column_index + k] for j in range(size) for k in range(size)]

	def get_row(self, i):
		return self.grid[i].copy()

	def get_column(self, i):
		return [row[i] for row in self.grid]

	# boxs are indexed left to right, and top to bottom.
	def get_box(self, i):
		return [self.grid[x][y] for [x, y] in self.get_coordinates_by_box(i)]

	def get_rows(self):
		return [self.get_row(i) for i in range(self.grid_size)]

	def get_columns(self):
		return [self.get_column(i) for i in range(self.grid_size)]

	def get_boxs(self):
		return [self.get_box(i) for i in range(self.grid_size)]

	# Returns a list of all rows, columns and boxs.
	# Each item is a row/column/box, and contains a sequence of squares.
	def get_all_sequences(self):
		return self.get_rows() + self.get_columns() + self.get_boxs()

	# Checks whether any row/column/box contains two or more of the same number, except for 0.
	def is_valid(self):
		for sequence in self.get_all_sequences():
			if any(sequence.count(n) > 1 for n in self.all_possible_numbers):
				return False

		return True

	def solve(self):
		self.total_tries = 0
		while any(square.is_empty() for row in self.grid for square in row):
			if not self.is_valid():
				print("Error occurred while solving.")
				return False

			self.total_tries += 1
			if self.total_tries >= max_tries:
				return False

			print_grid(self.grid)

			# Fill squares that are the only empty square in a row/column/box.
			if self.fill_single_empty_squares():
				self.max_difficulty = max(self.max_difficulty, 1)
				print("Difficulty: 1")
				continue

			# Fill squares that are the only possible square where a digit could go in a row/column/box.
			if self.fill_single_possible_squares():
				self.max_difficulty = max(self.max_difficulty, 2)
				print("Difficulty: 2")
				continue

			self.compute_candidates()
			
			# Fill squares that have only one candidate number (all other numbers are already in the same row/column/box)
			if self.fill_squares_with_one_candidate():
				self.max_difficulty = max(self.max_difficulty, 3)
				print("Difficulty: 3")
				continue

			groups_count = self.create_groups_with_same_candidates()
			if groups_count != 0:
				self.max_difficulty = max(self.max_difficulty, 4)
				print(f"Created {groups_count} groups.")

			# Fill squares that have only one candidate after groups have been formed
			if self.fill_squares_with_one_candidate():
				self.max_difficulty = max(self.max_difficulty, 3)
				print("Difficulty: 4")
				continue

			return False

		print_grid(self.grid)
		return True

	def fill_single_empty_squares(self):
		for sequence in self.get_all_sequences():
			i = missing_single_index(sequence)

			if i != -1:
				pos = sequence[i].pos

				self.set_square(pos[0], pos[1], self.first_missing_digit(sequence))
				return True

		return False

	def first_missing_digit(self, squares):
		missing_digit = 0
		for digit in self.all_possible_numbers:
			if digit not in squares:
				missing_digit = digit
				break

		return missing_digit

	def missing_digits(self, squares):
		missing_digits = []
		for digit in self.all_possible_numbers:
			if digit not in squares:
				missing_digits.append(digit)

		return missing_digits

	def could_contain(self, row_index, column_index, n):
		size = self.box_size
		in_same_row = n in self.get_row(row_index)
		in_same_column = n in self.get_column(column_index)
		in_same_box = n in self.get_box((row_index // size)*size + (column_index // size))

		return not in_same_row and not in_same_column and not in_same_box

	def possible_squares(self, sequence, n):
		possible_squares = []
		for pos in empty_squares(sequence):
			if self.could_contain(pos[0], pos[1], n):
				possible_squares.append(pos)

		return possible_squares

	def fill_single_possible_squares(self):
		for sequence in self.get_all_sequences():
			missing_digits = self.missing_digits(sequence)
			for n in missing_digits:
				possible_squares = self.possible_squares(sequence, n)
				if len(possible_squares) == 1:
					pos = possible_squares[0]
					if pos[0] == 0 and pos[1] == 0 and n == 3:
						print("!")

					self.set_square(pos[0], pos[1], n)
					return True

		return False

	# Note: this function always stores the candidates in order from lowest to highest.
	def compute_candidates(self):
		# Populate the candidates grid with empty lists of candidates on each row.
		self.candidates = [[[] for j in range(self.grid_size)] for i in range(self.grid_size)]

		for pos in empty_squares([square for row in self.get_rows() for square in row]):
			for n in self.all_possible_numbers:
				if self.could_contain(pos[0], pos[1], n):
					self.candidates[pos[0]][pos[1]].append(n)
	
	def fill_squares_with_one_candidate(self):
		for pos in empty_squares([square for row in self.get_rows() for square in row]):
			candidates = self.candidates[pos[0]][pos[1]]

			if len(candidates) == 1:
				self.set_square(pos[0], pos[1], candidates[0])
				return True

		return False

	# If [0, 0] and [0, 1] definitely contain either a 1 or a 2, no other squares in the first row and the first box
	# can have a 1 or a 2. For this to be true, the number of squares affected must equal the amount of numbers used.
	def create_groups_with_same_candidates(self):
		groups_count = 0

		for sequence in self.get_all_sequences():
			positions = empty_squares(sequence)
			for i, pos in enumerate(positions):
				candidates = self.candidates[pos[0]][pos[1]]
				group = [pos]

				for other_pos in positions[i+1:]:
					other_candidates = self.candidates[other_pos[0]][other_pos[1]]

					if other_candidates == candidates:
						group.append(other_pos)

				# If there's as many items in the group as there are candidates in each square,
				# we've exhausted the locations these numbers could go in.
				if len(group) == len(candidates):
					groups_count += 1

					for other_pos in positions:
						for candidate in candidates:
							if candidate in self.candidates[other_pos[0]][other_pos[1]]:
								self.candidates[other_pos[0]][other_pos[1]].remove(candidate)

		return groups_count


def empty_squares(sequence):
	empty_squares = []
	for square in sequence:
		if square.n == 0:
			empty_squares.append(square.pos)
	return empty_squares


def missing_single_index(squares):
	missing_single_index = -1
	empty_count = 0
	for i, square in enumerate(squares):
		if square.n == 0:
			empty_count += 1
			missing_single_index = i

		if empty_count > 1:
			return -1

	return missing_single_index if empty_count == 1 else -1


def print_grid(grid):
	max_number = max(max(row) for row in grid)
	max_number_length = len(str(max_number))

	for row in grid:
		line = ""
		for square in row:
			number_length = len(str(square))
			line += " " * ((max_number_length - number_length) + extra_spaces)

			line += str(square) + " "

		print(line)

	print()


def clear_grid_layout():
	for i in reversed(range(grid_layout.count())):
		grid_layout.itemAt(i).widget().deleteLater()


def update_grid_layout(sudoku):
	clear_grid_layout()

	for i in range(sudoku.grid_size):
		for j in range(sudoku.grid_size):
			label = QLabel(str(sudoku.grid[i][j]))
			label.setFont(QFont('Times', 12))
			label.setAlignment(Qt.AlignCenter)
			grid_layout.addWidget(label, i, j)


sudoku_rows = [
	[[4, 1, 2, 0],
	 [0, 2, 0, 4],
	 [1, 4, 0, 2],
	 [2, 3, 4, 1]],

	[[0, 1, 4, 0],
	 [0, 4, 0, 1],
	 [0, 3, 0, 2],
	 [0, 0, 0, 0]],

	[[3, 8, 6, 0, 0, 0, 2, 4, 5],
	 [0, 2, 0, 3, 5, 6, 8, 0, 0],
	 [0, 7, 0, 0, 8, 0, 0, 1, 0],
	 [0, 0, 0, 0, 6, 4, 9, 8, 7],
	 [0, 4, 0, 7, 3, 0, 0, 6, 0],
	 [1, 0, 7, 2, 0, 0, 0, 5, 4],
	 [7, 0, 0, 0, 4, 1, 5, 2, 0],
	 [0, 0, 2, 5, 7, 0, 4, 0, 8],
	 [0, 5, 0, 6, 2, 9, 7, 0, 0]],

	[[0, 0, 0, 0, 8, 0, 0, 0, 9],
	 [0, 0, 0, 0, 0, 1, 6, 2, 0],
	 [0, 9, 2, 0, 0, 6, 4, 7, 0],
	 [6, 0, 0, 1, 0, 0, 0, 9, 0],
	 [4, 5, 0, 0, 3, 0, 0, 6, 1],
	 [0, 1, 0, 0, 0, 5, 0, 0, 7],
	 [0, 8, 7, 4, 0, 0, 1, 3, 0],
	 [0, 2, 6, 8, 0, 0, 0, 0, 0],
	 [9, 0, 0, 0, 6, 0, 0, 0, 0]],

	[[5, 3, 0, 0, 7, 0, 0, 0, 0],
	 [6, 0, 0, 1, 9, 5, 0, 0, 0],
	 [0, 9, 8, 0, 0, 0, 0, 6, 0],
	 [8, 0, 0, 0, 6, 0, 0, 0, 3],
	 [4, 0, 0, 8, 0, 3, 0, 0, 1],
	 [7, 0, 0, 0, 2, 0, 0, 0, 6],
	 [0, 6, 0, 0, 0, 0, 2, 8, 0],
	 [0, 0, 0, 4, 1, 9, 0, 0, 5],
	 [0, 0, 0, 0, 8, 0, 0, 7, 9]],

	[[7, 0, 0, 0, 8, 3, 0, 0, 0],
	 [9, 0, 2, 0, 0, 5, 0, 0, 0],
	 [0, 0, 0, 0, 0, 7, 0, 5, 2],
	 [8, 0, 6, 0, 0, 0, 1, 0, 0],
	 [4, 0, 0, 8, 0, 1, 0, 0, 7],
	 [0, 0, 1, 0, 0, 0, 2, 0, 4],
	 [3, 6, 0, 1, 0, 0, 0, 0, 0],
	 [0, 0, 0, 3, 0, 0, 8, 0, 6],
	 [0, 0, 0, 5, 7, 0, 0, 0, 3]],

	[[ 3, 13,  0,  0, 15,  0,  0,  0,  0,  7,  6,  4,  0, 16,  0, 14],
	 [ 0,  0,  0,  2, 11,  0, 13,  8,  0,  0,  0,  0,  5, 10,  0,  3],
	 [ 0,  0,  0, 14,  9,  0, 16,  4,  0,  0,  2, 15,  0,  6,  0,  0],
	 [ 0, 11,  7, 10,  0,  0,  6,  0,  9,  0,  0, 13,  0,  4, 12,  0],
	 [ 0,  2, 15,  0,  0, 16,  0,  0,  0,  6, 10,  9,  0,  0,  0,  0],
	 [ 0,  0, 16,  0,  5,  8,  0, 15, 13,  3,  0,  0, 12,  0, 11, 10],
	 [ 7,  5,  0,  0,  0,  0, 10,  0,  0,  0,  8,  1,  6, 15, 16,  0],
	 [ 1, 10,  8,  0, 13,  6,  4,  0,  0,  0,  0,  0,  0,  0,  3,  9],
	 [11, 16,  0,  0,  0,  0,  0,  0,  0, 12,  9,  7,  0,  1, 10, 15],
	 [ 0,  1, 10, 15,  7, 13,  0,  0,  0,  2,  0,  0,  0,  0,  6, 12],
	 [ 9,  3,  0,  7,  0,  0, 15,  6,  5,  0, 16,  8,  0, 11,  0,  0],
	 [ 0,  0,  0,  0,  3, 11,  8,  0,  0,  0, 15,  0,  0,  9,  7,  0],
	 [ 0,  7,  5,  0,  6,  0,  0, 12,  0,  4,  0,  0,  9,  2, 14,  0],
	 [ 0,  0,  3,  0,  4, 10,  0,  0, 16,  5,  0,  6,  1,  0,  0,  0],
	 [ 6,  0, 11, 13,  0,  0,  0,  0,  2,  9,  0, 12, 10,  0,  0,  0],
	 [12,  0,  4,  0, 16,  9,  7,  0,  0,  0,  0, 10,  0,  0,  5,  6]]
]
sudoku = Sudoku(sudoku_rows[5], 3)


def solve():
	sudoku.solve()
	update_grid_layout(sudoku)


app = QApplication([])
main_window = QWidget()
main_window.setGeometry(100, 100, window_size + margin_size[0], window_size + margin_size[1])

main_window_layout = QGridLayout()
main_window.setLayout(main_window_layout)

grid_window = QWidget()
grid_window_layout = QGridLayout()
grid_window.setLayout(grid_window_layout)
main_window_layout.addWidget(grid_window, 0, 0)

background_widget = QWidget()
background = QGridLayout()
background_widget.setLayout(background)
background.addWidget(GridBackgroundWidget(sudoku.box_size, sudoku.grid_size), 0, 0)

grid_window_layout.addWidget(background_widget, 0, 0)

grid_widget = QWidget()
grid_layout = QGridLayout()
grid_widget.setLayout(grid_layout)
grid_window_layout.addWidget(grid_widget, 0, 0)

solve_button = QPushButton()
solve_button.setText("Solve")
solve_button.clicked.connect(solve)
main_window_layout.addWidget(solve_button, 1, 0)


update_grid_layout(sudoku)


main_window.show()
app.exec_()


solved = sudoku.solve()

print()
print("Solved!" if solved else "Not solved.")
print(f"{sudoku.total_tries} steps.")
print(f"Result is {'valid' if sudoku.is_valid() else 'invalid'}.")
print(f"Max difficulty: {sudoku.max_difficulty}")
