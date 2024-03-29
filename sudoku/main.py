import time

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

max_tries = 1000

extra_spaces = 1

window_size = 600
bg_margin_size = [18, 18]
grid_margin_size = [9, 9]

time_between_steps = 0.05

showing_previous_difference = False
showing_all_candidates = False


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


# Each square also stores its position in the squares array (indexed by [row][column]).
class Square:
	pos = []
	n = 0

	def __init__(self, pos, n):
		self.pos = pos
		self.n = n

	def __str__(self):
		return str(self.n)

	def __repr__(self):
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
	boxed_squares = []

	candidates = []
	candidates_red = []

	def __init__(self, text, modified_square_pos=None, affected_sequence=None,
				 crossed_lines=None, crossed_squares=None, circled_squares=None, boxed_squares=None,
				 candidates=None, candidates_red=None):
		self.text = text
		self.modified_square_pos = modified_square_pos
		self.affected_sequence = affected_sequence
		self.crossed_lines = crossed_lines
		self.crossed_squares = crossed_squares
		self.circled_squares = circled_squares
		self.boxed_squares = boxed_squares
		self.candidates = candidates
		self.candidates_red = candidates_red


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
	candidates_history = []

	current_step = 0

	total_steps = 0
	max_difficulty = 0

	is_solved = False
	solve_failed = False

	candidates_outdated = True

	pause_between_steps = True
	update_gui = True
	should_reset_gui_settings = False

	notes = {"Candidates": []}

	def __init__(self, rows, box_size):
		super().__init__()
		self.box_size = box_size
		self.grid_size = box_size ** 2

		self.all_possible_numbers = list(range(1, self.grid_size + 1))

		self.initial_rows = rows

		for row_index, row in enumerate(rows):
			self.grid.append([Square([row_index, square_index], n) for square_index, n in enumerate(row)])

		# Compute the initial candidates during initialization.
		# These will be updated dynamically as needed using update_candidates.
		self.compute_candidates()

		self.steps.append([[Square(s.pos, s.n) for s in row] for row in self.grid])
		self.candidates_history.append([[candidates.copy() for candidates in row] for row in self.candidates])
		self.explanations.append(Explanation("Loaded puzzle."))

	def reset_gui_settings(self):
		self.pause_between_steps = True
		self.update_gui = True
		self.should_reset_gui_settings = False

	def reset_gui_settings_later(self):
		self.should_reset_gui_settings = True

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
		for i, sequence in enumerate(self.get_all_sequences()):
			if any(sequence.count(n) > 1 for n in self.all_possible_numbers):
				return False

		return True

	def start_solve(self):
		self.is_solved = self.solve()

		if self.is_solved:
			self.current_step += 1
			self.steps.append([[Square(s.pos, s.n) for s in row] for row in self.grid])
			self.candidates_history.append([[candidates.copy() for candidates in row] for row in self.candidates])
			self.explanations.append(Explanation(f"Puzzle is solved. (Max difficulty: {self.max_difficulty})"))

		else:
			self.explanations.append(Explanation(
				f"Couldn't solve the puzzle. (Max difficulty: {self.max_difficulty})",
				candidates=self.candidates)
			)

		self.step_done.emit()
		self.finished.emit()

		# When we're done solving reset GUI settings to the default.
		self.reset_gui_settings()

	def solve(self):
		self.total_steps = 0
		while any(square.is_empty() for row in self.grid for square in row):
			self.total_steps += 1
			if self.total_steps >= max_tries:
				self.solve_failed = True
				return False

			print_grid(self.grid)
			self.current_step += 1
			self.steps.append([[Square(s.pos, s.n) for s in row] for row in self.grid])
			self.candidates_history.append([[candidates.copy() for candidates in row] for row in self.candidates])

			if self.update_gui:
				self.step_done.emit()

			if self.pause_between_steps and self.total_steps > 1:
				time.sleep(time_between_steps)

			if self.should_reset_gui_settings:
				self.reset_gui_settings()

			# Wait for an unpause command.
			while self.paused:
				time.sleep(0.01)

			if not self.is_valid():
				print("Error occurred while solving.")
				return False

			# Fill squares that are the only empty square in a row/column/box.
			if self.fill_single_empty_squares():
				self.complete_step(1)
				continue

			# Fill squares that are the only possible square where a digit could go in a row/column/box.
			if self.fill_single_possible_squares():
				self.complete_step(2)
				continue

			self.update_candidates()

			# Fill squares that have only one candidate number (all other numbers are already in the same row/column/box)
			if self.fill_squares_with_one_candidate():
				self.complete_step(3)
				continue

			# Backup the candidates grid to use for explanations.
			self.notes["Candidates"] = [[candidates.copy() for candidates in row] for row in self.candidates]

			if self.remove_candidates_by_elimination():
				self.complete_step(4)
				continue

			if self.create_groups_with_same_candidates():
				self.complete_step(5)
				continue

			if self.create_disjoint_subsets():
				self.complete_step(6)
				continue

			self.solve_failed = True
			return False

		print_grid(self.grid)
		return True

	def complete_step(self, difficulty):
		self.max_difficulty = max(self.max_difficulty, difficulty)
		print(f"Difficulty: {difficulty}")

	def fill_single_empty_squares(self):
		for sequence in self.get_all_sequences():
			i = missing_single_index(sequence)

			if i != -1:
				pos = sequence[i].pos

				n = self.first_missing_digit(sequence)
				self.set_square(pos, n)
				self.explanations.append(Explanation(
					f"Only {n} is missing in this sequence.",
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
		self.candidates = [[set() for _ in range(self.grid_size)] for _ in range(self.grid_size)]

		for pos in empty_squares([square for row in self.get_rows() for square in row]):
			for n in self.all_possible_numbers:
				if self.could_contain(pos[0], pos[1], n):
					self.candidates[pos[0]][pos[1]].add(n)

	def update_candidates(self):
		for pos in [square.pos for row in self.get_rows() for square in row]:
			# If the square was filled remove all candidates.
			if self.grid[pos[0]][pos[1]] != 0:
				self.candidates[pos[0]][pos[1]] = []

			# Remove any candidates that could no longer go on the square.
			for n in self.candidates[pos[0]][pos[1]].copy():
				if not self.could_contain(pos[0], pos[1], n):
					self.candidates[pos[0]][pos[1]].remove(n)

	def fill_squares_with_one_candidate(self):
		for pos in empty_squares([square for row in self.get_rows() for square in row]):
			candidates = self.candidates[pos[0]][pos[1]]

			if len(candidates) == 1:
				n = list(candidates)[0]
				self.set_square(pos, n)

				circled_squares = []
				for excluded_number in self.all_possible_numbers:
					if excluded_number == n:
						continue

					circled_squares += self.conflicts(pos[0], pos[1], excluded_number)

				self.explanations.append(Explanation(
					f"{n} is the only number that could go in this square.", pos,
					circled_squares=circled_squares
				))

				return True

		return False

	# If box 1 has only two positions where the number 8 could be, both in
	# the same row, no other squares in that row may contain an 8.
	def remove_candidates_by_elimination(self):
		for sequence in self.get_all_sequences():
			positions = empty_squares(sequence)
			for n in self.all_possible_numbers:
				possible_squares = [pos for pos in positions if n in self.candidates[pos[0]][pos[1]]]

				if len(possible_squares) < 2:
					continue

				for other_sequence in self.get_all_sequences():
					if other_sequence == sequence:
						continue

					other_sequence_positions = [square.pos for square in other_sequence]

					if all(pos in other_sequence_positions for pos in possible_squares):
						eliminations_count = 0
						affected_squares = []

						for pos in other_sequence_positions:
							if pos in positions:
								continue

							if n in self.candidates[pos[0]][pos[1]]:
								self.candidates[pos[0]][pos[1]].remove(n)
								affected_squares.append(pos)
								eliminations_count += 1

						if eliminations_count == 0:
							continue

						candidates_shown = []
						for i, row in enumerate(self.candidates):
							new_row = []
							for j, candidates in enumerate(row):
								if [i, j] in other_sequence_positions:
									# Show only the number being eliminated
									if [i, j] in possible_squares:
										new_row.append([n])
									else:
										new_row.append(list(candidates))
								else:
									new_row.append([])
							candidates_shown.append(new_row)

						red_candidates_shown = []
						for i, row in enumerate(self.notes["Candidates"]):
							new_row = []
							for j, candidates in enumerate(row):
								new_row.append([n] if [i, j] in affected_squares else [])
							red_candidates_shown.append(new_row)

						self.explanations.append(Explanation(
							f"Removed {eliminations_count} candidates from elimination.",
							affected_sequence=sequence,
							candidates=candidates_shown,
							candidates_red=red_candidates_shown
						))

						return True

		return False

	# If multiple squares share the same candidates and there are as many squares in the group as there
	# are total candidates involved, these numbers may not go in any other square in the sequence.
	# This is true even if some squares in the group only have part of the set of candidates.
	# For example, if [0, 0] and [0, 1] definitely contain either a 1 or a 2, no other squares in the first row
	# can have a 1 or a 2. For this to be true, the number of squares affected must equal the amount of numbers used.
	def create_groups_with_same_candidates(self):
		for sequence in self.get_all_sequences():
			print(sequence)
			positions = empty_squares(sequence)
			for i, pos in enumerate(positions):
				candidates = self.candidates[pos[0]][pos[1]]
				if len(candidates) < 2:
					continue

				candidates_shown = [[[] for _ in range(self.grid_size)] for _ in range(self.grid_size)]
				red_candidates_shown = [[[] for _ in range(self.grid_size)] for _ in range(self.grid_size)]

				candidates_shown[pos[0]][pos[1]] = list(candidates)

				group = [pos]
				group_candidates = candidates.copy()

				# The first option is that this square is a superset of all the other squares in the group,
				# so it has all of their candidates combined and possibly more.
				# The superset of all the group's candidates must be formed first, before finding smaller subsets.
				for other_pos in positions[i+1:]:
					other_candidates = self.candidates[other_pos[0]][other_pos[1]]

					if group_candidates <= other_candidates:
						# Update the superset of all candidates in the group
						group_candidates = other_candidates.copy()

						group.append(other_pos)
						candidates_shown[other_pos[0]][other_pos[1]] = list(other_candidates)

				# Another option is that this square contains some candidates from the other members of the group,
				# and no others. In this case it would be a subset of the set of total candidates.
				# To correctly identify these, group_candidates has to be populated first.
				for other_pos in positions[i+1:]:
					other_candidates = self.candidates[other_pos[0]][other_pos[1]]

					if other_pos not in group and other_candidates <= group_candidates:
						group.append(other_pos)
						candidates_shown[other_pos[0]][other_pos[1]] = list(other_candidates)

				# If there's as many items in the group as there are total candidates involved,
				# we've exhausted the locations these numbers could go in.
				if len(group) == len(group_candidates):
					affected_squares = []
					for other_pos in positions:
						if other_pos in group:
							continue

						candidates_shown[other_pos[0]][other_pos[1]] = list(self.candidates[other_pos[0]][other_pos[1]])

						for candidate in group_candidates:
							if candidate in self.candidates[other_pos[0]][other_pos[1]]:
								self.candidates[other_pos[0]][other_pos[1]].remove(candidate)
								affected_squares.append(other_pos)

								candidates_shown[other_pos[0]][other_pos[1]].remove(candidate)
								red_candidates_shown[other_pos[0]][other_pos[1]].append(candidate)

					if len(affected_squares) == 0:
						continue

					self.explanations.append(Explanation(
						f"Removed candidates using candidate groups.", affected_sequence=sequence,
						candidates=candidates_shown, candidates_red=red_candidates_shown
					))

					return True

		return False

	# If a set of numbers share the same possible squares, and the set is as big as the
	# amount of squares involved, we can assume those squares may not contain other numbers.
	def create_disjoint_subsets(self):
		for sequence in self.get_all_sequences():
			positions = empty_squares(sequence)
			# Note: a square cannot be part of multiple subsets as there wouldn't be enough room for all the numbers.
			for i, pos in enumerate(positions):
				candidates = self.candidates[pos[0]][pos[1]]
				if len(candidates) < 2:
					continue

				subset = [pos]
				subset_candidates = []

				# Attempt an intersection with any combination of the other empty squares.
				# If any of the intersections has as many candidates as its size, it will be selected as a disjoint subset.
				other_squares = positions.copy()
				other_squares.remove(pos)
				for mask in range(1, 2 ** len(other_squares)):
					# Select which squares to intersect with using a bitmask.
					subset += [other_squares[j] for j in range(len(other_squares)) if (1 << j) & mask]

					# Try to intersect the candidates of the selected squares.
					candidates_intersection = set.intersection(*[self.candidates[other_pos[0]][other_pos[1]] for other_pos in subset])

					# If there's as many squares in the subset as there are shared candidates, it's certain* that
					# all squares involved will contain one of these numbers, so other candidates can be removed.
					# *there needs to be one last verification step to make sure those numbers couldn't go anywhere else.
					if len(candidates_intersection) == len(subset):
						subset_candidates = candidates_intersection

						# Any given square can only be part of at most 1 disjoint subset,
						# so there's no need to try other combinations.
						break

					# If the subset is not valid, reset it and continue with the next combination.
					subset = [pos]

				# If a valid subset was found, remove all other candidates from the squares involved.
				if len(subset) > 1:
					verification_failed = False
					# First verify that the candidates in the subset cannot be placed anywhere else in the sequence.
					for other_pos in positions:
						if other_pos not in subset:
							if self.candidates[other_pos[0]][other_pos[1]] & subset_candidates:
								verification_failed = True
								break

					if verification_failed:
						continue

					eliminations = 0

					candidates_shown = [[[] for _ in range(self.grid_size)] for _ in range(self.grid_size)]
					red_candidates_shown = [[[] for _ in range(self.grid_size)] for _ in range(self.grid_size)]

					# Note: the excess candidates are also removed from the current square, included in subset.
					for other_pos in subset:
						eliminations += len(self.candidates[other_pos[0]][other_pos[1]] - subset_candidates)

						candidates_shown[other_pos[0]][other_pos[1]] = list(subset_candidates)
						red_candidates_shown[other_pos[0]][other_pos[1]] = list(
							self.candidates[other_pos[0]][other_pos[1]] - subset_candidates)

						# Remove other candidates from the square.
						self.candidates[other_pos[0]][other_pos[1]] = subset_candidates.copy()

					# Don't complete the step if no candidates were removed.
					if eliminations == 0:
						continue

					self.explanations.append(Explanation(
						f"Removed candidates using disjoint subsets.", affected_sequence=sequence,
						candidates=candidates_shown, candidates_red=red_candidates_shown
					))

					return True

		return False


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


def show_candidates(candidates, candidates_red=None):
	candidates_widget = QWidget()
	candidates_layout = QHBoxLayout()
	candidates_layout.setSpacing(0)
	candidates_widget.setLayout(candidates_layout)

	if candidates_red is not None and len(candidates_red) > 0:
		label_red = QLabel(' '.join([str(n) for n in candidates_red]))
		label_red.setFont(QFont('Times', 10))
		label_red.setStyleSheet(" color: red ")
		label_red.setAlignment(Qt.AlignLeft)
		label_red.setAlignment(Qt.AlignTop)
		label_red.adjustSize()

		candidates_layout.addWidget(label_red)

	label_gray = QLabel(' '.join([str(n) for n in candidates]))
	label_gray.setFont(QFont('Times', 10))
	label_gray.setStyleSheet(" color: #5a5a5a ")
	label_gray.setAlignment(Qt.AlignLeft)
	label_gray.setAlignment(Qt.AlignTop)
	label_gray.adjustSize()

	candidates_layout.addWidget(label_gray)

	empty = QWidget()
	candidates_layout.addWidget(empty)

	return candidates_widget


def update_grid_layout(current_step=-1, show_previous_difference=False, show_explanations=True, show_all_candidates=False):
	# Only update the UI if we are in a step-by-step solution
	if not sudoku.pause_between_steps:
		return

	global showing_previous_difference, showing_all_candidates
	showing_previous_difference = show_previous_difference
	showing_all_candidates = show_all_candidates

	clear_grid_layout()

	explanation = None
	if len(sudoku.explanations) > 1 or (len(sudoku.explanations) == 1 and not show_previous_difference):
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
			n = sudoku.steps[current_step][i][j]
			label = QLabel(str(n) if n != 0 else "")
			label.setFont(QFont('Times', 12))
			label.setAlignment(Qt.AlignCenter)

			if explanation is not None and show_explanations:
				if explanation.modified_square_pos == [i, j]:
					label.setStyleSheet("QLabel { background-color : green; }")

			grid_layout.addWidget(label, i, j)

	if show_all_candidates and sudoku.candidates is not None:
		for i in range(sudoku.grid_size):
			for j in range(sudoku.grid_size):
				grid_layout.addWidget(show_candidates(
					sudoku.candidates[i][j]), i, j)

	elif explanation.candidates is not None and len(explanation.candidates) > 0:
		for i in range(sudoku.grid_size):
			for j in range(sudoku.grid_size):
				has_red_candidates = explanation.candidates_red is not None and len(explanation.candidates_red[i][j]) > 0

				grid_layout.addWidget(show_candidates(
					explanation.candidates[i][j],
					explanation.candidates_red[i][j] if has_red_candidates else None
				), i, j)


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
sudoku = Sudoku(examples[5], 3)
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


def toggle_show_all_candidates():
	if not showing_all_candidates:
		show_candidates_button.setText("Hide candidates")
		update_grid_layout(sudoku.current_step, showing_previous_difference, show_all_candidates=True)

	else:
		show_candidates_button.setText("Show candidates")
		update_grid_layout(sudoku.current_step, showing_previous_difference, show_all_candidates=False)


def toggle_paused(force_pause=False):
	if not sudoku.paused or force_pause:
		sudoku.paused = True
		pause_button.setIcon(QIcon("icons//play.png"))

	else:
		sudoku.paused = False
		pause_button.setIcon(QIcon("icons//pause.png"))

		start_solve()


def pause_once():
	toggle_paused(True)
	sudoku.reset_gui_settings_later()
	sudoku.step_done.disconnect(pause_once)


def previous_step():
	toggle_paused(True)

	if sudoku.current_step <= 1:
		return

	sudoku.current_step -= 1
	sudoku.grid = sudoku.steps[sudoku.current_step]
	sudoku.candidates = sudoku.candidates_history[sudoku.current_step]
	update_grid_layout(sudoku.current_step, True)


def next_step():
	toggle_paused(True)

	if sudoku.current_step == len(sudoku.steps) - 1:
		if sudoku.is_solved or sudoku.solve_failed:
			return

		sudoku.pause_between_steps = False
		sudoku.update_gui = True

		sudoku.step_done.connect(pause_once)
		toggle_paused(False)

	else:
		sudoku.current_step += 1
		sudoku.grid = sudoku.steps[sudoku.current_step]
		sudoku.candidates = sudoku.candidates_history[sudoku.current_step]
		update_grid_layout(sudoku.current_step, True)


def jump_to_start():
	toggle_paused(True)

	if sudoku.current_step == 1:
		return

	sudoku.current_step = 1
	sudoku.grid = sudoku.steps[sudoku.current_step]
	sudoku.candidates = sudoku.candidates_history[sudoku.current_step]
	update_grid_layout(sudoku.current_step, True)


def jump_to_end():
	toggle_paused(True)

	if sudoku.current_step == len(sudoku.steps) - 1:
		return

	sudoku.current_step = len(sudoku.steps) - 1
	sudoku.grid = sudoku.steps[sudoku.current_step]
	sudoku.candidates = sudoku.candidates_history[sudoku.current_step]
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

show_candidates_button = QPushButton()
show_candidates_button.setText("Show candidates")
show_candidates_button.clicked.connect(toggle_show_all_candidates)
main_window_layout.addWidget(show_candidates_button, 3, 0)

navigation_widget = QWidget()
navigation_layout = QGridLayout()
navigation_widget.setLayout(navigation_layout)
main_window_layout.addWidget(navigation_widget, 4, 0)

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
