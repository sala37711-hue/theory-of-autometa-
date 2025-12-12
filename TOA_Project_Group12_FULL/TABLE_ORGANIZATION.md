# Table and Data Organization Documentation

## Overview
The tables and data created after running the pipeline have been reorganized into a well-structured, organized system that provides:
- **Consistent formatting** across all tables
- **Type-safe data structures** using dataclasses
- **Clear visual hierarchy** with proper headers and separators
- **Detailed metadata** for states (start, accept markers)
- **Reusable components** for different automation types

## New Structure

### Core Components

#### 1. **table_formatter.py**
The main module providing structured table formatting and data organization.

##### Key Classes:

**StateType (Enum)**
```python
- NORMAL: Regular state
- START: Starting state
- ACCEPT: Accepting state
- START_ACCEPT: Both start and accept
```

**State (Dataclass)**
- Represents a state with metadata
- Properties:
  - `name`: State identifier
  - `state_type`: Type of state (using StateType enum)
  - `get_marker()`: Returns string representation for display

**TransitionRow (Dataclass)**
- Represents a single row in transition table
- Properties:
  - `state`: State object
  - `transitions`: Dict mapping symbols to next states
  - `extra_info`: Additional information for the state

**TransitionTable (Dataclass)**
- Structured representation of complete transition table
- Properties:
  - `title`: Table title
  - `symbols`: List of alphabet symbols
  - `rows`: List of TransitionRow objects
  - `table_type`: 'standard' or 'minimized'
  - `to_formatted_string()`: Generates formatted output

**MinimizationSteps (Dataclass)**
- Organizes DFA minimization steps
- Properties:
  - `steps`: List of (title, partitions) tuples
  - `to_formatted_string()`: Nicely formats all minimization steps

**StringSimulation (Dataclass)**
- Represents string simulation trace
- Properties:
  - `input_string`: The input being tested
  - `trace`: List of (current_state, symbol, next_state) transitions
  - `result`: 'Accepted' or 'Rejected'
  - `to_formatted_string()`: Formats the simulation trace

**TableFormatter (Static Helper Class)**
- Provides formatting methods:
  - `format_pipeline_start(regex, postfix)`: Pipeline initialization
  - `format_section_header(title)`: Section dividers
  - `format_info_message(message)`: Info messages with ✓
  - `format_error_message(message)`: Error messages with ✗
  - `format_section_separator()`: Visual separators

##### Factory Functions:

```python
create_nfa_table(nfa) -> TransitionTable
  Converts NFA object to structured TransitionTable
  
create_dfa_table(dfa) -> TransitionTable
  Converts DFA object to structured TransitionTable
  
create_minimized_dfa_table(min_dfa) -> TransitionTable
  Converts minimized DFA to structured TransitionTable with orig-states column
```

### Pipeline Output Structure

#### Stage 1: Regex → Postfix
```
================================================================================
REGULAR EXPRESSION TO FINITE AUTOMATON PIPELINE
================================================================================

Regular Expression: ggh + m(pg + gg + ggg)*m + hg
Postfix Notation:   gg.h.mpg.gg.+gg.g.+*.m.+hg.+
```

#### Stage 2: Thompson NFA Construction
```
================================================================================
STEP 1: THOMPSON NFA CONSTRUCTION
================================================================================

NFA TRANSITION TABLE

State | eps | g   | h   | m   | p
-----|-----|-----|-----|-----|-----
q0    | -   | q1  | -   | -   | -
...
q37   | -   | -   | -   | -   | -   [ACCEPT]

✓ NFA built successfully with 38 states
```

#### Stage 3: Subset Construction (DFA)
```
================================================================================
STEP 2: SUBSET CONSTRUCTION (DFA)
================================================================================

DFA TRANSITION TABLE

State | g   | h   | m   | p
------|-----|-----|-----|-----
D0    | D1  | D2  | D3  | -   [START]
...
D5    | -   | -   | -   | -   [ACCEPT]

✓ DFA constructed with 15 states
```

#### Stage 4: DFA Minimization
```
================================================================================
STEP 3: DFA MINIMIZATION (HOPCROFT)
================================================================================

Minimization Steps

Initial partition:
  P0 = {D5, D7, D9}
  P1 = {D0, D1, D10, ...}

Refine on symbol 'g':
  P0 = {D5, D7, D9}
  P1 = {D2}
  ...

MINIMIZED DFA TRANSITION TABLE

State | Orig-States       | g  | h  | m  | p
------|-------------------|----|----|----|----- 
M0    | {D5,D7,D9}        | M9 | M9 | M9 | M9  [ACCEPT]
...
M5    | {D0}              | M6 | M1 | M4 | M9  [START]

✓ DFA minimized: 15 states → 10 states
```

#### Stage 5: String Simulation
```
================================================================================
STEP 4: STRING SIMULATION
================================================================================

String Simulation
Input: 'ggh'

Transition Trace:
--------------------------------------------------
M5 --g--> M6
M6 --g--> M2
M2 --h--> M0

Result: Accepted
```

## Implementation Details

### Table Formatting Algorithm

1. **Header Construction**: Create column headers including state and symbols
2. **Width Calculation**: Scan all cells to determine minimum column widths
3. **Alignment**: Use left-justified padding for consistent formatting
4. **Separator Lines**: Create visual separators with dashes
5. **State Markers**: Append [START], [ACCEPT], or [START, ACCEPT] labels
6. **Minimized Table Handling**: Add "Orig-States" column showing original state sets

### Data Flow

```
NFA Object (from thompson_nfa.py)
    ↓
create_nfa_table(nfa)
    ↓
TransitionTable object
    ↓
to_formatted_string()
    ↓
Formatted string output
```

## Benefits

1. **Consistency**: All tables use the same formatting rules
2. **Type Safety**: Using dataclasses prevents formatting errors
3. **Maintainability**: Centralized formatting logic easy to update
4. **Extensibility**: Easy to add new table types or formatting styles
5. **Readability**: Clear visual hierarchy with proper spacing and markers
6. **Reusability**: Components can be used in both GUI and CLI
7. **Traceability**: Each stage clearly marked with headers and info messages

## Usage in GUI and CLI

### In main.py (CLI):
```python
from table_formatter import (
    TableFormatter, create_nfa_table, create_dfa_table,
    create_minimized_dfa_table, MinimizationSteps, StringSimulation
)

# Build NFA
nfa = build_from_postfix(postfix)
nfa_table = create_nfa_table(nfa)
print(nfa_table.to_formatted_string())
```

### In gui.py (GUI):
```python
# Build DFA
dfa = nfa_to_dfa(nfa)
dfa_table = create_dfa_table(dfa)
self.log(dfa_table.to_formatted_string())
```

## Customization

### To change table formatting:
Edit `TransitionTable.to_formatted_string()` method

### To add new state markers:
Extend `StateType` enum and update `State.get_marker()` method

### To format different data:
Create new dataclass similar to `StringSimulation` and implement `to_formatted_string()` method

---

**Version**: 1.0
**Last Updated**: December 12, 2025
