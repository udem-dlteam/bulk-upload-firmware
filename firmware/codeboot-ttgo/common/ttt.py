import ttgo as dev
import net
import mate
import apps
import ui
import random

max_rounds = 4  # maximum number of rounds to play

size = 0  # width/height of tic-tac-toe grid in number of cells, set later

X = 1  # code for player X
O = 2  # code for player O

syms      = ['X', 'O']        # symbols for each player
player_fg = ['#D00', '#0A0']  # foreground colors for mate and me
player_bg = ['#FCC', '#CFC']  # background colors for mate and me

bg = '#000'  # general background color

cell_bg      = '#FF0'  # cell background color
cell_spacing = 2       # spacing between cells
cell_size    = 0       # size of a cell (width/height), set later
cell_step    = 0       # cell_size+cell_spacing, set later

grid_x = 4 # screen position of grid
grid_y = grid_x + (dev.screen_height - min(dev.screen_width, dev.screen_height)) // 2

# game state

grid     = []    # state of all the cells (0=empty, 1=X, 2=O), set later
occupied = 0     # number of non-empty cells, set later
scores   = []    # score of mate and me, set later
rounds   = 0     # number of rounds played, set later
me       = None  # am I X or O?, set later

# the following global variables are useful for the networked version

networked   = False  # are we playing over the network?
random_seed = 0      # to get same random order on both nodes, set later
msg_type    = None   # type of the messages sent between the nodes, set later
ping_timer  = 0      # used to check that the mate is still with us

def quit():  # called to quit the game
    if networked:
        net.send(mate.id, [msg_type, 'quit'])
    leave()

def leave():
    if networked:
        net.pop_handler()  # remove message_handler
    apps.menu()

def current_player():  # returns the current player (X=1, O=2)
    return occupied % 2 + 1  # player X is always first to go

def get_alignment():

    # returns the list of positions where there are aligned symbols
    # or None when there is no alignment

    def check_alignment(i, step):
        player = grid[i]
        if player != 0:
            alignment = [i]
            for y in range(1, size):
                i += step
                if grid[i] != player:
                    break
                alignment.append(i)
            else:
                return alignment
        return None

    # check columns
    for x in range(size):
        a = check_alignment(x, size)
        if a is not None: return a

    # check rows
    for y in range(size):
        a = check_alignment(y*size, 1)
        if a is not None: return a

    # check diagonals
    return check_alignment(0, size+1) or check_alignment(size-1, size-1)

def game_over():
    if rounds == max_rounds: return True
    # score difference less than number of rounds left to play?
    return max_rounds - rounds < abs(scores[0] - scores[1])

def draw_player_status(player):
    score = scores[player==me]
    fg = player_fg[player==me]
    if player == current_player() or (game_over() and score >= scores[player!=me]):
        bg2 = player_bg[player==me]
    else:
        bg2 = bg
    side = -1 if player == me else +1
    lines = []
    if networked:
        lines.append(net.id if player == me else mate.id)
    if not game_over():
        lines.append(syms[player-1])
    if rounds > 0:
        lines.append(str(score) + '/' + str(rounds))
        if game_over():
            if scores[player==me] > scores[player!=me]:
                lines.append('\x10WINNER\x11')
            elif scores[player==me] < scores[player!=me]:
                lines.append('LOSER')
            else:
                lines.append('\x10\x10DRAW\x11\x11')
    ui.draw_status(lines, side, fg, bg2)

def draw_status():
    draw_player_status(X)
    draw_player_status(O)

