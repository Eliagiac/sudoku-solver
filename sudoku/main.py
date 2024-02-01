max_tries = 1000

extra_spaces = 1


# Each cell also stores its position in the cells array (indexed by [row][column])
class Cell:
	pos = []
	n = 0

	def __init__(self, pos, n):
		self.pos = pos
		self.n = n

	def __str__(self):
		return str(self.n)

	# For simplicity, equality between a Cell and an int is supported
	def __eq__(self, other):
		if type(other) is int:
			return other == self.n
		if type(other) is Cell:
			return other.n == self.n

		return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def __gt__(self, other):
		return self.n > other.n

	def is_empty(self):
		return self.n == 0


def empty_cells(sequence):
	empty_cells = []
	for cell in sequence:
		if cell.n == 0:
			empty_cells.append(cell.pos)
	return empty_cells


class Sudoku:
	box_size = 0
	num_digits = 0

	initial_rows = []

	# 2D array indexed by [row][column].
	grid = []

	total_tries = 0

	def __init__(self, rows, box_size):
		self.box_size = box_size
		self.num_digits = box_size ** 2

		self.initial_rows = rows

		for row_index, row in enumerate(rows):
			self.grid.append([Cell([row_index, cell_index], n) for cell_index, n in enumerate(row)])

	def set_cell(self, row_index, column_index, n):
		self.grid[row_index][column_index] = Cell([row_index, column_index], n)

	# Returns a list of coordinates for all cells in the row.
	# Indexed by [X; Y]
	# X: row index; Y: column index
	def get_coordinates_by_row(self, i):
		return [[i, j] for j in range(self.num_digits)]

	def get_coordinates_by_column(self, i):
		return [[j, i] for j in range(self.num_digits)]

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
		return [self.get_row(i) for i in range(self.num_digits)]

	def get_columns(self):
		return [self.get_column(i) for i in range(self.num_digits)]

	def get_boxs(self):
		return [self.get_box(i) for i in range(self.num_digits)]

	# Returns a list of all rows, columns and boxs.
	# Each item is a row/column/box, and contains a sequence of cells.
	def get_all(self):
		return self.get_rows() + self.get_columns() + self.get_boxs()

	# Checks whether any row/column/box contains two or more of the same number, except for 0.
	def is_valid(self):
		for sequence in self.get_all():
			if any(sequence.count(n) > 1 for n in range(1, self.num_digits + 1)):
				return False

		return True

	def solve(self):
		self.total_tries = 0
		while any(cell.is_empty() for row in self.grid for cell in row):
			if not self.is_valid():
				print("Error occurred while solving.")
				return False

			self.total_tries += 1
			if self.total_tries >= max_tries:
				return False

			print_grid(self.grid)

			if self.fill_missing_single():
				continue

			if self.fill_single_possible():
				continue

			return False

		return True

	def fill_missing_single(self):
		for sequence in self.get_all():
			i = missing_single_index(sequence)

			if i != -1:
				pos = sequence[i].pos

				self.set_cell(pos[0], pos[1], self.first_missing_digit(sequence))
				return True

		return False

	def first_missing_digit(self, cells):
		missing_digit = 0
		for digit in range(1, self.num_digits + 1):
			if digit not in cells:
				missing_digit = digit
				break

		return missing_digit

	def missing_digits(self, cells):
		missing_digits = []
		for digit in range(1, self.num_digits + 1):
			if digit not in cells:
				missing_digits.append(digit)

		return missing_digits

	def could_contain(self, row_index, column_index, n):
		size = self.box_size
		in_same_row = n in self.get_row(row_index)
		in_same_column = n in self.get_column(column_index)
		in_same_box = n in self.get_box((row_index // size)*size + (column_index // size))

		return not in_same_row and not in_same_column and not in_same_box

	def possible_cells(self, sequence, n):
		possible_cells = []
		for pos in empty_cells(sequence):
			if self.could_contain(pos[0], pos[1], n):
				possible_cells.append(pos)

		return possible_cells

	def fill_single_possible(self):
		for sequence in self.get_all():
			missing_digits = self.missing_digits(sequence)
			for n in missing_digits:
				possible_cells = self.possible_cells(sequence, n)
				if len(possible_cells) == 1:
					pos = possible_cells[0]
					if pos[0] == 0 and pos[1] == 0 and n == 3:
						print("!")

					self.set_cell(pos[0], pos[1], n)
					return True

		return False


def missing_single_index(cells):
	missing_single_index = -1
	empty_count = 0
	for i, cell in enumerate(cells):
		if cell.n == 0:
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
		for cell in row:
			number_length = len(str(cell))
			line += " " * ((max_number_length - number_length) + extra_spaces)

			line += str(cell) + " "

		print(line)

	print()


test_rows = [
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

test = Sudoku(test_rows[5], 3)
solved = test.solve()

print()
print("Solved!" if solved else "Not solved.")
print_grid(test.grid)
print(f"{test.total_tries} steps. Result is {'valid' if test.is_valid() else 'invalid'}.")
