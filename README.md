# Snake — Terminal Game on the Web

A simple terminal-style Snake game written in Python and made playable through a web browser using Flask.

The original game was designed to run entirely in the terminal. This project puts a lightweight web interface in front of it so multiple users can play their own independent Snake game sessions through a browser.

## How It Works

The Python program remains responsible for the actual Snake game.

Flask acts as the communication layer between the browser and the Python game:

```text
Browser
   │
   ├── Keyboard input
   │
   ▼
 Flask
   │
   ▼
 SnakeGame
   │
   ├── Game logic
   ├── Movement
   ├── Collision detection
   ├── Food
   ├── Score
   └── Game speed
   │
   ▼
 Terminal-style screen
   │
   ▼
 Flask
   │
   ▼
 Browser
```

The browser does not run the Snake game itself. Python runs the game and generates the text-based game screen, while Flask streams that screen to the browser.

## Features

* Terminal-style Snake gameplay
* Python handles the complete game logic
* Browser-based controls
* Arrow keys for movement
* Spacebar to start/restart
* `Ctrl+C` to return to the start screen
* Individual game session for each connected player
* Real-time screen updates using Server-Sent Events (SSE)
* Automatic cleanup of abandoned sessions
* Five-minute inactivity timeout
* Expired browser connections are automatically closed
* No database required
* No file uploads
* No user accounts
* Lightweight Flask application

## Controls

| Key             | Action                 |
| --------------- | ---------------------- |
| `↑` `↓` `←` `→` | Move                   |
| `SPACE`         | Start / Play Again     |
| `CTRL+C`        | Return to start screen |

## Requirements

* Python 3
* Flask

No database or additional services are required to run the game locally.

## Installation

Clone the repository:

```bash
git clone https://github.com/nxs8739/snake-web.git
cd snake-web
```

Enter the application directory:

```bash
cd snake-python-online
```

Install Flask if necessary:

```bash
python3 -m pip install flask
```

## Configuration

Flask uses a secret key to identify and secure each browser session.

Before running the application, generate your own secret key:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated string and put it into `app.py`:

```python
app.secret_key = "YOUR_GENERATED_SECRET_KEY"
```

Replace `YOUR_GENERATED_SECRET_KEY` with the string you generated.

**Do not use the secret key from this repository, it has been rotated. Also do not share your own secret key publicly.**

Start the application:

```bash
python3 app.py
```

The Flask server will listen on:

```text
http://127.0.0.1:5000
```

To access it from another device on the same network, connect using the computer's LAN address.

## Project Structure

```text
.
├── app.py
└── templates/
    └── index.html
```

### `app.py`

Contains:

* Snake game logic
* Game rendering
* Player session management
* Keyboard input handling
* Server-Sent Events screen streaming
* Abandoned-session cleanup
* Flask routes

### `templates/index.html`

Contains the browser interface and JavaScript responsible for:

* Displaying the streamed game screen
* Detecting keyboard input
* Sending keyboard commands to Flask
* Maintaining the screen connection
* Closing the connection when a session expires

## Player Sessions

Each browser is assigned its own game session.

For example:

```text
Player A → Snake Game A
Player B → Snake Game B
Player C → Snake Game C
```

Players do not share the same Snake game or game state.

Sessions are tracked in memory and automatically removed after five minutes without actual player activity.

The screen stream itself does not reset the inactivity timer. Keyboard input and other player actions are what count as activity.

When a session expires, the server stops the associated game, removes the session from memory, and sends an expiration event to the browser so the browser closes its Server-Sent Events connection.

## Architecture

The project intentionally keeps the architecture small.

```text
                    Internet
                       │
                       ▼
                  Web Browser
                       │
                HTTP / SSE
                       │
                       ▼
                    Flask
                       │
              ┌────────┴────────┐
              │                 │
        Keyboard Input      Screen Stream
              │                 │
              ▼                 ▲
                    SnakeGame
                       │
                       ▼
                  Game State
```

The goal is not to recreate Snake as a JavaScript game.

Instead, the Python program remains the game engine and the browser acts as a remote interface for it.

## Why Flask?

Flask was chosen because the application only needs a small amount of web functionality.

The server needs to:

1. Serve the web page.
2. Receive keyboard input.
3. Maintain a screen stream.
4. Keep separate player sessions.
5. Run alongside the Python game loop.

Flask provides those capabilities without requiring a large application framework or complicated infrastructure.

## Security Considerations

This application is intentionally small and has a limited public interface.

The browser can only send the defined game inputs:

```text
UP
DOWN
LEFT
RIGHT
SPACE
CTRL_C
```

The application does not provide:

* Arbitrary command execution
* File uploads
* Arbitrary file access
* Shell access
* Database administration
* User-supplied code execution

User input is treated as data rather than executable code.

The application can still receive malformed or unexpected HTTP requests like any Internet-facing web application, so keeping dependencies updated and reviewing future code changes is recommended.

## Running Behind Cloudflare Tunnel

The application can be published through Cloudflare Tunnel without directly forwarding the Flask port through the home router.

Example architecture:

```text
Internet
   │
   ▼
Cloudflare
   │
   ▼
Cloudflare Tunnel
   │
   ▼
cloudflared
   │
   ▼
Flask :5000
   │
   ▼
Snake
```

This allows the application to have a public hostname while keeping the Flask listening port off the public Internet.

## License

This project is released under the MIT License.

See [`LICENSE`](LICENSE) for the full license text.

---

**Created by Beanz / Nathaniel**

A small experiment in taking a terminal-based Python application and putting a web interface in front of it.

## Repository

https://github.com/nxs8739/snake-web
