# created from optimized_zombiesim.py by chatting more with Claude
import random, math
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

def get_velocity(speed: float, direction: float):
    """Takes a speed and direction and returns change in x and y coords"""
    x = math.cos(direction) * speed
    y = math.sin(direction) * speed
    return (x, y)

def get_direction(x: float, y: float):
    """Gets a direction from two differences in coordinates"""
    return math.atan2(y, x)

def distance_squared(x1, y1, x2, y2):
    """Calculate squared distance between two points (avoids expensive sqrt)"""
    return (x2 - x1)**2 + (y2 - y1)**2

class Simulator(object):
    """The master object that holds all the game state"""

    def __init__(self, xbound: int, ybound: int, num_humans: int, num_zombies: int, debug: bool, num_threads: int = 4):
        self.xbound = xbound
        self.ybound = ybound
        
        self.humans = []
        self.zombies = []
        self.new_humans = []
        self.new_zombies = []
        
        self.debug = debug
        self.num_threads = num_threads
        
        # Thread safety
        self.lock = threading.RLock()  # Reentrant lock for nested acquire/release
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=num_threads)
        
        # Spatial partitioning - divide the space into cells
        self.cell_size = 10  # Size of each cell in the grid
        self.grid = defaultdict(list)  # Will hold agents by grid cell
        
        for _ in range(0, num_humans):
            self.humans.append(Human(random.randint(0, xbound), random.randint(0, ybound), 
                                    xbound, ybound, 0.3, self))

        for _ in range(0, num_zombies):
            self.zombies.append(Zombie(random.randint(0, xbound), random.randint(0, ybound), 
                                      xbound, ybound, self))
        
        # Add all entities to the spatial grid
        self.update_spatial_grid()

    def update_spatial_grid(self):
        """Update the spatial partitioning grid with current agent positions"""
        # Create a new grid to avoid modification during iteration
        new_grid = defaultdict(list)
        
        for human in self.humans:
            cell_x = int(human.xcord // self.cell_size)
            cell_y = int(human.ycord // self.cell_size)
            new_grid[(cell_x, cell_y)].append(("human", human))
            
        for zombie in self.zombies:
            cell_x = int(zombie.xcord // self.cell_size)
            cell_y = int(zombie.ycord // self.cell_size)
            new_grid[(cell_x, cell_y)].append(("zombie", zombie))
        
        # Thread-safe grid update
        with self.lock:
            self.grid = new_grid

    def get_nearby_agents(self, agent, agent_type, search_radius=1):
        """Get nearby agents of specified type using spatial partitioning"""
        cell_x = int(agent.xcord // self.cell_size)
        cell_y = int(agent.ycord // self.cell_size)
        
        nearby = []
        # Check current cell and surrounding cells
        # Use a snapshot of the grid to avoid concurrent modification
        with self.lock:
            grid_snapshot = self.grid
            
            for dx in range(-search_radius, search_radius + 1):
                for dy in range(-search_radius, search_radius + 1):
                    cell = (cell_x + dx, cell_y + dy)
                    if cell in grid_snapshot:
                        for type_tag, other_agent in grid_snapshot[cell]:
                            if type_tag == agent_type and other_agent != agent:
                                nearby.append(other_agent)
        
        return nearby

    def update_batch(self, agents, is_zombie=False):
        """Update a batch of agents in parallel"""
        for agent in agents:
            if is_zombie:
                agent.update()
            else:
                agent.update()

    def update(self):
        # Divide humans and zombies into batches for parallel processing
        human_count = len(self.humans)
        zombie_count = len(self.zombies)
        
        # Only use multithreading if we have enough agents to make it worthwhile
        if human_count > self.num_threads * 10:
            # Split humans into batches
            batch_size = max(1, human_count // self.num_threads)
            human_batches = [self.humans[i:i+batch_size] for i in range(0, human_count, batch_size)]
            
            # Submit human update tasks to thread pool
            human_futures = [self.executor.submit(self.update_batch, batch, False) for batch in human_batches]
            
            # Wait for all human updates to complete
            for future in human_futures:
                future.result()
        else:
            # Sequential update for small number of humans
            for human in self.humans:
                human.update()
        
        # Shuffle zombies to ensure fair chance to eat humans
        with self.lock:
            random.shuffle(self.zombies)
        
        if zombie_count > self.num_threads * 5:
            # Split zombies into batches
            batch_size = max(1, zombie_count // self.num_threads)
            zombie_batches = [self.zombies[i:i+batch_size] for i in range(0, zombie_count, batch_size)]
            
            # Submit zombie update tasks to thread pool
            zombie_futures = [self.executor.submit(self.update_batch, batch, True) for batch in zombie_batches]
            
            # Wait for all zombie updates to complete
            for future in zombie_futures:
                future.result()
        else:
            # Sequential update for small number of zombies
            for zombie in self.zombies:
                zombie.update()
        
        # Add new agents with thread safety
        with self.lock:
            self.humans.extend(self.new_humans)
            self.zombies.extend(self.new_zombies)
            
            self.new_humans = []
            self.new_zombies = []
        
        # Update spatial grid after all positions have changed
        self.update_spatial_grid()
        
        if self.debug:
            print(f"There are {len(self.humans)} Humans alive")
            print(f"There are {len(self.zombies)} Zombies alive")


class Human(object):
    """Individual agent that can be turned into a zombie"""

    def __init__(self, xcord: float, ycord: float, xbound: int, ybound: int, immunity: float, sim: Simulator):
        self.xcord = xcord
        self.ycord = ycord
        self.xbound = xbound
        self.ybound = ybound
        self.immunity = immunity
        self.age = 0
        self.max_age = random.randint(190, 275)
        self.infected = random.random()
        
        # Movement attributes
        self.speed = 1
        self.direction = random.random() * 2 * math.pi
        self.xvel, self.yvel = get_velocity(self.speed, self.direction)
        
        self.closest_zombie = None
        self.sim = sim
        
        # Counter to reduce frequency of expensive operations
        self.update_counter = 0
        
        # Flag to mark if this human is already dead
        self.is_dead = False
        
        # Lock for thread safety
        self.lock = threading.RLock()

    def move(self):
        # Bounce off walls
        with self.lock:
            if self.xcord + self.xvel > self.xbound or self.xcord + self.xvel < 0:
                self.xvel = -self.xvel

            if self.ycord + self.yvel > self.ybound or self.ycord + self.yvel < 0:
                self.yvel = -self.yvel

            self.xcord += self.xvel
            self.ycord += self.yvel

    def set_direction(self):
        """The human tries to run away from the closest zombie"""
        with self.lock:
            if self.closest_zombie:
                # Get direction away from zombie
                self.direction = -get_direction(
                    self.closest_zombie.xcord - self.xcord, 
                    self.closest_zombie.ycord - self.ycord
                )
                # Add some randomness to movement
                self.direction += (random.random() - 0.5) * .25 * math.pi
            else:
                # Random direction if no zombies nearby
                self.direction = random.random() * math.pi * 2

    def find_closest_zombie(self):
        """Find the closest zombie using spatial partitioning"""
        nearby_zombies = self.sim.get_nearby_agents(self, "zombie", search_radius=2)
        
        if not nearby_zombies:
            with self.lock:
                self.closest_zombie = None
            return
            
        shortest_dist = float('inf')
        closest = None
        
        for zombie in nearby_zombies:
            # Use squared distance to avoid sqrt operation
            dist_squared = distance_squared(
                self.xcord, self.ycord, zombie.xcord, zombie.ycord
            )
            
            if dist_squared < shortest_dist:
                shortest_dist = dist_squared
                closest = zombie
        
        # Only care about zombies within a certain range
        max_distance_squared = (self.xbound / 4) ** 2
        
        with self.lock:
            if shortest_dist < max_distance_squared:
                self.closest_zombie = closest
            else:
                self.closest_zombie = None

    def turn(self):
        """Create a new zombie at human's location"""
        new_zombie = Zombie(self.xcord, self.ycord, self.xbound, self.ybound, self.sim)
        with self.sim.lock:
            self.sim.new_zombies.append(new_zombie)

    def die(self):
        """Remove human from simulation"""
        # Check if this human is already dead to prevent the "x not in list" error
        with self.lock:
            if not self.is_dead:
                self.is_dead = True
                with self.sim.lock:
                    if self in self.sim.humans:
                        self.sim.humans.remove(self)

    def get_eaten(self):
        """Determines whether a human that is eaten is turned into a zombie or not"""
        if random.random() >= self.immunity:
            self.turn()
        self.die()

    def reproduce(self):
        """Humans have a random chance to reproduce"""
        if random.randint(0, 499) == 0:
            with self.sim.lock:
                self.sim.new_humans.append(
                    Human(self.xcord, self.ycord, self.xbound, self.ybound, 
                         self.immunity, self.sim)
                )

    def update(self):
        """Run all time step operations on the human"""
        # Skip update if already dead
        with self.lock:
            if self.is_dead:
                return
                
            # Check for death by old age
            if self.age >= self.max_age:
                self.die()
                return
            
            self.age += 1
            
        self.reproduce()
        
        # Only update direction and find closest zombie periodically
        with self.lock:
            self.update_counter += 1
            should_update = self.update_counter >= 3  # Update every 3 frames
        
        if should_update:
            self.find_closest_zombie()
            self.set_direction()
            
            with self.lock:
                self.xvel, self.yvel = get_velocity(self.speed, self.direction)
                self.xvel *= -1  # Preserved from original code
                self.update_counter = 0
        
        self.move()


class Zombie(object):
    """A Zombie that chases Humans around to eat them"""

    def __init__(self, xcord: float, ycord: float, xbound: int, ybound: int, sim: Simulator):
        self.xcord = xcord
        self.ycord = ycord
        self.xbound = xbound
        self.ybound = ybound
        self.sim = sim
        
        self.speed = 0.8
        self.direction = 0
        self.xvel, self.yvel = get_velocity(self.speed, self.direction)
        
        self.closest_human = None
        self.hunger = 0
        self.max_hunger = random.randint(200, 260)
        
        self.incr = 0
        self.update_counter = 0
        
        # Flag to mark if this zombie is already dead
        self.is_dead = False
        
        # Lock for thread safety
        self.lock = threading.RLock()

    def set_direction(self):
        """The zombie sets after the nearest human"""
        with self.lock:
            if self.closest_human:
                self.direction = get_direction(
                    self.closest_human.xcord - self.xcord, 
                    self.closest_human.ycord - self.ycord
                )
                # Add some randomness
                self.direction += (random.random() - 0.5) * .5 * math.pi
            else:
                # Random direction if no humans nearby
                self.direction = random.random() * math.pi * 2

    def find_closest_human(self):
        """Find closest human using spatial partitioning"""
        nearby_humans = self.sim.get_nearby_agents(self, "human", search_radius=2)
        
        if not nearby_humans:
            with self.lock:
                self.closest_human = None
            return
            
        shortest_dist = float('inf')
        closest = None
        
        for human in nearby_humans:
            # Skip already dead humans
            if human.is_dead:
                continue
                
            # Use squared distance to avoid sqrt
            dist_squared = distance_squared(
                self.xcord, self.ycord, human.xcord, human.ycord
            )
            
            if dist_squared < shortest_dist:
                shortest_dist = dist_squared
                closest = human
        
        with self.lock:
            self.closest_human = closest

    def move(self):
        """Moves the zombie to the next location"""
        # Handle wall collisions
        with self.lock:
            if self.xcord + self.xvel > self.xbound or self.xcord + self.xvel < 0:
                self.xvel = -self.xvel
                
                if self.incr >= 3:
                    self.direction = random.random() * math.pi * 2
                    self.move()
                    return

            if self.ycord + self.yvel > self.ybound or self.ycord + self.yvel < 0:
                self.yvel = -self.yvel
                
                if self.incr >= 3:
                    self.direction = random.random() * math.pi * 2
                    self.move()
                    return

            self.xcord += self.xvel
            self.ycord += self.yvel

    def can_eat(self):
        """Check if closest human is close enough to eat"""
        with self.lock:
            if not self.closest_human or self.closest_human.is_dead:
                return False
                
            # Use squared distance (threshold is 1 unit, so 1²)
            dist_squared = distance_squared(
                self.xcord, self.ycord, 
                self.closest_human.xcord, self.closest_human.ycord
            )
            
            return dist_squared <= 1

    def eat(self):
        """Eat the closest human"""
        with self.lock:
            if self.hunger < 40:
                self.hunger = 0
            else:
                self.hunger -= 40
                
            human_to_eat = self.closest_human
            
            # Clear reference to human being eaten
            self.closest_human = None
        
        # Eat the human outside the lock to avoid deadlock
        if human_to_eat and not human_to_eat.is_dead:
            human_to_eat.get_eaten()
        
        if self.sim.debug:
            print("A Zombie has eaten")

    def die(self):
        """Remove zombie from simulation"""
        # Check if this zombie is already dead to prevent the "x not in list" error
        with self.lock:
            if not self.is_dead:
                self.is_dead = True
                with self.sim.lock:
                    if self in self.sim.zombies:
                        self.sim.zombies.remove(self)

    def update(self):
        """Update zombie state"""
        # Skip update if already dead
        with self.lock:
            if self.is_dead:
                return
                
            # Only find a new closest human periodically or if current target is gone
            self.update_counter += 1
            should_update = (self.update_counter >= 4 or 
                            not self.closest_human or 
                            self.closest_human.is_dead)
        
        if should_update:
            self.find_closest_human()
            with self.lock:
                self.update_counter = 0
        
        # Set direction and velocity
        with self.lock:
            should_set_direction = (self.incr == 0 or 
                                    not self.closest_human or 
                                    self.closest_human.is_dead)
        
        if should_set_direction:
            self.set_direction()
            with self.lock:
                self.xvel, self.yvel = get_velocity(self.speed, self.direction)
        
        # Update hunger
        with self.lock:
            self.hunger += 1
            if self.hunger >= self.max_hunger:
                self.die()
                return
        
        self.move()
        
        # Try to eat nearby humans
        if self.can_eat():
            self.eat()
        
        with self.lock:
            self.incr += 1
            if self.incr > 6:
                self.incr = 0