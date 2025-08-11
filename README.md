# 🐍 Snake Tournament

A competitive, AI-driven snake game built using Pygame. This project features a tournament-style system where multiple bots compete in rounds to determine the ultimate winner.

![Gameplay Screenshot](assets/Screenshot.png) 

[Game Description](https://www.canva.com/design/DAGljK4FwoY/MUPUNkEUZ-6tbTE-2l5Wgg/view?utm_content=DAGljK4FwoY&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h470378f78b)
---

## 🚀 Features

- AI-controlled snakes (Strategic, Greedy, Random, Custom)
- Tournament system with multiple rounds
- Traps, food, and collision detection
- Time-based survival advantage logic
- Extensible bot interface
- Human player support (`UserBot` placeholder)
- Configurable game settings

---

## 🛠️ Installation

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/snake-tournament.git
cd snake-tournament
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```
Make sure you have Python 3.8+ and pygame installed.

## 🎮 How to Play

Run the game:

```bash
python main.py
```

- Press `SPACE` to start a new tournament or begin the next round.  
- Press the close button or `CTRL+C` in the terminal to quit the game.

---

## 🤖 Available Bots

The following AI bots are included in the game:

| Bot            | Strategy Description                                           |
|--------------  |----------------------------------------------------------------|
| `RandomBot`    | Chooses directions randomly                                    |
| `GreedyBot`    | Moves toward the nearest food                                  |
| `StrategicBot` | Avoids traps, considers opponent position, seeks survival      |
| `CustomBot`    | Placeholder for your own custom logic                          |
| `UserBot`      | Allows human input (currently not active by default)           |

To change the bots used in the game, modify the following lines in `main.py` (or wherever `SnakeGame` is initialized):

```python
self.bot1 = StrategicBot()
self.bot2 = GreedyBot()
# self.user_bot = UserBot()
```

---

## ⚙️ Game Settings

You can tweak gameplay settings in `game_settings.py`, such as:

- `Segment_Penalty` 
- `round_time`
- `trap_count`
- `growth_per_food`
- `Colors`, `fonts`, and more

---

## 🧠 Tournament Logic

- A match consists of multiple rounds.
- If both bots tie in win count, a **tiebreaker round** is triggered.
- Each round can be won by:
  - Outlasting the opponent
  - Scoring more points (by collecting food)
- Special logic ensures fairness with timed **"survival advantage"** if one bot dies first due to self-collision.

---

## 📁 Project Structure

```
snake-tournament/
│
├── main.py               # Main game logic
├── game_settings.py      # Game config and constants
├── bot.py                # Bot strategies
├── tournament.py         # Tournament manager
├── README.md             # You're reading it!
└── requirements.txt      # Python dependencies
```

---

## ✅ TODOs

- [ ] Enable `UserBot` for human vs AI mode  
- [ ] Add more advanced AI strategies   
- [ ] Multiplayer support  

---

## 🧪 Example Output

Here's what a round result might look like in the console:

```
=== FINAL TOURNAMENT RESULTS ===
Total Rounds: 2
Draw Rounds: 0
Crashed Rounds: 0
StrategicBot: 1 wins, Total Apples: 18
GreedyBot: 2 wins, Total Apples: 20
```

---

## 📜 License

This project is licensed under the MIT License. Feel free to fork and modify it.

---

## 🙌 Contributions

Contributions are welcome! To add your own bot:

1. Open `bot.py`  
2. Implements a `decide_move(snake, food, opponent)` method or other logics
3. Instantiate your bot in `main.py`

**Example:**

```python
class UserBot(Bot):
    def __init__(self):
        super().__init__()
        self.name = "MyBot"
    
    def decide_move(self, snake, food, opponent=None):
        # Implement your custom logic here
        pass
```

---

## 🔗 Bugs Announcement
if you see bugs on the game please feel free and tell us in telegram account of each contributors 
---

## 👨‍💻 Author

Developed with ❤️ by [🧑‍💻Sepehr, 🧑‍💻Amir, 🧑‍💻Mohammad]

