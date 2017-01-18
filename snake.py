
# Scatters dots randomly on your terminal as a quick demo of curses.

import collections
import curses
import random
import time
from enum import Enum
import os

os.environ['TERM'] = 'xterm-256color'

COLOR_PALLET = None

import itertools
counter = itertools.count(1)

class GameOverException(Exception): pass

class BoardRenderer(object):

    def __init__(self, width, height, lives=3, score=0): 
        # This represents 1 character in height and 2 characters in width to frame the board
        self.borderUnits = 1
        self.width, self.height = width, height
        self._board = curses.newwin(height, width)
        self._board.bkgd(" ", COLOR_PALLET.BORDER.get())

        self.playarea = self._board.subwin(height-(2*self.borderUnits),  # nlines
                                          width-(4*self.borderUnits) ,  # ncols
                                          int(self.borderUnits),        # begin_y
                                          self.borderUnits*2)           # begin_x
        self.playarea.bkgd(" ", COLOR_PALLET.BG.get())
        # Curses bug: http://stackoverflow.com/questions/30879873/bug-with-refresh-in-python-curses/30880305#30880305
        self.playarea.keypad(1)

        # the getchr() timeout controls the pace of the game
        self._timeout = 525

        # Box in the top right corner with the score
        self._scoreWidth=20
        self._scoreScr = self._board.subwin(1,                    # nlines
                                           self._scoreWidth+1,   # ncols
                                           0,                    # begin_y
                                           width-(self.borderUnits*2)-self._scoreWidth)  # begin_x

        # Show the number of lives in the top left
        self._livesWidth=20
        self._livesScr = self._board.subwin(1,                    # nlines
                                           self._livesWidth+1,   # ncols
                                           0,                    # begin_y
                                           2*self.borderUnits)   # begin_x

        # Show the speed in the bottom left
        self._speedWidth=20
        self._speedScr = self._board.subwin(1,                    # nlines
                                            self._speedWidth+1,   # ncols
                                            height-1,             # begin_y
                                            2*self.borderUnits)   # begin_x

        # Show the title in the top middle
        title = "SNAKE!"
        titleWidth=len(title)
        self._titleScr = self._board.subwin(1,              # nlines
                                           titleWidth+1,   # ncols
                                           0,              # begin_y
                                           int(width/2)-int(titleWidth/2))   # begin_x
        self._titleScr.addstr(title, COLOR_PALLET.BORDER.get() | curses.A_BOLD )

        # Set initial values
        self._board.refresh()
        self.setScore(score)
        self.setLives(lives)
        self.speedUp()

    def add(self, coords, color):
        if not isinstance(coords, collections.Sequence):
            coords = [coords]
        self._render(coords, color)

    def clear(self, coords):
        if not isinstance(coords, collections.Sequence):
            coords = [coords]
        
        rm = []
        for coord in coords:
            if coord != None and \
               (coord.y < 0 or coord.y >= self.height-(2*self.borderUnits) or \
                coord.x < 0 or coord.x >= (2*self.width)-(4*self.borderUnits)):
                rm.append(coord)
        
        for r in rm:
            coords.remove(r)

        self._render(coords, COLOR_PALLET.BG)

    def _render(self, coords, color):
        for coord in coords:
            try:
                if coord != None:
                    # The board grid is scaled by 2x in the X direction and
                    # by 1x in the Y direction such that added objets are close
                    # to square.
                    if coord.y >= 0 and coord.y < self.height-(2*self.borderUnits) and \
                       coord.x >= 0 and coord.x < (2*self.width)-(4*self.borderUnits):
                        self.playarea.addstr(coord.y, coord.x*2, " ", color.get())
                        self.playarea.addstr(coord.y, (coord.x*2) +1, " ", color.get())
                    else:
                        raise GameOverException("Renderer out of bounds!")

            except curses.error:
               raise RuntimeError("Could not render %s!" % str(coord))

    def refresh(self):
        self._board.refresh()

    def getRandomCoord(self):
        return Coordinate(random.randint(0, int(self.width/2)-2*self.borderUnits-1),
                          random.randint(0, int(self.height)-2*self.borderUnits-1))

    def speedUp(self):
        self._timeout = max(self._timeout - 25, 15)
        self.playarea.timeout(self._timeout)

        # update display
        speedStr = str("Speed: %d" % min(525-self._timeout, 500)).ljust(self._speedWidth)
        self._speedScr.addstr(0,0,speedStr,COLOR_PALLET.BORDER.get())
        self._speedScr.refresh()

    def setScore(self, score):
        scoreStr = str("Score: %d" % score).rjust(self._scoreWidth)
        self._scoreScr.addstr(0,0,scoreStr,COLOR_PALLET.BORDER.get())
        self._scoreScr.refresh()

    def setLives(self, lives):
        livesStr = str("Lives: %d" % lives).ljust(self._livesWidth)
        self._livesScr.addstr(0,0,livesStr,COLOR_PALLET.BORDER.get())
        self._livesScr.refresh()     

    def showGameOver(self):
        overlay = self.playarea.subwin(int(self.height/4),  # nlines
                                       int(self.width/2) ,  # ncols
                                       int(self.height/4),  # begin_y
                                       int(self.width/4))   # begin_x

        # Curses bug: http://stackoverflow.com/questions/30879873/bug-with-refresh-in-python-curses/30880305#30880305
        overlay.keypad(1)

        overlay.bkgd(" ", COLOR_PALLET.BORDER.get())
        
        title = "GAME OVER!"
        overlay.addstr(int(self.height/4)-int(self.height/8)-2, int(self.width/4) - int(len(title)/2), title)

        title = "Press any key to exit"
        overlay.addstr(int(self.height/4)-int(self.height/8), int(self.width/4) - int(len(title)/2), title)

        overlay.refresh()

        overlay.getch()

