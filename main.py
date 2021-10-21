import pygame
from pygame.math import Vector2
from pygame import USEREVENT

from copy import deepcopy
import math
import itertools
import time

from ui_elements import *
from utils import *

#### TODO #####################################################################
'''
- deep copy very slow
- RAM problems
- manage order of pins when saving chips

FUTURE

- save chips to disk
- delete chips
- add multiple chips at once
- area selection with mouse
- edit chip

'''


if __name__ == '__main__':

	pygame.init()
	clock = pygame.time.Clock()

	infoObject = pygame.display.Info()
	current_w, current_h = infoObject.current_w, infoObject.current_h

	screen = pygame.display.set_mode((current_w,current_h), pygame.FULLSCREEN)
	pygame.display.set_caption('NAND')

	pins_nand = {'i':['a','b'], 'o':['o']}
	logic_nand = (['o'], ['a', 'b'], lambda x: [not (x[0] and x[1])])
	nand_gate = chip('NAND', (150,50,150), (100,200), pins_nand, logic_nand)
	
	left_pbar = pin_bar('left', current_w, current_h)
	right_pbar = pin_bar('right', current_w, current_h)

	cbar = chip_bar([deepcopy(nand_gate)])
	the_board = board(cbar, left_pbar, right_pbar, [])
	
	
	###########################################################################
	# Game Loop ###############################################################
	###########################################################################

	k = 1

	running = True
	while running:
		
		#k+=1

		##### Handle events ###################################################
		for event in pygame.event.get():
			
			if event.type == pygame.QUIT:
				running = False

			else:
				if event.type == pygame.KEYDOWN and event.key == pygame.K_k:
					the_board.wrap_into_chip()

				elif event.type == USEREVENT and event.task == 'save_board_to_chip':
						
						del the_board

						left_pbar = pin_bar('left', current_w, current_h)
						right_pbar = pin_bar('right', current_w, current_h)
						the_board = board(cbar, left_pbar, right_pbar, [])
						the_board.chip_bar.add_chip(event.obj)

				elif event.type == USEREVENT and event.task == 'edit_chip':
					del the_board

					the_board = event.obj.get_board()

				else:
					#start_events = time.time()
					the_board.handle_event(event)
					#end_events = time.time()

		##### Handle mouse position ###########################################
		#start_hover = time.time()
		mouse_pos = pygame.mouse.get_pos()
		
		# mouse position over elements
		the_board.handle_hover(mouse_pos)
		#end_hover = time.time()

		##### Execute logic ###################################################
		#start_logic = time.time()
		the_board.run_logic()
		#end_logic = time.time()

		##### Drawing stuff ###################################################
		#start_draw = time.time()
		the_board.draw(screen, mouse_pos)
		#end_draw = time.time()
		
		#if k%(60*5) == 0:
		#	k = 0
		#	print('\n')
		#	print(f'events: {round((end_events-start_events)/5*1000, 5)} ms')
		#	print(f'hover:  {round((end_hover-start_hover)/5*1000, 5)} ms')
		#	print(f'logic:  {round((end_logic-start_logic)/5*1000, 5)} ms')
		#	print(f'draw:   {round((end_draw-start_draw)/5*1000, 5)} ms')
		#	print(f'TOTAL:  {round((end_total-start_total)/5*1000, 5)} ms')
		
		
		clock.tick(60)
		#start_total = time.time()
		pygame.display.update()
		#end_total = time.time()
