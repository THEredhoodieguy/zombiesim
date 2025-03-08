# Did some basic optimizations by chatting with Claude

import pygame
import math
import time

pygame.init()

from optimized_zombiesim import Human, Simulator, Zombie

class Grid(object):
    def __init__(self, xbound, ybound, num_humans, num_zombies):
        pygame.init()

        self.sim = Simulator(xbound, ybound, num_humans, num_zombies, False)

        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)

        # Scale factor for drawing
        self.scale = 5
        self.scaled_width = xbound * self.scale
        self.scaled_height = ybound * self.scale

        # Set up display
        self.WINDOW_SIZE = [self.scaled_width, self.scaled_height]
        self.screen = pygame.display.set_mode(self.WINDOW_SIZE)
        pygame.display.set_caption("Zombie Survival Sim")

        # Font for text display
        self.myfont = pygame.font.SysFont('Arial', 30)

        # Create surfaces for agents (better than drawing rectangles each frame)
        self.human_surf = pygame.Surface((self.scale, self.scale))
        self.human_surf.fill(self.BLUE)
        
        self.zombie_surf = pygame.Surface((self.scale, self.scale))
        self.zombie_surf.fill(self.RED)
        
        # Performance tracking
        self.clock = pygame.time.Clock()
        self.fps_font = pygame.font.SysFont('Arial', 18)
        self.frame_times = []
        self.last_time = time.time()

        self.run_simulation()

    def draw_stats(self):
        """Draw statistics on screen"""
        humans = self.sim.humans
        zombies = self.sim.zombies
        
        # Count display
        humans_text = self.myfont.render("# Humans", True, self.BLACK)
        humans_num = self.myfont.render(str(len(humans)), True, self.BLACK)
        zombies_text = self.myfont.render("# Zombies", True, self.BLACK)
        zombies_num = self.myfont.render(str(len(zombies)), True, self.BLACK)
        
        self.screen.blit(humans_text, (10, 10))
        self.screen.blit(humans_num, (10, 40))
        self.screen.blit(zombies_text, (10, 70))
        self.screen.blit(zombies_num, (10, 100))
        
        # FPS display
        current_time = time.time()
        self.frame_times.append(current_time - self.last_time)
        self.last_time = current_time
        
        # Keep only the last 30 frames for average
        if len(self.frame_times) > 30:
            self.frame_times.pop(0)
            
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        
        fps_text = self.fps_font.render(f"FPS: {fps:.1f}", True, self.BLACK)
        self.screen.blit(fps_text, (self.scaled_width - 100, 10))

    def run_simulation(self):
        """Main simulation loop"""
        done = False

        while not done:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                elif event.type == pygame.KEYDOWN:
                    # Add some interactivity - press 'h' to add humans, 'z' to add zombies
                    if event.key == pygame.K_h:
                        for _ in range(10):
                            self.sim.new_humans.append(
                                Human(
                                    random.randint(0, self.sim.xbound),
                                    random.randint(0, self.sim.ybound),
                                    self.sim.xbound, self.sim.ybound,
                                    0.3, self.sim
                                )
                            )
                    elif event.key == pygame.K_z:
                        for _ in range(5):
                            self.sim.new_zombies.append(
                                Zombie(
                                    random.randint(0, self.sim.xbound),
                                    random.randint(0, self.sim.ybound),
                                    self.sim.xbound, self.sim.ybound,
                                    self.sim
                                )
                            )

            # Clear screen
            self.screen.fill(self.WHITE)

            # Update simulation
            self.sim.update()

            # Use blit instead of draw.rect for better performance
            for zombie in self.sim.zombies:
                self.screen.blit(
                    self.zombie_surf, 
                    (math.floor(zombie.xcord * self.scale), 
                     math.floor(zombie.ycord * self.scale))
                )

            for human in self.sim.humans:
                self.screen.blit(
                    self.human_surf, 
                    (math.floor(human.xcord * self.scale), 
                     math.floor(human.ycord * self.scale))
                )
            
            # Draw statistics
            self.draw_stats()
            
            # Maintain frame rate
            self.clock.tick(30)
            
            # Update display
            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    import random
    grid = Grid(100, 100, 2500, 3)