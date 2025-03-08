import random, math



def get_velocity(speed: float, direction: float):
	"""Takes a speed and direction and returns change in x and y coords"""
	x = math.cos(direction) * speed
	y = math.sin(direction) * speed

	return(x, y)



def get_direction(x: float, y: float):
	"""Gets a direction from two differences in coordinates"""

	return math.atan2(y, x)


class Simulator(object):
	"""The master object that holds all the game state"""


	def __init__(self, xbound: int, ybound: int, num_humans: int, num_zombies: int, debug: bool):

		self.xbound = xbound
		self.ybound = ybound

		self.humans: list[Human] = list()
		self.zombies: list[Zombie] = list()
		self.new_humans: list[Human] = list()
		self.new_zombies: list[Zombie] = list()
		
		self.debug = debug

		for _ in range(0, num_humans):
			self.humans.append(Human(random.randint(0, xbound), random.randint(0, ybound), xbound, ybound, 0.3, self))

		for _ in range(0, num_zombies):
			self.zombies.append(Zombie(random.randint(0, xbound), random.randint(0, ybound), xbound, ybound, self))


	def update(self):

		for i in self.humans:
			i.update()

		#Zombies get shuffled every turn to ensure older zombies don't necessarily have priority
		random.shuffle(self.zombies)

		for i in self.zombies:
			i.update()

		for i in self.new_humans:
			self.humans.append(i)
		for i in self.new_zombies:
			self.zombies.append(i)

		self.new_humans  = list()
		self.new_zombies = list()

		if self.debug:
			print("There are " + str(len(self.humans)) + " Humans alive")
			print("There are " + str(len(self.zombies)) + " Zombies alive")