class Coordinate(object):
    
    # Note: this is how the coordinate grid is oriented (as drawn on the screen)
    #   0 1 2 3 ...
    # 0
    # 1
    # 2
    # 3
    # ...

    def __init__(self, x, y):
        self.x, self.y = x, y
    def __add__(self, other):
        return Coordinate(self.x + other.x, self.y + other.y)
    def __sub__(self, other):
        return Coordinate(self.x - other.x, self.y - other.y)
    def __repr__(self):
        return "Coord(%d,%d)" % (self.x, self.y)
    def __eq__(self, other):
        return other and self.x == other.x and self.y == other.y

class Direction(Enum):
    UP    = (0, -1, curses.KEY_UP)
    DOWN  = (0, +1, curses.KEY_DOWN)
    LEFT  = (-1, 0, curses.KEY_LEFT)
    RIGHT = (+1, 0, curses.KEY_RIGHT)

    def __init__(self, xDiff, yDiff, key):
        self.coord = Coordinate(xDiff, yDiff)
        self.key = key

    @classmethod
    def fromCursesKey(cls, key):
        directions = [ direction for direction in list(cls) if direction.key == key ]
        if len(directions) == 0:
            return None
        return directions[0]

class Snake(object):

    def __init__(self, x, y, length, direction):
        self.startX, self.startY, self.startLength, self.startDir = x, y, length, direction
        self.reset()

    def reset(self):
        self.store = collections.deque()
        self.direction = self.startDir
        self.store.append(Coordinate(self.startX, self.startY))
        for idx in range(self.startLength-1):
            self.move(grow=True)

    def getCoords(self):
        return list(self.store)

    def getValidDirections(self):
        valid = list()
        for direction in list(Direction):
            newCoord = self.store[-1] + direction.coord
            if newCoord not in self.store:
                valid.append(direction)
        return valid

    def move(self, direction=None, grow=False):
        if direction:
            if direction == Direction.DOWN  and self.direction == Direction.UP or \
               direction == Direction.LEFT  and self.direction == Direction.RIGHT or \
               direction == Direction.RIGHT and self.direction == Direction.LEFT or \
               direction == Direction.UP    and self.direction == Direction.DOWN :
                pass
            else:
                self.direction = direction

        # Pops are done before appends to allow for a fully circular snake path
        if not grow:
            removedCoord = self.store.popleft()
        else:
            removedCoord = None
            
        newCoord = self.store[-1] + self.direction.coord
        if newCoord in self.store:
            # put back the tail coord on an end game condition so the redraw
            # on the next respawn will occur at this position
            self.store.append(removedCoord)
            raise GameOverException("Snake Bite!")
        self.store.append(newCoord)

        return (removedCoord, newCoord)

class Game(object):

    def __init__(self, height, width):
        self.width, self.height = width, height
        self.board  = BoardRenderer(width, height)
        self.snake  = Snake(int(width/4), int(height/2), 7, Direction.DOWN)

        self.appleCoords = list()
        self.score = 0
        self.lives = 3

    def spawnApple(self):
        # BUG: what if the random coord is in the snake?
        coord = self.board.getRandomCoord()
        self.appleCoords.append(coord)
        self.board.add(coord, COLOR_PALLET.APPLE)
        self.board.refresh()
        if self.score % 100 == 0:
            self.board.speedUp()

    def handleDeath(self):
        self.lives -= 1
        rm = self.snake.getCoords()
        self.board.clear(rm)
        self.snake.reset()  
        self.board.setLives(self.lives)      

    def loop(self, stdscr):
        # draw the snake in an original position
        coords = self.snake.getCoords()
        self.board.add(coords, COLOR_PALLET.SNAKE)
        self.spawnApple()

        doGrow = False
        while True:

            try:
                self.board.refresh()

                char = self.board.playarea.getch() 
                direction = Direction.fromCursesKey(char)

                rm, add = self.snake.move(direction, grow=doGrow)
                doGrow = False
                
                # If moving in a perfect circle, don't add or remove anything. 
                # Otherwise draw what is on the screen.
                if rm != add:
                    self.board.clear(rm)

                # check for eaten apples
                if add in self.appleCoords:
                    self.score += 50
                    self.board.setScore(self.score)
                    self.appleCoords.remove(add)
                    self.spawnApple()
                    doGrow = True

                self.board.add(add, COLOR_PALLET.SNAKE)

            except GameOverException:
                if self.lives <= 1:
                    break

                self.handleDeath()
            
        self.board.showGameOver()


def main(stdscr):
    global COLOR_PALLET

    curses.start_color()
    curses.use_default_colors()

    # hide the cursor
    curses.curs_set(0)

    class ColorPallet(Enum):
        BG = (179, 179)
        SNAKE = (5, 5)
        BORDER = (252, 124)
        APPLE = (76, 76)

        def __init__(self, fg, bg):
            self.num = next(counter)
            self.fg = fg
            self.bg = bg
            curses.init_pair(self.num, fg, bg)

        def get(self):
            return curses.color_pair(self.num)


    COLOR_PALLET = ColorPallet

    height, width = stdscr.getmaxyx()

    game = Game(height, width)
    game.loop(stdscr)

curses.wrapper(main)
