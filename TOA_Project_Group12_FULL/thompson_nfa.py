
# thompson_nfa.py - build NFA from postfix using Thompson's construction
from collections import defaultdict
from dataclasses import dataclass
from itertools import count
from typing import Dict, List

EPS = 'eps'
_counter = count()

def _new_state():
    return f'q{next(_counter)}'

@dataclass
class NFA:
    start: str
    accept: str
    states: Dict[str, Dict[str, List[str]]]

    def add_transition(self, src, symbol, dst):
        self.states.setdefault(src, defaultdict(list))
        self.states.setdefault(dst, defaultdict(list))
        self.states[src].setdefault(symbol, []).append(dst)

    def to_table(self):
        symbols = set()
        for trans in self.states.values():
            symbols.update(trans.keys())
        symbols = sorted(symbols)
        rows = []
        def idx(s):
            try: return int(s[1:])
            except: return 9999
        for s in sorted(self.states.keys(), key=idx):
            row = {'state': s}
            for sym in symbols:
                row[sym] = list(self.states[s].get(sym, []))
            rows.append(row)
        return symbols, rows

def build_from_postfix(postfix: str) -> NFA:
    stack = []
    for token in postfix:
        if token.isalnum():
            s = _new_state(); t = _new_state()
            states = {s: defaultdict(list), t: defaultdict(list)}
            nfa = NFA(start=s, accept=t, states=states)
            nfa.add_transition(s, token, t)
            stack.append(nfa)
        elif token == '*':
            n1 = stack.pop()
            s = _new_state(); t = _new_state()
            states = {**n1.states}
            states.setdefault(s, defaultdict(list))
            states.setdefault(t, defaultdict(list))
            n = NFA(start=s, accept=t, states=states)
            n.add_transition(s, EPS, n1.start)
            n.add_transition(s, EPS, t)
            n.add_transition(n1.accept, EPS, n1.start)
            n.add_transition(n1.accept, EPS, t)
            stack.append(n)
        elif token == '.':
            n2 = stack.pop(); n1 = stack.pop()
            states = {**n1.states, **n2.states}
            n = NFA(start=n1.start, accept=n2.accept, states=states)
            n.add_transition(n1.accept, EPS, n2.start)
            stack.append(n)
        elif token == '+':
            n2 = stack.pop(); n1 = stack.pop()
            s = _new_state(); t = _new_state()
            states = {**n1.states, **n2.states}
            states.setdefault(s, defaultdict(list))
            states.setdefault(t, defaultdict(list))
            n = NFA(start=s, accept=t, states=states)
            n.add_transition(s, EPS, n1.start)
            n.add_transition(s, EPS, n2.start)
            n.add_transition(n1.accept, EPS, t)
            n.add_transition(n2.accept, EPS, t)
            stack.append(n)
        else:
            raise ValueError(f"Unknown token {token}")
    return stack[0]
