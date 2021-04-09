# game imports
import pygame
import random
# twitch plays imports
import socket
import threading
import json 
# log files import 
import os
import datetime
import hashlib


# !!!!!!!!!!!!!! LOAD CONFIG !!!!!!!!!!!!!!
with open('config.json', 'r') as myfile:
    data=myfile.read()
configJson = json.loads(data)

LOG_FILE = configJson['TWITCH']["BOT"]["LOGS"]["FOLDER_PATH"]+"/"+str(datetime.datetime.now())+".csv"
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w') as log: 
        log.write("time,username,action,game_number,block_number,block_shape,block_rotation,board_state\n")

# !!!!!!!!!!!!!! SHARED GLOBAL VARS !!!!!!!!!!!!!!
message = ""
user = ""
running_flag = True
# !!!!!!!!!!!!!! TWITCH CHAT BOT !!!!!!!!!!!!!!

SERVER = configJson['TWITCH']['CONNECTION']['SERVER']
PORT = int(configJson['TWITCH']['CONNECTION']['PORT'])

#Your account
OWNER = str(configJson['TWITCH']['ACCOUNT']['NAME'])
#Your OAUTH Code Here https://twitchapps.com/tmi/
PASS = str(configJson['TWITCH']['ACCOUNT']['OAUTH'])

#What you'd like to name your bot
BOT = str(configJson['TWITCH']['BOT']['NAME'])
#The channel you want to monitor
CHANNEL = str(configJson['TWITCH']['BOT']['MONITORING-CHANNEL-NAME'])

irc = socket.socket()

irc.connect((SERVER, PORT))
irc.send((	"PASS " + PASS + "\n" +
			"NICK " + BOT + "\n" +
			"JOIN #" + CHANNEL + "\n").encode())

def twitch():

    global user
    global message
    global running_flag
    

    def joinchat():
        Loading = True
        while Loading:
            readbuffer_join = irc.recv(1024)
            readbuffer_join = readbuffer_join.decode()
            print(readbuffer_join)
            for line in readbuffer_join.split("\n")[0:-1]:
                print(line)
                Loading = loadingComplete(line)

    def loadingComplete(line):
        if("End of /NAMES list" in line):
            print("TwitchBot has joined " + CHANNEL + "'s Channel!")
            sendMessage(irc, "Lets play!\n!!!Controlls!!!\n")
            return False
        else:
            return True

    def sendMessage(irc, message):
        messageTemp = "PRIVMSG #" + CHANNEL + " :" + message
        irc.send((messageTemp + "\n").encode())

    def getUser(line):
        # global user
        colons = line.count(":")
        colonless = colons-1
        separate = line.split(":", colons)
        user = separate[colonless].split("!", 1)[0]
        return user

    def getMessage(line):
        #global message
        try:
            colons = line.count(":")
            message = (line.split(":", colons))[colons]
        except:
            message = ""
        return message

    def console(line):
        if "PRIVMSG" in line:
            return False
        else:
            return True

    joinchat()
    irc.send("CAP REQ :twitch.tv/tags\r\n".encode())
    # TODO:need to end thread on clode
    while running_flag:
        try:
            readbuffer = irc.recv(1024).decode()
        except:
            readbuffer = ""
        for line in readbuffer.split("\r\n"):
            if line == "":
                continue
            if "PING :tmi.twitch.tv" in line:
                print(line)
                msgg = "PONG :tmi.twitch.tv\r\n".encode()
                irc.send(msgg)
                print(msgg)
                continue
            else:
                try:
                    user = getUser(line)
                    message = getMessage(line)
                    print(user + " : " + message)
                except Exception:
                    pass
    print("BOT KILLED")
    return 

# !!!!!!!!!!!!!! GAME !!!!!!!!!!!!!!
pygame.font.init()

# GLOBALS VARS 
s_width = 800
s_height = 700
play_width = 300  # meaning 300 // 10 = 30 width per block
play_height = 600  # meaning 600 // 20 = 30 height per block
block_size = 30

top_left_x = (s_width - play_width) // 2
top_left_y = s_height - play_height

game_count = 1

# score file
score_file = str(configJson["GAME"]["SCORE-FILE"])


# SHAPE FORMATS

S = [['.....',
      '.....',
      '..00.',
      '.00..',
      '.....'],
     ['.....',
      '..0..',
      '..00.',
      '...0.',
      '.....']]

Z = [['.....',
      '.....',
      '.00..',
      '..00.',
      '.....'],
     ['.....',
      '..0..',
      '.00..',
      '.0...',
      '.....']]

I = [['..0..',
      '..0..',
      '..0..',
      '..0..',
      '.....'],
     ['.....',
      '0000.',
      '.....',
      '.....',
      '.....']]

O = [['.....',
      '.....',
      '.00..',
      '.00..',
      '.....']]

