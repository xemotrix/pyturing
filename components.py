import pygame
import pygame.gfxdraw
from pygame.event import Event
from pygame.event import post
from pygame import USEREVENT
from pygame.math import Vector2
import math
import main
import shapely

from utils import * 

from shapely.geometry import *


def distance_to_line(line, point):
	
	l = LineString(line)
	p = Point(point)

	return l.distance(p)


def get_aaline_vertices(p1, p2, thickness=2):
	center_p = ( (p1[0]+p2[0])/2, (p1[1]+p2[1])/2 )

	length = distance(p1, p2)
	angle = math.atan2(p1[1]-p2[1], p1[0]-p2[0]) 

	UL = (center_p[0] + (length / 2.) * math.cos(angle) - (thickness / 2.) * math.sin(angle),
		center_p[1] + (thickness / 2.) * math.cos(angle) + (length / 2.) * math.sin(angle))
	UR = (center_p[0] - (length / 2.) * math.cos(angle) - (thickness / 2.) * math.sin(angle),
		center_p[1] + (thickness / 2.) * math.cos(angle) - (length / 2.) * math.sin(angle))
	BL = (center_p[0] + (length / 2.) * math.cos(angle) + (thickness / 2.) * math.sin(angle),
		center_p[1] - (thickness / 2.) * math.cos(angle) + (length / 2.) * math.sin(angle))
	BR = (center_p[0] - (length / 2.) * math.cos(angle) + (thickness / 2.) * math.sin(angle),
		center_p[1] - (thickness / 2.) * math.cos(angle) - (length / 2.) * math.sin(angle))

	return UL, UR, BR, BL


class component:
	def destroy(self):
		return


	def handle_hover(self, mouse_pos):
		return


	def handle_event(self, event):
		return


	def draw(self, screen):
		return


class io_pin(component):
	def __init__(self, position, y):

		y = y//10*10
		current_w = get_current_w()

		self.h = 40
		self.position = position
		self.value = False
		self.hover = False
		self.clicked = False
		self.moving = False
		self.pin_radius = 12
		self.cables = []
		self.has_cable = False

		x_coord_text_box = None

		if position == 'left':
			self.is_active = True
			x_coord_text_box = 100

			self.sw_coords = [50, y]
			self.pin_coords = [50+20+self.pin_radius, y]

			self.grab_shape = pygame.Rect(0, self.sw_coords[1]-20, 20, self.h)
			self.shape = pygame.Rect(0, y-20, 70, self.h)

		elif position == 'right':
			self.is_active = False
			x_coord_text_box = current_w - 200 - 100

			self.sw_coords = [current_w - 50, y]
			self.pin_coords = [current_w - 50 - 20 - 12, y]

			self.grab_shape = pygame.Rect(current_w-20, self.sw_coords[1]-20, 20, self.h)
			self.shape = pygame.Rect(current_w - 70, y-20, 70, self.h)


		self.text_box = text_box(x_coord_text_box, self.shape.top, 200, self.h)


	@property
	def name(self):
		return self.text_box.text
	

	def handle_event(self, event):

		self.text_box.handle_event(event)
		
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			if self.grab_shape.collidepoint(event.pos):
				self.offset = Vector2(self.shape.topleft) - event.pos
				self.clicked = True

			elif distance(self.sw_coords, event.pos) < self.h/2:
				self.value = not self.value

		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
			if self.shape.collidepoint(event.pos):
				self.text_box.activate()


		elif event.type == pygame.MOUSEMOTION:
			if self.clicked:
				self.sw_coords[1] = (event.pos[1] + self.offset[1] + self.h/2)//10*10
				self.pin_coords[1] = (event.pos[1] + self.offset[1] + self.h/2)//10*10

				self.shape.topleft = (
					self.shape.topleft[0], 
					(event.pos[1] + self.offset[1])//10*10
				)
				self.grab_shape.topleft = (
					self.grab_shape.topleft[0], 
					(event.pos[1] + self.offset[1])//10*10
				)

				self.moving = True

		elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
			if self.clicked and not self.moving:
				self.clicked = False
				
			elif self.moving:
				self.moving = False
				self.clicked = False

			elif distance(self.pin_coords, event.pos) < self.pin_radius:
				post(Event(USEREVENT, obj=self, task='create_cable'))
				

	def handle_hover(self, mouse_pos):
		self.hover = distance(self.pin_coords, mouse_pos) < self.pin_radius
	

	def draw(self, screen):
	
		if self.position == 'left':
			x_coord = 25
		elif self.position == 'right':
			x_coord = self.sw_coords[0] + 25

		# colors
		if self.value:
			color_sw = (0, 220, 0)
		else:
			color_sw = (10, 10, 10)

		if self.hover:
			color_pin = (210, 210, 210)
		else:
			color_pin = (10, 10, 10)

		#bbox
		#pygame.draw.rect(screen, (120,0,0), self.shape)

		# on-off switch
		pygame.draw.circle(screen, color_sw, self.sw_coords, self.h/2)

		# pin
		pygame.draw.circle(screen, color_pin, self.pin_coords, self.pin_radius)

		# grab rectangle
		pygame.draw.rect(screen, (120,120,120), self.grab_shape)

		# text box
		if self.text_box.active:
			self.text_box.shape.top = self.shape.top 
			self.text_box.draw(screen)

		

