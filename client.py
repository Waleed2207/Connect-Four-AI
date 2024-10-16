"""
    By: Waleed Younis
"""

import socket
import time
import pickle
import numpy as np
import sys

host = '127.0.0.1'  # server ip
port = 60000  # server port
server_address = (host, port) # server address tuple


def start_client(socket):
    socket.connect(server_address)  # Connecting to server's socket

    # get the server acceptence of the connection
    server_accept = int(socket.recv(1024).decode('utf-8'))
    if server_accept == 1:
        # server accepted the connection
        print("Server accepted the connection, game starts soon!")
        
        # check if the player wants to play
        while True:
            will_play = input('Do you want to play? (yes/no): ').upper().strip()
            if will_play == 'YES' or will_play == 'NO':
                break
            else:
                print('Invalid input, Enter yes or no')

        socket.send(will_play.encode('utf-8'))
        if will_play == 'YES':
            # player wants to play, ask hime about the apponent
            while True:
                apponent = input('Who do you want to play with (AI/Player): ').upper().strip()
                if apponent == 'AI' or apponent == 'PLAYER':
                    break
                else:
                    print('Invalid input, Enter AI or Player')
                
            # send the apponent to the server
            socket.send(apponent.encode('utf-8'))
            if apponent == 'AI':
                # choose the difficulty level
                while True:
                    level = input('Choose the difficulty level (easy/hard): ').upper().strip()
                    if level == 'EASY' or level == 'HARD':
                        break
                    else:
                        print('Invalid input, Enter easy or hard')
                
                # send the level to the server
                socket.send(level.encode('utf-8'))
                # ask the user about the number of rounds
                while True:
                    rounds = int(input('Enter the number of rounds you want: '))
                    if rounds > 0:
                        break
                    else:
                        print('Invalid input, Enter a number greater than 0')
                # send the number of rounds to the server
                socket.send(str(rounds).encode('utf-8'))
                # start the game
                play_against_AI(socket, rounds)
            else:
                # player wants to play with another player
                print('Waiting for another player to join...')
                # wait for the other player to join
                player2 = socket.recv(1024).decode('utf-8')
                print(f'Player {player2} joined the game')
                print('Game starts soon!')
                # start the game
                play_One_to_One(socket)
        else:
            print('Goodbye:)! See you soon')
    else:
        print('Server is busy right now, try again later!')
    
 
def receive_round_summary(conn):
    print('The summary of the round:')
    for i in range(5):
        print(conn.recv(1024).decode('utf-8'))
    
def receive_game_summary(conn):
    print('The summary of the game:')
    for i in range(2):
        print(conn.recv(1024).decode('utf-8'))


def play_One_to_One(conn):
    # get my turn from the server
    turn = int(conn.recv(1024).decode('utf-8'))    
    game_over = 0
    this_round = 1
    round_num = this_round

    while this_round > 0:
        print (f'Round {round_num}')
        # get the initial board
        board = conn.recv(1024)
        board = pickle.loads(board)
        print(np.flip(board, 0))
        while game_over == 0:
            if turn == 1:
                print()
                col = int(input('make your move (0-6): '))
                conn.send(str(col).encode('utf-8'))
                turn = 2
                # receive the board after the move
                board = pickle.loads(conn.recv(1024))
                print(np.flip(board, 0))
            else:
                print()
                print('wait for opponent move!')
                turn = 1
                # receive the board after the move
                board = pickle.loads(conn.recv(1024))
                print(np.flip(board, 0))
            game_over = int(conn.recv(1024).decode('utf-8'))
        receive_round_summary(conn)
        this_round -= 1
        play = input('Do you want to play another round? (yes/no): ').upper().strip()
        conn.send(play.encode('utf-8'))
        play = conn.recv(1024).decode('utf-8')
        if play == 'YES':
            this_round = 1
            round_num += 1
            game_over = 0
        
    receive_game_summary(conn)


def play_against_AI(conn, rounds):
    turn = 1
    game_over = 0
    this_round = 1

    while this_round <= rounds:
        print(f'Round {this_round}')
        # get the initial board
        board = conn.recv(1024)
        board = pickle.loads(board)
        print(np.flip(board, 0))
        turn = 1
        while game_over == 0:
            if turn == 1:
                col = int(input('make your move (0-6): '))
                conn.send(str(col).encode('utf-8'))
                turn = 2
                # receive the board after the move
                board = pickle.loads(conn.recv(1024))
                print(np.flip(board, 0))
            else:
                print('AI is making a move...')
                # receive the board after the move
                board = pickle.loads(conn.recv(1024))
                print(np.flip(board, 0))
                turn = 1
            game_over = int(conn.recv(1024).decode('utf-8'))
        receive_round_summary(conn)
        this_round += 1
        game_over = 0
    receive_game_summary(conn)

if __name__ == "__main__":

    if len(sys.argv) != 3: # ip and port
        print("Usage:", sys.argv[0], "<host> <port>")
        sys.exit(1)

    server_host = sys.argv[1]
    server_port = int(sys.argv[2])

    IP = socket.gethostbyname(socket.gethostname())
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    print("[CLIENT] Started running")
    start_client(socket=client_socket)
    client_socket.close()
    print("\nGoodbye client:)")