J = [['.....',
      '.0...',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..00.',
      '..0..',
      '..0..',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '...0.',
      '.....'],
     ['.....',
      '..0..',
      '..0..',
      '.00..',
      '.....']]

L = [['.....',
      '...0.',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..0..',
      '..0..',
      '..00.',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '.0...',
      '.....'],
     ['.....',
      '.00..',
      '..0..',
      '..0..',
      '.....']]

T = [['.....',
      '..0..',
      '.000.',
      '.....',
      '.....'],
     ['.....',
      '..0..',
      '..00.',
      '..0..',
      '.....'],
     ['.....',
      '.....',
      '.000.',
      '..0..',
      '.....'],
     ['.....',
      '..0..',
      '.00..',
      '..0..',
      '.....']]

shapes = [S, Z, I, O, J, L, T]
shapes_letters = ["S", "Z", "I", "O", "J", "L", "T"]
shape_colors = [(0, 255, 0), (255, 0, 0), (0, 255, 255), (255, 255, 0), (255, 165, 0), (0, 0, 255), (128, 0, 128)]
# index 0 - 6 represent shape


class Piece(object): 
    def __init__(self, x, y, shape):
        self.shape_letter = shapes_letters[shapes.index(shape)]
        self.x = x
        self.y = y
        self.shape = shape
        self.color = shape_colors[shapes.index(shape)]
        self.rotation = 0


def create_grid(locked_pos={}):  # *
    grid = [[(0,0,0) for _ in range(10)] for _ in range(20)]

    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if (j, i) in locked_pos:
                c = locked_pos[(j,i)]
                grid[i][j] = c
    return grid


def convert_shape_format(shape):
    positions = []
    format = shape.shape[shape.rotation % len(shape.shape)]

    for i, line in enumerate(format):
        row = list(line)
        for j, column in enumerate(row):
            if column == '0':
                positions.append((shape.x + j, shape.y + i))

    for i, pos in enumerate(positions):
        positions[i] = (pos[0] - 2, pos[1] - 4)

    return positions


def valid_space(shape, grid):
    accepted_pos = [[(j, i) for j in range(10) if grid[i][j] == (0,0,0)] for i in range(20)]
    accepted_pos = [j for sub in accepted_pos for j in sub]

    formatted = convert_shape_format(shape)

    for pos in formatted:
        if pos not in accepted_pos:
            if pos[1] > -1:
                return False
    return True


def check_lost(positions):
    for pos in positions:
        x, y = pos
        if y < 1:
            return True

    return False


def get_shape():
    return Piece(5, 0, random.choice(shapes))


def draw_text_middle(surface, text, size, color):
    font = pygame.font.SysFont("comicsans", size, bold=True)
    label = font.render(text, 1, color)

    surface.blit(label, (top_left_x + play_width /2 - (label.get_width()/2), top_left_y + play_height/2 - label.get_height()/2))


def draw_grid(surface, grid):
    sx = top_left_x
    sy = top_left_y

    for i in range(len(grid)):
        pygame.draw.line(surface, (128,128,128), (sx, sy + i*block_size), (sx+play_width, sy+ i*block_size))
        for j in range(len(grid[i])):
            pygame.draw.line(surface, (128, 128, 128), (sx + j*block_size, sy),(sx + j*block_size, sy + play_height))


def clear_rows(grid, locked):

    inc = 0
    for i in range(len(grid)-1, -1, -1):
        row = grid[i]
        if (0,0,0) not in row:
            inc += 1
            ind = i
            for j in range(len(row)):
                try:
                    del locked[(j,i)]
                except:
                    continue

    if inc > 0:
        for key in sorted(list(locked), key=lambda x: x[1])[::-1]:
            x, y = key
            if y < ind:
                newKey = (x, y + inc)
                locked[newKey] = locked.pop(key)

    return inc


def draw_next_shape(shape, surface):
    font = pygame.font.SysFont('comicsans', 30)
    label = font.render('Next Shape', 1, (255,255,255))

    sx = top_left_x + play_width + 50
    sy = top_left_y + play_height/2 - 100
    format = shape.shape[shape.rotation % len(shape.shape)]

    for i, line in enumerate(format):
        row = list(line)
        for j, column in enumerate(row):
            if column == '0':
                pygame.draw.rect(surface, shape.color, (sx + j*block_size, sy + i*block_size, block_size, block_size), 0)

    surface.blit(label, (sx + 10, sy - 30))


def update_score(nscore):
    score = max_score()

    with open(score_file, 'w') as f:
        if int(score) > nscore:
            f.write(str(score))
        else:
            f.write(str(nscore))


def max_score():
    with open(score_file, 'r') as f:
        lines = f.readlines()
        score = lines[0].strip()

    return score


