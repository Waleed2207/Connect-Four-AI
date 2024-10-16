"""
    By: Waleed Younis
"""
import numpy as np
import random
import socket
import threading
import time
import pickle
import sys

"""Define constants """
server_host = '127.0.0.1'  #
server_port = 60000 # port
server_address = (server_host, server_port)  # server address tuple

# list of all the clients, One-On-One games
clients = []

def connect_4_in_a_row_start(conn, add, thread = threading.current_thread()):
    # get the client input
    opponent, level, rounds = get_client_input(conn, add)
    if opponent != 'AI' and opponent != 'PLAYER':
        return
    elif opponent == 'PLAYER':
        One_to_One_game(conn, add, thread)
    
    moves_counter = 0
    victories_counter1 = 0
    victories_counter2 = 0
    max_steps_game = 0
    victories_num = rounds

    while rounds > 0:
        game_over = 0
        # initialize the game
        board = initialize_board()
        turn = 1
        # send the initial board
        send_board_to_client(conn, board)
        # start the game
        while game_over == 0:
            if turn == 1:
                # player's turn
                board, victories_counter1, game_over = player_turn(conn, board, victories_counter1)
                moves_counter += 1
                turn = 2
                send_board_to_client(conn, board)
                time.sleep(0.1)
            else:
                # computer's turn
                board, victories_counter2, game_over = computer_turn(conn, board, level, victories_counter2)
                moves_counter += 1
                turn = 1
                send_board_to_client(conn, board)
                time.sleep(0.1)
            # send game over flag to the client
            conn.send(str(game_over).encode('utf-8'))
            time.sleep(0.1)
            if moves_counter > max_steps_game:
                max_steps_game = moves_counter            
        # round summary
        rounds -= 1
        round_summary(conn, board, moves_counter, victories_counter1, victories_counter2, victories_num)
        time.sleep(0.5)
    # game over summary
    game_over_summary(conn, victories_counter1, victories_counter2, max_steps_game)
    time.sleep(0.5)
    thread.join()


def One_to_One_game(conn, add, thread = threading.current_thread()):
    if len(clients) == 0:
        clients.append(conn)
        print('Waiting for another player to join...')
        thread.join()    
    else:
        client_1 = clients.pop()
        client_2 = conn        
        # send a players address to each other
        client_1.send(str(add).encode('utf-8'))
        client_2.send(str(add).encode('utf-8'))
        time.sleep(0.1)
        # give turns to the players
        turn = 1
        client_1.send('1'.encode('utf-8'))
        client_2.send('0'.encode('utf-8'))
        time.sleep(0.1)
        # palyers parameters
        moves_counter = 0
        victories_counter1 = 0
        victories_counter2 = 0
        max_steps_game = 0
        victories_num = 1 # only one round in One-On-One game, unless the players want to play again        
        this_rounds = 1
        # initialize the game
        while this_rounds > 0:
            game_over = 0
            board = initialize_board()
            # send the initial board
            send_board_to_client(client_1, board)
            send_board_to_client(client_2, board)
            # start the game
            while game_over == 0:
                if turn == 1:
                    # player's turn
                    board, victories_counter1, game_over = player_turn(client_1, board, victories_counter1, 1)
                    moves_counter += 1
                    turn = 0
                    send_board_to_client(client_1, board)
                    send_board_to_client(client_2, board)
                    time.sleep(0.1)
                else:
                    # player's turn
                    board, victories_counter2, game_over = player_turn(client_2, board, victories_counter2, 2)
                    moves_counter += 1
                    turn = 1
                    send_board_to_client(client_1, board)
                    send_board_to_client(client_2, board)
                    time.sleep(0.1)
                # send game over flag to the clients
                client_1.send(str(game_over).encode('utf-8'))
                client_2.send(str(game_over).encode('utf-8'))
                time.sleep(0.1)
                if moves_counter > max_steps_game:
                    max_steps_game = moves_counter
            # round summary
            this_rounds -= 1
            round_summary(client_1, board, moves_counter, victories_counter1, victories_counter2, victories_num)
            round_summary(client_2, board, moves_counter, victories_counter1, victories_counter2, victories_num)
            time.sleep(0.5)
            # ask if they want to play again
            play = client_1.recv(1024).decode('utf-8')
            play = client_2.recv(1024).decode('utf-8')
            if play == 'YES':
                this_rounds = 1
                victories_num += 1
            # send the play again flag to the clients
            client_1.send(play.encode('utf-8'))
            client_2.send(play.encode('utf-8'))
            time.sleep(0.1)
        # game over summary
        game_over_summary(client_1, victories_counter1, victories_counter2, max_steps_game)
        game_over_summary(client_2, victories_counter1, victories_counter2, max_steps_game)
        time.sleep(0.5)
        thread.join()


