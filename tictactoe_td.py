'''
To recreate the system described in the text, we need the following components:
1. Enumerate all legal states and neighbor relationships in TicTacToe
2. Assign each state a value. (Initially 0.5 for most states, 1 or 0 for states where we have won or lost/drawn).
    2a. This implies we have a function that can evaluate a position.
3. Create an agent that can use these weights to play. 
    3a. Make sure to integrate exploration vs. exploitation
4. Set up a training harness, pitting our agent against a random bot
    4a. Implement temporal difference weight updates
    4b. Make sure the size of the updates decreases over time
5. Profit! (Extend to visualize and check my answers to the various discussion questions)
'''

# constants
from random import seed
seed('foo')

X_TOK, O_TOK = 'x', 'o'

ILLEGAL_STATE, XWIN_STATE, OWIN_STATE, DRAW_STATE, XTURN_STATE, OTURN_STATE = \
    'illegal', 'xwin', 'owin', 'draw', 'xturn', 'oturn'

EMPTY = tuple((None,)*3 for _ in range(3))

NEW_GAME_ACTION, END_GAME_ACTION, MOVE_ACTION = \
    'newgame', 'endgame', 'move'

'''
count_pieces

This method counts the number of X's and O's in a board, useful to determine
whose turn it is and check for a legal board state.
'''
def count_pieces(board):
    x, o = 0, 0
    for row in board:
        for col in row:
            if col == X_TOK:
                x += 1
            elif col == O_TOK:
                o += 1
    return x, o


'''
    has_win
    
Determine if there is a win on the board for the given player.
Note that if this method is presented with a board that shows
3-in-a-row for both players, it will return 'true', even though
that's an illegal board state. As such, this method should be 
only used a helper by more sophisticated methods like 
classify_board.
'''
def has_win(board, player):
    for (ar, ac), (br, bc), (cr, cc) in [
        ((0, 0), (0, 1), (0, 2)), # top row
        ((1, 0), (1, 1), (1, 2)), # mid row
        ((2, 0), (2, 1), (2, 2)), # bot row
        ((0, 0), (1, 0), (2, 0)), # left col
        ((0, 1), (1, 1), (2, 1)), # mid col
        ((0, 2), (1, 2), (2, 2)), # right col
        ((0, 0), (1, 1), (2, 2)), # down diagonal
        ((2, 0), (1, 1), (0, 2)), # up diagonal
    ]:
        if board[ar][ac] == board[br][bc] == board[cr][cc] == player:
            return True
    return False


'''
   classify_board:

   This method classifies a board in one of the following categories:
   * ILLEGAL: Not possible to reach this state by a valid combination of moves
   * XWIN: 'X' won.
   * OWIN: 'O' won.
   * DRAW: No more moves are possible, and it's a draw.
   * XTURN: The game is not over, and it's X's turn.
   * OTURN: The game is not over, and it's O's turn.

   "board" should be an array[3][3] of X/O/None.
'''
def classify_board(board):
    # 1. board dimensions

    if len(board) != 3:
        raise ValueError("Board does not have 3 rows: ", board)
        return ILLEGAL_STATE
    for row in board:
        if len(row) != 3:
            raise ValueError("Board is misshaped : ", board)
            return ILLEGAL_STATE
    
    # 2. parity
    x, o = count_pieces(board)
    if abs(x - o) > 1:
        return ILLEGAL_STATE

    # 3. has anyone won yet?
    xwin, owin = has_win(board, X_TOK), has_win(board, O_TOK)

    # 4. options!
    if xwin and owin:
        return ILLEGAL_STATE
    elif xwin:
        return XWIN_STATE
    elif owin:
        return OWIN_STATE
    elif x + o == 9:
        return DRAW_STATE
    elif x > o:
        return OTURN_STATE
    else: # X moves first
        return XTURN_STATE

'''
    get_children:

    This method takes a board and returns a list of valid successor states.
    We do this by (1) determining whose turn it is, and (2) attempting to place
    their token in each possible square in token.

    If the game is finished or in an illegal state, we return an empty list of states. 
'''
def get_children(board):
    state = classify_board(board)

    def _move(board, r, c, piece):
        return tuple(
            tuple(piece if (i == r and j == c) else val
                for j, val in enumerate(row))
            for i, row in enumerate(board)
        )


    def _attempt_place(board, piece):
        ret = []
        for i, row in enumerate(board):
            for j, cell in enumerate(row):
                if not cell:
                    copy = _move(board, i, j, piece)
                    ret.append(copy)
        return ret

    if state == XTURN_STATE:
        return _attempt_place(board, X_TOK)
    elif state == OTURN_STATE:
        return _attempt_place(board, O_TOK)
    else: # for whatever reason, there are no continuations from here
        return []

'''
make_states:
    This function returns a list of all possible tic-tac-toe positions.

    We proceed in a breadth-first-search style, with a queue and neighbor function.
'''
def make_states():
    from collections import deque
    q = deque([EMPTY])
    value_map = dict()
    seen = set([EMPTY])
    
    while len(q):
        top = q.popleft()
        state = classify_board(top)
        if state == XWIN_STATE:
            score = { X_TOK: 1, O_TOK: 0} # 1 if we're X, 0 if we're O, obviously
        elif state == OWIN_STATE:
            score = { X_TOK: 0, O_TOK: 1}
        elif state == DRAW_STATE:
            score = { X_TOK: 0, O_TOK: 0} # we never want to draw
        else:
            score = { X_TOK: 0.5, O_TOK: 0.5} # initialize unknown positions to 0.5 for both players

        value_map[top] = score
        neighbors = get_children(top)
        for neighbor in neighbors:
            if neighbor not in seen:
                seen.add(neighbor)
                q.append(neighbor)

    return value_map

    
