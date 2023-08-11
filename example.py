"""Example

An example of sending commands from one process to another process, where the
second process is running a pygame window.
"""

from multiprocessing import Process, Queue
import os
import queue
import random
import time

DEBUG_MODE = False
KIND = 'kind'
NUM = 'num'

def game_proc(q):
    PROC_NAME = "game_proc"
    FPS = 60
    QUEUE_TIMEOUT_S = 8 / 1000 # 8 milliseconds, around half a 60 FPS frame

    if DEBUG_MODE:
        print(f"{PROC_NAME} started")
        import pygame
    else:
        # Hide pygame import message
        import contextlib
        with contextlib.redirect_stdout(None):
            import pygame

    # pygame setup
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()
    running = True

    red = 255
    green = 0
    blue = 255

    while running:
        # poll for events
        # pygame.QUIT event means the user clicked X to close your window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        try:
            payload = q.get(True, QUEUE_TIMEOUT_S)
        except queue.Empty:
            # Keep waiting for more input
            pass
        except ValueError:
            # Queue was closed. All done.
            break
        else:
            # Examine the payload and act accordingly
            if DEBUG_MODE:
                print(f"payload was {payload}")

            if type(payload) == dict:
                kind = payload[KIND]
                # Check the KIND field to allow adding more commands easily in
                # the future
                if kind == NUM:
                    num = payload[NUM]
                    if type(num) == int:
                        # Extract just the lower 3 bytes into separate colour
                        # channels. Note that extra bits will be ignored, and
                        # missing ones will default to 0
                        red = (num >> 16) & 0xFF
                        green = (num >> 8) & 0xFF
                        blue = num & 0xFF
                        if DEBUG_MODE:
                            print(f"(red, green, blue): {(red, green, blue)}")
                    else:
                        print(f"num was {num}?!")
                else:
                    print(f"kind was {kind}?!")
            else:
                print(f"payload was {payload}?!")
            

        # fill the screen with a color to wipe away anything from last frame
        screen.fill((red, green, blue))

        # RENDER YOUR GAME HERE

        # flip() the display to put your work on screen
        pygame.display.flip()

        clock.tick(FPS)  # limits FPS

    pygame.quit()

# This if makes it such that the contained code runs only if this file is run 
# directly. So if the file is imported it won't run.
if __name__ == "__main__":
    queue = Queue()

    processes = [Process(target=game_proc, args=(queue,))]

    for p in processes:
        p.start()

    while (1):
        num_str = input("Enter RGB number (q to quit): ")
        try:
            # 0 means try to guess the base
            num = int(num_str, 0)
            print(f"got {num}, AKA {(hex(num).upper())}")
            queue.put({KIND: NUM, NUM: num})
        except ValueError:
            if num_str.lower().startswith('q'):
                break
            else:
                print("lol wut?")

    print("Quitting...")

    for p in processes:
        # Just join or close can leave locked processes around still
        p.terminate()
        
    print("Bye!")



