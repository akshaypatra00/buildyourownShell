def completer(text, state):
    """Tab completion function for readline"""
    builtins = ["echo", "exit", "type", "pwd", "cd"]
    
    # Track if this is a new completion or continuation
    if completion_state['last_text'] != text:
        completion_state['last_text'] = text
        completion_state['attempt'] = 0
    
    # Get all matches: builtins + executables in PATH
    builtin_matches = [cmd for cmd in builtins if cmd.startswith(text)]
    executable_matches = get_executables_in_path(text)
    
    # Combine all matches and sort alphabetically
    all_matches = sorted(builtin_matches + executable_matches)
    
    # If we're at state 0 and there are multiple matches
    if state == 0 and len(all_matches) > 1:
        completion_state['attempt'] += 1
        
        if completion_state['attempt'] == 1:
            # First TAB: ring the bell
            sys.stdout.write('\a')
            sys.stdout.flush()
            return None
        elif completion_state['attempt'] >= 2:
            # Second TAB: display all matches
            sys.stdout.write('\n')
            sys.stdout.write('  '.join(all_matches))
            sys.stdout.write('\n')
            sys.stdout.write('$ ' + text)
            sys.stdout.flush()
            # Reset for next completion
            completion_state['attempt'] = 0
            return None
    
    # Single match or returning matches normally
    matches_with_space = [cmd + ' ' for cmd in all_matches]
    
    # Return the state-th match
    if state < len(matches_with_space):
        return matches_with_space[state]
    else:
        return None