class Human(object):
	"""Individual agent that can be turned into a zombie"""

	def __init__(self, xcord: float, ycord: float, xbound: int, ybound: int, immunity: float, sim: Simulator):
		self.xcord = xcord
		self.ycord = ycord

		#The x and y bounds represent the walls of the simulation. The cordinate grid
		#goes from 0 to xbound and 0 to ybound.
		self.xbound = xbound
		self.ybound = ybound

		self.immunity = immunity

		self.age = 0
		self.max_age = random.randint(190, 275)

		self.infected = random.random()

		#Humans have a random velocity that they will follow until they hit a wall
		self.speed = 1
		self.direction = random.random() * 2 * math.pi

		self.xvel, self.yvel = get_velocity(self.speed, self.direction)

		self.closest_zombie: Zombie|None = None

		self.sim = sim


	def move(self):
		""""""

		if(self.xcord + self.xvel > self.xbound or self.xcord + self.xvel < 0):
			self.xvel = -self.xvel

		if(self.ycord + self.yvel > self.ybound or self.ycord + self.yvel < 0):
			self.yvel = -self.yvel

		self.xcord += self.xvel
		self.ycord += self.yvel


	def set_direction(self):
		"""The human tries to run away from the closest zombie
		if there are no nearby zombies, the human takes a random direction"""

		if(len(self.sim.zombies) > 0 and self.closest_zombie):
			self.direction = -get_direction(self.closest_zombie.xcord - self.xcord, self.closest_zombie.ycord - self.ycord)
			self.direction += (random.random() - 0.5) * .25 * math.pi

		else:
			self.direction = random.random() * math.pi * 2

	def find_closest_zombie(self):
		"""Compares all zombies and finds the closest one"""
		self.closest_zombie = None

		shortest = self.xbound * self.ybound

		if(len(self.sim.zombies) > 0):
			#Compares all humans and finds the closest one
			for i in self.sim.zombies:
				dist_to_i = abs( ((i.xcord - self.xcord)**2 + (i.ycord - self.ycord)**2)**0.5 )
				if(dist_to_i < shortest):
					shortest = dist_to_i
					self.closest_zombie = i


	def turn(self):
		"""If a human is successfully infected, they will create a new zombie at their location"""

		new = Zombie(self.xcord, self.ycord, self.xbound, self.ybound, self.sim)
		self.sim.new_zombies.append(new)


	def die(self):
		"""If a human is attacked by a zombie, they will die. This function
		removes them from the action array"""

		self.sim.humans.remove(self)


	def get_eaten(self):
		"""Determines whether a human that is eaten is turned into a zombie or not"""

		if( random.random() >= self.immunity ):
			self.turn()
			self.die()
		else:
			self.die()


	def reproduce(self):
		"""Humans have a random chance to reproduce every turn"""
		if(random.randint(0, 499) == 0):
			self.sim.new_humans.append(Human(self.xcord, self.ycord, self.xbound, self.ybound, self.immunity, self.sim))


	def update(self):
		"""Run all time step operations on the human"""

		if(self.age >= self.max_age):
			self.die()
			return
		self.age += 1

		self.reproduce()

		self.find_closest_zombie()
		if(self.closest_zombie):
			dist_to_closest_zombie = abs( ((self.closest_zombie.xcord - self.xcord)**2 + (self.closest_zombie.ycord - self.ycord)**2)**0.5 )
		else:
			dist_to_closest_zombie = math.sqrt(self.xbound**2 + self.ybound**2)
		if(dist_to_closest_zombie > self.xbound / 4):
			self.closest_zombie = None
		self.set_direction()

		self.xvel, self.yvel = get_velocity(self.speed, self.direction)

		self.xvel *= -1

		self.move()

		# if(self.infected <= 0.01 and random.randint(0, 999) == 0):
		# 	self.get_eaten()



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

		self.closest_human: Human|None = None

		self.hunger = 0
		self.max_hunger = random.randint(200, 260)

		self.incr = 0


	def set_direction(self):
		"""The zombie sets after the nearest human
		if there are no nearby humans, the zombie takes a random direction"""

		if(len(self.sim.humans) > 0 and self.closest_human):
			self.direction = get_direction(self.closest_human.xcord - self.xcord, self.closest_human.ycord - self.ycord)
			self.direction += (random.random() - 0.5) * .5 * math.pi

		else:
			self.direction = random.random() * math.pi * 2


	def find_closest_human(self):
		"""Compares all humans and finds the closest one"""
		self.closest_human = None

		shortest = self.xbound * self.ybound

		if(len(self.sim.humans) > 0):
			#Compares all humans and finds the closest one
			for i in self.sim.humans:
				dist_to_i = abs( ((i.xcord - self.xcord)**2 + (i.ycord - self.ycord)**2)**0.5 )
				if(dist_to_i < shortest):
					shortest = dist_to_i
					self.closest_human = i


	def move(self):
		"""Moves the zombie to the next location"""

		if(self.xcord + self.xvel > self.xbound or self.xcord + self.xvel < 0):
			self.xvel = -self.xvel

			if(self.incr >= 3):
				self.direction = random.random() * math.pi * 2
				self.move()
				return

		if(self.ycord + self.yvel > self.ybound or self.ycord + self.yvel < 0):
			self.yvel = -self.yvel

			if(self.incr >= 3):
				self.direction = random.random() * math.pi * 2
				self.move()
				return

		self.xcord += self.xvel
		self.ycord += self.yvel


	def can_eat(self):
		"""Looks to see if the closest human is close enough to eat"""

		if(len(self.sim.humans) > 0 and self.closest_human):
			if( abs( ((self.closest_human.xcord - self.xcord)**2 + (self.closest_human.ycord - self.ycord)**2)**0.5 ) <= 1 ):
				return True
			else:
				return False
		else:
			return False


	def eat(self):
		"""Eats the closest human"""

		if(self.hunger < 40):
			self.hunger = 0
		else:
			self.hunger -= 40
		if self.closest_human:
			self.closest_human.get_eaten()
		
		if self.sim.debug:
			print("A Zombie has eaten")


	def die(self):
		""""""

		self.sim.zombies.remove(self)


	def update(self):
		""""""

		if(self.incr == 0 or self.closest_human not in self.sim.humans):
			self.find_closest_human()

		self.set_direction()
		self.xvel, self.yvel = get_velocity(self.speed, self.direction)

		self.hunger += 1
		if(self.hunger >= self.max_hunger):
			self.die()
			return

		self.move()

		able_to_eat = self.can_eat()
		if(able_to_eat):
			self.eat()

		self.incr += 1
		if (self.incr > 6):
			self.incr = 0