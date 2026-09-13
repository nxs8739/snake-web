#!/usr/bin/env python3

from flask import Flask, render_template, request, Response, session
import random
import time
import threading
import queue
import uuid


app = Flask(__name__)


# Used by Flask to identify each browser session.
app.secret_key = "d610606cad831e1c464e5c6bdf6d624ef34918175aadcfb15b3ab91e45207811"


# ============================================================
# SETTINGS
# ============================================================

WIDTH = 50
HEIGHT = 20
START_SPEED = 0.11

# How long a player can remain inactive before the
# session is considered abandoned.
SESSION_TIMEOUT = 300

# How often the cleanup thread checks for abandoned games.
CLEANUP_INTERVAL = 60


# ============================================================
# GAME
# ============================================================

def place_food(snake):

    while True:

        food = (
            random.randint(1, WIDTH - 2),
            random.randint(1, HEIGHT - 2)
        )

        if food not in snake:
            return food


def make_screen(snake=None, food=None, score=0, message=None):

    # --------------------------------------------------------
    # Start screen
    # --------------------------------------------------------

    if message == "start":

        lines = [" " * WIDTH for _ in range(HEIGHT)]

        title = "SNAKE"

        lines[5] = title.center(WIDTH)

        lines[7] = "Arrow keys = Move".center(WIDTH)

        lines[9] = "SPACE = Start".center(WIDTH)

        lines[11] = "CTRL+C = Quit".center(WIDTH)

        return "\n".join(lines)


    # --------------------------------------------------------
    # Game-over screen
    # --------------------------------------------------------

    if message == "gameover":

        lines = [" " * WIDTH for _ in range(HEIGHT)]

        game_over_lines = [
            "GAME OVER",
            "",
            f"Score: {score}",
            "",
            "SPACE = Play Again",
            "CTRL+C = Quit",
        ]

        start_y = 6

        for index, line in enumerate(game_over_lines):

            if start_y + index < HEIGHT:

                lines[start_y + index] = line.center(WIDTH)

        return "\n".join(lines)


    # --------------------------------------------------------
    # Game screen
    # --------------------------------------------------------

    board = [
        [" " for _ in range(WIDTH)]
        for _ in range(HEIGHT)
    ]


    # Border

    for x in range(WIDTH):

        board[0][x] = "#"
        board[HEIGHT - 1][x] = "#"


    for y in range(HEIGHT):

        board[y][0] = "#"
        board[y][WIDTH - 1] = "#"


    # Food

    if food is not None:

        board[food[1]][food[0]] = "*"


    # Snake

    if snake:

        head = snake[0]

        board[head[1]][head[0]] = "@"

        for segment in snake[1:]:

            board[segment[1]][segment[0]] = "o"


    return "\n".join(
        "".join(row)
        for row in board
    )


# ============================================================
# GAME SESSION
# ============================================================

class SnakeGame:

    def __init__(self):

        self.lock = threading.Lock()

        self.screen = make_screen(message="start")

        self.key_queue = queue.Queue()

        self.running = False

        self.game_over = False

        self.score = 0

        self.snake = []

        self.food = None

        self.direction = (1, 0)

        self.speed = START_SPEED

        self.thread = None


    # --------------------------------------------------------
    # Start game
    # --------------------------------------------------------

    def start(self):

        with self.lock:

            center_x = WIDTH // 2
            center_y = HEIGHT // 2

            self.snake = [
                (center_x, center_y),
                (center_x - 1, center_y),
                (center_x - 2, center_y),
            ]

            self.direction = (1, 0)

            self.food = place_food(self.snake)

            self.score = 0

            self.speed = START_SPEED

            self.running = True

            self.game_over = False

            self.screen = make_screen(
                self.snake,
                self.food,
                self.score
            )


        if self.thread is None or not self.thread.is_alive():

            self.thread = threading.Thread(
                target=self.game_loop,
                daemon=True
            )

            self.thread.start()


    # --------------------------------------------------------
    # Return to start screen
    # --------------------------------------------------------

    def quit_to_menu(self):

        with self.lock:

            self.running = False

            self.game_over = False

            self.snake = []

            self.food = None

            self.score = 0

            self.direction = (1, 0)

            self.speed = START_SPEED

            self.screen = make_screen(
                message="start"
            )


    # --------------------------------------------------------
    # Handle keyboard input
    # --------------------------------------------------------

    def handle_key(self, key):

        with self.lock:

            if key == "UP":

                if self.direction != (0, 1):

                    self.direction = (0, -1)


            elif key == "DOWN":

                if self.direction != (0, -1):

                    self.direction = (0, 1)


            elif key == "LEFT":

                if self.direction != (1, 0):

                    self.direction = (-1, 0)


            elif key == "RIGHT":

                if self.direction != (-1, 0):

                    self.direction = (1, 0)


    # --------------------------------------------------------
    # Stop game
    # --------------------------------------------------------

    def stop(self):

        with self.lock:

            self.running = False


    # --------------------------------------------------------
    # Game loop
    # --------------------------------------------------------

    def game_loop(self):

        while True:

            with self.lock:

                if not self.running:

                    return

                head_x, head_y = self.snake[0]

                dx, dy = self.direction

                new_head = (
                    head_x + dx,
                    head_y + dy
                )


                # ------------------------------------------------
                # Wall collision
                # ------------------------------------------------

                if (
                    new_head[0] <= 0
                    or new_head[0] >= WIDTH - 1
                    or new_head[1] <= 0
                    or new_head[1] >= HEIGHT - 1
                ):

                    self.running = False

                    self.game_over = True

                    self.screen = make_screen(
                        score=self.score,
                        message="gameover"
                    )

                    return


                # ------------------------------------------------
                # Self collision
                # ------------------------------------------------

                if new_head in self.snake:

                    self.running = False

                    self.game_over = True

                    self.screen = make_screen(
                        score=self.score,
                        message="gameover"
                    )

                    return


                # ------------------------------------------------
                # Move
                # ------------------------------------------------

                self.snake.insert(0, new_head)


                # ------------------------------------------------
                # Food
                # ------------------------------------------------

                if new_head == self.food:

                    self.score += 1

                    self.food = place_food(self.snake)

                    self.speed = max(
                        0.045,
                        START_SPEED - (self.score * 0.002)
                    )

                else:

                    self.snake.pop()


                # ------------------------------------------------
                # Render
                # ------------------------------------------------

                self.screen = make_screen(
                    self.snake,
                    self.food,
                    self.score
                )


            time.sleep(self.speed)


    # --------------------------------------------------------
    # Current screen
    # --------------------------------------------------------

    def get_screen(self):

        with self.lock:

            return self.screen


