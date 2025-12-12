
# subset_dfa.py - convert NFA to DFA via subset construction
from collections import defaultdict, deque
from dataclasses import dataclass
from itertools import count
from typing import Dict, Set, FrozenSet
from thompson_nfa import NFA, EPS

_dcounter = count()

def _new_dstate():
    return f'D{next(_dcounter)}'

@dataclass
class DFA:
    start: str
    states: Dict[str, Set[str]]
    transitions: Dict[str, Dict[str, str]]
    final_states: Set[str]
    alphabet: Set[str]

    def to_table(self):
        header = ['State', 'NFA-set'] + sorted(self.alphabet)
        rows = []
        def idx(s):
            try: return int(s[1:])
            except: return 9999
        for s in sorted(self.states.keys(), key=idx):
            nfaset = '{' + ','.join(sorted(self.states[s])) + '}'
            row = [s, nfaset]
            for a in sorted(self.alphabet):
                row.append(self.transitions.get(s, {}).get(a, '-'))
            rows.append(row)
        return header, rows

def epsilon_closure(nfa: NFA, state_set: Set[str]):
    stack = list(state_set)
    closure = set(state_set)
    while stack:
        s = stack.pop()
        for nxt in nfa.states.get(s, {}).get(EPS, []):
            if nxt not in closure:
                closure.add(nxt)
                stack.append(nxt)
    return closure

def move(nfa: NFA, state_set: Set[str], symbol: str):
    res = set()
    for s in state_set:
        res.update(nfa.states.get(s, {}).get(symbol, []))
    return res

def nfa_to_dfa(nfa: NFA) -> DFA:
    alphabet = set()
    for trans in nfa.states.values():
        for sym in trans:
            if sym != EPS:
                alphabet.add(sym)

    start_closure = frozenset(epsilon_closure(nfa, {nfa.start}))
    mapping = {start_closure: _new_dstate()}
    dstates = {mapping[start_closure]: set(start_closure)}
    dtrans = {}
    dfinal = set()
    q = deque([start_closure])

    while q:
        T = q.popleft()
        Td = mapping[T]
        dtrans.setdefault(Td, {})
        if nfa.accept in T:
            dfinal.add(Td)

        for a in sorted(alphabet):
            moved = move(nfa, set(T), a)
            if not moved:
                continue
            U = frozenset(epsilon_closure(nfa, moved))
            if U not in mapping:
                mapping[U] = _new_dstate()
                dstates[mapping[U]] = set(U)
                q.append(U)
            dtrans[Td][a] = mapping[U]

    return DFA(start=mapping[start_closure], states=dstates, transitions=dtrans, final_states=dfinal, alphabet=alphabet)
