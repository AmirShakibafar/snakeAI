from typing import Tuple, Optional, List
from game_settings import Snake, Food, Direction, get_distance, is_safe
import random
import math


class Bot:
    """
    Base class for all snake agents.
    Subclasses must implement the decide_move() method.
    Adding Some Function for getting_possible_moves and so on and changing other bot classes
    """
    def __init__(self, name: str = "BaseBot"):
        self.name = name
        self.config = {
            'food_weight': 100,
            'mobility_weight': 20,
            'danger_weight': 150,
            'prediction_depth': 3
        }
    
    def decide_move(self, 
                   snake: Snake, 
                   food: Food, 
                   opponent: Optional[Snake] = None) -> Tuple[int, int]:
        """
        Determine the next move for the snake.
        Args:
            snake: The snake being controlled
            food: Food objects in the game
            opponent: Optional opponent snake
        Returns:
            Tuple[int, int]: Direction vector (dx, dy)
        """
        raise NotImplementedError

class RandomBot(Bot):
    """Moves randomly"""
    def __init__(self):
        super().__init__()
        self.name = "RandomBot"
    
    def decide_move(self, snake, food, opponent=None):
        possible_moves = [Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN]
        possible_moves = [m for m in possible_moves if m != Direction.opposite(snake.direction)]
        return random.choice(possible_moves)

class GreedyBot(Bot):
    """Goes for nearest food"""
    def __init__(self):
        super().__init__()
        self.name = "GreedyBot"
    
    def decide_move(self, snake, food, opponent=None):
        head_pos = snake.get_head_position()
        current_dir = snake.direction

        if not food.positions:
            return current_dir

        # Find closest food
        closest_food = min(food.positions, key=lambda pos: get_distance(head_pos, pos))

        possible_moves = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        possible_moves = [move for move in possible_moves if move != (-current_dir[0], -current_dir[1])]

        best_move = current_dir
        best_score = -float('inf')

        for move in possible_moves:
            new_head = [head_pos[0] + move[0], head_pos[1] + move[1]]
            if not is_safe(snake, new_head, opponent):
                continue

            # Calculate food proximity score
            food_dist = get_distance(new_head, closest_food)
            food_score = 1 / (food_dist + 1e-5) * 100  # Avoid division by zero

            # Calculate mobility score
            mobility = 0
            next_moves = [m for m in [(1,0), (-1,0), (0,1), (0,-1)] if m != (-move[0], -move[1])]
            for next_move in next_moves:
                next_head_pos = [new_head[0] + next_move[0], new_head[1] + next_move[1]]
                if is_safe(snake, next_head_pos, opponent):
                    mobility += 1

            # Calculate danger score
            danger = 0
            if opponent and opponent.alive:
                other_head = opponent.get_head_position()
                dist_to_other = get_distance(new_head, other_head)
                if dist_to_other < 4 and len(opponent.segments) >= len(snake.segments):
                    danger = 1
                    # Predict other snake's movement
                    other_dir = opponent.direction
                    predicted_other_head = [other_head[0] + other_dir[0], other_head[1] + other_dir[1]]
                    if new_head == predicted_other_head:
                        danger += 1

            total_score = food_score + mobility * 15 - danger * 100
            if total_score > best_score:
                best_score = total_score
                best_move = move

        return best_move
        

class StrategicBot(Bot):
    """Avoids opponent and traps"""
    def __init__(self):
        super().__init__()
        self.name = "StrategicBot"
    
    def decide_move(self, snake, food, opponent=None):
        head_pos = snake.get_head_position()
        current_dir = snake.direction

        if not food.positions:
            return current_dir

        # Find safest food considering other snake
        food_scores = []
        for f in food.positions:
            base_score = 1 / (get_distance(head_pos, f) + 1e-5)
            # Penalize food close to other snake
            if opponent:
                other_dist = get_distance(f, opponent.get_head_position())
                base_score *= max(0.1, 1 - (1 / (other_dist + 1)))
            food_scores.append(base_score)
        target_food = food.positions[food_scores.index(max(food_scores))]

        possible_moves = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        possible_moves = [move for move in possible_moves if move != (-current_dir[0], -current_dir[1])]

        best_move = current_dir
        best_score = -float('inf')

        for move in possible_moves:
            new_head = [head_pos[0] + move[0], head_pos[1] + move[1]]
            if not is_safe(snake, new_head, opponent):
                continue

            # Food proximity
            food_dist = get_distance(new_head, target_food)
            food_score = 1 / (food_dist + 1e-5) * 100

            # Mobility
            mobility = 0
            next_moves = [m for m in [(1,0), (-1,0), (0,1), (0,-1)] if m != (-move[0], -move[1])]
            for next_move in next_moves:
                next_head_pos = [new_head[0] + next_move[0], new_head[1] + next_move[1]]
                if is_safe(snake, next_head_pos, opponent):
                    mobility += 1

            # Advanced danger detection
            danger = 0
            if opponent and opponent.alive:
                # Check if other snake is targeting same area
                other_path = []
                temp_head = opponent.get_head_position()
                for _ in range(3):  # Predict next 3 moves
                    temp_head = [temp_head[0] + opponent.direction[0], 
                                temp_head[1] + opponent.direction[1]]
                    other_path.append(temp_head)
                if new_head in other_path:
                    danger += 2

                # Space around other snake
                other_space = 0
                for m in [(1,0), (-1,0), (0,1), (0,-1)]:
                    check_pos = [temp_head[0] + m[0], temp_head[1] + m[1]]
                    if is_safe(opponent, check_pos, snake):
                        other_space += 1
                if other_space <= 1:  # Other snake in tight space
                    danger -= 1  # Less dangerous

            total_score = food_score + mobility * 20 - danger * 150
            if total_score > best_score:
                best_score = total_score
                best_move = move

        return best_move

# User implements their bot by extending the Bot class
class CustomBot(Bot):
    def __init__(self):
        super().__init__()
        self.name = "MyCustomBot"
    
    def decide_move(self, snake, food, opponent=None):
        # Implement your custom logic here
        pass
    
# User implements their bot by extending the Bot class
class UserBot(Bot):
    def __init__(self):
        super().__init__()
        self.name = "MyBot"
    
    def decide_move(self, snake, food, opponent=None):
        # Implement your custom logic here
        return (0, 3)