# ============================================================
# PLAYER GAME SESSIONS
# ============================================================

games = {}

games_lock = threading.Lock()


class PlayerSession:

    def __init__(self):

        self.game = SnakeGame()

        # Last time the PLAYER actually did something.
        self.last_activity = time.monotonic()

        # Whether the browser currently has an SSE connection.
        self.connected = False

        # Becomes True when cleanup destroys this session.
        self.expired = False


    def touch(self):

        self.last_activity = time.monotonic()


# ------------------------------------------------------------
# Get current player's session
# ------------------------------------------------------------

def get_player_session(touch_activity=False):

    game_id = session.get("game_id")


    if game_id is None:

        game_id = str(uuid.uuid4())

        session["game_id"] = game_id


    with games_lock:

        if game_id not in games:

            games[game_id] = PlayerSession()


        player = games[game_id]


    if touch_activity:

        player.touch()


    return player


# ============================================================
# SESSION CLEANUP
# ============================================================

def cleanup_sessions():

    while True:

        time.sleep(CLEANUP_INTERVAL)

        now = time.monotonic()

        abandoned = []


        with games_lock:

            for game_id, player in list(games.items()):

                age = now - player.last_activity


                if age >= SESSION_TIMEOUT:

                    abandoned.append(
                        (game_id, player, age)
                    )


            for game_id, player, age in abandoned:

                # Tell the SSE connection that the session
                # has been destroyed.

                player.expired = True

                # Stop the Snake game.

                player.game.stop()

                # Remove the session from memory.

                games.pop(game_id, None)


        # Report cleanup to the Flask terminal.

        for game_id, player, age in abandoned:

            print(
                "Cleaned up abandoned Snake session "
                f"{game_id} "
                f"after {int(age)} seconds of inactivity.",
                flush=True
            )


# Start cleanup thread.

cleanup_thread = threading.Thread(
    target=cleanup_sessions,
    daemon=True
)

cleanup_thread.start()


# ============================================================
# WEB PAGE
# ============================================================

@app.route("/")
def index():

    # Loading the page counts as player activity.

    get_player_session(
        touch_activity=True
    )

    return render_template("index.html")


# ============================================================
# START GAME
# ============================================================

@app.route("/start", methods=["POST"])
def start():

    player = get_player_session(
        touch_activity=True
    )

    player.game.start()

    return ("", 204)


# ============================================================
# KEYBOARD
# ============================================================

@app.route("/key", methods=["POST"])
def key():

    data = request.get_json()

    if not data:

        return ("", 400)


    pressed_key = data.get("key")


    # Actual keyboard input counts as player activity.

    player = get_player_session(
        touch_activity=True
    )


    # --------------------------------------------------------
    # Space
    # --------------------------------------------------------

    if pressed_key == "SPACE":

        if not player.game.running:

            player.game.start()


    # --------------------------------------------------------
    # Ctrl+C
    # --------------------------------------------------------

    elif pressed_key == "CTRL_C":

        player.game.quit_to_menu()


    # --------------------------------------------------------
    # Arrow keys
    # --------------------------------------------------------

    elif pressed_key in (
        "UP",
        "DOWN",
        "LEFT",
        "RIGHT"
    ):

        player.game.handle_key(
            pressed_key
        )


    return ("", 204)


# ============================================================
# SCREEN STREAM
# ============================================================

@app.route("/screen")
def screen():

    # The SSE connection itself does NOT count as activity.

    player = get_player_session(
        touch_activity=False
    )

    player.connected = True


    def generate():

        last_screen = None


        try:

            while True:

                # ------------------------------------------------
                # Session expired
                # ------------------------------------------------

                if player.expired:

                    yield (
                        "event: expired\n"
                        "data: expired\n\n"
                    )

                    return


                current_screen = player.game.get_screen()


                if current_screen != last_screen:

                    yield (
                        "data: "
                        + current_screen.replace(
                            "\n",
                            "\\n"
                        )
                        + "\n\n"
                    )

                    last_screen = current_screen


                time.sleep(0.02)


        finally:

            player.connected = False


    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        threaded=True
    )
