import re
from random import choice
from nonogram import Nonogram

class Guess:

    def __init__(self):
        self.dependent_cells = list()

class CellGuess(Guess):

    def __init__(self, pos):
        super().__init__()
        self.pos = pos

    def __repr__(self):
        return f"CellGuess({self.pos})"

class SequenceGuess(Guess):
    
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

    @staticmethod
    def check_regex(nonogram, pos):
        current_row = nonogram.sequences["row"][pos[0]]
        current_col = nonogram.sequences["col"][pos[1]]
        check_0_row = current_row.value[0:pos[1]] + "0" + current_row.value[pos[1]+1:]
        check_0_col = current_col.value[0:pos[0]] + "0" + current_col.value[pos[0]+1:]
        check_1_row = current_row.value[0:pos[1]] + "1" + current_row.value[pos[1]+1:]
        check_1_col = current_col.value[0:pos[0]] + "1" + current_col.value[pos[0]+1:]
        valid_with_0 = bool(re.match(current_row.regex, check_0_row)) and bool(re.match(current_col.regex, check_0_col))
        valid_with_1 = bool(re.match(current_row.regex, check_1_row)) and bool(re.match(current_col.regex, check_1_col))
        if valid_with_0 and valid_with_1:
            return None
        if not valid_with_0 and not valid_with_1:
            return "error"
        if valid_with_0:
            return check_0_row, check_0_col
        if valid_with_1:
            return check_1_row, check_1_col

    @staticmethod
    def deduce(nonogram, guesses):
        solved_count = 0
        unsolved = nonogram.unsolved.copy()
        for pos in unsolved:
            if pos not in nonogram.unsolved:
                continue
            check_result = Solver.check_regex(nonogram, pos)
            if not check_result:
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
        pos = choice(list(nonogram.unsolved))
        guesses.append(CellGuess(pos))
        nonogram.update_at_pos(pos, "1")

    @staticmethod
    def guess_sequence(line_type, index, nonogram, guesses):
        new_value = nonogram.sequences[line_type][index].solutions[0]
        guesses.append(SequenceGuess(line_type, index, new_value, nonogram.sequences[line_type][index].value))
        nonogram.update_single_sequence(line_type, index, new_value)
    
    @staticmethod
    def revert_guess(nonogram, guess):
        for cell in guess.dependent_cells:
            nonogram.update_at_pos(cell, "x")
        if isinstance(guess, SequenceGuess):
            nonogram.update_single_sequence(guess.line_type, guess.index, guess.old_value)
        elif isinstance(guess, CellGuess):
            nonogram.update_at_pos(guess.pos, "x")

    def get_next_guess(nonogram, guesses, revert):
        if not guesses and revert:
            raise Exception("Not solvable")
        if not guesses:
            nonogram.update_sequence_complexity()
        if not revert:
            for line_type, index, _ in nonogram.sequence_complexity:
                if "x" in nonogram.sequences[line_type][index].value and (line_type, index) not in guesses and line_type == "row":
                    Solver.guess_sequence(line_type, index, nonogram, guesses)
                    return
            Solver.guess_cell(nonogram, guesses)
            return
        last_guess = guesses.pop()
        if isinstance(last_guess, CellGuess):
            guess_value = nonogram.sequences["row"][last_guess.pos[0]].value[last_guess.pos[1]]
            Solver.revert_guess(nonogram, last_guess)
            if guess_value == "0":
                Solver.get_next_guess(nonogram, guesses, True)
            elif guess_value == "1":
                guesses.append(CellGuess(last_guess.pos))
                nonogram.update_at_pos(last_guess.pos, "0")
            else:
                raise Exception("Error: a previous guess did not update the Nonogram")
        if isinstance(last_guess, SequenceGuess):
            last_guess_value = nonogram.sequences[last_guess.line_type][last_guess.index].value
            solutions_list = nonogram.sequences[last_guess.line_type][last_guess.index].solutions
            last_guess_index = solutions_list.index(last_guess_value)
            Solver.revert_guess(nonogram, last_guess)
            if last_guess_index + 1 < len(solutions_list):
                next_guess_value = solutions_list[last_guess_index + 1]
                guesses.append(SequenceGuess(last_guess.line_type, last_guess.index, next_guess_value, last_guess.old_value))
                nonogram.update_single_sequence(last_guess.line_type, last_guess.index, next_guess_value)
            else:
                Solver.get_next_guess(nonogram, True)

    @staticmethod
    def solve(*args):
        nonogram = Nonogram(*args)
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
                raise Exception("Not solvable")
            else:
                Solver.get_next_guess(nonogram, guesses, True)