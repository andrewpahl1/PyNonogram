import re
from nonogram import Nonogram

class UnsolvableError(Exception):
    pass

class Guess:
    """Parent class of CellGuess and SequenceGuess."""

    def __init__(self):
        self.dependent_cells = list()

class CellGuess(Guess):
    """Represents a guess in a single cell, contains all information necessary to revert this guess and all deductions made based on it."""

    def __init__(self, pos):
        super().__init__()
        self.pos = pos

    def __repr__(self):
        return f"CellGuess({self.pos})"

class SequenceGuess(Guess):
    """Represents a guess of an entire sequence, contains all information necessary to revert this guess and all deductions made based on it."""
    
    def __init__(self, line_type, index, new_value, old_value):
        super().__init__()
        self.line_type = line_type
        self.index = index
        self.old_value = old_value
        self.new_value = new_value
        
    def __repr__(self):
        return f"SequenceGuess(line_type={self.line_type}, index={self.index}, new_value = {self.new_value}, old_value={self.old_value})"
        
    def __eq__(self, iterable):
        return iterable[0] == self.line_type and iterable[1] == self.index

class Solver:
    """Contains the solve method and its helper methods, used to find the values of all unknown cells in a Nonogram object."""

    @staticmethod
    def check_regex(nonogram, pos):
        """Given a nonogram and a set of (y,x) coordinates to a cell whose value is unknown, checks whether marking that cell as filled or unfilled invalidates the puzzle. If only one of the two values is valid, returns the values updated values of both sequences."""
        current_row = nonogram.sequences["row"][pos[0]]
        current_col = nonogram.sequences["col"][pos[1]]
        check_0_row = current_row.value[0:pos[1]] + "0" + current_row.value[pos[1]+1:]
        check_0_col = current_col.value[0:pos[0]] + "0" + current_col.value[pos[0]+1:]
        check_1_row = current_row.value[0:pos[1]] + "1" + current_row.value[pos[1]+1:]
        check_1_col = current_col.value[0:pos[0]] + "1" + current_col.value[pos[0]+1:]
        valid_with_0 = bool(re.match(current_row.regex, check_0_row)) and bool(re.match(current_col.regex, check_0_col))
        valid_with_1 = bool(re.match(current_row.regex, check_1_row)) and bool(re.match(current_col.regex, check_1_col))
        if valid_with_0 and valid_with_1:
            return "either"
        if not valid_with_0 and not valid_with_1:
            return "error"
        if valid_with_0:
            return check_0_row, check_0_col
        if valid_with_1:
            return check_1_row, check_1_col

    @staticmethod
    def deduce(nonogram, guesses):
        """Uses check_regex to attempt to solve the nonogram by deduction. Returns an integer counting the number of cells updated."""
        solved_count = 0
        unsolved = nonogram.unsolved.copy()
        for pos in unsolved:
            if pos not in nonogram.unsolved:
                continue
            check_result = Solver.check_regex(nonogram, pos)
            if check_result == "either":
                continue
            elif check_result == "error":
                return -1
            else:
                new_row, new_col = check_result
                nonogram.update_sequences(pos, new_row, new_col)
                solved_count += 1
                if len(guesses) > 0:
                    guesses[-1].dependent_cells.append(pos)
        return solved_count

    @staticmethod
    def guess_cell(nonogram, guesses):
        """Adds a new CellGuess object to the guesses list, updates the nonogram object to reflect this guess."""
        pos = list(nonogram.unsolved)[0]
        guesses.append(CellGuess(pos))
        nonogram.update_at_pos(pos, "1")

    @staticmethod
    def guess_sequence(line_type, index, nonogram, guesses):
        """Adds a new SequenceGuess object to the guesses list, updates the nonogram object to reflect this guess."""
        new_value = nonogram.sequences[line_type][index].solutions[0]
        guesses.append(SequenceGuess(line_type, index, new_value, nonogram.sequences[line_type][index].value))
        nonogram.update_single_sequence(line_type, index, new_value)
    
    @staticmethod
    def revert_guess(nonogram, guess):
        """Given a nonogram object and a guess applied to that object, reverses all changes made to the nonogram as a result of that guess."""
        for cell in guess.dependent_cells:
            nonogram.update_at_pos(cell, "x")
        if isinstance(guess, SequenceGuess):
            nonogram.update_single_sequence(guess.line_type, guess.index, guess.old_value)
        elif isinstance(guess, CellGuess):
            nonogram.update_at_pos(guess.pos, "x")

    def get_next_guess(nonogram, guesses, revert):
        """Determines the next step to take in the guess-and-check algorithm. Identifies when the nonogram is unsolvable."""
        if not guesses and revert:
            raise UnsolvableError("This nonogram cannot be solved.")
        if not guesses:
            nonogram.update_known_solution_sets()
        if not revert:
            for line_type, index, _ in nonogram.known_solution_sets:
                if "x" in nonogram.sequences[line_type][index].value and (line_type, index) not in guesses:
                    Solver.guess_sequence(line_type, index, nonogram, guesses)
                    return
            Solver.guess_cell(nonogram, guesses)
            return
        last_guess = guesses.pop()
        if isinstance(last_guess, CellGuess):
            Solver.get_next_cell_guess(nonogram, last_guess, guesses)
        elif isinstance(last_guess, SequenceGuess):
            Solver.get_next_sequence_guess(nonogram, last_guess, guesses)
    
    def get_next_cell_guess(nonogram, last_guess, guesses):
        """Called when the last CellGuess lead to the nonogram being unsolvable. Reverts that guess and either changes its value to unfilled (if its value was previously filled) or reverts the last two guesses and makes a new guess (if both guessing filled and unfilled for the last cell made the nonogram unsolvable)."""
        guess_value = nonogram.sequences["row"][last_guess.pos[0]].value[last_guess.pos[1]]
        Solver.revert_guess(nonogram, last_guess)
        if guess_value == "0":
            Solver.get_next_guess(nonogram, guesses, True)
        elif guess_value == "1":
            guesses.append(CellGuess(last_guess.pos))
            nonogram.update_at_pos(last_guess.pos, "0")
        else:
            raise Exception("Error: a previous guess did not update the Nonogram")
    
    def get_next_sequence_guess(nonogram, last_guess, guesses):
        """Called when the last SequenceGuess lead to the nonogram being unsolvable. Either changes that guess to the next value in that sequence's solutions variable, or reverts the last two guesses and makes a new guess."""
        last_guess_value = nonogram.sequences[last_guess.line_type][last_guess.index].value
        solutions_list = nonogram.sequences[last_guess.line_type][last_guess.index].solutions
        last_guess_index = solutions_list.index(last_guess_value)
        Solver.revert_guess(nonogram, last_guess)
        if last_guess_index + 1 < len(solutions_list):
            next_guess_value = solutions_list[last_guess_index + 1]
            guesses.append(SequenceGuess(last_guess.line_type, last_guess.index, next_guess_value, last_guess.old_value))
            nonogram.update_single_sequence(last_guess.line_type, last_guess.index, next_guess_value)
        else:
            Solver.get_next_guess(nonogram, guesses, True)

    @staticmethod
    def solve(clues):
        """Main function in the Solver class - updates the unknown values in a nonogram object using the Solver class' helper functions."""
        nonogram = Nonogram(clues)
        guesses = list()
        while True:
            deduction_result = Solver.deduce(nonogram, guesses)
            if deduction_result > 0:
                continue
            elif len(nonogram.unsolved) == 0:
                return nonogram.get_grid()
            elif deduction_result == 0:
                Solver.get_next_guess(nonogram, guesses, False)
            elif deduction_result == -1 and not guesses:
                raise UnsolvableError("This nonogram cannot be solved.")
            else:
                Solver.get_next_guess(nonogram, guesses, True)