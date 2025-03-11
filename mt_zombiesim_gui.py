# created from optimized_zombiesim_gui.py by chatting more with Claudes
import pygame
import math
import time
import threading
import random

pygame.init()

# Import from the multithreaded version
from mt_zombiesim import Human, Simulator, Zombie

class Grid(object):
    def __init__(self, xbound, ybound, num_humans, num_zombies, num_threads=4):
        pygame.init()

        # Create a multithreaded simulator
        self.sim = Simulator(xbound, ybound, num_humans, num_zombies, False, num_threads)

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
        pygame.display.set_caption("Zombie Survival Sim (Multithreaded)")

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
        
        # Thread for simulation updates
        self.simulation_lock = threading.Lock()
        self.simulation_thread = None
        self.running = True
        
        # Buffers for rendering (to avoid race conditions)
        self.human_positions = []
        self.zombie_positions = []
        self.human_count = 0
        self.zombie_count = 0
        
        # Start the simulation in a separate thread
        self.start_simulation_thread()
        
        # Main rendering loop
        self.run_rendering()

    def simulation_loop(self):
        """Run simulation updates in a separate thread"""
        while self.running:
            # Update the simulation
            self.sim.update()
            
            # Copy positions for rendering under lock to avoid race conditions
            with self.simulation_lock:
                self.human_positions = [(math.floor(human.xcord * self.scale), 
                                        math.floor(human.ycord * self.scale)) 
                                       for human in self.sim.humans]
                self.zombie_positions = [(math.floor(zombie.xcord * self.scale), 
                                         math.floor(zombie.ycord * self.scale)) 
                                        for zombie in self.sim.zombies]
                self.human_count = len(self.sim.humans)
                self.zombie_count = len(self.sim.zombies)
            
            # Sleep a bit to avoid hogging the CPU
            time.sleep(1/60)  # Cap at roughly 60 updates per second

    def start_simulation_thread(self):
        """Start the simulation in a separate thread"""
        self.simulation_thread = threading.Thread(target=self.simulation_loop)
        self.simulation_thread.daemon = True  # Thread will close when main program exits
        self.simulation_thread.start()

    def draw_stats(self):
        """Draw statistics on screen"""
        # Count display
        humans_text = self.myfont.render("# Humans", True, self.BLACK)
        humans_num = self.myfont.render(str(self.human_count), True, self.BLACK)
        zombies_text = self.myfont.render("# Zombies", True, self.BLACK)
        zombies_num = self.myfont.render(str(self.zombie_count), True, self.BLACK)
        
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
        
        # Display thread count
        thread_text = self.fps_font.render(f"Threads: {self.sim.num_threads}", True, self.BLACK)
        self.screen.blit(thread_text, (self.scaled_width - 100, 30))

    def run_rendering(self):
        """Main rendering loop"""
        done = False

        while not done and self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    # Add some interactivity
                    if event.key == pygame.K_h:
                        with self.sim.lock:
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
                        with self.sim.lock:
                            for _ in range(5):
                                self.sim.new_zombies.append(
                                    Zombie(
                                        random.randint(0, self.sim.xbound),
                                        random.randint(0, self.sim.ybound),
                                        self.sim.xbound, self.sim.ybound,
                                        self.sim
                                    )
                                )
                    # Thread count controls
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        self.sim.num_threads += 1
                    elif event.key == pygame.K_MINUS and self.sim.num_threads > 1:
                        self.sim.num_threads -= 1

            # Clear screen
            self.screen.fill(self.WHITE)

            # Get a snapshot of the positions to render
            positions_snapshot = []
            with self.simulation_lock:
                human_positions = self.human_positions.copy()
                zombie_positions = self.zombie_positions.copy()
                human_count = self.human_count
                zombie_count = self.zombie_count

            # Render zombies
            for pos in zombie_positions:
                self.screen.blit(self.zombie_surf, pos)

            # Render humans
            for pos in human_positions:
                self.screen.blit(self.human_surf, pos)
            
            # Draw statistics
            self.draw_stats()
            
            # Maintain frame rate
            self.clock.tick(60)
            
            # Update display
            pygame.display.flip()

        # Clean up
        self.running = False
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=1.0)
        pygame.quit()

if __name__ == "__main__":
    import random
    # Use 6 threads by default - adjust based on your CPU
    grid = Grid(100, 100, num_humans=3000, num_zombies=3, num_threads=8)