# main.py - Integration runner for Group 12 project (hardcoded RE)
import os
from regex_parser import to_postfix
from thompson_nfa import build_from_postfix, NFA
from subset_dfa import nfa_to_dfa, DFA
from minimizer import hopcroft_minimize
from visualize import draw_nfa, draw_dfa, draw_min_dfa
from table_formatter import (
    TableFormatter, create_nfa_table, create_dfa_table,
    create_minimized_dfa_table, MinimizationSteps, StringSimulation
)

# ensure diagrams folder exists
os.makedirs('diagrams', exist_ok=True)

# Hardcoded group RE (Group 12)
REGEX = "ggh + m(pg + gg + ggg)*m + hg"
DEFAULT_TEST = "ggh"


def run(regex, teststring):
    """Execute the complete RE to automaton pipeline with structured output"""
    
    # 1) Parse regex to postfix
    try:
        postfix = to_postfix(regex)
        print(TableFormatter.format_pipeline_start(regex, postfix))
    except Exception as e:
        print(TableFormatter.format_error_message(f"Regex parsing failed: {str(e)}"))
        return

    # 2) Build NFA
    try:
        print(TableFormatter.format_section_header("STEP 1: THOMPSON NFA CONSTRUCTION"))
        nfa = build_from_postfix(postfix)
        nfa_table = create_nfa_table(nfa)
        print(nfa_table.to_formatted_string())
        print(TableFormatter.format_info_message(
            f"NFA built successfully with {len(nfa_table.rows)} states"
        ))
        draw_nfa(nfa, filename='diagrams/nfa')
        print(TableFormatter.format_info_message("NFA diagram saved: diagrams/nfa.png"))
    except Exception as e:
        print(TableFormatter.format_error_message(f"NFA construction failed: {str(e)}"))
        return

    # 3) Build DFA
    try:
        print(TableFormatter.format_section_header("STEP 2: SUBSET CONSTRUCTION (DFA)"))
        dfa = nfa_to_dfa(nfa)
        dfa_table = create_dfa_table(dfa)
        print(dfa_table.to_formatted_string())
        print(TableFormatter.format_info_message(
            f"DFA constructed with {len(dfa_table.rows)} states"
        ))
        draw_dfa(dfa, filename='diagrams/dfa')
        print(TableFormatter.format_info_message("DFA diagram saved: diagrams/dfa.png"))
    except Exception as e:
        print(TableFormatter.format_error_message(f"DFA construction failed: {str(e)}"))
        return

    # 4) Minimize DFA
    try:
        print(TableFormatter.format_section_header("STEP 3: DFA MINIMIZATION (HOPCROFT)"))
        min_dfa, steps = hopcroft_minimize(dfa)
        
        # Format and print minimization steps
        min_steps_obj = MinimizationSteps(steps=steps)
        print(min_steps_obj.to_formatted_string())
        
        # Show minimized table
        min_table = create_minimized_dfa_table(min_dfa)
        print(min_table.to_formatted_string())
        
        print(TableFormatter.format_info_message(
            f"DFA minimized: {len(dfa_table.rows)} states → {len(min_table.rows)} states"
        ))
        
        draw_min_dfa(min_dfa, filename='diagrams/min_dfa')
        print(TableFormatter.format_info_message("Minimized DFA diagram saved: diagrams/min_dfa.png"))
    except Exception as e:
        print(TableFormatter.format_error_message(f"DFA minimization failed: {str(e)}"))
        return

    # 5) Simulate string
    try:
        print(TableFormatter.format_section_header("STEP 4: STRING SIMULATION"))
        
        simulation = StringSimulation(input_string=teststring)
        current = min_dfa.start
        
        if teststring:
            for ch in teststring:
                next_state = min_dfa.transitions.get(current, {}).get(ch)
                next_str = next_state if next_state is not None else "REJECT"
                simulation.trace.append((current, ch, next_str))
                
                if next_state is None:
                    simulation.result = "Rejected"
                    break
                current = next_state
            
            if simulation.result == "Pending":
                if current in min_dfa.final_states:
                    simulation.result = "Accepted"
                else:
                    simulation.result = "Rejected"
        else:
            simulation.result = "Rejected (empty input)"
        
        print(simulation.to_formatted_string())
    except Exception as e:
        print(TableFormatter.format_error_message(f"String simulation failed: {str(e)}"))

    print("\n" + "=" * 70)
    print("PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    user = input("Enter test string (press Enter to use default 'ggh'): ").strip()
    if user == "":
        user = DEFAULT_TEST
    run(REGEX, user)

