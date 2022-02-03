from math import comb
import re

class Sequence:
    
    def __init__(self, clue, length, max_solutions_to_find):
        self.length = length
        self.clue = clue
        self.value = self.get_value()
        self.solutions_possible = self.get_possible_solution_count(clue, length)
        self.solutions = list()
        if self.solutions_possible <= max_solutions_to_find:
            self.get_possible_solutions(self.solutions, clue, length)
        self.regex = self.get_regex()

    def __repr__(self):
        return f"Sequence(clue={self.clue}, length={self.length}, value={str(self.value)})"

    def __str__(self):
        return "".join({"0":"░", "1":"█", "x":"?"}[cell] for cell in self.value)

    def get_value(self):
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
        regex = list()
        for section in self.clue:
            regex.append("[1x]{" + str(section) + "}")
        return re.compile("^[0x]*?" + "[0x]+".join(regex) + "[0x]*$")

    @staticmethod
    def get_possible_solutions(solutions, clue, length, prev=""):
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
        if not clue:
            return 1
        n = length - (len(clue) - 1) - (sum(clue) - len(clue))
        solution_count = comb(n, len(clue))
        return solution_count

class Nonogram:

    def __init__(self, *args):
        self.max_solutions_to_find = 50
        clues = args[0]
        self.width = len(args[0][0])
        self.height = len(args[0][1])
        self.sequences = {"row":dict(), "col":dict()}
        self.sequence_complexity = list()
        self.unsolved = set()
        for i, line_type in enumerate(("col", "row")):
            for j, clue in enumerate(clues[i]):
                length = self.width if line_type == "row" else self.height
                self.sequences[line_type][j] = Sequence(clue, length, self.max_solutions_to_find)
                self.reconcile_sequences(line_type, j)
                if 1 < self.sequences[line_type][j].solutions_possible <= self.max_solutions_to_find:
                    self.sequence_complexity.append([line_type, j, self.sequences[line_type][j].solutions_possible])
        self.unsolved = self.get_unsolved()
        self.update_sequence_complexity()
    
    def __repr__(self):
        return f"Nonogram(width={self.width}, height={self.height})\n{str(self)}"
        
    def __str__(self):
        return "\n".join(str(row) for row in self.sequences["row"].values())
    
    def get_grid(self):
        grid = list()
        for row in self.sequences["row"].values():
            grid.append(tuple(int(cell) if cell in "10" else "x" for cell in row.value))
        return tuple(grid)
    
    def reconcile_sequences(self, line_type, index):
        opp_line_type = "row" if line_type == "col" else "col"
        for i, cell_value in enumerate(self.sequences[line_type][index].value):
            if i in self.sequences[opp_line_type] and cell_value != self.sequences[opp_line_type][i].value[index]:
                pos = (index, i) if line_type == "row" else (i, index)
                new_value = cell_value if cell_value != "x" else self.sequences[opp_line_type][i].value[index]
                ignored_sequence = line_type if cell_value != "x" else opp_line_type
                self.update_at_pos(pos, new_value, ignored_sequence)

    def update_sequence_complexity(self):
        new_sequence_complexity = list()
        for line_type, index, _ in self.sequence_complexity:
            solutions_to_remove = set()
            for solution in self.sequences[line_type][index].solutions:
                for i, cell_value in enumerate(solution):
                    if self.sequences[line_type][index].value[i] not in ("x", cell_value):
                        solutions_to_remove.add(solution)
            new_solutions_list = list(set(self.sequences[line_type][index].solutions) - solutions_to_remove)
            self.sequences[line_type][index].solutions = new_solutions_list
            self.sequences[line_type][index].solutions_possible -= len(solutions_to_remove)
            new_sequence_complexity.append([line_type, index, self.sequences[line_type][index].solutions_possible])
        self.sequence_complexity = sorted(new_sequence_complexity, key=lambda e:e[2])
        
    def get_unsolved(self):
        unsolved = set()
        for y, row in self.sequences["row"].items():
            for x, cell_value in enumerate(row.value):
                if cell_value == "x":
                    unsolved.add((y, x))
        return unsolved
    
    def update_unsolved(self, pos, new_value):
        if new_value == "x":
            self.unsolved.add(pos)
        elif pos in self.unsolved:
            self.unsolved.remove(pos)
    
    def update_at_pos(self, pos, new_value, ignored_sequence=None):
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
        self.update_unsolved(pos, new_row[pos[1]])
        self.sequences["row"][pos[0]].value = new_row
        self.sequences["col"][pos[1]].value = new_col
    
    def update_single_sequence(self, line_type, index, new_value):
        self.sequences[line_type][index].value = new_value
        for i in range(self.sequences[line_type][index].length):
            pos = (index, i) if line_type == "row" else (i, index)
            self.update_at_pos(pos, new_value[i], line_type)