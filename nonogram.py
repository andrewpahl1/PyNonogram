import math
import re

class Sequence:
    """Holds information related to a single row or column of a nonogram. Contains the following instance variables:
    - length: The number of cells in the sequence.
    - clue: A tuple containing the order and length of the filled blocks in the sequence.
    - value: A string of 1s, 0s, and xs showing the filled, unfilled, and unkown cells in the sequence respectively.
    - solutions: If the number of possible solutions is less or equal to than max_solutions_to_find, contains all possible solutions to the sequence as strings of 1s and 0s.
    - regex: A compiled regular expression that will match with any value string compatible with the sequence's clue."""
    
    def __init__(self, clue, length, max_solutions_to_find):
        self.length = length
        self.clue = clue
        self.value = self.get_initial_value()
        self.solutions_possible = self.get_possible_solution_count(clue, length)
        if self.solutions_possible <= max_solutions_to_find:
            self.solutions = list()
            self.get_possible_solutions(self.solutions, clue, length)
        self.regex = self.get_regex()

    def __repr__(self):
        return f"Sequence(clue={self.clue}, length={self.length}, value={str(self.value)})"

    def __str__(self):
        return "".join({"0":"░", "1":"█", "x":"?"}[cell] for cell in self.value)

    def get_initial_value(self):
        """Determines which cells in the sequence must be filled, returns a string of 1s and xs to represent filled and unknown cells."""
        extra_space = self.length - (sum(self.clue) + len(self.clue) - 1)
        if not self.clue:
            return "0" * self.length
        if max(self.clue) <= extra_space:
            return "x" * self.length
        value = ["x"] * self.length
        for i, section in enumerate(self.clue):
            if section <= extra_space:
                continue
            start_fill = sum(self.clue[:i]) + i + extra_space
            end_fill = start_fill + section - extra_space
            for cell_index in range(start_fill, end_fill):
                value[cell_index] = "1"
        return "".join(value)

    def get_regex(self):
        """Returns a compiled regex that will only match with value strings compatible with the sequence's clue and length (e.g. if the clue is (1,) and the length is 3, the regex will match with x1x, 0x1, 100, xxx, etc., but won't match with 11x, 000, 1x1, etc)."""
        regex = list()
        for section in self.clue:
            regex.append("[1x]{" + str(section) + "}")
        return re.compile("^[0x]*?" + "[0x]+".join(regex) + "[0x]*$")

    @staticmethod
    def get_possible_solutions(solutions, clue, length, prev=""):
        """Returns all possible completed value stings (no unknowns, just filled and unfilled cells) that match the sequences clue and length."""
        if not clue:
            solutions.append(prev + "0" * length)
            return
        reserved_space = sum(clue[1:]) + len(clue[1:])
        for i in range(length - reserved_space - clue[0] + 1):
            new_length = length - (clue[0] + i + (len(clue[1:]) > 0))
            new_prev = prev + "0" * i + "1" * clue[0] + "0" * (len(clue[1:]) > 0)
            Sequence.get_possible_solutions(solutions, clue[1:], new_length, new_prev)

    @staticmethod
    def get_possible_solution_count(clue, length):
        """Returns the maximum number of possible solutions to a given sequence given a clue and a length."""
        if not clue:
            return 1
        n = length - (len(clue) - 1) - (sum(clue) - len(clue))
        solution_count = math.comb(n, len(clue))
        return solution_count

