# PyNonogram

## Overview

PyNonogram aims to quickly solve nonograms of any size using a combination of regular expression matching and, when necessary, guessing-and-checking.

## How to use PyNonogram

### Step-by-step

1. Import nonogram.py and solver.py.
2. Create a tuple of clues that represent the nonogram to be solved (see Input section).
3. Pass the tuple of clues to the Solver.solve function.
4. A solved Nonogram object will be returned (see Output section).

### Example code
 
import solver

clues = (((1,2),(4,),(2,2),(1,),(1,)),((3,),(3,),(1,),(3,),(3,)))

solved_puzzle = solver.Solver.solve(clues)  
solved_puzzle_grid = solved_puzzle.get_grid()

### Input

This program expects a tuple containing two tuples that represent a nonogram's clues. The first tuple should contain the vertical clues and the second should contain the horizontal clues. Each value contained in each of these tuples should itself be a tuple representing an individual column or row's clue, e.g. (2,) for a row or column that has a single filled segment that is two cells in length. The following is an example of a valid input for a 5x5 nonogram:

(((1,2),(4,),(2,2),(1,),(1,)),((3,),(3,),(1,),(3,),(3,)))

Vertical clues are: ((1,2),(4,),(2,2),(1,),(1,))  
Horizontal clues are: ((3,),(3,),(1,),(3,),(3,))

Empty clues (i.e. clues indicating that there are no filled cells in the row/column) should be represented by empty tuples.

### Output

The Solver.solve method returns a solved Nonogram object. Printing this object to the console shows a visual representation of the solved puzzle. Example:

░░███  
███░░  
░█░░░  
███░░  
███░░

The get_grid() method of a Nonogram object will return a tuple of tuples representing the rows of the solved nonogram. Calling this method on the puzzle above returns the following:

((0,0,1,1,1),  
 (1,1,1,0,0),  
 (0,1,0,0,0),  
 (1,1,1,0,0),  
 (1,1,1,0,0))