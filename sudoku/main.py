import time

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

max_tries = 1000

extra_spaces = 1

window_size = 600
bg_margin_size = [18, 18]
grid_margin_size = [9, 9]

time_between_steps = 1


class GridBackgroundWidget(QWidget):
	box_size = 3
	grid_size = 9

	def __init__(self, box_size, grid_size):
		super().__init__()
		self.box_size = box_size
		self.grid_size = grid_size

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


class Rectangle(QWidget):
	color = Qt.red
	stroke_width = 3

	x = 0
	y = 0
	w = 0
	h = 0

	def __init__(self, x, y, w, h, color=Qt.red, stroke_width=3):
		super().__init__()
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.color = color
		self.stroke_width = stroke_width

	def paintEvent(self, event):
		painter = QPainter(self)
		pen = QPen()

		pen.setWidth(self.stroke_width)
		pen.setColor(self.color)
		painter.setPen(pen)

		painter.drawRect(self.x, self.y, self.w, self.h)


class Circle(QWidget):
	color = Qt.red
	stroke_width = 2

	center = 0
	r = 0

	def __init__(self, center, r, color=Qt.red, stroke_width=2):
		super().__init__()
		self.center = center
		self.r = r
		self.color = color
		self.stroke_width = stroke_width

	def paintEvent(self, event):
		painter = QPainter(self)
		pen = QPen()

		pen.setWidth(self.stroke_width)
		pen.setColor(self.color)
		painter.setPen(pen)

		painter.drawEllipse(self.center, self.r, self.r)


class Line(QWidget):
	color = Qt.red
	stroke_width = 2

	x1 = 0
	y1 = 0
	x2 = 0
	y2 = 0

	def __init__(self, x1, y1, x2, y2, color=Qt.red, stroke_width=2):
		super().__init__()
		self.x1 = x1
		self.y1 = y1
		self.x2 = x2
		self.y2 = y2
		self.color = color
		self.stroke_width = stroke_width

	def paintEvent(self, event):
		painter = QPainter(self)
		pen = QPen()

		pen.setWidth(self.stroke_width)
		pen.setColor(self.color)
		painter.setPen(pen)

		painter.drawLine(self.x1, self.y1, self.x2, self.y2)


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


class Explanation:
	text = ""

	modified_square_pos = None

	affected_sequence = []

	# Each line is stored as [from_square_pos][to_square_pos].
	crossed_lines = []

	crossed_squares = []
	circled_squares = []

	def __init__(self, text, modified_square_pos=None, affected_sequence=None,
				 crossed_lines=None, crossed_squares=None, circled_squares=None):
		self.text = text
		self.modified_square_pos = modified_square_pos
		self.affected_sequence = affected_sequence
		self.crossed_lines = crossed_lines
		self.crossed_squares = crossed_squares
		self.circled_squares = circled_squares