class pin_bar(component):
	def __init__(self, position, current_w, current_h):
		self.position = position
		self.pins = []

		current_w = get_current_w()
		current_h = get_current_h()

		if self.position == 'left':
			self.shape = pygame.Rect(0, 0, 50, current_h-60)

		elif self.position == 'right':
			self.shape = pygame.Rect(current_w - 50, 0, 50, current_h-60)


	def __getitem__(self, pin_name):


		if type(pin_name) != str:
			raise TypeError(f'pin_bar indices must be str')

		for p in self.pins:
			if p.name == pin_name:
				return p

		raise KeyError(f'"{pin_name}" is not a pin in this pin_bar')
	

	def handle_event(self, event):
		
		for p in self.pins:
			p.handle_event(event)

		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			if self.shape.collidepoint(event.pos):
				
				# check if an io_pin is clicked:
				io_p_clicked = False
				for io_p in self.pins:
					if io_p.shape.collidepoint(event.pos):
						io_p_clicked = True
						break

				# add io_pin if none is clicked
				if not io_p_clicked:
					self.add_io_pin(event.pos)

		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
			for i, io_p in enumerate(self.pins):
				if distance(io_p.sw_coords, event.pos) < io_p.h/2:
					self.del_io_pin(i)
					post(Event(USEREVENT, obj=io_p, task='delete_me'))
					


	def handle_hover(self, mouse_pos):
		for p in self.pins:
			p.handle_hover(mouse_pos)


	def draw(self, screen):
		
		pygame.draw.rect(screen, (80,80,80), self.shape)
		
		for pin in self.pins:
			pin.draw(screen)
		

	def add_io_pin(self, position):
		h = position[1]
		self.pins.append(io_pin(self.position, h))


	def del_io_pin(self, index):
		del self.pins[index]

class chip_pin(component):
	def __init__(self, name, io_type, pin_radius):
		self.name = name
		self.io_type = io_type
		self.is_active = io_type == 'o'
		self.value = False
		self.rel_coords = () 
		self.chip_coords = () 
		self.radius = pin_radius
		self.hover = False
		self.pin_coords = ()
		self.has_cable = False
		self.focus = False


	def handle_hover(self, mouse_pos):
		if self.pin_coords:
			if distance(self.pin_coords, mouse_pos) < self.radius:
				self.hover = True
			else:
				self.hover = False


	def handle_event(self, event):
		if event.type == pygame.MOUSEBUTTONUP and event.button == 1:

			if distance(self.pin_coords, event.pos) < self.radius:
				post(Event(USEREVENT, obj=self, task='create_cable'))
				

	def update_coords(self):
		self.pin_coords = tuple(
			map(sum, zip(self.chip_coords, self.rel_coords))
		)


	def draw(self, screen):
		self.update_coords()
		if self.value:
			color = (0, 210, 0)
		elif self.hover:
			color = (210, 210, 210)
		else:
			color = (0, 0, 0)

		pygame.draw.circle(screen, color, self.pin_coords, self.radius)



