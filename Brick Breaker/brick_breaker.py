import tkinter as tk
import sys
import time
from typing import DefaultDict

WIN_WIDTH = 620
WIN_HEIGHT = 480
FPS = 50

ROOT = tk.Tk()
ROOT.title('Brick Breaker')


# common class for all game objects
class Component:
    # initializing items and surface
    def __init__(self, item):
        self.item = item
        Game.components[item] = self

    # display component
    def display(self, x, y):
        Game.canvas.move(self.item, x, y)

    # coordinates of an object
    def get_position(self) -> dict:
        coords = Game.canvas.coords(self.item)
        if coords:
            return {'left': coords[0], 'top': coords[1], 'right': coords[2], 'bottom': coords[3]}

    # destroy component
    def __del__(self):
        # silent debug
        try:
            Game.canvas.delete(self.item)
        except:
            pass


class Brick(Component):
    colorArray = {1: 'lightsteelblue', 2: 'royalblue', 3: 'blue'}
    WIDTH = 80
    HEIGHT = 20

    def __init__(self, x, y, hits):
        self.hits = hits
        color = Brick.colorArray[hits]
        item = Game.canvas.create_rectangle(
            (x - Brick.WIDTH // 2, y - Brick.HEIGHT // 2),
            (x + Brick.WIDTH // 2, y + Brick.HEIGHT // 2),
            fill=color, outline='black', tag='brick')
        super().__init__(item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.__del__()
        else:
            Game.canvas.itemconfig(self.item, fill=Brick.colorArray[self.hits])

    @staticmethod
    def set_many():
        BLOCK_WIDTH = Brick.WIDTH
        BLOCK_HEIGHT = Brick.HEIGHT

        START_HITS = 2

        line = range(BLOCK_WIDTH, WIN_WIDTH -
                     BLOCK_WIDTH // 2, BLOCK_WIDTH * 3 // 2)
        lines = range(BLOCK_HEIGHT, BLOCK_HEIGHT *
                      4, BLOCK_HEIGHT * 2)

        for y in lines:
            for x in line:
                Brick(x, y, START_HITS)


# no singleton: can extent to 2-player game
class Paddle(Component):
    # paddle settings
    HEIGHT = 20
    WIDTH = 100
    SPEED = 30

    def __init__(self, x, y, color='yellow'):
        self.color = color
        item = Game.canvas.create_rectangle(
            (x - Paddle.WIDTH // 2, y - Paddle.HEIGHT // 2),
            (x + Paddle.WIDTH // 2, y + Paddle.HEIGHT // 2),
            fill=self.color, outline='black')
        super().__init__(item)

    def display(self, direction):
        global WIN_WIDTH
        # coordinates
        coord = self.get_position()

        diff = direction * Paddle.SPEED
        dist = min(WIN_WIDTH - coord['right'], max(diff, -coord['left']))

        super().display(dist, 0)


# singleton: only one ball allowed
class Ball(Component):
    # ball settings
    ball = None  # singleton
    RADIUS = 12
    SPEED = 8
    direction = {'x': -1, 'y': 1}

    # creating the ball
    def __init__(self, paddle: Paddle):
        self.paddle = paddle
        paddle_coords = self.paddle.get_position()

        # ensuring singleton when displaying the object
        if Ball.ball is not None:
            raise MemoryError("Singleton violation:\n\
                              Only one ball instance allowed")

        # creating the ball object
        START_X = (paddle_coords['left'] + paddle_coords['right']) // 2
        START_Y = paddle_coords['top'] - Ball.RADIUS * 2

        # setting the ball component
        item = Game.canvas.create_oval(
            (START_X - Ball.RADIUS, START_Y - Ball.RADIUS),
            (START_X + Ball.RADIUS, START_Y + Ball.RADIUS),
            fill='red', outline='black')

        # initialized parent instance
        super().__init__(item)
        # initialized ball instance
        Ball.ball = self

    # update coordinates and move the ball
    def update(self):
        # loading necessary variables
        global WIN_WIDTH
        ball_coords = self.get_position()

        # wall collision
        if ball_coords['top'] <= 0:
            Ball.direction['y'] *= -1
        if ball_coords['right'] >= WIN_WIDTH or ball_coords['left'] <= 0:
            Ball.direction['x'] *= -1

        x = Ball.direction['x'] * Ball.SPEED
        y = Ball.direction['y'] * Ball.SPEED

        Ball.ball.display(x, y)

    def check_collision(self):
        for item in Game.components:
            item_instance = Game.components[item]
            if isinstance(item_instance, Paddle)\
                    and (item_instance.get_position() is not None):
                self.paddle_collision(item_instance)
            elif isinstance(item_instance, Brick)\
                    and (item_instance.get_position() is not None):
                self.brick_collision(item_instance)

    def paddle_collision(self, paddle: Paddle):
        paddle_coords = paddle.get_position()
        ball_coords = self.get_position()
        ball_centerx = (ball_coords['left'] + ball_coords['right']) // 2
        paddle_centerx = (paddle_coords['left'] + paddle_coords['right']) // 2

        # checking y
        if paddle_coords['top'] - Ball.SPEED <= ball_coords['bottom']:
            # checking x
            if paddle_coords['left'] <= ball_centerx <= paddle_coords['right']:
                Ball.direction['y'] = -1
            elif paddle_coords['left'] <= ball_coords['right'] <= paddle_centerx:
                Ball.direction['x'] = -1
            elif paddle_centerx <= ball_coords['left'] <= paddle_coords['right']:
                Ball.direction['x'] = 1

    def brick_collision(self, brick: Brick):
        brick_coords = brick.get_position()
        ball_coords = self.get_position()
        ball_centerx = (ball_coords['left'] + ball_coords['right']) // 2
        brick_centerx = (brick_coords['left'] + brick_coords['right']) // 2

        # checking y
        if brick_coords['bottom'] + Ball.SPEED >= ball_coords['top']:
            # checking x
            
            if brick_coords['left'] <= ball_centerx <= brick_coords['right']:
                Ball.direction['y'] *= -1
                brick.hit()
            elif brick_coords['left'] <= ball_coords['right'] <= brick_centerx:
                Ball.direction['x'] = -1
                brick.hit()
            elif brick_centerx <= ball_coords['left'] <= brick_coords['right']:
                Ball.direction['x'] = 1
                brick.hit()
    
    def __del__(self):
        Ball.ball = None
        super().__del__()


class Text(Component):
    @staticmethod
    def draw(x, y, text, font='Gill Sans', size=50):
        font = ('Arial', size)
        return Game.canvas.create_text(x, y, text=text, fill='black', font=font)


class Game(tk.Frame):
    # game settings
    canvas = None   # singleton: only one surface allowed
    components = DefaultDict()
    BACKGROUND = 'beige'

    def __init__(self, master):
        global WIN_WIDTH
        super(Game, self).__init__(master)

        if Game.canvas is not None:
            raise MemoryError("Singleton violation:\n\
                              Only one surface instance allowed")
        # initializing widgets
        Game.canvas = tk.Canvas(self,
                                bg=Game.BACKGROUND,
                                width=WIN_WIDTH,
                                height=WIN_HEIGHT)

        # packing widgets to parent
        Game.canvas.pack()
        self.pack()

        # interact with parent surface
        Game.canvas.focus_set()

        # welcoming text
        self.text = Text.draw(WIN_WIDTH / 2, WIN_HEIGHT /
                              2, 'Press "S" for start')
        self.canvas.bind('<s>', lambda _: self.start_game())

    def start_game(self):
        # removing starting text and unbinding key
        Game.canvas.unbind('<s>')
        Game.canvas.delete(self.text)

        # initializing paddle
        self.paddle = Paddle(WIN_WIDTH // 2, WIN_HEIGHT - Paddle.HEIGHT * 2)

        # binding paddle keys
        self.canvas.bind('<Left>',
                         lambda _: self.paddle.display(-1))
        self.canvas.bind('<Right>',
                         lambda _: self.paddle.display(1))

        # initializing ball
        Ball(self.paddle)

        # initializing bricks
        Brick.set_many()

        self.game_loop()

    def game_loop(self):
        Ball.ball.check_collision()

        # keep playing
        if not self.game_over():
            Ball.ball.update()
            self.after(FPS, self.game_loop)

    def game_over(self):
        num_bricks = len(self.canvas.find_withtag('brick'))
        flag = False

        message = ''
        if num_bricks == 0:
            flag = True
            message = 'Winner-winner!\n\
                      Chicken dinner!'
        elif Ball.ball.get_position()['top'] >= WIN_HEIGHT:
            flag = True
            message = 'Better luck next time.'
        
        if flag:
            # removing all the previous game components
            # and states
            for item in Game.components:
                Game.components[item].__del__()
            self.text = Text.draw(WIN_WIDTH / 2, WIN_HEIGHT /
                                2, message + '\nPress "R" to restart')
            self.canvas.bind('<r>', lambda _: self.start_game())
        
        return flag


# main script
if __name__ == '__main__':
    game = Game(ROOT)
    game.mainloop()
