import pygame, math

pygame.init()

from zombiesim import *

class Grid(object):

	def __init__(self, xbound, ybound, num_humans, num_zombies):

		pygame.init()

		sim = Simulator(xbound, ybound, num_humans, num_zombies, False)

		BLACK = (  0,  0,  0)
		WHITE = (255,255,255)
		GREEN = (  0,255,  0)
		RED   = (255,  0,  0)
		BLUE  = (  0,  0,255)


		scaled_width = xbound * 10
		scaled_height = ybound * 10

		WINDOW_SIZE = [scaled_width, scaled_height]
		screen = pygame.display.set_mode(WINDOW_SIZE)
		pygame.display.set_caption("Zombie Survival Sim")

		myfont = pygame.font.SysFont('American Typewriter', 30)

		clock = pygame.time.Clock()

		done = False

		while not done:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					done = True

			screen.fill(WHITE)

			humans  = sim.humans
			zombies = sim.zombies

			humans_text  = myfont.render("# Humans", 1, BLACK)
			humans_num   = myfont.render(str(len(humans)), 1, BLACK)

			zombies_text = myfont.render("# Zombies", 1, BLACK)
			zombies_num  = myfont.render(str(len(zombies)), 1, BLACK)

			for i in zombies:
				pygame.draw.rect(screen,
					RED,
					[math.floor(i.xcord * 10),
					math.floor(i.ycord * 10),
					10, 10
					])

			for i in humans:
				pygame.draw.rect(screen,
					BLUE,
					[math.floor(i.xcord * 10),
					math.floor(i.ycord * 10),
					10, 10
					])
			
			screen.blit(humans_text, (10, 10))
			screen.blit(humans_num, (10, 40))
			screen.blit(zombies_text, (10, 70))
			screen.blit(zombies_num, (10, 100))

			clock.tick(30)

			sim.update()

			pygame.display.flip()

		pygame.quit()


if __name__ == "__main__":
	grid = Grid(80, 80, 1000, 3)
