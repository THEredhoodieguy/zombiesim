import pygame, math

pygame.init()

from zombiesim import *

class Grid(object):

	def __init__(self, xbound, ybound, num_humans, num_zombies):

		pygame.init()

		sim = Simulator(xbound, ybound, num_humans, num_zombies)

		BLACK = (  0,  0,  0)
		WHITE = (255,255,255)
		GREEN = (  0,255,  0)
		RED   = (255,  0,  0)
		BLUE  = (  0,  0,255)


		width = xbound * 10 #+ 500
		height = ybound * 10

		WINDOW_SIZE = [width, height]
		screen = pygame.display.set_mode(WINDOW_SIZE)
		pygame.display.set_caption("Zombie Survival Sim")

		myfont = pygame.font.Font(None, 30)

		clock = pygame.time.Clock()

		done = False

		while not done:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					done = True

			screen.fill(WHITE)

			humans  = sim.get_humans()
			zombies = sim.get_zombies()

			humans_text  = myfont.render("# Humans", 1, BLACK)
			humans_num   = myfont.render(str(len(humans)), 1, BLACK)
			screen.blit(humans_text, ((width * 10) + 100, 20))
			screen.blit(humans_num, ((width * 10) + 100, 40))

			zombies_text = myfont.render("# Zombies", 1, BLACK)
			zombies_num  = myfont.render(str(len(zombies)), 1, BLACK)
			screen.blit(zombies_text, ((width * 10) + 100, 80))
			screen.blit(zombies_num, ((width * 10) + 100, 100))

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

			clock.tick(30)

			sim.update()

			pygame.display.update()

		pygame.quit()


if __name__ == "__main__":
	grid = Grid(100, 100, 500, 3)