def get_client_input(conn, address):
    print('[CONNECTED] Client' + str(address) + ' has connected')
    if conn.recv(1024).decode('utf-8') == 'YES':
        # get opponent
        opponent = conn.recv(1024).decode('utf-8')
        if opponent == 'AI':
            # get the level of difficulty
            level = conn.recv(1024).decode('utf-8')
            # get the number of rounds
            rounds = int(conn.recv(1024).decode('utf-8'))
            return opponent, level, rounds
        else:        
            return opponent, 'EASY', 1
    else:
        print('player' + str(address) + ' does not want to play')
        print('[DISCONNECTED] Client' + str(address) + ' has disconnected')
        conn.close()
        return 'NO', 'EASY', 0

def is_column_available(board, column):  # Check if the column is available for placing a token
    return board[5][column] == 0


def find_next_available_row(board, column):  # Find the first available row in the given column
    for i in range(6):
        if board[i][column] == 0:
            return i
    return -1

# hard mode functions
def is_column_of_3(board):  # Check if there's a column with three consecutive tokens for the computer
    for column in range(7):  # Iterate over all columns
        for row in range(3):  # Iterate over all rows
            if board[row][column] == 2 and board[row + 1][column] == 2 and board[row + 2][column] == 2 and board[row + 3][column] == 0:
                return column  # Return the column where the computer can connect four
    return -1



def connect_3_in_column(board):   # Check if there's a possibility to create 3 tokens in a column
    # Check each column
    for column in range(7):  # Iterate over all columns
        for row in range(3):  # Iterate over all rows
            if board[row][column] == 2 and board[row + 1][column] == 2 and board[row + 2][column] == 0:
                return column  # Return the column where 3 tokens can be connected
    return -1


def connect_3_in_row(board):   # Check if there's a possibility to create 3 tokens in a row
    # Check each row
    for row in range(6):  # Iterate over all rows
        for column in range(4):  # Iterate over all columns
            if board[row][column] == 2 and board[row][column + 1] == 2 and board[row][column + 2] == 0 \
                    and board[row][column + 3] == 0:
                return column + 2
    return -1


def block_winning_column(board):   # Check if there's a need to block the opponent's potential winning column
    # Check each column
    for column in range(7):  # Iterate over all columns
        for row in range(3):  # Iterate over all rows
            if board[row][column] == 1 and board[row + 1][column] == 1 and board[row + 2][column] == 1 \
                    and board[row + 3][column] == 0:
                return column  # Return the column to block the opponent's winning move
    return -1


def block_winning_row(board):   # Check if there's a need to block the opponent's potential winning row
    # Check each row
    for row in range(6):  # Iterate over all rows
        for column in range(4):  # Iterate over all columns
            if row == 0:
                if board[row][column] == 1 and board[row][column + 1] == 1 and board[row][column + 2] == 1 \
                        and board[row][column + 3] == 0:
                    return column + 3
            else:
                if board[row][column] == 1 and board[row][column + 1] == 1 and board[row][column + 2] == 1 \
                        and board[row][column + 3] == 0 and board[row - 1][column + 3] != 0:
                    return column + 3

    for row in range(6):  # Iterate over all rows
        for column in range(4):  # Iterate over all columns
            if row == 0:
                if board[row][column] == 0 and board[row][column + 1] == 1 and board[row][column + 2] == 1 \
                        and board[row][column + 3] == 1:
                    return column
            else:
                if board[row][column] == 0 and board[row][column + 1] == 1 and board[row][column + 2] == 1 \
                        and board[row][column + 3] == 1 and board[row - 1][column] != 0:
                    return column

    for row in range(6):  # Iterate over all rows
        for column in range(4):  # Iterate over all columns
            if row == 0:
                if board[row][column] == 1 and board[row][column + 1] == 0 and board[row][column + 2] == 1 \
                        and board[row][column + 3] == 1:
                    return column + 1
            else:
                if board[row][column] == 1 and board[row][column + 1] == 0 and board[row][column + 2] == 1 \
                        and board[row][column + 3] == 1 and board[row - 1][column + 1] != 0:
                    return column + 1

    for row in range(6):  # Iterate over all rows
        for column in range(4):  # Iterate over all columns
            if row == 0:
                if board[row][column] == 1 and board[row][column + 1] == 1 and board[row][column + 2] == 0 \
                        and board[row][column + 3] == 1:
                    return column + 2
            else:
                if board[row][column] == 1 and board[row][column + 1] == 1 and board[row][column + 2] == 0 \
                        and board[row][column + 3] == 1 and board[row - 1][column + 2] != 0:
                    return column + 2
    return -1

