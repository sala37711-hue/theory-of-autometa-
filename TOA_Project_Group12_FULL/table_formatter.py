# table_formatter.py - Structured table formatting and data organization
"""
Provides organized, well-structured table formatting for the TOA pipeline.
Handles NFA, DFA, and Minimized DFA tables with consistent styling.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from enum import Enum


class StateType(Enum):
    """Marking for special state types"""
    NORMAL = 0
    START = 1
    ACCEPT = 2
    START_ACCEPT = 3


@dataclass
class State:
    """Represents a state with metadata"""
    name: str
    state_type: StateType = StateType.NORMAL
    
    def get_marker(self) -> str:
        """Get the marker string for this state"""
        if self.state_type == StateType.START_ACCEPT:
            return "[START, ACCEPT]"
        elif self.state_type == StateType.START:
            return "[START]"
        elif self.state_type == StateType.ACCEPT:
            return "[ACCEPT]"
        return ""


@dataclass
class TransitionRow:
    """Represents a single row in a transition table"""
    state: State
    transitions: Dict[str, Any] = field(default_factory=dict)
    extra_info: str = ""


@dataclass
class TransitionTable:
    """Structured representation of a transition table"""
    title: str
    symbols: List[str] = field(default_factory=list)
    rows: List[TransitionRow] = field(default_factory=list)
    table_type: str = "standard"  # 'standard' or 'minimized'
    
    def to_formatted_string(self) -> str:
        """Format the table as a nicely aligned string"""
        if not self.rows:
            return f"{self.title}\n(No data)\n"
        
        # Build header
        if self.table_type == "minimized":
            header = ["State", "Orig-States"] + self.symbols
        else:
            header = ["State"] + self.symbols
        
        # Collect all cell values for width calculation
        all_rows = []
        for row in self.rows:
            cells = [row.state.name]
            
            if self.table_type == "minimized" and hasattr(row, 'orig_states'):
                cells.append(str(row.orig_states))
            
            for sym in self.symbols:
                cells.append(str(row.transitions.get(sym, '-')))
            
            all_rows.append((row, cells))
        
        # Calculate column widths
        col_widths = [len(h) for h in header]
        for _, cells in all_rows:
            for i, cell in enumerate(cells):
                col_widths[i] = max(col_widths[i], len(cell))
        
        # Format header
        lines = [self.title]
        lines.append("")
        header_row = " | ".join(h.ljust(w) for h, w in zip(header, col_widths))
        lines.append(header_row)
        lines.append("-" * len(header_row))
        
        # Format data rows
        for row, cells in all_rows:
            row_text = " | ".join(c.ljust(w) for c, w in zip(cells, col_widths))
            marker = row.state.get_marker()
            if marker:
                row_text += f"  {marker}"
            lines.append(row_text)
        
        lines.append("")
        return "\n".join(lines)


@dataclass
class MinimizationSteps:
    """Represents the steps in DFA minimization"""
    steps: List[Tuple[str, List[set]]] = field(default_factory=list)
    
    def to_formatted_string(self) -> str:
        """Format minimization steps nicely"""
        if not self.steps:
            return "Minimization Steps\n(No data)\n"
        
        lines = ["Minimization Steps"]
        lines.append("")
        
        for title, partitions in self.steps:
            lines.append(f"{title}:")
            for i, partition in enumerate(partitions):
                sorted_states = sorted(partition)
                lines.append(f"  P{i} = {{{', '.join(sorted_states)}}}")
            lines.append("")
        
        return "\n".join(lines)


@dataclass
class StringSimulation:
    """Represents string simulation trace"""
    input_string: str
    trace: List[Tuple[str, str, str]] = field(default_factory=list)  # (current_state, symbol, next_state)
    result: str = "Pending"  # 'Accepted', 'Rejected'
    
    def to_formatted_string(self) -> str:
        """Format simulation trace nicely"""
        lines = ["String Simulation"]
        lines.append(f"Input: '{self.input_string}'")
        lines.append("")
        
        if not self.trace:
            lines.append("No transitions")
        else:
            lines.append("Transition Trace:")
            lines.append("-" * 50)
            for current, symbol, next_state in self.trace:
                arrow = f" --{symbol}--> "
                lines.append(f"{current}{arrow}{next_state}")
        
        lines.append("")
        lines.append(f"Result: {self.result}")
        lines.append("")
        
        return "\n".join(lines)


class TableFormatter:
    """Helper class for formatting pipeline output"""
    
    @staticmethod
    def format_pipeline_start(regex: str, postfix: str) -> str:
        """Format the pipeline start information"""
        lines = ["=" * 70]
        lines.append("REGULAR EXPRESSION TO FINITE AUTOMATON PIPELINE")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Regular Expression: {regex}")
        lines.append(f"Postfix Notation:   {postfix}")
        lines.append("")
        return "\n".join(lines)
    
    @staticmethod
    def format_section_header(title: str) -> str:
        """Format a section header"""
        lines = [""]
        lines.append("=" * 70)
        lines.append(title)
        lines.append("=" * 70)
        lines.append("")
        return "\n".join(lines)
    
    @staticmethod
    def format_info_message(message: str) -> str:
        """Format an info message"""
        return f"✓ {message}\n"
    
    @staticmethod
    def format_error_message(message: str) -> str:
        """Format an error message"""
        return f"✗ ERROR: {message}\n"
    
    @staticmethod
    def format_section_separator() -> str:
        """Format a separator between sections"""
        return "\n" + "-" * 70 + "\n"


def create_nfa_table(nfa) -> TransitionTable:
    """Create a structured NFA transition table from NFA object"""
    symbols, rows = nfa.to_table()
    
    table_rows = []
    for r in rows:
        state_type = StateType.NORMAL
        if r['state'] == nfa.start and r['state'] == nfa.accept:
            state_type = StateType.START_ACCEPT
        elif r['state'] == nfa.start:
            state_type = StateType.START
        elif r['state'] == nfa.accept:
            state_type = StateType.ACCEPT
        
        state = State(r['state'], state_type)
        transitions = {}
        for s in symbols:
            dest = ','.join(sorted(r[s])) if r[s] else ''
            transitions[s] = dest if dest else '-'
        
        table_rows.append(TransitionRow(state, transitions))
    
    return TransitionTable(
        title="NFA TRANSITION TABLE",
        symbols=symbols,
        rows=table_rows,
        table_type="standard"
    )


def create_dfa_table(dfa) -> TransitionTable:
    """Create a structured DFA transition table from DFA object"""
    header, rows = dfa.to_table()
    symbols = header[1:]  # Skip 'State' column
    
    table_rows = []
    for row in rows:
        state_name = row[0]
        state_type = StateType.NORMAL
        if state_name == dfa.start and state_name in dfa.final_states:
            state_type = StateType.START_ACCEPT
        elif state_name == dfa.start:
            state_type = StateType.START
        elif state_name in dfa.final_states:
            state_type = StateType.ACCEPT
        
        state = State(state_name, state_type)
        transitions = {symbols[i]: row[i + 1] for i in range(len(symbols))}
        
        table_rows.append(TransitionRow(state, transitions))
    
    return TransitionTable(
        title="DFA TRANSITION TABLE",
        symbols=symbols,
        rows=table_rows,
        table_type="standard"
    )


def create_minimized_dfa_table(min_dfa) -> TransitionTable:
    """Create a structured minimized DFA transition table"""
    symbols = sorted(min_dfa.alphabet)
    
    table_rows = []
    for state_name, orig_states_set in min_dfa.states.items():
        state_type = StateType.NORMAL
        if state_name == min_dfa.start and state_name in min_dfa.final_states:
            state_type = StateType.START_ACCEPT
        elif state_name == min_dfa.start:
            state_type = StateType.START
        elif state_name in min_dfa.final_states:
            state_type = StateType.ACCEPT
        
        state = State(state_name, state_type)
        transitions = {}
        for a in symbols:
            transitions[a] = min_dfa.transitions.get(state_name, {}).get(a, '-')
        
        row = TransitionRow(state, transitions)
        row.orig_states = '{' + ','.join(sorted(orig_states_set)) + '}'
        table_rows.append(row)
    
    return TransitionTable(
        title="MINIMIZED DFA TRANSITION TABLE",
        symbols=symbols,
        rows=table_rows,
        table_type="minimized"
    )
