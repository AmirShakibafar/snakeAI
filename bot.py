from typing import Tuple, Optional
from game_settings import Snake, Food, Trap, Direction, get_distance, is_safe
import random

class Bot:
    def __init__(self, name: str = "BaseBot"):
        self.name = name

    def decide_move(self,
                   snake: Snake,
                   food: Food,
                   traps: Trap,
                   opponent: Optional[Snake] = None) -> Tuple[int, int]:
        raise NotImplementedError

class RandomBot(Bot):
    def __init__(self):
        super().__init__("RandomBot")

    def decide_move(self, snake, food, traps, opponent=None):
        possible_moves = [Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN]
        possible_moves = [m for m in possible_moves if m != Direction.opposite(snake.direction)]
        
        safe_moves = []
        for move in possible_moves:
            new_head = [snake.get_head_position()[0] + move[0], snake.get_head_position()[1] + move[1]]
            if is_safe(snake, new_head, opponent, traps):
                safe_moves.append(move)
        
        if safe_moves:
            return random.choice(safe_moves)
        
        return random.choice(possible_moves) if possible_moves else snake.direction

class GreedyBot(Bot):
    def __init__(self):
        super().__init__("GreedyBot")

    def decide_move(self, snake, food, traps, opponent=None):
        head_pos = snake.get_head_position()
        current_dir = snake.direction

        if not food.positions:
            return current_dir

        closest_food = min(food.positions, key=lambda pos: get_distance(head_pos, pos))
        possible_moves = [Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN]
        possible_moves = [m for m in possible_moves if m != Direction.opposite(current_dir)]

        best_move = current_dir
        best_score = -float('inf')

        for move in possible_moves:
            new_head = [head_pos[0] + move[0], head_pos[1] + move[1]]
            if not is_safe(snake, new_head, opponent, traps):
                continue

            food_dist = get_distance(new_head, closest_food)
            score = 1000 / (food_dist + 1)
            
            if score > best_score:
                best_score = score
                best_move = move

        return best_move if best_score > -float('inf') else current_dir

class StrategicBot(Bot):
    def __init__(self):
        super().__init__("StrategicBot")

    def decide_move(self, snake, food, traps, opponent=None):
        head_pos = snake.get_head_position()
        current_dir = snake.direction
        possible_moves = [Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN]
        possible_moves = [m for m in possible_moves if m != Direction.opposite(current_dir)]

        best_move = current_dir
        best_score = -float('inf')

        for move in possible_moves:
            new_head = [head_pos[0] + move[0], head_pos[1] + move[1]]
            if not is_safe(snake, new_head, opponent, traps):
                continue

            # Base score is high, gets penalized by risk
            score = 1000.0
            
            # Food score
            if food.positions:
                closest_food = min(food.positions, key=lambda pos: get_distance(new_head, pos))
                food_dist = get_distance(new_head, closest_food)
                score += 500 / (food_dist + 1)
            
            # Opponent danger score
            if opponent and opponent.alive:
                dist_to_other = get_distance(new_head, opponent.get_head_position())
                if dist_to_other < 4 and opponent.length >= snake.length:
                    score -= 800 / (dist_to_other + 1) # High penalty for getting close to a larger/equal snake

            if score > best_score:
                best_score = score
                best_move = move

        return best_move if best_score > -float('inf') else current_dir

class CustomBot(Bot):
    def __init__(self):
        super().__init__("MyCustomBot")
    
    def decide_move(self, snake, food, traps, opponent=None):
        # Implement your custom logic here
        return Direction.RIGHT

class UserBot(Bot):
    def __init__(self):
        super().__init__("UserBot")
        self.next_move = None
    
    def decide_move(self, snake, food, traps, opponent=None):
        pass
    

