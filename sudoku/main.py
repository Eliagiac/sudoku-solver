max_tries = 100


class Sudoku:
	square_size = 0
	num_digits = 0

	initial_rows = []
	rows = []

	def __init__(self, rows, square_size):
		self.initial_rows = rows
		self.rows = [row.copy() for row in rows]
		self.square_size = square_size
		self.num_digits = square_size ** 2

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
		return self.rows[i].copy()

	def get_column(self, i):
		return [row[i] for row in self.rows]

	# Squares are indexed left to right, and top to bottom.
	def get_square(self, i):
		return [self.rows[x][y] for [x, y] in self.get_coordinates_by_square(i)]

	def get_rows(self):
		return [self.get_row(i) for i in range(self.num_digits)]

	def get_columns(self):
		return [self.get_column(i) for i in range(self.num_digits)]

	def get_squares(self):
		return [self.get_square(i) for i in range(self.num_digits)]

	def set_cell_by_row(self, row_index, i, n):
		self.rows[row_index][i] = n

	def set_cell_by_column(self, column_index, i, n):
		self.rows[i][column_index] = n

	def set_cell_by_square(self, square_index, i, n):
		size = self.square_size
		first_row_index = (square_index // size) * size
		first_column_index = (square_index % size) * size

		self.rows[first_row_index + (i // size)][first_column_index + (i % size)] = n

	def solve(self):
		tries = 0
		while any(0 in row for row in self.rows):
			tries += 1
			if tries >= max_tries:
				return False

			print()
			for row in self.rows:
				print(row)

			if self.fill_missing_single_rows():
				continue

			if self.fill_missing_single_columns():
				continue

			if self.fill_missing_single_squares():
				continue

			if self.fill_single_possible_rows():
				continue

			if self.fill_single_possible_columns():
				continue

			if self.fill_single_possible_squares():
				continue

			return False

		return True

	def fill_missing_single_rows(self):
		has_any_missing_single = False
		for row_index, row in enumerate(self.get_rows()):
			i = missing_single_index(row)

			if i != -1:
				has_any_missing_single = True
				self.set_cell_by_row(row_index, i, self.first_missing_digit(row))

		return has_any_missing_single

	def fill_missing_single_columns(self):
		has_any_missing_single = False
		for column_index, column in enumerate(self.get_columns()):
			i = missing_single_index(column)

			if i != -1:
				has_any_missing_single = True
				self.set_cell_by_column(column_index, i, self.first_missing_digit(column))

		return has_any_missing_single

	def fill_missing_single_squares(self):
		has_any_missing_single = False
		for square_index, square in enumerate(self.get_squares()):
			i = missing_single_index(square)

			if i != -1:
				has_any_missing_single = True
				self.set_cell_by_square(square_index, i, self.first_missing_digit(square))

		return has_any_missing_single

	def first_missing_digit(self, cells):
		missing_digit = 0
		for digit in range(1, self.num_digits + 1):
			if digit not in cells:
				missing_digit = digit
				break

		return missing_digit

	def missing_digits(self, cells):
		missing_digits = []
		for digit in range(self.num_digits):
			if digit not in cells:
				missing_digits.append(digit)

		return missing_digits

	def could_contain(self, row_index, column_index, n):
		size = self.square_size
		in_same_row = n in self.get_row(row_index)
		in_same_column = n in self.get_column(column_index)
		in_same_square = n in self.get_square((row_index // size) + (column_index & size))

		return not in_same_row and not in_same_column and not in_same_square

	def empty_cells_in_row(self, row_index):
		empty_cells = []
		for pos, cell in zip(self.get_coordinates_by_row(row_index), self.get_row(row_index)):
			if cell == 0:
				empty_cells.append(pos)
		return empty_cells

	def empty_cells_in_column(self, column_index):
		empty_cells = []
		for pos, cell in zip(self.get_coordinates_by_column(column_index), self.get_column(column_index)):
			if cell == 0:
				empty_cells.append(pos)
		return empty_cells

	def empty_cells_in_square(self, square_index):
		empty_cells = []
		for pos, cell in zip(self.get_coordinates_by_square(square_index), self.get_square(square_index)):
			if cell == 0:
				empty_cells.append(pos)
		return empty_cells

	def possible_cells_by_row(self, row_index, n):
		possible_cells = []
		for pos in self.empty_cells_in_row(row_index):
			if self.could_contain(pos[0], pos[1], n):
				possible_cells.append(pos)

		return possible_cells

	def possible_cells_by_column(self, column_index, n):
		possible_cells = []
		for pos in self.empty_cells_in_column(column_index):
			if self.could_contain(pos[0], pos[1], n):
				possible_cells.append(pos)

		return possible_cells

	def possible_cells_by_square(self, square_index, n):
		possible_cells = []
		for pos in self.empty_cells_in_square(square_index):
			if self.could_contain(pos[0], pos[1], n):
				possible_cells.append(pos)

		return possible_cells

	def fill_single_possible_rows(self):
		has_any_single_possible = False
		for row_index, row in enumerate(self.get_rows()):
			missing_digits = self.missing_digits(row)
			for n in missing_digits:
				possible_cells = self.possible_cells_by_row(row_index, n)
				if len(possible_cells) == 1:
					has_any_single_possible = True

					pos = possible_cells[0]
					self.set_cell_by_row(pos[0], pos[1], n)

		return has_any_single_possible

	def fill_single_possible_columns(self):
		has_any_single_possible = False
		for column_index, column in enumerate(self.get_columns()):
			missing_digits = self.missing_digits(column)
			for n in missing_digits:
				possible_cells = self.possible_cells_by_column(column_index, n)
				if len(possible_cells) == 1:
					has_any_single_possible = True

					pos = possible_cells[0]
					self.set_cell_by_column(pos[0], pos[1], n)

		return has_any_single_possible

	def fill_single_possible_squares(self):
		has_any_single_possible = False
		for square_index, square in enumerate(self.get_squares()):
			missing_digits = self.missing_digits(square)
			for n in missing_digits:
				possible_cells = self.possible_cells_by_square(square_index, n)
				if len(possible_cells) == 1:
					has_any_single_possible = True

					pos = possible_cells[0]
					self.set_cell_by_square(pos[0], pos[1], n)

		return has_any_single_possible


def missing_single_index(cells):
	if cells.count(0) == 1:
		return cells.index(0)

	return -1


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

test = Sudoku(test_rows[2], 3)
solved = test.solve()

print()
print("Solved!" if solved else "Not solved.")

for row in test.rows:
	print(row)