class chip(component):
	def __init__(self, name, color, coords, pins, logic):
		
		self.name = name
		font = pygame.font.Font('freesansbold.ttf', 20)
		#self.w = len(name)*20
		self.w = font.size(name)[0] + 24
		self.logic = logic
		self.vars = pins
		self.color = color
		self.clicked = False
		self.focus = False

		self.n_i_pins = 0
		self.n_o_pins = 0

		self.pins = {}
		self.vars = {}

		self.pin_radius = 10

		for io_type, pin_names in pins.items():
			
			for pin_name in pin_names:	
				if io_type == 'i':
					self.n_i_pins += 1
				elif io_type == 'o':
					self.n_o_pins += 1

				self.pins[pin_name] = chip_pin(pin_name, io_type, self.pin_radius)
				self.vars[pin_name] = False

		
		max_pins_side = (max(self.n_i_pins, self.n_o_pins))
		self.h = max_pins_side * self.pin_radius*2
		self.shape = pygame.Rect(coords[0], coords[1], self.w, self.h)

		self.assing_pin_coords()
		self.exec_logic()


	def handle_event(self, event):
		
		for pin_name in self.pins:
			self.pins[pin_name].handle_event(event)

		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			
			if self.shape.collidepoint(event.pos):

				self.offset = Vector2(self.shape.topleft) - event.pos
				self.clicked = True
				self.focus = True
				for pin_name in self.pins:
					self.pins[pin_name].focus = True
			else:
				self.clicked = False
				self.focus = False
				for pin_name in self.pins:
					self.pins[pin_name].focus = False

		elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
			self.clicked = False

		elif event.type == pygame.MOUSEMOTION:
			if self.clicked:
				self.shape.topleft = (event.pos + self.offset)//10*10

				
		
		elif event.type == pygame.KEYDOWN:
			if self.focus:
				if event.key == pygame.K_DELETE:
						post(Event(USEREVENT, obj=self, task='delete_me'))	

				elif event.key == pygame.K_UP:
					if self.shape.top > 10:
						self.shape.top -= 5 

				elif event.key == pygame.K_DOWN:
					if self.shape.bottom < get_current_h()-10:
						self.shape.bottom += 5 

				elif event.key == pygame.K_LEFT:
					if self.shape.left > 10:
						self.shape.left -= 5

				elif event.key == pygame.K_RIGHT:
					if self.shape.right < get_current_w()-10:
						self.shape.right += 5
	

	def handle_hover(self, mouse_pos):
		for pin in self.pins.values():
			pin.handle_hover(mouse_pos)


	def exec_logic(self):
		
		out_vars, in_vars, instr = self.logic

		if not callable(instr):
			
			logic_board = instr

			for v in in_vars:
				logic_board.left_pin_bar[v].value = self.pins[v].value
			
			logic_board.run_logic()

			for v in out_vars:
				self.pins[v].value = logic_board.right_pin_bar[v].value
			
		else: 
			in_values = [self.pins[v].value for v in in_vars]
			result = instr(in_values)

			for out_var, res in zip(out_vars, result):
				self.pins[out_var].value = res 


	def get_pin_values(self):
		result = {}

		for pin_name, p in self.pins.items():
			result[pin_name] = p.value

		return result


	def assing_pin_coords(self):
		res = {}

		i_i = 0
		i_o = 0

		for pin_name, pin in self.pins.items():
			if pin.io_type == 'i':
				rel_coords = (0, self.pin_radius *(1 + i_i*2))
				i_i += 1
			else:
				rel_coords = (self.w, self.pin_radius*(1 + i_o*2))
				i_o += 1

			self.pins[pin_name].chip_coords = (self.shape[0], self.shape[1])
			self.pins[pin_name].rel_coords = rel_coords
	

	def draw(self, screen):
		if self.focus:
			pygame.draw.rect(screen, (140,200,220), 
				pygame.Rect(
					self.shape[0]-5, self.shape[1]-5, self.shape[2]+10, self.shape[3]+10)
			)
		pygame.draw.rect(screen, self.color, self.shape)
		
		for pin in self.pins.values():
			pin.chip_coords = self.shape.topleft
			pin.draw(screen)

		font_obj = pygame.font.Font('freesansbold.ttf', 20)
		text_surface_obj = font_obj.render(self.name, True, (10,10,10))
		text_coords = tuple(map(sum, zip(self.shape.topleft, (12,12))))
		screen.blit(text_surface_obj, text_coords)
	


