import pygame
import sys
from typing import Optional, Tuple, List
from collections import deque
from game_settings import (
    WIDTH, HEIGHT, GRID_SIZE, GRID_WIDTH, GRID_HEIGHT,
    GameState, GameConfig, Snake, Food, Trap,
    generate_spawn_positions, BLACK, WHITE, GREEN,
    YELLOW, RED, PURPLE, GRID_COLOR, WALL_COLOR, DARK_GREEN, DARK_YELLOW, WALL_THICKNESS
)
from bot import RandomBot, GreedyBot, StrategicBot, CustomBot, UserBot
from tournament import Tournament

class SnakeGame:
    def __init__(self, bot_name1:str=None, bot_name2:str=None):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake Tournament")
        self.clock = pygame.time.Clock()
        self.displayed_round = 1
        
        # Fonts
        self.font = pygame.font.SysFont('Arial', 24)
        self.medium_font = pygame.font.SysFont('Arial', 36)
        self.large_font = pygame.font.SysFont('Arial', 60, bold=True)
        
        # Game state
        self.config = GameConfig()
        self.game_state = GameState.START
        self.current_round = 1
        self.round_winner: Optional[str] = None
        self.final_winner: Optional[str] = None
        
        # Initialize tournament tracking
        self.tournament = Tournament(self.config)
        
        # Tournament tracking
        self.tournament.snake1_wins = 0
        self.tournament.snake2_wins = 0
        self.tournament.snake1_name = None
        self.tournament.snake2_name = None
        self.losers_bracket = []
        self.rematches = []
        
        # Game objects
        self.snake1: Optional[Snake] = None
        self.snake2: Optional[Snake] = None
        self.food: Optional[Food] = None
        self.traps: Optional[Trap] = None
    
        # Initialize bots
        # you can add your bots here...
        self.bot1 = StrategicBot()  # Default AI
        self.bot2 = UserBot()     # Default AI
        # self.user_bot = UserBot()   # For human player
        
        self._name_handling(bot_name1, bot_name2)
        # for self collision handlig
        self.snake1_advantage_time = 0
        self.snake2_advantage_time = 0
        self.snake1_advantage_start = 0
        self.snake2_advantage_start = 0
    
    
        self.VALID_DIRECTIONS = {(0, 1), (0, -1), (1, 0), (-1, 0)}
    
        # Initialize game
        self.reset_round()
    
    def _name_handling(self, name1:str, name2:str):
        if type(self.bot1) == type(self.bot2):
            if name1 and name2 is not None:
                self.bot1.name = name1
                self.bot2.name = name2
            
            else:
                self.bot1.name = "Snake1"
                self.bot2.name = "Snake2"
        
    
    def reset_round(self, swap_positions: bool = False) -> None:
        """Initialize or reset the current round"""
        spawn1, spawn2, layout = generate_spawn_positions()
        
        if swap_positions:
            spawn1, spawn2 = spawn2, spawn1
        
        self.snake1_advantage_time = 3.0  
        self.snake2_advantage_time = 3.0
        self.snake1_advantage_start = pygame.time.get_ticks() / 1000.0
        self.snake2_advantage_start = pygame.time.get_ticks() / 1000.0
        
        self.snake1 = Snake(GREEN, DARK_GREEN, *spawn1, self.bot1.name)
        self.snake2 = Snake(YELLOW, DARK_YELLOW, *spawn2, self.bot2.name)
        
        # Initialize food with positions from layout
        self.food = Food(0)
        self.food.positions = layout.copy()  
        
        self.tournament.snake1_name = self.snake1.agent_id
        self.tournament.snake2_name = self.snake2.agent_id
        
        # Initialize traps with food positions to avoid
        self.traps = Trap(self.config.trap_count)
        self.traps.spawn_multiple(
            self.config.trap_count,
            self.snake1.segments + self.snake2.segments,
            self.food.positions
        )
        self.displayed_round = self.tournament.current_round
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
                    elif self.game_state in [GameState.START, GameState.DRAW]:
                        self.start_new_tournament()

    def quit_game(self) -> None:
        """Clean up and exit the game"""
        pygame.quit()
        sys.exit()
    
    def check_collisions(self) -> None:
        """Check all game collisions"""
        # Check food collisions
        if self.snake1.alive and self.food.check_collision(self.snake1.get_head_position()):
            self.snake1.grow += self.config.growth_per_food
            self.snake1.score += 1

        if self.snake2.alive and self.food.check_collision(self.snake2.get_head_position()):
            self.snake2.grow += self.config.growth_per_food
            self.snake2.score += 1

        # Check trap collisions
        if self.snake1.alive:
            self.traps.check_collision(self.snake1)
        if self.snake2.alive:
            self.traps.check_collision(self.snake2)

        # Check snake collisions
        if self.snake1.alive and self.snake2.alive:
            self.snake1.check_collision_with_other(self.snake2)
            self.snake2.check_collision_with_other(self.snake1)

    def start_new_tournament(self) -> None:
        """Reset everything for a new tournament"""
        self.tournament = Tournament(self.config)
        self.tournament.snake1_wins = 0  # Explicitly reset
        self.tournament.snake2_wins = 0  # Explicitly reset
        self.game_state = GameState.PLAYING
        self.current_round = 1
        self.reset_round()
    
    def start_next_round(self) -> None:
        """Prepare for the next round in the tournament"""
        # Check if this is a tiebreaker round
        is_tiebreaker = (self.tournament.current_round > self.tournament.config.max_rounds and
                        self.tournament.snake1_wins != self.tournament.snake2_wins and
                        sum(r["snake1_score"] for r in self.tournament.results) == 
                        sum(r["snake2_score"] for r in self.tournament.results))
        
        if is_tiebreaker:
            print("\n=== TIEBREAKER ROUND ===")
            self.displayed_round = "TB"  # Special display for tiebreaker
        else:
            self.displayed_round = self.tournament.current_round
        
        # Reset the round (swap positions if not first round)
        swap = self.tournament.current_round > 1
        self.reset_round(swap_positions=swap)
        self.game_state = GameState.PLAYING
    
    def update(self) -> None:
        """Update game state"""
        if self.game_state != GameState.PLAYING:
            return
            
        current_time = pygame.time.get_ticks() / 1000.0  
        elapsed_game_time = current_time - self.round_start_time
        time_left = self.config.round_time - elapsed_game_time
        
        if not self.snake1.alive and not self.snake2.alive:
            self.end_round(None)
            return

        if self.snake1.alive:
            move = self.bot1.decide_move(self.snake1, self.food, self.snake2)
            if move in self.VALID_DIRECTIONS:
                self.snake1.change_direction(move)
            self.snake1.update(self.clock.get_time() / 1000.0)
            
            if not self.snake1.alive and self.snake1.self_collision:
                self.snake2_advantage_start = current_time
                self.snake2_advantage_time = min(8.0, time_left)
        
        if self.snake2.alive:
            move = self.bot2.decide_move(self.snake2, self.food, self.snake1)
            if move in self.VALID_DIRECTIONS:
                self.snake2.change_direction(move)
            self.snake2.update(self.clock.get_time() / 1000.0)
            
            if not self.snake2.alive and self.snake2.self_collision:
                self.snake1_advantage_start = current_time
                self.snake1_advantage_time = min(8.0, time_left)
        
        if not self.snake1.alive and self.snake2.alive:
            if current_time - self.snake2_advantage_start >= self.snake2_advantage_time:
                self.snake2.alive = False
        
        if not self.snake2.alive and self.snake1.alive:
            if current_time - self.snake1_advantage_start >= self.snake1_advantage_time:
                self.snake1.alive = False
        
        self.check_collisions()
        
        if self.check_round_end():
            self.handle_round_end()
            
    
    def check_round_end(self) -> bool:
        """Check if round should end"""
        elapsed = pygame.time.get_ticks() / 1000.0 - self.round_start_time
        time_up = elapsed >= self.config.round_time
        both_dead = not self.snake1.alive and not self.snake2.alive
        no_food = len(self.food.positions) == 0
        
        return time_up or both_dead or no_food
    
    def handle_round_end(self) -> None:
        """Process round end and tournament progression"""
        current_time = pygame.time.get_ticks() / 1000.0
        time_remaining = max(0, self.config.round_time - (current_time - self.round_start_time))
        
        # Determine winner
        snake1_alive = self.snake1.alive
        snake2_alive = self.snake2.alive

        # Modified this section to handle self-collision cases properly
        if not snake1_alive and not snake2_alive:
            # Both snakes are dead - check who died last
            if self.snake1.death_time < self.snake2.death_time:
                self.round_winner = self.snake2.agent_id
            elif self.snake2.death_time < self.snake1.death_time:
                self.round_winner = self.snake1.agent_id
            else:
                self.round_winner = None  # Both died at same time = draw
        elif snake1_alive and not snake2_alive:
            self.round_winner = self.snake1.agent_id
        elif snake2_alive and not snake1_alive:
            self.round_winner = self.snake2.agent_id
        elif snake1_alive and snake2_alive:
            if self.snake1.score > self.snake2.score:
                self.round_winner = self.snake1.agent_id
            elif self.snake2.score > self.snake1.score:
                self.round_winner = self.snake2.agent_id
            else:
                self.round_winner = None  # Draw
        else:
            self.round_winner = None  # Shouldn't reach here

        # Rest of the method remains the same...
        self.tournament.record_round(
            winner=self.round_winner,
            snake1_score=self.snake1.score,
            snake2_score=self.snake2.score,
            snake1_traps_hit=self.snake1.traps_hit,
            snake2_traps_hit=self.snake2.traps_hit,
            snake1_collisions=self.snake1.collisions,
            snake2_collisions=self.snake2.collisions,
            snake1_collision_types=self.snake1.collision_types,
            snake2_collision_types=self.snake2.collision_types,
            time_remaining=time_remaining
        )

        if self.tournament.is_tournament_over():
            self.final_winner = self.tournament.get_winner()
            self.tournament.save_to_csv()
            self.show_final_results()
            self.game_state = GameState.GAME_OVER
        else:
            self.game_state = GameState.ROUND_OVER
  
    def draw(self) -> None:
        """Render all game elements"""
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
        """Draw the main game screen"""
        # Draw grid
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (WIDTH, y))
        pygame.draw.rect(self.screen, WALL_COLOR, (0, 0, WIDTH, HEIGHT), WALL_THICKNESS)
        
        # Draw game objects
        self.food.draw(self.screen)
        self.traps.draw(self.screen)
        self.snake1.draw(self.screen)
        self.snake2.draw(self.screen)
        
        # Draw HUD
        current_time = pygame.time.get_ticks() / 1000.0
        elapsed_game_time = current_time - self.round_start_time
        time_left = max(0, self.config.round_time - elapsed_game_time)
        
        # Calculate advantage time remaining
        snake1_advantage_remaining = 0
        snake2_advantage_remaining = 0
        
        if not self.snake1.alive and self.snake2.alive:
            snake2_advantage_remaining = max(0, self.snake2_advantage_time - (current_time - self.snake2_advantage_start))
            time_text = f"Snake2 Advantage: {snake2_advantage_remaining:.1f}s"
        elif not self.snake2.alive and self.snake1.alive:
            snake1_advantage_remaining = max(0, self.snake1_advantage_time - (current_time - self.snake1_advantage_start))
            time_text = f"Snake1 Advantage: {snake1_advantage_remaining:.1f}s"
        else:
            time_text = f"Time: {int(time_left)}s"
        
        self.draw_scores(time_text)
    
    def draw_scores(self, time_text: str) -> None:
        """Draw score and tournament information"""
        score1_text = f"{self.snake1.agent_id}: {self.snake1.score}"
        score2_text = f"{self.snake2.agent_id}: {self.snake2.score}"
        
        if isinstance(self.displayed_round, str):  # For tiebreaker
            round_text = "Tiebreaker"
        else:
            round_text = f"Round {self.displayed_round}/{self.config.max_rounds}"
        
        # Render text surfaces
        score1_surface = self.font.render(score1_text, True, GREEN)
        score2_surface = self.font.render(score2_text, True, YELLOW)
        round_surface = self.font.render(round_text, True, WHITE)
        time_surface = self.font.render(time_text, True, WHITE)
        
        # Position and draw text
        self.screen.blit(score1_surface, (10, 10))
        self.screen.blit(score2_surface, (WIDTH - score2_surface.get_width() - 10, 10))
        self.screen.blit(round_surface, (WIDTH // 2 - round_surface.get_width() // 2, 10))
        self.screen.blit(time_surface, (WIDTH // 2 - time_surface.get_width() // 2, HEIGHT - 30))

    def draw_start_screen(self) -> None:
        """Draw the game start screen"""
        title = self.large_font.render("Snake Tournament", True, GREEN)
        instruction = self.medium_font.render("Press SPACE to begin", True, WHITE)
        controls = self.font.render("Use arrow keys for human player", True, WHITE)
        
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
        self.screen.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, HEIGHT // 2))
        self.screen.blit(controls, (WIDTH // 2 - controls.get_width() // 2, HEIGHT // 2 + 50))

    def draw_round_over(self) -> None:
        """Draw the round over screen"""
        round_num = (self.tournament.current_round - 1 if isinstance(self.displayed_round, int) 
                else self.displayed_round)
        title = self.large_font.render(f"Round {round_num} Over", True, WHITE)
    
        if self.round_winner:
            result = self.medium_font.render(f"{self.round_winner} wins!", 
                                           True, GREEN if self.round_winner == self.snake1.agent_id else YELLOW)
        else:
            result = self.medium_font.render("Draw!", True, WHITE)

        score_text = self.font.render(
            f"{self.snake1.agent_id}: {self.snake1.score}  |  {self.snake2.agent_id}: {self.snake2.score}", 
            True, WHITE
        )
        instruction = self.font.render("Press SPACE to continue", True, WHITE)

        # Tournament progress - use tournament's win counts
        progress = self.font.render(
            f"Tournament: {self.tournament.snake1_wins}-{self.tournament.snake2_wins}", 
            True, WHITE
        )

        # Position and draw elements
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))
        self.screen.blit(result, (WIDTH // 2 - result.get_width() // 2, HEIGHT // 2 - 50))
        self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
        self.screen.blit(progress, (WIDTH // 2 - progress.get_width() // 2, HEIGHT // 2 + 30))
        self.screen.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, HEIGHT // 2 + 80))

    def draw_tournament_end(self) -> None:
        """Draw the tournament end screen"""
        title = self.large_font.render("Tournament Over", True, RED)
        
        if self.final_winner:
            winner_text = self.medium_font.render(
                f"Winner: {self.final_winner}", 
                True, GREEN if self.final_winner == self.snake1.agent_id else YELLOW
            )
        else:
            winner_text = self.medium_font.render("Tournament Draw!", True, WHITE)
        
        rounds_text = self.font.render(
            f"Rounds Played: {len(self.tournament.results)}", 
            True, WHITE
        )
        score_text = self.font.render(
            f"Final Score: {self.tournament.snake1_wins}-{self.tournament.snake2_wins}", 
            True, WHITE
        )
        ratio_text = self.font.render(
            f"Win Ratios: {self.tournament.snake1_win_ratio:.2f}-{self.tournament.snake2_win_ratio:.2f}",
            True, WHITE
        )
        instruction = self.font.render("Press SPACE to exit", True, WHITE)
        
        # Position and draw elements
        self.screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
        self.screen.blit(winner_text, (WIDTH//2 - winner_text.get_width()//2, HEIGHT//2 - 70))
        self.screen.blit(rounds_text, (WIDTH//2 - rounds_text.get_width()//2, HEIGHT//2 - 30))
        self.screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2 + 10))
        self.screen.blit(ratio_text, (WIDTH//2 - ratio_text.get_width()//2, HEIGHT//2 + 50))
        self.screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT//2 + 100))
    
    def draw_draw_screen(self) -> None:
        """Draw the tournament draw screen"""
        title = self.large_font.render("Tournament Draw!", True, YELLOW)
        score_text = self.font.render(
            f"Final Score: {self.tournament.snake1_wins}-{self.tournament.snake2_wins}", 
            True, WHITE
        )
        instruction = self.font.render("Press SPACE to play again", True, WHITE)
        
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 3))
        self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
        self.screen.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, HEIGHT // 2 + 50))

    
    def show_final_results(self) -> None:
        """Display and print final tournament results"""
        snake1_wins = self.tournament.snake1_wins
        snake2_wins = self.tournament.snake2_wins
        snake1_losses = self.tournament.snake1_losses
        snake2_losses = self.tournament.snake2_losses
        total_s1 = self.tournament.total_snake1_apples
        total_s2 = self.tournament.total_snake2_apples
        
        had_tiebreaker = len(self.tournament.results) > self.tournament.config.max_rounds
        
        print("\n=== FINAL TOURNAMENT RESULTS ===")
        print(f"Total Rounds: {len(self.tournament.results)}")
        if had_tiebreaker:
            print("(Including tiebreaker rounds)")
        print(f"Draw Rounds: {self.tournament.draw_rounds}")
        print(f"Crashed Rounds: {self.tournament.crashed_rounds}")
        print(f"{self.snake1.agent_id}: {snake1_wins} wins, {snake1_losses} losses, Win Ratio: {self.tournament.snake1_win_ratio:.2f}")
        print(f"{self.snake2.agent_id}: {snake2_wins} wins, {snake2_losses} losses, Win Ratio: {self.tournament.snake2_win_ratio:.2f}")
        
        # Check for early victory
        diff = abs(total_s1 - total_s2)
        if diff >= self.config.early_victory_diff and len(self.tournament.results) >= self.config.min_rounds_for_early_victory:
            print(f"\nEarly victory with {diff} point difference!")
        
        if self.final_winner:
            print(f"\nTOURNAMENT WINNER: {self.final_winner}!")
        else:
            print("\nTOURNAMENT ENDED IN A DRAW!")
        
    def run(self) -> None:
        """Main game loop"""
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

if __name__ == "__main__":
    game = SnakeGame()
    game.run()