def draw_window(surface, grid, score=0, last_score = 0):
    surface.fill((0, 0, 0))

    pygame.font.init()
    font = pygame.font.SysFont('comicsans', 60)
    label = font.render('Tetris', 1, (255, 255, 255))

    surface.blit(label, (top_left_x + play_width / 2 - (label.get_width() / 2), 30))

    # current score
    font = pygame.font.SysFont('comicsans', 30)
    label = font.render('Score: ' + str(score), 1, (255,255,255))

    sx = top_left_x + play_width + 50
    sy = top_left_y + play_height/2 - 100

    surface.blit(label, (sx + 20, sy + 160))
    # last score
    label = font.render('High Score: ' + last_score, 1, (255,255,255))

    sx = top_left_x - 200
    sy = top_left_y + 200

    surface.blit(label, (sx + 20, sy + 160))

    for i in range(len(grid)):
        for j in range(len(grid[i])):
            pygame.draw.rect(surface, grid[i][j], (top_left_x + j*block_size, top_left_y + i*block_size, block_size, block_size), 0)

    pygame.draw.rect(surface, (255, 0, 0), (top_left_x, top_left_y, play_width, play_height), 5)

    draw_grid(surface, grid)
    #pygame.display.update()



def game(win): 

    global message
    global user
    global running_flag
    global game_count
    last_score = max_score()
    locked_positions = {}
    grid = create_grid(locked_positions)

    change_piece = False
    piece_count = 1

    run = True
    current_piece = get_shape()
    next_piece = get_shape()
    clock = pygame.time.Clock()
    fall_time = 0
    fall_speed = 0.27 * 2
    level_time = 0
    score = 0

    while run:
        grid = create_grid(locked_positions)
        fall_time += clock.get_rawtime()
        level_time += clock.get_rawtime()
        clock.tick()

        if level_time/1000 > 5:
            level_time = 0
            if level_time > 0.12:
                level_time -= 0.005

        if fall_time/1000 > fall_speed:
            fall_time = 0
            current_piece.y += 1
            if not(valid_space(current_piece, grid)) and current_piece.y > 0:
                current_piece.y -= 1
                change_piece = True

                

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                running_flag = False
                pygame.display.quit()
            # TODO:Chanage key press to twitch chat
        if "up" == message.lower():
            current_piece.rotation += 1
        elif not(valid_space(current_piece, grid)):
            current_piece.rotation -= 1
        elif "down" == message.lower():
            current_piece.y += 1
            if not(valid_space(current_piece, grid)):
                current_piece.y -= 1
        elif "right" == message.lower():
            current_piece.x += 1
            if not(valid_space(current_piece, grid)):
                current_piece.x -= 1
        elif "left" == message.lower():
            current_piece.x -= 1
            if not(valid_space(current_piece, grid)):
                current_piece.x += 1
        else: 
            # not a valed comand
            pass

        # log action  TODO:Might need to move
        if(message != "" and user != ""): 
            logAction(user, 
                message, 
                game_count, 
                piece_count, 
                current_piece.shape_letter,
                current_piece.rotation,
                grid)


        message = ""
        shape_pos = convert_shape_format(current_piece)

        for i in range(len(shape_pos)):
            x, y = shape_pos[i]
            if y > -1:
                grid[y][x] = current_piece.color

        if change_piece:
            for pos in shape_pos:
                p = (pos[0], pos[1])
                locked_positions[p] = current_piece.color
            current_piece = next_piece
            next_piece = get_shape()
            change_piece = False
            piece_count = piece_count+1
            score += clear_rows(grid, locked_positions) * 10

        draw_window(win, grid, score, last_score)
        draw_next_shape(next_piece, win)
        pygame.display.update()

        # TODO: update csv here with new move

        if check_lost(locked_positions):
            draw_text_middle(win, "YOU LOST!", 80, (255,255,255))
            game_count = game_count + 1
            pygame.display.update()
            pygame.time.delay(1500)
            run = False
            update_score(score)

def logAction(username, action, game_number, block_number, block_shape_letter, block_rotation, grid):
    with open(LOG_FILE, 'a') as log: 
            log.write("{0},{1},{2},{3},{4},{5},{6},{7}\n".format(
                str(datetime.datetime.now()), 
                username,
                action,
                game_number,
                block_number,
                block_shape_letter,
                block_rotation, 
                grid))

def main_menu():
    global running_flag
    run = True
    while run:
        win = pygame.display.set_mode((s_width, s_height))
        pygame.display.set_caption('Tetris')
        win.fill((0,0,0))
        draw_text_middle(win, 'Press Any Key To Play', 60, (255,255,255))
        pygame.display.update()

        twitch_chat_bot = threading.Thread(target = twitch)
        twitch_chat_bot.start()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                running_flag = False
            else:
                game(win)
    running_flag = False

    pygame.display.quit()

# !!!!!!!!!!!!!! MAIN !!!!!!!!!!!!!!

def main():
    if __name__ =='__main__':
        global running_flag
        try: 
            main_menu()
            running_flag = False
        except:
            running_flag = False
main()
