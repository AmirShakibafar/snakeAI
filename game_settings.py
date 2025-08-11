from dataclasses import dataclass
from enum import Enum, auto
import pygame
from typing import Tuple, List, Deque, Optional
from collections import deque
import random
import math

# Constants
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
SNAKE_SPEED = 10
WALL_THICKNESS = 10

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (50, 255, 50)
DARK_GREEN = (0, 200, 0)
YELLOW = (255, 255, 0)
DARK_YELLOW = (200, 200, 0)
RED = (255, 50, 50)
PURPLE = (150, 50, 200)
GRID_COLOR = (40, 40, 40)
WALL_COLOR = (50, 50, 100)
SHIELD_BLUE = (100, 100, 255)

class GameState(Enum):
    START = auto()
    PLAYING = auto()
    GAME_OVER = auto()
    DRAW = auto()
    ROUND_OVER = auto()

@dataclass
class GameConfig:
    tournament_mode: bool = True
    max_rounds: int = 3
    round_time: int = 20
    trap_count: int = 15
    trap_penalty: int = 2
    trap_segment_penalty: int = 4
    head_collision_penalty: int = 4
    body_collision_penalty: int = 3
    shield_duration: float = 2.0
    collision_segment_penalty: int = 2 
    initial_food: int = 35
    growth_per_food: int = 2
    min_snake_length: int = 1
    advantage_time: int = 5
    early_victory_diff: int = 30
    min_rounds_for_early_victory: int = 2

class Direction:
    RIGHT = (1, 0)
    LEFT = (-1, 0)
    UP = (0, -1)
    DOWN = (0, 1)

    @staticmethod
    def opposite(direction: Tuple[int, int]) -> Tuple[int, int]:
        return (-direction[0], -direction[1])

class GameObject:
    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError

class Snake(GameObject):
    def __init__(self, color_primary: Tuple[int, int, int],
                 color_secondary: Tuple[int, int, int],
                 start_x: int, start_y: int,
                 agent_id: str = "player"):
        self.collision_penalty = 0
        self.consecutive_collisions = 0
        self.last_collision_time = 0
        self.color_primary = color_primary
        self.color_secondary = color_secondary
        self.config = GameConfig()
        self.death_time = float('inf')
        self.agent_id = agent_id
        self.self_collision_start_time = 0
        self.self_collision_delay = 3.0
        self.is_colliding_with_self = False
        self.reset(start_x, start_y)

    def reset(self, start_x: int, start_y: int) -> None:
        self.segments: Deque[List[int]] = deque([[start_x, start_y]])
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.speed = SNAKE_SPEED
        self.grow = 0
        self.length = 1
        self.alive = True
        self.score = 0
        self.death_time = float('inf')
        self.move_timer = 0
        self.shield_timer = 0
        self.shield_flash = 0
        self.self_collision = False
        self.traps_hit = 0
        self.collisions = 0
        self.collision_types = []

    def get_head_position(self) -> List[int]:
        return self.segments[0][:]

    def get_body_positions(self) -> List[List[int]]:
        # Fixed the deque slicing TypeError
        return [segment[:] for segment in list(self.segments)[1:]]

    def update(self, dt:float) -> bool:
        if not self.alive:
            return False
        
        if self.shield_timer > 0:
            self.shield_timer -= dt
            self.shield_flash = (self.shield_flash + dt * 10) % 1

        self.move_timer += dt
        move_interval = 1.0 / self.speed
        
        if self.move_timer >= move_interval:
            self.move_timer = 0
            self.direction = self.next_direction
            
            head_x, head_y = self.segments[0]
            new_head = [
                head_x + self.direction[0],
                head_y + self.direction[1]
            ]
            
            if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or
                new_head[1] < 0 or new_head[1] >= GRID_HEIGHT):
                self.alive = False
                self.death_time = pygame.time.get_ticks() / 1000.0
                return False

            self.segments.appendleft(new_head)

            if self.grow > 0:
                self.grow -= 1
                self.length += 1
            else:
                self.segments.pop()

            for segment in list(self.segments)[1:]:
                if new_head == segment:
                    self.alive = False
                    self.self_collision = True
                    self.score = 0
                    self.death_time = pygame.time.get_ticks() / 1000.0
                    return False
                
        return True
    
    def check_collision_with_other(self, other_snake: 'Snake') -> None:
        # This logic is now handled centrally in the SnakeGame class
        pass
    
    def change_direction(self, new_dir: Tuple[int, int]) -> None:
        if new_dir != Direction.opposite(self.direction):
            self.next_direction = new_dir

    def draw(self, surface: pygame.Surface) -> None:
        for i, segment in enumerate(self.segments):
            color = self.color_primary if i % 2 == 0 else self.color_secondary
            pixel_x = segment[0] * GRID_SIZE + GRID_SIZE // 2
            pixel_y = segment[1] * GRID_SIZE + GRID_SIZE // 2

            if self.shield_timer > 0 and self.shield_flash < 0.5:
                shield_color = SHIELD_BLUE
                pygame.draw.circle(
                    surface, shield_color,
                    (pixel_x, pixel_y),
                    GRID_SIZE//2 + 2, 2
                )
            
            if i == 0:
                cx, cy = pixel_x, pixel_y
                half = GRID_SIZE // 2
                if self.direction == (1, 0):
                    points = [(cx + half, cy), (cx - half, cy - half), (cx - half, cy + half)]
                elif self.direction == (-1, 0):
                    points = [(cx - half, cy), (cx + half, cy - half), (cx + half, cy + half)]
                elif self.direction == (0, -1):
                    points = [(cx, cy - half), (cx - half, cy + half), (cx + half, cy + half)]
                else:
                    points = [(cx, cy + half), (cx - half, cy - half), (cx + half, cy - half)]

                pygame.draw.polygon(surface, self.color_primary, points)

                eye_size = GRID_SIZE // 5
                pupil_size = eye_size // 2

                if self.direction == (1, 0):
                    left_eye_pos = (pixel_x - GRID_SIZE//4, pixel_y - GRID_SIZE//4)
                    right_eye_pos = (pixel_x - GRID_SIZE//4, pixel_y + GRID_SIZE//4)
                elif self.direction == (-1, 0):
                    left_eye_pos = (pixel_x + GRID_SIZE//4, pixel_y - GRID_SIZE//4)
                    right_eye_pos = (pixel_x + GRID_SIZE//4, pixel_y + GRID_SIZE//4)
                elif self.direction == (0, 1):
                    left_eye_pos = (pixel_x - GRID_SIZE//4, pixel_y - GRID_SIZE//4)
                    right_eye_pos = (pixel_x + GRID_SIZE//4, pixel_y - GRID_SIZE//4)
                else:
                    left_eye_pos = (pixel_x - GRID_SIZE//4, pixel_y + GRID_SIZE//4)
                    right_eye_pos = (pixel_x + GRID_SIZE//4, pixel_y + GRID_SIZE//4)

                pygame.draw.circle(surface, WHITE, left_eye_pos, eye_size)
                pygame.draw.circle(surface, WHITE, right_eye_pos, eye_size)
                pygame.draw.circle(surface, BLACK, left_eye_pos, pupil_size)
                pygame.draw.circle(surface, BLACK, right_eye_pos, pupil_size)
            else:
                pygame.draw.rect(
                    surface,
                    color,
                    (segment[0] * GRID_SIZE, segment[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                )

class Food(GameObject):
    def __init__(self, num_foods: int = 1):
        self.num_foods = num_foods
        self.positions: List[Tuple[int, int]] = []

    def spawn(self, snake_segments: Optional[List[List[int]]] = None) -> Optional[Tuple[int, int]]:
        for _ in range(100):
            position = (random.randint(1, GRID_WIDTH - 2), random.randint(1, GRID_HEIGHT - 2))
            if snake_segments and any(position == (seg[0], seg[1]) for seg in snake_segments):
                continue
            if position not in self.positions:
                return position
        return None

    def spawn_multiple(self, num_foods: int, snake_segments: Optional[List[List[int]]] = None) -> None:
        self.positions = []
        for _ in range(num_foods):
            new_food = self.spawn(snake_segments)
            if new_food:
                self.positions.append(new_food)

    def check_collision(self, head_position: List[int]) -> bool:
        for i, pos in enumerate(self.positions):
            if head_position == [pos[0], pos[1]]:
                self.positions.pop(i)
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        for pos in self.positions:
            pixel_x = pos[0] * GRID_SIZE + GRID_SIZE // 2
            pixel_y = pos[1] * GRID_SIZE + GRID_SIZE // 2
            pygame.draw.circle(surface, RED, (pixel_x, pixel_y), GRID_SIZE // 2 - 2)
            pygame.draw.rect(surface, DARK_GREEN, (pixel_x - 2, pixel_y - GRID_SIZE // 2, 4, GRID_SIZE // 4))

class Trap(GameObject):
    def __init__(self, num_traps: int = 3):
        self.config = GameConfig()
        self.num_traps = num_traps
        self.positions: List[Tuple[int, int]] = []
        
    def get_positions(self) -> List[Tuple[int, int]]:
        return self.positions.copy()

    def spawn(self,
          snake_segments: Optional[List[List[int]]] = None,
          food_positions: Optional[List[Tuple[int, int]]] = None) -> Optional[Tuple[int, int]]:
        for _ in range(100):
            position = (random.randint(1, GRID_WIDTH - 2), random.randint(1, GRID_HEIGHT - 2))
            if snake_segments and any(position == (seg[0], seg[1]) for seg in snake_segments):
                continue
            if food_positions and position in food_positions:
                continue
            if position not in self.positions:
                return position
        return None

    def spawn_multiple(self,
                  num_traps: int,
                  snake_segments: Optional[List[List[int]]] = None,
                  food_positions: Optional[List[Tuple[int, int]]] = None) -> None:
        self.positions = []
        for _ in range(num_traps):
            new_trap = self.spawn(snake_segments, food_positions)
            if new_trap:
                self.positions.append(new_trap)

    def check_collision(self, snake: Snake) -> bool:
        """Check if snake collides with trap"""
        head = snake.get_head_position()
        for i, pos in enumerate(self.positions):
            if head == [pos[0], pos[1]]:
                snake.traps_hit += 1
                snake.score = max(0, snake.score - self.config.trap_penalty)
                
                for _ in range(self.config.trap_segment_penalty):
                    if len(snake.segments) > 0: 
                        if snake.grow > 0:
                            snake.grow -= 1
                        else:
                            snake.segments.pop()
                        snake.length -= 1
                
                snake.shield_timer = self.config.shield_duration
                self.positions.pop(i)
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        for pos in self.positions:
            pixel_x = pos[0] * GRID_SIZE + GRID_SIZE // 2
            pixel_y = pos[1] * GRID_SIZE + GRID_SIZE // 2
            pygame.draw.circle(surface, PURPLE, (pixel_x, pixel_y), GRID_SIZE // 3)
            pygame.draw.line(surface, BLACK, (pixel_x - GRID_SIZE // 4, pixel_y - GRID_SIZE // 4), (pixel_x + GRID_SIZE // 4, pixel_y + GRID_SIZE // 4), 3)
            pygame.draw.line(surface, BLACK, (pixel_x + GRID_SIZE // 4, pixel_y - GRID_SIZE // 4), (pixel_x - GRID_SIZE // 4, pixel_y + GRID_SIZE // 4), 3)

def get_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
    return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1])

def generate_spawn_positions() -> Tuple[Tuple[int, int], Tuple[int, int], List[Tuple[int, int]]]:
    # Generate snake positions first
    s1 = (random.randint(1, GRID_WIDTH // 3), random.randint(1, GRID_HEIGHT - 2))
    s2 = (random.randint(2 * GRID_WIDTH // 3, GRID_WIDTH - 2), 
          random.randint(1, GRID_HEIGHT - 2))
    
    # Create quadrants for balanced distribution
    quadrants = [
        (1, GRID_WIDTH // 2, 1, GRID_HEIGHT // 2),       # Top-left
        (GRID_WIDTH // 2, GRID_WIDTH - 2, 1, GRID_HEIGHT // 2),  # Top-right
        (1, GRID_WIDTH // 2, GRID_HEIGHT // 2, GRID_HEIGHT - 2),  # Bottom-left
        (GRID_WIDTH // 2, GRID_WIDTH - 2, GRID_HEIGHT // 2, GRID_HEIGHT - 2)  # Bottom-right
    ]
    
    fruit_positions = []
    apples_per_quadrant = 8  # Distribute apples evenly
    
    for q in quadrants:
        min_x, max_x, min_y, max_y = q
        for _ in range(apples_per_quadrant):
            pos = (random.randint(min_x, max_x), random.randint(min_y, max_y))
            while pos in [s1, s2] or pos in fruit_positions:
                pos = (random.randint(min_x, max_x), random.randint(min_y, max_y))
            fruit_positions.append(pos)
    
    # Add some random apples for variety
    for _ in range(8):
        pos = (random.randint(1, GRID_WIDTH - 2), random.randint(1, GRID_HEIGHT - 2))
        while pos in [s1, s2] or pos in fruit_positions:
            pos = (random.randint(1, GRID_WIDTH - 2), random.randint(1, GRID_HEIGHT - 2))
        fruit_positions.append(pos)
    
    return s1, s2, fruit_positions

def is_safe(snake: Snake, new_head_pos: List[int], other_snake: Optional[Snake], traps: Trap) -> bool:
    """
    Check if a position is safe for the snake to move to
    """
    # Wall collision
    if not (0 <= new_head_pos[0] < GRID_WIDTH and 0 <= new_head_pos[1] < GRID_HEIGHT):
        return False
    
    # Self-collision
    if new_head_pos in snake.segments:
        return False

    # Other snake collision
    if other_snake and new_head_pos in other_snake.segments:
        return False

    # Trap collision (compare tuple against tuple)
    if tuple(new_head_pos) in traps.positions:
        return False

    return True