class cable_pin(component):
	def __init__(self, coords):
		self.is_active = True
		self.pin_coords = coords
		self.radius = 10
		self.value = False
		self.hover = False
		self.clicked = False
		self.moving = False
		self.cable_being_created = True


	def handle_hover(self, mouse_pos):
		if distance(self.pin_coords, mouse_pos) < self.radius:
			self.hover = True
		else:
			self.hover = False


	def handle_event(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			if self.hover:
				self.clicked = True

		elif event.type == pygame.MOUSEMOTION:
			if self.clicked:
				self.moving = True
				self.pin_coords = event.pos

		elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
			if self.moving:
				self.moving = False

			elif not self.cable_being_created and self.hover:
				post(Event(USEREVENT, obj=self, task='create_cable'))
			self.clicked = False	


	def draw(self, screen):

		if self.value:
			color = (0, 220, 0)
		else:
			color = (10, 10, 10)

		if self.hover:
			pygame.draw.circle(screen, (210,210,210), snap_coords_2_grid( self.pin_coords ), 
				self.radius)

		pygame.draw.circle(screen, color, snap_coords_2_grid( self.pin_coords ), 
			int(self.radius/2))


class cable(component):
	def __init__(self, origin_pin):

		self.being_drawn = True
		self.pin_coords = None
		self.origin_pin = origin_pin
		self.value = False
		self.pins = []

		self.hover = False
		self.active_pin = None
		self.passive_pins = []

		if origin_pin.is_active:
			self.active_pin = origin_pin
		else:
			self.passive_pins.append(origin_pin)


	def destroy(self):
		for p in self.passive_pins:
			p.has_cable = False
			p.value = False


	def handle_event(self, event):
		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			pass

		elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
			if self.being_drawn:
				coord = event.pos[0]//10*10, event.pos[1]//10*10
				self.pins.append(cable_pin(coord))
				
		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
			if self.being_drawn:
				post(Event(USEREVENT, obj = self, task='cancel_draw_cable'))

		elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
			if self.hover:
				post(Event(USEREVENT, obj = self, task='delete_me'))

		for p in self.pins:
			p.handle_event(event)


	def exec_logic(self):

		if not self.being_drawn:
			self.value = self.active_pin.value
			
			for p in self.passive_pins:
				p.value = self.value

			for p in self.pins:
				p.value = self.value


	def handle_hover(self, mouse_pos):
		self.hover_node = None
		

		for i, p in enumerate(self.pins):
			if p.handle_hover(mouse_pos):
				self.hover_node = i
				break

		if not self.being_drawn:

			coords_origin = self.active_pin.pin_coords
			coords_dest = self.passive_pins[0].pin_coords

			path = [coords_origin] + [p.pin_coords for p in self.pins] + [coords_dest]
			self.hover = False
			for p1, p2 in zip(path[:-1], path[1:]):
				if distance_to_line((p1,p2), mouse_pos) < 10:
					self.hover = True


	def close_cable(self, destination_pin):

		self.destination_pin = destination_pin 
		
		if self.active_pin is None:
			if not destination_pin.is_active:
				return False
			else:
				self.active_pin = destination_pin
		else:
			if destination_pin.is_active:
				return False
			else:
				self.passive_pins.append(destination_pin)

		self.being_drawn = False
		
		del self.pins[-1]

		if self.passive_pins[0].has_cable:
			return False

		for p in self.pins:
			p.cable_being_created = False
		
		self.active_pin.has_cable = True
		self.passive_pins[0].has_cable = True

		return True
		

	def draw(self, screen):
		
		coords_origin = self.origin_pin.pin_coords

		if self.being_drawn:
			coords_dest = pygame.mouse.get_pos()
		else:
			coords_dest = self.destination_pin.pin_coords

		path = [coords_origin] + [p.pin_coords for p in self.pins] + [coords_dest]

		if self.value:
			color = (0, 220, 0)
		else:
			color = (10, 10, 10)

		# drawing lines
		if self.hover:
			thickness = 8
		else:
			thickness = 4

		for p1, p2 in zip(path[:-1], path[1:]):
			vertices = get_aaline_vertices(
				snap_coords_2_grid( p1 ), snap_coords_2_grid( p2 ), thickness)
			
			pygame.gfxdraw.aapolygon(screen, vertices, color)
			pygame.gfxdraw.filled_polygon(screen, vertices, color)
			#pygame.draw.line(
			#	screen, color, snap_coords_2_grid( p1 ), snap_coords_2_grid( p2 ), thickness)

		# drawing pins
		for p in self.pins:
			p.draw(screen)
		

