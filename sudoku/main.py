max_tries = 1000


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

	def is_empty(self):
		return self.n == 0


def empty_cells(sequence):
	empty_cells = []
	for cell in sequence:
		if cell.n == 0:
			empty_cells.append(cell.pos)
	return empty_cells


class Sudoku:
	square_size = 0
	num_digits = 0

	initial_rows = []

	# 2D array indexed by [row][column].
	grid = []

	def __init__(self, rows, square_size):
		self.square_size = square_size
		self.num_digits = square_size ** 2

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

	def get_coordinates_by_square(self, i):
		size = self.square_size
		first_row_index = (i // size) * size
		first_column_index = (i % size) * size

		return [[first_row_index + j, first_column_index + k] for j in range(size) for k in range(size)]

	def get_row(self, i):
		return self.grid[i].copy()

	def get_column(self, i):
		return [row[i] for row in self.grid]

	# Squares are indexed left to right, and top to bottom.
	def get_square(self, i):
		return [self.grid[x][y] for [x, y] in self.get_coordinates_by_square(i)]

	def get_rows(self):
		return [self.get_row(i) for i in range(self.num_digits)]

	def get_columns(self):
		return [self.get_column(i) for i in range(self.num_digits)]

	def get_squares(self):
		return [self.get_square(i) for i in range(self.num_digits)]

	# Returns a list of all rows, columns and squares.
	# Each item is a row/column/square, and contains a sequence of cells.
	def get_all(self):
		return self.get_rows() + self.get_columns() + self.get_squares()

	def solve(self):
		tries = 0
		while any(cell.is_empty() for row in self.grid for cell in row):
			tries += 1
			if tries >= max_tries:
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
		size = self.square_size
		in_same_row = n in self.get_row(row_index)
		in_same_column = n in self.get_column(column_index)
		in_same_square = n in self.get_square((row_index // size)*size + (column_index % size))

		return not in_same_row and not in_same_column and not in_same_square

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
	for row in grid:
		line = ""
		for cell in row:
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
	 [0, 5, 0, 6, 2, 9, 7, 0, 0]]]

test = Sudoku(test_rows[1], 2)
solved = test.solve()

print()
print("Solved!" if solved else "Not solved.")
print_grid(test.grid)