def is_row_of_3(board):   # Check if there's a possibility to create 3 tokens in a row
    # Check each row
    for i in range(4):  # Iterate over all starting positions of columns
        for j in range(6):  # Iterate over all rows
            if board[j][i] == 2 and board[j][i + 1] == 2 and board[j][i + 2] == 2 and \
                    board[j][i + 3] == 0:
                return i + 3  # Return the column where 3 tokens can be connected
    for i in range(4):  # Iterate over all starting positions of columns
        for j in range(6):  # Iterate over all rows
            if board[j][i] == 0 and board[j][i + 1] == 2 and board[j][i + 2] == 2 and \
                    board[j][i + 3] == 2:
                return i  # Return the column where the fourth token should be placed
    for i in range(4):  # Iterate over all starting positions of columns
        for j in range(6):  # Iterate over all rows
            if board[j][i] == 2 and board[j][i + 1] == 0 and board[j][i + 2] == 2 and \
                    board[j][i + 3] == 2:
                return i + 1  # Return the column where the fourth token should be placed
    for i in range(4):  # Iterate over all starting positions of columns
        for j in range(6):  # Iterate over all rows
            if board[j][i] == 2 and board[j][i + 1] == 2 and board[j][i + 2] == 0 and \
                    board[j][i + 3] == 2:
                return i + 2  # Return the column where the fourth token should be placed
    return -1  # If a row of 3 tokens cannot be completed, return -1


def server_ai_move(board): # all moves of computer
    # col = -1
    col = is_column_of_3(board)
    if col != -1:
        return col
    col = is_row_of_3(board)
    if col != -1:
        return col
    col = block_winning_column(board)
    if col != -1:
        return col
    col = block_winning_row(board)
    if col != -1:
        return col
    col = connect_3_in_column(board)
    if col != -1:
        return col
    col = connect_3_in_row(board)
    if col != -1:
        return col
    col = random.randint(0, 6)
    return col


def is_winner_exist(board, peice): # Check if there's a winner for the given peice token
    # Check rows
    for i in range(4):  # Iterate over all starting positions of columns
        for j in range(6):  # Iterate over all rows
            if board[j][i] == peice and board[j][i + 1] == peice and board[j][i + 2] == peice and \
                    board[j][i + 3] == peice:
                return True  # Return True if there's a winning row

    # Check columns
    for i in range(7):  # Iterate over all starting positions of columns
        for j in range(3):  # Iterate over all rows
            if board[j][i] == peice and board[j + 1][i] == peice and board[j + 2][i] == peice and \
                    board[j + 3][i] == peice:
                return True  # Return True if there's a winning column

    # Check diagonals
    # Diagonal from top-left to bottom-right
    for i in range(4):  # Iterate over all starting positions of columns
        for j in range(3):  # Iterate over all rows
            if board[j][i] == peice and board[j + 1][i + 1] == peice and board[j + 2][i + 2] == peice and \
                    board[j + 3][i + 3] == peice:
                return True  # Return True if there's a winning diagonal

    # Diagonal from bottom-left to top-right
    for i in range(4):  # Iterate over all starting positions of columns
        for j in range(3, 6):  # Iterate over all rows
            if board[j][i] == peice and board[j - 1][i + 1] == peice and board[j - 2][i + 2] == peice and \
                    board[j - 3][i + 3] == peice:
                return True  # Return True if there's a winning diagonal

    return False  # Return False if there's no winner



# Connect 4 in a row game algorithm
def initialize_board():
    return np.zeros((6, 7))

def send_board_to_client(conn, board):
    conn.send(pickle.dumps(board))

