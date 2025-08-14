import pygame
import sys
from typing import Optional
from game_settings import (
    WIDTH, HEIGHT, GRID_SIZE, WALL_THICKNESS,  
    GameState, GameConfig, Snake, Food, Trap,
    generate_spawn_positions, BLACK, WHITE, GREEN,
    YELLOW, RED, PURPLE, GRID_COLOR, WALL_COLOR
)
from bot import RandomBot, GreedyBot, StrategicBot, CustomBot, UserBot
from tournament import Tournament

class SnakeGame:
    def __init__(self, bot_name1:str=None, bot_name2:str=None):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake Tournament")
        self.clock = pygame.time.Clock()
        
        self.font = pygame.font.SysFont('Arial', 24)
        self.medium_font = pygame.font.SysFont('Arial', 36)
        self.large_font = pygame.font.SysFont('Arial', 60, bold=True)
        
        self.config = GameConfig()
        self.game_state = GameState.START
        self.round_winner: Optional[str] = None
        self.final_winner: Optional[str] = None
        
        # Initialize tournament tracking
        self.tournament = Tournament(self.config)
        
        self.snake1: Optional[Snake] = None
        self.snake2: Optional[Snake] = None
        self.food: Optional[Food] = None
        self.traps: Optional[Trap] = None
    
        self.bot1 = StrategicBot()
        self.bot2 = GreedyBot()
        
        self.VALID_DIRECTIONS = {(0, 1), (0, -1), (1, 0), (-1, 0)}
        self.reset_round()
        
    def start_new_tournament(self) -> None:
        self.tournament = Tournament(self.config)
        self.game_state = GameState.PLAYING
        self.reset_round()

    def start_next_round(self) -> None:
        self.game_state = GameState.PLAYING
        self.reset_round(swap_positions=True)
    
    def reset_round(self, swap_positions: bool = False) -> None:
        spawn1, spawn2, layout = generate_spawn_positions()
        
        if swap_positions:
            spawn1, spawn2 = spawn2, spawn1
        
        self.snake1 = Snake(GREEN, (0, 200, 0), *spawn1, self.bot1.name)
        self.snake2 = Snake(YELLOW, (200, 200, 0), *spawn2, self.bot2.name)
        
        # Add these two lines to fix the names
        self.tournament.snake1_name = self.snake1.agent_id
        self.tournament.snake2_name = self.snake2.agent_id
        
        self.food = Food(0)
        self.food.positions = layout.copy()
        
        all_segments = self.snake1.segments + self.snake2.segments
        self.traps = Trap(self.config.trap_count)
        self.traps.spawn_multiple(self.config.trap_count, all_segments, self.food.positions)
        
        self.round_start_time = pygame.time.get_ticks() / 1000.0
    
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.game_state == GameState.GAME_OVER:
                        self.quit_game()
                    elif self.game_state == GameState.ROUND_OVER:
                        self.start_next_round()
                    elif self.game_state == GameState.START:
                        self.start_new_tournament()
            

    def quit_game(self) -> None:
        pygame.quit()
        sys.exit()
        
    def check_self_collisions(self):
        current_time = pygame.time.get_ticks() / 1000.0
        
        for snake in [self.snake1, self.snake2]:
            if not snake.alive:
                continue
                
            head = snake.get_head_position()
            body = snake.get_body_positions()
            
            # Check if head hit body
            if any(tuple(head) == tuple(segment) for segment in body):
                if not hasattr(snake, 'self_collision_start_time'):
                    snake.self_collision_start_time = current_time
                    snake.self_collision_delay = 3.0  # 3 second delay
                    snake.is_colliding_with_self = True
                    
                # Check if delay has passed
                if current_time - snake.self_collision_start_time >= snake.self_collision_delay:
                    snake.alive = False
                    snake.score = 0
                    snake.death_time = current_time
            else:
                # Only try to delete if attributes exist
                if hasattr(snake, 'is_colliding_with_self'):
                    delattr(snake, 'is_colliding_with_self')
                if hasattr(snake, 'self_collision_start_time'):
                    delattr(snake, 'self_collision_start_time')

    def draw_collision_warnings(self):
        current_time = pygame.time.get_ticks() / 1000.0
        
        for snake in [self.snake1, self.snake2]:
            if hasattr(snake, 'is_colliding_with_self') and snake.is_colliding_with_self:
                time_left = snake.self_collision_delay - (current_time - snake.self_collision_start_time)
                
                # Draw countdown
                font = pygame.font.SysFont('Arial', 20)
                countdown_text = font.render(f"{max(0, int(time_left))}s", True, (255, 0, 0))
                head_pos = snake.get_head_position()
                text_pos = (head_pos[0] * GRID_SIZE, head_pos[1] * GRID_SIZE - 25)
                self.screen.blit(countdown_text, text_pos)
                
                # Flash effect
                if int(time_left * 2) % 2 == 0:
                    pygame.draw.rect(
                        self.screen, (255, 0, 0),
                        (head_pos[0] * GRID_SIZE, head_pos[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE),
                        2
                    )

    def handle_snake_on_snake_collision(self) -> None:
        if not self.snake1.alive or not self.snake2.alive: return
        if self.snake1.shield_timer > 0 or self.snake2.shield_timer > 0: return

        head1 = self.snake1.get_head_position()
        head2 = self.snake2.get_head_position()
        
        body1_set = set(tuple(seg) for seg in self.snake1.get_body_positions())
        body2_set = set(tuple(seg) for seg in self.snake2.get_body_positions())

        # Check collision types
        head_to_head = tuple(head1) == tuple(head2)
        s1_hits_s2_body = tuple(head1) in body2_set
        s2_hits_s1_body = tuple(head2) in body1_set

        current_time = pygame.time.get_ticks() / 1000.0
    
        # Apply penalties based on collision type
        if head_to_head or s1_hits_s2_body or s2_hits_s1_body:
            if current_time - self.snake1.last_collision_time < 1.0:
                self.snake1.consecutive_collisions += 1
            if current_time - self.snake2.last_collision_time < 1.0:
                self.snake2.consecutive_collisions += 1
                
            self.snake1.last_collision_time = current_time
            self.snake2.last_collision_time = current_time
            # Check for 3 consecutive collisions
            if (self.snake1.consecutive_collisions >= 3 or 
                self.snake2.consecutive_collisions >= 3):
                self.snake1.score = 0
                self.snake2.score = 0
                return
            
            len1, len2 = self.snake1.length, self.snake2.length
            penalty = self.config.collision_segment_penalty

            if len1 < len2:
                self.apply_collision_penalty(self.snake1, penalty)
            elif len2 < len1:
                self.apply_collision_penalty(self.snake2, penalty)
            else:
                self.apply_collision_penalty(self.snake1, penalty//2)
                self.apply_collision_penalty(self.snake2, penalty//2)
              
    def apply_collision_penalty(self, snake: Snake, penalty: int):
        """Helper method to apply collision penalties"""
        for _ in range(penalty):
            if len(snake.segments) > 0:
                if snake.grow > 0:
                    snake.grow -= 1
                else:
                    snake.segments.pop()
                snake.length -= 1
        snake.shield_timer = self.config.shield_duration
        snake.score = max(0, snake.score - penalty)  # Deduct score
        snake.collisions += 1
                
    def check_food_and_trap_collisions(self) -> None:
        for snake in [self.snake1, self.snake2]:
            if not snake.alive: continue
            if self.food.check_collision(snake.get_head_position()):
                snake.grow += self.config.growth_per_food
                snake.score += 1
            self.traps.check_collision(snake)

    def start_new_game(self) -> None:
        self.game_state = GameState.PLAYING
        self.reset_round()
    
    def update(self) -> None:
        if self.game_state != GameState.PLAYING: return

        for snake, bot, opponent in [(self.snake1, self.bot1, self.snake2), (self.snake2, self.bot2, self.snake1)]:
            if snake.alive:
                move = bot.decide_move(snake, self.food, self.traps, opponent)
                if move in self.VALID_DIRECTIONS:
                    snake.change_direction(move)
                snake.update(self.clock.get_time() / 1000.0)
        
        self.check_self_collisions()
        self.check_food_and_trap_collisions()
        self.handle_snake_on_snake_collision()

        for snake in [self.snake1, self.snake2]:
            if snake.alive and snake.length < 1:
                snake.alive = False
                snake.death_time = pygame.time.get_ticks() / 1000.0

        if self.check_round_end():
            self.handle_round_end()
            
    def check_round_end(self) -> bool:
        elapsed = (pygame.time.get_ticks() / 1000.0) - self.round_start_time
        time_up = elapsed >= self.config.round_time
        one_or_both_dead = not self.snake1.alive or not self.snake2.alive
        no_food = len(self.food.positions) == 0
        return time_up or one_or_both_dead or no_food
    
    def handle_round_end(self) -> None:
        if self.snake1.alive and not self.snake2.alive:
            self.round_winner = self.snake1.agent_id
        elif self.snake2.alive and not self.snake1.alive:
            self.round_winner = self.snake2.agent_id
        else:
            if self.snake1.score > self.snake2.score: self.round_winner = self.snake1.agent_id
            elif self.snake2.score > self.snake1.score: self.round_winner = self.snake2.agent_id
            else: self.round_winner = None
        
        self.tournament.record_round(
            winner=self.round_winner,
            snake1_score=self.snake1.score,
            snake2_score=self.snake2.score,
            snake1_traps_hit=self.snake1.traps_hit,
            snake2_traps_hit=self.snake2.traps_hit,
            snake1_collisions=self.snake1.collisions,
            snake2_collisions=self.snake2.collisions
        )

        # Check tournament status
        if self.tournament.is_tournament_over():
            self.final_winner = self.tournament.get_winner()
            self.show_final_results()
            self.tournament.save_to_csv()
            self.game_state = GameState.GAME_OVER
        else:
            self.game_state = GameState.ROUND_OVER
    
    def show_final_results(self) -> None:
        print("\n=== FINAL TOURNAMENT RESULTS ===")
        print(f"Total Rounds Played: {len(self.tournament.results)}")
        print(f"Draws: {self.tournament.draw_rounds}")
        
        s1_name = self.tournament.snake1_name
        s2_name = self.tournament.snake2_name
        
        print(f"\n--- {s1_name} ---")
        print(f"Wins: {self.tournament.snake1_wins}")
        print(f"Total Score: {self.tournament.total_snake1_apples}")
        print(f"Traps Hit: {self.tournament.snake1_total_traps}")
        
        print(f"\n--- {s2_name} ---")
        print(f"Wins: {self.tournament.snake2_wins}")
        print(f"Total Score: {self.tournament.total_snake2_apples}")
        print(f"Traps Hit: {self.tournament.snake2_total_traps}")
        
        if self.final_winner:
            print(f"\n>>> TOURNAMENT WINNER: {self.final_winner}! <<<")
        else:
            print("\n>>> TOURNAMENT ENDED IN A DRAW! <<<")
        
  
    def draw(self) -> None:
        self.screen.fill(BLACK)
        if self.game_state == GameState.PLAYING:
            self.draw_playing()
        elif self.game_state == GameState.START:
            self.draw_start_screen()
        elif self.game_state == GameState.ROUND_OVER:
            self.draw_round_over()
        elif self.game_state in (GameState.GAME_OVER, GameState.DRAW):
            self.draw_tournament_end()
        pygame.display.flip()
        
    def draw_playing(self) -> None:
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (WIDTH, y))
        pygame.draw.rect(self.screen, WALL_COLOR, (0, 0, WIDTH, HEIGHT), WALL_THICKNESS)
        
        self.food.draw(self.screen)
        self.traps.draw(self.screen)
        self.snake1.draw(self.screen)
        self.snake2.draw(self.screen)
        
        elapsed_game_time = (pygame.time.get_ticks() / 1000.0) - self.round_start_time
        time_left = max(0, self.config.round_time - elapsed_game_time)
        time_text = f"Time: {int(time_left)}s"
        self.draw_scores(time_text)
    
    def draw_scores(self, time_text: str) -> None:
        score1_text = f"{self.snake1.agent_id}: {self.snake1.score}"
        score2_text = f"{self.snake2.agent_id}: {self.snake2.score}"
        round_text = "Snake AI"
        
        score1_surface = self.font.render(score1_text, True, GREEN)
        score2_surface = self.font.render(score2_text, True, YELLOW)
        round_surface = self.font.render(round_text, True, WHITE)
        time_surface = self.font.render(time_text, True, WHITE)
        
        self.screen.blit(score1_surface, (10, 10))
        self.screen.blit(score2_surface, (WIDTH - score2_surface.get_width() - 10, 10))
        self.screen.blit(round_surface, (WIDTH // 2 - round_surface.get_width() // 2, 10))
        self.screen.blit(time_surface, (WIDTH // 2 - time_surface.get_width() // 2, HEIGHT - 30))

    def draw_start_screen(self) -> None:
        title = self.large_font.render("Snake AI Tournament", True, GREEN)
        instruction = self.medium_font.render("Press SPACE to Begin", True, WHITE)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
        self.screen.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, HEIGHT // 2))

    def draw_round_over(self) -> None:
        title_text = f"Round {self.tournament.current_round - 1} Over"
        title = self.large_font.render(title_text, True, WHITE)

        if self.round_winner:
            winner_color = GREEN if self.round_winner == self.snake1.agent_id else YELLOW
            result = self.medium_font.render(f"{self.round_winner} wins!", True, winner_color)
        else:
            result = self.medium_font.render("Round Draw!", True, WHITE)

        # Show overall tournament score
        score_text = f"{self.tournament.snake1_name} {self.tournament.snake1_wins} - {self.tournament.snake2_wins} {self.tournament.snake2_name}"
        score_surface = self.font.render(score_text, True, WHITE)

        instruction = self.font.render("Press SPACE for Next Round", True, WHITE)
        
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))
        self.screen.blit(result, (WIDTH // 2 - result.get_width() // 2, HEIGHT // 2 - 50))
        self.screen.blit(score_surface, (WIDTH // 2 - score_surface.get_width() // 2, HEIGHT // 2 + 20))
        self.screen.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, HEIGHT // 2 + 80))

    def draw_tournament_end(self) -> None:
        title = self.large_font.render("Tournament Over", True, RED)
        
        if self.final_winner:
            winner_color = GREEN if self.final_winner == self.snake1.agent_id else YELLOW
            winner_text = self.medium_font.render(f"Winner: {self.final_winner}", True, winner_color)
        else:
            winner_text = self.medium_font.render("Tournament is a Draw!", True, WHITE)
            
        final_score_text = f"Final Score: {self.tournament.snake1_wins} - {self.tournament.snake2_wins}"
        final_score_surface = self.font.render(final_score_text, True, WHITE)

        instruction = self.font.render("Press SPACE to Exit", True, WHITE)
        
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
        self.screen.blit(winner_text, (WIDTH//2 - winner_text.get_width()//2, HEIGHT//2 - 70))
        self.screen.blit(final_score_surface, (WIDTH//2 - final_score_surface.get_width()//2, HEIGHT//2))
        self.screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT//2 + 100))
        
    def run(self) -> None:
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

if __name__ == "__main__":
    game = SnakeGame()
    game.run()