def draw_cell(i, bg):
    x = (i % size) * cell_step + grid_x
    y = (i // size)  * cell_step + grid_y
    dev.fill_rect(x, y, cell_size, cell_size, bg)
    p = grid[i]
    if p != 0:
        ui.center(x + cell_size//2, y + cell_size//2, syms[p-1], player_fg[p==me], bg)

def draw_selection(bg):
    draw_cell(selection, bg)

def draw_grid():
    for i in range(size**2):
        draw_cell(i, cell_bg)

def init_game():
    global cell_size, cell_step, me, rounds, scores

    cell_size = (min(dev.screen_width, dev.screen_height)-2*grid_x-(size-1)*cell_spacing) // size
    cell_step = cell_size + cell_spacing

    me = None
    rounds = 0
    scores = [0, 0]

    dev.clear_screen(bg)

    x = dev.screen_width//2
    y = 0
    ui.center(x, y+dev.font_height*1, 'BEST OF', '#FFF', bg)
    ui.center(x, y+dev.font_height*3, str(max_rounds), '#FFF', bg)
    ui.center(x, y+dev.font_height*10, 'QUIT =', '#FFF', bg)
    ui.center(x, y+dev.font_height*11, 'PUSH', '#FFF', bg)
    ui.center(x, y+dev.font_height*12, 'BOTH', '#FFF', bg)
    ui.center(x, y+dev.font_height*13, 'BUTTONS', '#FFF', bg)

    init_round()

def init_round():
    global grid, occupied

    grid = [0] * size**2  # start with empty grid
    occupied = 0

def move_selection(direction):
    if occupied < len(grid):
        repeat = True
        i = selection
        while repeat:
            i = (i + direction) % len(grid)
            repeat = grid[i] != 0
        set_selection(i)

def set_selection(i):
    global selection
    draw_selection(cell_bg)
    selection = i
    player = current_player()
    draw_selection(player_bg[player==me])
    if networked and player == me:
        net.send(mate.id, [msg_type, 'set_selection', selection])

def play_at_selection():
    global occupied
    player = current_player()
    if networked and player == me:
        net.send(mate.id, [msg_type, 'play_at_selection'])
    grid[selection] = player
    alignment = get_alignment()
    if alignment is None:
        occupied += 1
        move_selection(+1)
        draw_status()
        if occupied < len(grid):
            select_cell()
        else:
            dev.after(1, end_of_round)
    else:
        for i in alignment:
            draw_cell(i, player_bg[player==me])
        dev.after(1, victory)

def victory():
    player = current_player()
    scores[player==me] += 1
    end_of_round()

def end_of_round():
    global rounds, me
    rounds += 1
    if game_over():
        draw_status()  # show how game ended (win/lose/draw)
        dev.after(3, quit)  # quit the game after 3 sec
    else:
        me = 3 - me  # alternate between X and O
        start_round()

def button_handler(event, resume):
    global ping_timer
    player = current_player()
    if event == 'left_down' or event == 'right_down':
        resume()
    elif event == 'left_up' or event == 'right_up':
        move_selection(-1 if event == 'left_up' else +1)
        resume()
    elif event == 'left_ok' or event == 'right_ok':
        play_at_selection()
    elif event == 'cancel':
        quit()
    elif event == 'tick':
        if networked:
            ping_timer -= 1
            if ping_timer < 0:
                ping_timer = int(2 / ui.time_delta)  # send ping every 2 secs
                net.send(mate.id, [msg_type, 'ping'])
        dev.after(ui.time_delta, resume) # need to wait...

def select_cell():
    if occupied < len(grid)-1:  # at least 2 cells are empty?
        if not networked or current_player() == me:
            ui.when_buttons_released(select_cell_using_buttons)
    else:
        play_at_selection()  # force playing at empty cell

def select_cell_using_buttons():
    ui.track_button_presses(button_handler)

def start_game():
    dev.after(3, start_round_after_clearing_screen)

def start_round_after_clearing_screen():
    dev.clear_screen(bg)
    start_round()

def start_round():
    global selection
    init_round()
    selection = len(grid) // 2
    draw_grid()
    draw_status()
    player = current_player()
    draw_selection(player_bg[player==me])
    select_cell()

def ttt_non_networked():
    global me
    init_game()
    me = X
    start_game()

# The following functions are used when playing the game over the network

def master():  # the master is the node with the smallest id
    return net.id < mate.id

def message_handler(peer, msg):
    global me
    if peer is None:
        if msg == 'found_mate':
            found_mate()
        else:
            print('#####', peer, msg)  # ignore other messages from system
    elif type(msg) is list and msg[0] == msg_type:
        if me == None:
            random.seed(random_seed ^ msg[1])  # set same RNG on both nodes
            # if 2 random bits are equal, master is the active player
            me = X if master() is (random.randrange(2) == 0) else O
            start_game()
        elif current_player() == me:
            # active player received a message
            print('active got', msg)
        else:
            # passive player received a message
            if msg[1] == 'set_selection':
                set_selection(int(msg[2]))
            elif msg[1] == 'play_at_selection':
                play_at_selection()
            elif msg[1] == 'quit':
                leave()
            else:
                print('passive got', msg)

def found_mate():
    global random_seed

    init_game()

    # exchange random seeds so both nodes have the same RNG
    random_seed = random.randrange(0x1000000)
    net.send(mate.id, [msg_type, random_seed])

def ttt_networked():
    global msg_type
    msg_type = 'TTT' + str(size) + 'NET'
    mate.find(msg_type, message_handler)

def ttt(s, n):
    global size, networked
    size = s
    networked = n
    if networked:
        ttt_networked()
    else:
        ttt_non_networked()

apps.register('TTT3', lambda: ttt(3, False), False)
apps.register('TTT4', lambda: ttt(4, False), False)

apps.register('TTT3NET', lambda: ttt(3, True), True)
apps.register('TTT4NET', lambda: ttt(4, True), True)