class Sudoku(QObject):
	finished = pyqtSignal()
	step_done = pyqtSignal()

	paused = False

	box_size = 0
	grid_size = 0

	all_possible_numbers = []

	initial_rows = []

	# 2D arrays indexed by [row][column].
	grid = []
	candidates = []

	# Stores the grid state after each step.
	steps = []
	explanations = []

	current_step = 0

	total_steps = 0
	max_difficulty = 0

	is_solved = False

	pause_between_steps = True
	update_gui = True

	def __init__(self, rows, box_size):
		super().__init__()
		self.box_size = box_size
		self.grid_size = box_size ** 2

		self.all_possible_numbers = range(1, self.grid_size + 1)

		self.initial_rows = rows

		for row_index, row in enumerate(rows):
			self.grid.append([Square([row_index, square_index], n) for square_index, n in enumerate(row)])

		self.steps.append([[Square(s.pos, s.n) for s in row] for row in self.grid])
		self.explanations.append(Explanation("Loaded puzzle."))

	def reset_gui_settings(self):
		self.pause_between_steps = True
		self.update_gui = True

	def set_square(self, pos, n):
		self.grid[pos[0]][pos[1]] = Square([pos[0], pos[1]], n)

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

	def start_solve(self):
		self.is_solved = self.solve()

		self.current_step += 1
		self.steps.append([[Square(s.pos, s.n) for s in row] for row in self.grid])
		self.explanations.append(Explanation("Puzzle is solved."))

		self.step_done.emit()
		self.finished.emit()

		# When we're done solving reset GUI settings to the default.
		self.reset_gui_settings()

	def solve(self):
		self.total_steps = 0
		while any(square.is_empty() for row in self.grid for square in row):
			if not self.is_valid():
				print("Error occurred while solving.")
				return False

			self.total_steps += 1
			if self.total_steps >= max_tries:
				return False

			print_grid(self.grid)
			self.current_step += 1
			self.steps.append([[Square(s.pos, s.n) for s in row] for row in self.grid])

			if self.update_gui:
				self.step_done.emit()

			if self.pause_between_steps and self.total_steps > 1:
				time.sleep(time_between_steps)

			# Wait for an unpause command.
			while self.paused:
				time.sleep(0.01)

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
			if self.fill_squares_with_one_candidate(True):
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

				n = self.first_missing_digit(sequence)
				self.set_square(pos, n)
				self.explanations.append(Explanation(
					f"Only one empty square remaining in the sequence. The only number missing is {n}.",
					pos, sequence))
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

	def conflicts(self, row_index, column_index, n, return_early=False):
		size = self.box_size

		in_same_row = [square.pos for square in self.get_row(row_index) if square == n]

		if len(in_same_row) > 0 and return_early:
			return in_same_row

		in_same_column = [square.pos for square in self.get_column(column_index) if square == n]

		if len(in_same_column) > 0 and return_early:
			return in_same_column

		box_index = (row_index // size)*size + (column_index // size)
		in_same_box = [square.pos for square in self.get_box(box_index) if square == n]

		if len(in_same_box) > 0 and return_early:
			return in_same_box

		return in_same_row + in_same_column + in_same_box

	def could_contain(self, row_index, column_index, n):
		return len(self.conflicts(row_index, column_index, n, return_early=True)) == 0

	def possible_squares(self, sequence, n):
		possible_squares = []
		conflicts = []

		for pos in empty_squares(sequence):
			new_conflicts = self.conflicts(pos[0], pos[1], n)

			if len(new_conflicts) == 0:
				possible_squares.append(pos)

			else:
				conflicts.append((new_conflicts, pos))

		return possible_squares, conflicts

	def fill_single_possible_squares(self):
		for sequence in self.get_all_sequences():
			missing_digits = self.missing_digits(sequence)
			for n in missing_digits:
				(possible_squares, conflicts) = self.possible_squares(sequence, n)

				if len(possible_squares) == 1:
					pos = possible_squares[0]

					self.set_square(pos, n)
					self.explanations.append(Explanation(
						f"There is only one square in the sequence where {n} could go.", pos, sequence,
						circled_squares=[conflicting_square for conflict in conflicts for conflicting_square in conflict[0]],
						crossed_lines=[[conflicting_square, conflict[1]] for conflict in conflicts for conflicting_square in conflict[0]],
						crossed_squares=[conflict[1] for conflict in conflicts]
					))
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

	def fill_squares_with_one_candidate(self, using_candidate_groups=False):
		for pos in empty_squares([square for row in self.get_rows() for square in row]):
			candidates = self.candidates[pos[0]][pos[1]]

			if len(candidates) == 1:
				n = candidates[0]
				self.set_square(pos, n)

				explanation = ""
				if not using_candidate_groups:
					explanation = f"{n} is the only number that could go in this square."
				else:
					explanation = f"{n} is the only number that could go in this square (using candidate groups)."

				self.explanations.append(Explanation(explanation, pos))
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

	for i in reversed(range(drawings.count())):
		drawings.itemAt(i).widget().deleteLater()


def highlight_sequence(sequence):
	square_width = window_size / sudoku.grid_size

	start_square = sequence[0]
	end_square = sequence[-1]

	x = round(square_width * start_square.pos[1])
	y = round(square_width * start_square.pos[0])
	w = round((square_width * (end_square.pos[1]+1)) - x)
	h = round((square_width * (end_square.pos[0]+1)) - y)

	drawings.addWidget(Rectangle(x, y, w, h), 0, 0)


def circle_squares(squares):
	square_width = window_size / sudoku.grid_size

	for i, pos in enumerate(squares):
		# Avoid drawing two circles on the same square.
		if pos in squares[:i]:
			continue

		x = round(square_width * pos[1] + square_width/2)
		y = round(square_width * pos[0] + square_width/2)

		center = QPoint(x, y)

		center_width = 0.8
		r = (square_width/2) * center_width

		drawings.addWidget(Circle(center, r), 0, 0)


def draw_lines(lines):
	square_width = window_size / sudoku.grid_size

	for line in lines:
		start_pos = line[0]
		end_pos = line[1]

		x1 = round((start_pos[1] * square_width) + square_width/2)
		y1 = round((start_pos[0] * square_width) + square_width/2)
		x2 = round((end_pos[1] * square_width) + square_width/2)
		y2 = round((end_pos[0] * square_width) + square_width/2)

		drawings.addWidget(Line(x1, y1, x2, y2), 0, 0)


def cross_squares(squares):
	square_width = window_size / sudoku.grid_size

	for i, pos in enumerate(squares):
		# Avoid drawing two crosses on the same square.
		if pos in squares[:i]:
			continue

		line1_x1 = round((pos[1] * square_width) + 0.2*square_width)
		line1_y1 = round((pos[0] * square_width) + 0.2*square_width)
		line1_x2 = round(((pos[1] + 1) * square_width) - 0.2*square_width)
		line1_y2 = round(((pos[0] + 1) * square_width) - 0.2*square_width)

		drawings.addWidget(Line(line1_x1, line1_y1, line1_x2, line1_y2), 0, 0)

		line2_x1 = round((pos[1] * square_width) + 0.2*square_width)
		line2_y1 = round(((pos[0] + 1) * square_width) - 0.2*square_width)
		line2_x2 = round(((pos[1] + 1) * square_width) - 0.2*square_width)
		line2_y2 = round((pos[0] * square_width) + 0.2*square_width)

		drawings.addWidget(Line(line2_x1, line2_y1, line2_x2, line2_y2), 0, 0)


def update_grid_layout(current_step=-1, show_previous_difference=False, show_explanations=True):
	# Only update the UI if we are in a step-by-step solution
	if not sudoku.pause_between_steps:
		return

	clear_grid_layout()

	explanation = None
	if len(sudoku.explanations) > 0:
		explanation = sudoku.explanations[current_step-show_previous_difference]

	if explanation is not None and show_explanations:
		explanation_label.setText(explanation.text)

		if explanation.affected_sequence is not None and len(explanation.affected_sequence) > 0:
			highlight_sequence(explanation.affected_sequence)

		if explanation.circled_squares is not None and len(explanation.circled_squares) > 0:
			circle_squares(explanation.circled_squares)

		if explanation.crossed_lines is not None and len(explanation.crossed_lines) > 0:
			draw_lines(explanation.crossed_lines)

		if explanation.crossed_squares is not None and len(explanation.crossed_squares) > 0:
			cross_squares(explanation.crossed_squares)

	for i in range(sudoku.grid_size):
		for j in range(sudoku.grid_size):
			label = QLabel(str(sudoku.steps[current_step][i][j]))
			label.setFont(QFont('Times', 12))
			label.setAlignment(Qt.AlignCenter)

			if explanation is not None and show_explanations:
				if explanation.modified_square_pos == [i, j]:
					label.setStyleSheet("QLabel { background-color : green; }")

			grid_layout.addWidget(label, i, j)


examples = [
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

	[[0, 0, 0, 9, 0, 3, 0, 0, 0],
	 [0, 0, 5, 4, 0, 8, 1, 0, 0],
	 [0, 9, 0, 0, 2, 0, 0, 3, 0],
	 [1, 2, 0, 0, 0, 0, 0, 5, 3],
	 [0, 0, 0, 0, 0, 0, 0, 0, 0],
	 [9, 5, 0, 0, 0, 0, 0, 7, 8],
	 [0, 7, 0, 0, 4, 0, 0, 1, 0],
	 [0, 0, 9, 6, 0, 1, 3, 0, 0],
	 [0, 0, 0, 7, 0, 5, 0, 0, 0]],

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
sudoku = Sudoku(examples[7], 4)
sudoku_thread = QThread()


def start_solve():
	if sudoku.paused:
		toggle_paused()

	sudoku.moveToThread(sudoku_thread)
	sudoku.step_done.connect(update_grid_layout)
	sudoku.finished.connect(sudoku_thread.exit)
	sudoku.finished.connect(lambda: toggle_paused(True))
	sudoku_thread.started.connect(sudoku.start_solve)

	sudoku_thread.start()


def show_solution():
	if sudoku.is_solved:
		jump_to_end()
		return

	toggle_calculating_solution(True)
	sudoku.finished.connect(toggle_calculating_solution)

	sudoku.pause_between_steps = False
	sudoku.update_gui = False
	start_solve()


def toggle_calculating_solution(calculating=False):
	show_solution_button.setText("Calculating solution..." if calculating else "Show solution")


def toggle_paused(force_pause=False):
	if not sudoku.paused or force_pause:
		pause_button.setIcon(QIcon("icons//play.png"))
		sudoku.paused = True

	else:
		pause_button.setIcon(QIcon("icons//pause.png"))
		sudoku.paused = False

		start_solve()


def previous_step():
	if sudoku.current_step == 1:
		return

	toggle_paused(True)
	sudoku.current_step -= 1
	sudoku.grid = sudoku.steps[sudoku.current_step]
	update_grid_layout(sudoku.current_step, True)


def next_step():
	if sudoku.current_step == len(sudoku.steps) - 1:
		return

	toggle_paused(True)
	sudoku.current_step += 1
	sudoku.grid = sudoku.steps[sudoku.current_step]
	update_grid_layout(sudoku.current_step, True)


def jump_to_start():
	if sudoku.current_step == 1:
		return

	toggle_paused(True)
	sudoku.current_step = 1
	sudoku.grid = sudoku.steps[sudoku.current_step]
	update_grid_layout(sudoku.current_step, True)


def jump_to_end():
	if sudoku.current_step == len(sudoku.steps) - 1:
		return

	toggle_paused(True)
	sudoku.current_step = len(sudoku.steps) - 1
	sudoku.grid = sudoku.steps[sudoku.current_step]
	update_grid_layout(sudoku.current_step, True)


app = QApplication([])
main_window = QWidget()

main_window_layout = QGridLayout()
main_window.setLayout(main_window_layout)

explanation_label = QLabel()
explanation_label.setFont(QFont('Times', 12))
explanation_label.setAlignment(Qt.AlignCenter)
main_window_layout.addWidget(explanation_label, 0, 0)

grid_window = QWidget()
grid_window_layout = QGridLayout()
grid_window.setLayout(grid_window_layout)
main_window_layout.addWidget(grid_window, 1, 0)

grid_widget = QWidget()
grid_layout = QGridLayout()
grid_layout.setContentsMargins(grid_margin_size[0], grid_margin_size[1], grid_margin_size[0], grid_margin_size[1])
grid_layout.setSpacing(0)
grid_widget.setFixedHeight(window_size + bg_margin_size[1])
grid_widget.setFixedWidth(window_size + bg_margin_size[0])
grid_widget.setLayout(grid_layout)
grid_window_layout.addWidget(grid_widget, 0, 0)

background_widget = QWidget()
background = QGridLayout()
background_widget.setLayout(background)
background.addWidget(GridBackgroundWidget(sudoku.box_size, sudoku.grid_size), 0, 0)
grid_window_layout.addWidget(background_widget, 0, 0)

drawings_widget = QWidget()
drawings = QGridLayout()
drawings_widget.setLayout(drawings)
grid_window_layout.addWidget(drawings_widget, 0, 0)

show_solution_button = QPushButton()
show_solution_button.setText("Show solution")
show_solution_button.clicked.connect(show_solution)
main_window_layout.addWidget(show_solution_button, 2, 0)

navigation_widget = QWidget()
navigation_layout = QGridLayout()
navigation_widget.setLayout(navigation_layout)
main_window_layout.addWidget(navigation_widget, 3, 0)

jump_to_start_button = QPushButton()
jump_to_start_button.setIcon(QIcon("icons//left-jump.png"))
jump_to_start_button.clicked.connect(jump_to_start)
navigation_layout.addWidget(jump_to_start_button, 0, 0, 0, 1)

previous_button = QPushButton()
previous_button.setIcon(QIcon("icons//left-arrow.png"))
previous_button.clicked.connect(previous_step)
navigation_layout.addWidget(previous_button, 0, 1, 0, 3)

pause_button = QPushButton()
pause_button.setIcon(QIcon("icons//pause.png"))
pause_button.clicked.connect(toggle_paused)
navigation_layout.addWidget(pause_button, 0, 4, 0, 2)

next_button = QPushButton()
next_button.setIcon(QIcon("icons//right-arrow.png"))
next_button.clicked.connect(next_step)
navigation_layout.addWidget(next_button, 0, 6, 0, 3)

jump_to_end_button = QPushButton()
jump_to_end_button.setIcon(QIcon("icons//right-jump.png"))
jump_to_end_button.clicked.connect(jump_to_end)
navigation_layout.addWidget(jump_to_end_button, 0, 9, 0, 1)


toggle_paused(True)
update_grid_layout()


main_window.show()
app.exec_()

print()
print("Solved!" if sudoku.is_solved else "Not solved.")
print(f"{sudoku.total_steps} steps.")
print(f"Result is {'valid' if sudoku.is_valid() else 'invalid'}.")
print(f"Max difficulty: {sudoku.max_difficulty}")
