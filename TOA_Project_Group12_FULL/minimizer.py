
# minimizer.py - Hopcroft's minimization algorithm (returns MinDFA and steps)
from collections import deque
from dataclasses import dataclass
from typing import Dict, Set
from subset_dfa import DFA

@dataclass
class MinDFA:
    start: str
    states: Dict[str, Set[str]]
    transitions: Dict[str, Dict[str, str]]
    final_states: Set[str]
    alphabet: Set[str]

def hopcroft_minimize(dfa: DFA):
    alphabet = sorted(dfa.alphabet)
    states = set(dfa.states.keys())
    trans = {s: {a: dfa.transitions.get(s, {}).get(a) for a in alphabet} for s in states}

    # add dead state if needed
    dead_needed = any(trans[s].get(a) is None for s in states for a in alphabet)
    if dead_needed:
        dead = 'DEAD'
        states.add(dead)
        trans[dead] = {a: dead for a in alphabet}
        for s in list(states):
            for a in alphabet:
                if trans.get(s, {}).get(a) is None:
                    trans[s][a] = dead

    P = [set(dfa.final_states), states - set(dfa.final_states)]
    P = [p for p in P if p]
    W = deque(P.copy())
    steps = [('Initial partition', [set(x) for x in P])]

    while W:
        A = W.popleft()
        for c in alphabet:
            X = set(q for q in states if trans[q][c] in A)
            newP = []
            for Y in P:
                inter = Y & X
                diff = Y - X
                if inter and diff:
                    newP.extend([inter, diff])
                    if Y in W:
                        W.remove(Y)
                        W.extend([inter, diff])
                    else:
                        if len(inter) <= len(diff):
                            W.append(inter)
                        else:
                            W.append(diff)
                else:
                    newP.append(Y)
            if newP != P:
                P = newP
                steps.append((f"Refine on symbol '{c}'", [set(x) for x in P]))

    # build minimized DFA
    rep = {}
    mname = {}
    for i, block in enumerate(P):
        name = f"M{i}"
        mname[name] = block
        for q in block:
            rep[q] = name

    min_trans = {}
    for name, members in mname.items():
        rep_state = next(iter(members))
        min_trans[name] = {a: rep[trans[rep_state][a]] for a in alphabet}

    min_start = rep[dfa.start]
    min_finals = {rep[s] for s in dfa.final_states}
    return MinDFA(start=min_start, states=mname, transitions=min_trans, final_states=min_finals, alphabet=set(alphabet)), steps
