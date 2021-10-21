import pygame
import copy
from components import *
from utils import * 

from pygame.event import Event
from pygame.event import post
from pygame import USEREVENT


class board:
	def __init__(self, chip_bar, left_pin_bar, right_pin_bar, elements):
		
		self.left_pin_bar = left_pin_bar
		self.right_pin_bar = right_pin_bar
		self.elements = elements
		self.chip_bar = chip_bar
		self.cable_being_created = None
		self.handle_lock = None

		self.name = None

		self.saving = False
		self.save_text_box = None
		

	def handle_event(self, event):

		if event.type == pygame.USEREVENT:
			if event.task == 'create_cable':
				if self.cable_being_created is None:
					self.cable_being_created = cable(event.obj)
					self.elements.append(self.cable_being_created)
				
				elif self.cable_being_created is not None:
					closable = self.cable_being_created.close_cable(event.obj)
					if not closable:
						self.elements.remove(self.cable_being_created)
					self.cable_being_created = None
				
			elif event.task == 'cancel_draw_cable':
				self.elements.remove(self.cable_being_created)
				self.cable_being_created = None

			elif event.task == 'delete_me':
				self.delete_element(event.obj)

			elif event.task == 'confirm_create_chip':
				self.elements.append(event.obj)

			elif event.task == 'write_on_text_box':
				self.handle_lock = event.obj
				self.handle_lock.has_event_lock = True
			
			elif event.task == 'clear_event_lock':
				self.handle_lock = None
			
				if self.saving:
					self.save()
					

		if self.handle_lock is None:
			
			for e in self.elements:
				e.handle_event(event) 

			self.chip_bar.handle_event(event)
			self.left_pin_bar.handle_event(event)
			self.right_pin_bar.handle_event(event)
		
		else:
			self.handle_lock.handle_event(event)


	def save(self):
		left_pin_names = [p.name for p in self.left_pin_bar.pins]
		right_pin_names = [p.name for p in self.right_pin_bar.pins]

		pins = {'i':left_pin_names, 'o':right_pin_names}

		self.name = self.save_text_box.text

		new_chip = chip(
			self.name,
			(50,50,250),
			(1000,1000),
			pins,
			(right_pin_names , left_pin_names, self)
		)
		post(Event(USEREVENT, obj=new_chip, task='save_board_to_chip'))

		self.saving = False
		self.save_text_box = None


	def wrap_into_chip(self):
		
		self.save_text_box = text_box(500, 500, 300, 50, text_size = 30)

		current_w = pygame.display.Info().current_w/2
		current_h = pygame.display.Info().current_h/3

		self.save_text_box.shape.center = current_w, current_h
		self.saving = True	


	def delete_element(self, obj):

		# delete cables connected to chip
		if type(obj) == chip:
			for e in list(self.elements):
				if type(e) == cable:
					for _, pin in obj.pins.items():
						if pin is e.origin_pin or pin is e.destination_pin:
							self.delete_element(e)

		# delete cables connected to cable
		elif type(obj) == cable:
			for e in list(self.elements):
				if type(e) == cable:
					for p in obj.pins:
						if p is e.origin_pin or p is e.destination_pin:
							self.delete_element(e)

		elif type(obj) == io_pin:
			for e in list(self.elements):
				if type(e) == cable:
					if obj is e.origin_pin or obj is e.destination_pin:
						self.delete_element(e)
			return
							
		obj.destroy()
		self.elements.remove(obj)


	def handle_hover(self, mouse_pos):
		for e in self.elements:
			e.handle_hover(mouse_pos)

		self.left_pin_bar.handle_hover(mouse_pos)
		self.right_pin_bar.handle_hover(mouse_pos)


	def run_logic(self):
		for e in self.elements:
			if type(e) in (chip, cable):
				e.exec_logic()


	def draw(self, screen, mouse_pos):

		if self.saving:
			self.save_text_box.draw(screen)
			return
		
		current_w = pygame.display.Info().current_w
		current_h = pygame.display.Info().current_h

		screen.fill((56,145,196))

		LGRAY = (40,120,165)
		VLGRAY = (160,160,160)
		px_grid = 10
		
		# drawing grid
		for i in range(0, current_w, px_grid):
			p1 = (i, 0)
			p2 = (i, current_h)
			pygame.draw.line(screen, LGRAY, p1, p2)

		for i in range(0, current_h, px_grid):
			p1 = (0, i)
			p2 = (current_w, i)
			pygame.draw.line(screen, LGRAY, p1, p2)

		# cursor lines:
		i_mouse = mouse_pos[0]//10*10
		p1 = (i_mouse, 0)
		p2 = (i_mouse, current_h)
		pygame.draw.line(screen, VLGRAY, p1, p2)

		i_mouse = mouse_pos[1]//10*10
		p1 = (0, i_mouse)
		p2 = (current_w, i_mouse)
		pygame.draw.line(screen, VLGRAY, p1, p2)

		# drawing components
		for e in self.elements:
			e.draw(screen)

		#drawing pin bars
		self.left_pin_bar.draw(screen)
		self.right_pin_bar.draw(screen)

		#drawing chip bar
		self.chip_bar.draw(screen)