def print_board(board):
    line = '-------'
    def _printrow(row):
        print(f'|{row[0] or ' '}|{row[1] or ' '}|{row[2] or ' '}|')
        print(line)
    print(line)
    for row in board:
        _printrow(row)
    

'''
play

This method plays a single game between xplayer and oplayer
and reports the result
'''
def play(xplayer, oplayer, verbose=False):
    board = EMPTY
    state = classify_board(board)

    while state in (XTURN_STATE, OTURN_STATE):
        if verbose:
            print_board(board)
            print(state)

        # 1. find possible moves
        moves = get_children(board)
        if state == XTURN_STATE:
            board = xplayer(MOVE_ACTION, (board, moves))
        else:
            board = oplayer(MOVE_ACTION, (board, moves))
        
        state = classify_board(board)

    print_board(board)
    print(state)
    return state

def play_tourney(p1, p2, games=1000):

    x, o = p1, p2
    stats = {
        "p1": 0,
        "p2": 0,
        "x": 0,
        "o": 0,
        "draw": 0
    }
    for game in range(games):

        # signal that the game has started
        # (for stateful agents)
        p1(NEW_GAME_ACTION)
        p2(NEW_GAME_ACTION)

        result = play(x, o)

        # judge
        if result == DRAW_STATE:
            stats["draw"] += 1
            x(END_GAME_ACTION, (X_TOK, 0))
            o(END_GAME_ACTION, (O_TOK, 0))
        elif result == XWIN_STATE:
            stats["x"] += 1
            x(END_GAME_ACTION, (X_TOK, 1))
            o(END_GAME_ACTION, (O_TOK, 0))

            if x == p1:
                stats["p1"] += 1
            else:
                stats["p2"] += 1
        elif result == OWIN_STATE:
            stats["o"] += 1
            x(END_GAME_ACTION, (X_TOK, 0))
            o(END_GAME_ACTION, (O_TOK, 1))

            if o == p1:
                stats["p1"] += 1
            else:
                stats["p2"] += 1
        else:
            raise ValueError("Invalid state: " + result)
        
        # print results
        print(f"#{game + 1}/{games}: {result} | {"p1 = x, p2 = o" if p1 == x else "p1 = o, p2 = x"} | ", stats)

        # switch sides for next game
        x, o = o, x




def random_player(action, data=None):
    # random player can ignore other signals
    if action == MOVE_ACTION:
        from random import choice
        board, moves = data
        return choice(moves)

def rl_player_factory(explore_rate=0.10, decay=0.99999, weights=None):
    # weights 
    if not weights:
        weights = make_states()

    alpha = 0.5
    last_move = None

    def get_internals():
        return {
            'alpha': alpha,
            'weights': weights,
        }
    
    def backup(turn, outcome):
        nonlocal alpha
        # backup outcome to our last move's weights. 
        prev_score = weights[last_move][turn]
        adjusted_prev_score = prev_score + alpha * (outcome - prev_score)
        weights[last_move][turn] = adjusted_prev_score

        # turn down the knob, just a bit.
        alpha *= decay

    def rl_player(action, data=None):
        nonlocal last_move

        if action == NEW_GAME_ACTION:
            last_move = None
        elif action == END_GAME_ACTION:
            turn, outcome = data
            backup(turn, outcome)
        elif action == MOVE_ACTION:
            board, moves = data
            from random import random, choice, shuffle

            exploratory = random() < explore_rate
            if exploratory:
                move = choice(moves)
                last_move = move
                # no backup on exploratory moves

            else:
                state = classify_board(board)
                turn = X_TOK if state == XTURN_STATE else O_TOK

                # 1. pick our move greedily
                move, score = None, -1
                shuffle(moves) # break ties randomly
                for candidate in moves:
                    our_score = weights[candidate][turn]
                    if our_score > score:
                        move = candidate
                        score = our_score

                # 2. backup (since this is not an exploratory move)
                if last_move:
                    cur_score = weights[move][turn]
                    backup(turn, cur_score)

                # 3. Now we are the last move...
                last_move = move

            return move
        
    return rl_player, get_internals



# A wrapper to ensure that player identities 
# are unique.
def fac(player):
    def fn(action, data=None):
        return player(action, data)
    
    return fn

def main():
    states = make_states()
    # for state, value in states.items():
    #     print_board(state)
    #     print(value)
    print("total states: ", len(states))

    agent, get_internals = rl_player_factory(explore_rate=0.4, decay=0.99999)
    agent2, get_internals2 = rl_player_factory(explore_rate=0.4, decay=0.99999)
    rando = fac(random_player)
    # play(agent, rando, verbose=True)


    # play_tourney(rando, agent, 100000)
    play_tourney(agent, agent2, 100000)

    rl_internals = get_internals()
    rl_internals2 = get_internals2()

    sumo = rl_player_factory(weights=rl_internals["weights"], explore_rate=0)[0]
    sumo2 = rl_player_factory(weights=rl_internals2["weights"], explore_rate=0)[0]

    # play_tourney(rando, sumo)
    play_tourney(rando, sumo)

    print(rl_internals["alpha"])
    print(rl_internals2["alpha"])

    # for _ in range(2):
    #     print("sumo vs rando:")
    #     play(sumo, rando, verbose=True)
    #     print("rando vs sumo:")
    #     play(rando, sumo, verbose=True)
    #     print("sumo vs sumo!:")
    #     play(sumo, sumo, verbose=True)



if __name__ == '__main__':
    main()