# visualize.py - Graphviz diagrams for NFA, DFA, Minimized DFA
try:
    from graphviz import Digraph
except ImportError:
    Digraph = None


def draw_nfa(nfa, filename='diagrams/nfa'):
    if Digraph is None:
        print("Graphviz not installed. Skipping NFA diagram.")
        return

    g = Digraph(format='png')
    g.attr('node', shape='circle', fontsize='10')

    for s in nfa.states:
        if s == nfa.accept:
            g.node(s, peripheries='2', style='filled', fillcolor='lightblue')
        else:
            g.node(s)

    g.node('start', shape='point')
    g.edge('start', nfa.start)

    for s, trans in nfa.states.items():
        for sym, lst in trans.items():
            label = sym if sym != 'eps' else 'ε'
            for d in lst:
                g.edge(s, d, label=label)

    g.render(filename, cleanup=True)
    print(f"NFA diagram saved as: {filename}.png")


def draw_dfa(dfa, filename='diagrams/dfa'):
    if Digraph is None:
        print("Graphviz not installed. Skipping DFA diagram.")
        return

    g = Digraph(format='png')
    g.attr('node', shape='circle', fontsize='10')

    for s in dfa.states:
        if s in dfa.final_states:
            g.node(s, peripheries='2', style='filled', fillcolor='lightblue')
        else:
            g.node(s)

    g.node('start', shape='point')
    g.edge('start', dfa.start)

    for s, trans in dfa.transitions.items():
        for sym, d in trans.items():
            g.edge(s, d, label=sym)

    g.render(filename, cleanup=True)
    print(f"DFA diagram saved as: {filename}.png")


def draw_min_dfa(min_dfa, filename='diagrams/min_dfa'):
    if Digraph is None:
        print("Graphviz not installed. Skipping Minimized DFA diagram.")
        return

    g = Digraph(format='png')
    g.attr('node', shape='circle', fontsize='10')

    for s in min_dfa.states:
        if s in min_dfa.final_states:
            g.node(s, peripheries='2', style='filled', fillcolor='lightblue')
        else:
            g.node(s)

    g.node('start', shape='point')
    g.edge('start', min_dfa.start)

    for s, transitions in min_dfa.transitions.items():
        for sym, d in transitions.items():
            g.edge(s, d, label=sym)

    g.render(filename, cleanup=True)
    print(f"Minimized DFA diagram saved as: {filename}.png")