class Nonogram:
    """Holds the data needed to represent nonogram, provides methods that allow the values of cells and sequences in the nonogram to be changed. Contains the following instance variables:
    - max_solutions_to_find: All sequences in the nonogram whose solution set is smaller than this number will have all possible solutions calculated and stored as an instance variable in that sequence.
    - width: The number of cells in all row sequences of the nonogram.
    - height: The number of cells in all column sequences of the nonogram.
    - sequences: A dictionary containing two sub-dictionaries of Sequence objects, one for rows and one for columns.
    - unsolved: A set of all unsolved cells in the nonogram.
    - known_solution_sets: A list of lists, each containing information about a Sequence object that has a solutions instance variable. Each sub-list contains: [line_type ("row" or "col"), row or column index (e.g. "row" and 0 for the top row of the nonogram), number of possible solutions]."""

    def __init__(self, clues):
        self.max_solutions_to_find = 50
        self.width = len(clues[0])
        self.height = len(clues[1])
        self.sequences = {"row":dict(), "col":dict()}
        self.known_solution_sets = list()
        self.unsolved = set()
        for i, line_type in enumerate(("col", "row")):
            for j, clue in enumerate(clues[i]):
                length = self.width if line_type == "row" else self.height
                self.sequences[line_type][j] = Sequence(clue, length, self.max_solutions_to_find)
                self.reconcile_sequences(line_type, j)
                if 1 < self.sequences[line_type][j].solutions_possible <= self.max_solutions_to_find:
                    self.known_solution_sets.append([line_type, j, self.sequences[line_type][j].solutions_possible])
        self.unsolved = self.get_unsolved()
        self.update_known_solution_sets()
    
    def __repr__(self):
        return f"Nonogram(width={self.width}, height={self.height})\n{str(self)}"
        
    def __str__(self):
        return "\n".join(str(row) for row in self.sequences["row"].values())
    
    def get_grid(self):
        """Returns the current state of the nonogram as a tuple of tuples. Each tuple represents a row, with each value in the tuple ("1", "0", or "x") showing whether that cell is filled, unfilled, or unknown."""
        grid = list()
        for row in self.sequences["row"].values():
            grid.append(tuple(int(cell) if cell in "10" else "x" for cell in row.value))
        return tuple(grid)
    
    def reconcile_sequences(self, line_type, index):
        """Called during initialization of each of the nonogram's sequences. If the cell that marks the intersection between two sequences is known in one sequence and unknown in the other, updates the sequence in which the cell is unknown."""
        opp_line_type = "row" if line_type == "col" else "col"
        for i, cell_value in enumerate(self.sequences[line_type][index].value):
            if i in self.sequences[opp_line_type] and cell_value != self.sequences[opp_line_type][i].value[index]:
                pos = (index, i) if line_type == "row" else (i, index)
                new_value = cell_value if cell_value != "x" else self.sequences[opp_line_type][i].value[index]
                ignored_sequence = line_type if cell_value != "x" else opp_line_type
                self.update_at_pos(pos, new_value, ignored_sequence)

    def update_known_solution_sets(self):
        """For any Sequence object in the nonogram that has a solutions list defined, finds and removes any possible solutions that don't fit the current state of the nonogram."""
        new_solution_sets = list()
        for line_type, index, _ in self.known_solution_sets:
            solutions_to_remove = set()
            for solution in self.sequences[line_type][index].solutions:
                for i, cell_value in enumerate(solution):
                    if self.sequences[line_type][index].value[i] not in ("x", cell_value):
                        solutions_to_remove.add(solution)
            new_solutions_list = list(set(self.sequences[line_type][index].solutions) - solutions_to_remove)
            self.sequences[line_type][index].solutions = new_solutions_list
            self.sequences[line_type][index].solutions_possible -= len(solutions_to_remove)
            new_solution_sets.append([line_type, index, self.sequences[line_type][index].solutions_possible])
        self.known_solution_sets = sorted(new_solution_sets, key=lambda e:e[2])
        
    def get_unsolved(self):
        """Returns a set of tuples representing the (y, x) coordinates of all unsolved cells in the nonogram."""
        unsolved = set()
        for y, row in self.sequences["row"].items():
            for x, cell_value in enumerate(row.value):
                if cell_value == "x":
                    unsolved.add((y, x))
        return unsolved
    
    def update_unsolved(self, pos, new_value):
        """Helper function for the update methods, keeps the unsolved instance variable up-to-date as cells and sequences in the nonogram are updated."""
        if new_value == "x":
            self.unsolved.add(pos)
        elif pos in self.unsolved:
            self.unsolved.remove(pos)
    
    def update_at_pos(self, pos, new_value, ignored_sequence=None):
        """Updates the value of a single cell in the nonogram."""
        old_row = self.sequences["row"][pos[0]].value
        old_col = self.sequences["col"][pos[1]].value
        self.update_unsolved(pos, new_value)
        if ignored_sequence == "col" or ignored_sequence == None:
            new_row = old_row[0:pos[1]] + new_value + old_row[pos[1]+1:]
            self.sequences["row"][pos[0]].value = new_row
        if ignored_sequence == "row" or ignored_sequence == None:
            new_col = old_col[0:pos[0]] + new_value + old_col[pos[0]+1:]
            self.sequences["col"][pos[1]].value = new_col
        
    def update_sequences(self, pos, new_row, new_col):
        """Updates the value of a single cell in the nonogram, used as a more efficient alternative to update_at_pos when the values of both sequences have already been calculated."""
        self.update_unsolved(pos, new_row[pos[1]])
        self.sequences["row"][pos[0]].value = new_row
        self.sequences["col"][pos[1]].value = new_col
    
    def update_single_sequence(self, line_type, index, new_value):
        """Updates the values of all cells along one sequence in the nonogram."""
        self.sequences[line_type][index].value = new_value
        for i in range(self.sequences[line_type][index].length):
            pos = (index, i) if line_type == "row" else (i, index)
            self.update_at_pos(pos, new_value[i], line_type)