"""Example

An example of sending commands from one process to another process, where the
second process is running a pygame window.

This exmaple also adds a second command,  asset loading, and sprite transformations.
"""

from multiprocessing import Process, Queue
import os
import queue
import random
import time

DEBUG_MODE = False
KIND = 'kind'
COLOUR = 'colour'
ROTATE = 'rotate'
ANGLE = 'angle'

def game_proc(q):
    PROC_NAME = "game_proc"
    FPS = 60
    QUEUE_TIMEOUT_S = 8 / 1000 # 8 milliseconds, around half a 60 FPS frame
    ANGLE_CHANGE_PER_FRAME = 1.5

    asset_path = os.path.join(os.path.dirname(__file__), "assets")

    def load_image(name):
        path = os.path.join(asset_path, name)
        if DEBUG_MODE:
            print(f"loading {path}")
        image = pygame.image.load(path)
        image = pygame.Surface.convert_alpha(image)
        return image

    # See https://stackoverflow.com/a/54714144
    def blitRotateCenter(surf, image, topleft, angle):
        rotated_image = pygame.transform.rotate(image, angle)
        new_rect = rotated_image.get_rect(center = image.get_rect(topleft = topleft).center)

        surf.blit(rotated_image, new_rect)

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

    star_image = load_image("star.png")
    star_image = pygame.transform.scale_by(star_image, (1/2, 1/2))

    red = 255
    green = 0
    blue = 255

    current_angle = 0
    target_angle = 0

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
                if kind == COLOUR:
                    colour = payload[COLOUR]
                    if type(colour) == int:
                        # Extract just the lower 3 bytes into separate colour
                        # channels. Note that extra bits will be ignored, and
                        # missing ones will default to 0
                        red = (colour >> 16) & 0xFF
                        green = (colour >> 8) & 0xFF
                        blue = colour & 0xFF
                        if DEBUG_MODE:
                            print(f"(red, green, blue): {(red, green, blue)}")
                    else:
                        print(f"colour was {colour}?!")
                elif kind == ROTATE:
                    angle = payload[ANGLE]
                    if type(angle) == int:
                        target_angle += angle
                    else:
                        print(f"angle was {angle}?!")
                else:
                    print(f"kind was {kind}?!")
            else:
                print(f"payload was {payload}?!")
            

        # fill the screen with a color to wipe away anything from last frame
        screen.fill((red, green, blue))

        # RENDER YOUR GAME HERE
        
        # Avoid jitter
        if abs(current_angle - target_angle) < 0.001:
            current_angle = target_angle
        
        if current_angle > target_angle:
            angle_signum = -1
        elif current_angle < target_angle:
            angle_signum = 1
        else:
            angle_signum = 0
        current_angle += angle_signum * ANGLE_CHANGE_PER_FRAME
        
        blitRotateCenter(screen, star_image, (100, 100), current_angle)

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

    UNKNOWN_INPUT_MESSAGE = "lol wut?"

    while (1):
        mode_str = input(
        """Enter number to pick mode
        1) Set background
        2) Rotate sprite
        (q to quit): 
        """).lower()
        if mode_str == "1" or mode_str == "1)":
            colour_str = input("Enter RGB number (q to quit): ").lower()
            try:
                # 0 means try to guess the base
                colour = int(colour_str, 0)
                print(f"got {colour}, AKA {(hex(colour).upper())}")
                queue.put({KIND: COLOUR, COLOUR: colour})
            except ValueError:
                if colour_str.startswith('q'):
                    break
                else:
                    print(UNKNOWN_INPUT_MESSAGE)
        elif mode_str == "2" or mode_str == "2)":
            degrees_str = input("Enter angle in degees (q to quit): ").lower()
            try:
                degrees = int(degrees_str)
                print(f"got {degrees}")
                queue.put({KIND: ROTATE, ANGLE: degrees})
            except ValueError:
                if colour_str.startswith('q'):
                    break
                else:
                    print(UNKNOWN_INPUT_MESSAGE)
        elif mode_str.startswith('q'):
            break
        else:
            print(UNKNOWN_INPUT_MESSAGE)
        

    print("Quitting...")

    for p in processes:
        # Just join or close can leave locked processes around still
        p.terminate()
        
    print("Bye!")