class chip_button:
	def __init__(self, ch, x, y, h):
		self.chip = ch
		self.h = h 
		self.w = ch.shape.width
		self.shape = pygame.Rect(x, y, self.w, self.h)
		self.color = self.chip.color


	def draw(self, screen):
		
		pygame.draw.rect(screen, self.color, self.shape)

		font_obj = pygame.font.Font('freesansbold.ttf', 20)
		text_surface_obj = font_obj.render(self.chip.name, True, (10,10,10))
		text_coords = tuple(map(sum, zip(self.shape.topleft, (10,10))))
		screen.blit(text_surface_obj, text_coords)

	def get_board(self):

		logic = self.chip.logic[2]

		if callable(logic):
			return None
		else:
			return logic

	def handle_event(self, event):

		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			if self.shape.collidepoint(event.pos):
				chip_copy = copy.deepcopy(self.chip)
				chip_copy.shape.topleft = event.pos
				post(Event(USEREVENT, obj=chip_copy, task='create_chip'))

		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
			if self.shape.collidepoint(event.pos):
				post(Event(USEREVENT, obj=self, task='edit_chip'))

class chip_bar:
	def __init__(self, chips = []):
		current_w = pygame.display.Info().current_w
		current_h = pygame.display.Info().current_h

		self.h = 60
		self.spacing = 10

		self.creating_chip = False

		self.w = current_w
		self.shape = pygame.Rect(0, current_h - self.h, self.w, self.h)
		self.chips = chips
		self.chip_buttons = []
		
		for c in chips:
			self.add_chip(c)

	def add_chip(self, c):
		x = sum([cb.w for cb in self.chip_buttons])
		x += (len(self.chip_buttons)+1)*self.spacing
		y = self.shape.bottom-self.h+self.spacing
		h = self.h - 2*self.spacing

		new_chip_button = chip_button(c, x, y, h)

		for i, cb in enumerate(self.chip_buttons):
			if cb.chip.name == c.name:
				new_chip_button.shape = cb.shape
				self.chip_buttons[i] = new_chip_button
				return

		self.chip_buttons.append(new_chip_button)

	def handle_event(self, event):

		if event.type == USEREVENT and event.task == 'create_chip':
			if not self.creating_chip:
				self.creating_chip = True
				self.chip_being_created = event.obj

		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
			if self.creating_chip:
				self.creating_chip = False
				self.chip_being_created = None

		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			if self.creating_chip:
				post(Event(USEREVENT, obj=self.chip_being_created, task='confirm_create_chip'))
				self.creating_chip = False
				self.chip_being_created = None

		elif event.type == pygame.MOUSEMOTION:
			if self.creating_chip:
				self.chip_being_created.shape.center = snap_coords_2_grid(event.pos)
				for pin_name in self.chip_being_created.pins:
					self.chip_being_created.pins[pin_name].chip_coords =\
					 self.chip_being_created.shape.topleft

		for cb in self.chip_buttons:
			cb.handle_event(event)


	def draw(self, screen):

		pygame.draw.rect(screen, (100,100,100), self.shape)
		pygame.draw.line(
			screen, 
			(0,0,0), 
			self.shape.topleft, 
			self.shape.topright,
			2
		)

		i = 0
		spacing = 10
		chip_w = 100

		for c in self.chip_buttons:
			c.draw(screen)

		if self.creating_chip:
			self.chip_being_created.draw(screen)

		