def player_turn(conn, board, victories_counter, player = 1):
    col = int(conn.recv(1024).decode('utf-8'))
    if is_column_available(board, col):
        row = find_next_available_row(board, col)
        board[row][col] = player
        if is_winner_exist(board, player):
            victories_counter += 1
            game_over = 1
            return board, victories_counter, game_over
    return board, victories_counter, 0

def computer_turn(conn, board, ai_level, victories_counter2):
    game_over = 0
    if ai_level == 'EASY':
        col = random.randint(0, 6)
    else:
        col = server_ai_move(board)
    if is_column_available(board, col):
        row = find_next_available_row(board, col)
        board[row][col] = 2
        if is_winner_exist(board, 2):
            victories_counter2 += 1
            game_over = 1
            return board, victories_counter2, game_over
    
    return board, victories_counter2, game_over


def round_summary(conn, board, moves_counter, victories_counter1, victories_counter2, victories_num):
    print("\nSTATUS OF THE GAME:\n")
    message = "\nSTATUS OF THE GAME:\n"
    time.sleep(0.5)
    conn.send(message.encode('utf-8'))
    time.sleep(0.2)

    print("This round took ", moves_counter, "moves")
    message = "This round took " + str(moves_counter) + "moves"
    conn.send(message.encode('utf-8'))
    time.sleep(0.2)

    print("Player 1 Victories: ", victories_counter1)
    message = "Player 1 Victories: " + str(victories_counter1)
    conn.send(message.encode('utf-8'))
    time.sleep(0.2)

    print("Player 2 Victories: ", victories_counter2)
    message = "Player 2 Victories: " + str(victories_counter2)
    conn.send(message.encode('utf-8'))
    time.sleep(0.2)

    if victories_counter1 > victories_counter2:
        leading_player = "Advance player: player 1\nplayer 1 will need " + str(victories_num - victories_counter1) + " more victories to win\n"
    elif victories_counter1 < victories_counter2:
        leading_player = "Advance player: player 2\nplayer 2 will need " + str(victories_num - victories_counter2) + " more victories to win\n"
    else:
        leading_player = "There's a tie! You both need " + str(victories_num - victories_counter2) + " more victories to win\n"
    print(leading_player)
    conn.send(leading_player.encode('utf-8'))
    time.sleep(0.2)

def game_over_summary(conn, victories_counter1, victories_counter2, max_steps_game):
    print("\nGAME OVER!")
    time.sleep(0.5)

    if victories_counter1 > victories_counter2:
        winner = "The winner is: player 1!!!"
    elif victories_counter1 < victories_counter2:
        winner = "The winner is: player 2!!!"
    else:
        winner = "It's a tie!"
    print(winner)
    conn.send(winner.encode('utf-8'))
    time.sleep(0.2)

    message = "Summary of the game:\nTotal victories of player 1: " + str(victories_counter1) + "\nTotal victories of player 2: " + str(victories_counter2) + "\nThe longest game took: " + str(max_steps_game) + " moves\nTotal rounds in the game: " + str(victories_counter1 + victories_counter2)
    conn.send(message.encode('utf-8'))
    print(message)


def start_game_server(server_socket):
    server_socket.bind(server_address)  

    server_socket.listen()  # Server is open for connections    
    print("Server is waiting for connections...")
    while True:
        connection, address = server_socket.accept()  # Waiting for client to connect to server (blocking call)
        
        if threading.active_count() > 5:            
            connection.send(str(0).encode('utf-8'))  # Send a flag to the client indicating server overload
            print("Server is busy. Please try again later.")
        else:
            print("Server is connected to: ", address)
            connection.send(str(1).encode('utf-8'))  # Send the number of active threads to the client            
            thread = threading.Thread(target=connect_4_in_a_row_start, args=(connection, address, threading.current_thread()))
            thread.start()  # Start the thread

# Main
if __name__ == '__main__':

    if len(sys.argv) != 3: # ip and port
        print("Usage:", sys.argv[0], "<host> <port>")
        sys.exit(1)

    server_host = sys.argv[1]
    server_port = int(sys.argv[2])

    IP = socket.gethostbyname(socket.gethostname())  # finding your current IP address
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Opening Server socket

    print("Server is running on: ", (IP, server_port))
    start_game_server(server_socket=server_socket)
    print("Server is closing...")
