import pygame

from pygame.event import Event
from pygame.event import post
from pygame import USEREVENT

import math

import time

def snap_coords_2_grid(coords):
	return (coords[0]//10*10, coords[1]//10*10)


def distance(point1, point2):
	sqx = (point1[0] - point2[0])**2
	sqy = (point1[1] - point2[1])**2

	return math.sqrt(sqx + sqy)


def get_current_w():
	return pygame.display.Info().current_w


def get_current_h():
	return pygame.display.Info().current_h



class text_box:
	def __init__(self, x, y, w, h, text_size=20, max_characters=12):

		self.text_size = text_size
		
		self.text = ''
		self.cursor = 0
		self.active = True
		self.has_event_lock = False

		self.max_characters = max_characters
		self.cursor_pulse_ms = 800

		self.x = x
		self.y = y

		self.w = w
		self.h = h

		self.shape = pygame.Rect(x, y, self.w, self.h)

		post(Event(USEREVENT, obj=self, task='write_on_text_box'))


	def handle_event(self, event):
		
		if self.active:
			if self.has_event_lock:
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
						if self.text:
							self.has_event_lock = False
							self.active = False
							post(Event(USEREVENT, obj=self, task='clear_event_lock'))

					elif event.key == pygame.K_BACKSPACE:
						self.text = self.text[:-1]

				elif event.type == pygame.TEXTINPUT:
					if len(self.text) <= self.max_characters:
						self.text += event.text

				elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					if self.text:
						self.has_event_lock = False
						self.active = False
						post(Event(USEREVENT, obj=self, task='clear_event_lock'))

			elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
				if self.shape.collidepoint(event.pos):
					post(Event(USEREVENT, obj = self, task='write_on_text_box'))

	def activate(self):
		self.active = True
		post(Event(USEREVENT, obj=self, task='write_on_text_box'))


	def draw(self, screen):


		pygame.draw.rect(screen, (60,60,60), self.shape)

		if int(time.time()*1000) % self.cursor_pulse_ms < self.cursor_pulse_ms/2:
			text_to_print = self.text + '|'
		else:
			text_to_print = self.text

		font_obj = pygame.font.Font('freesansbold.ttf', self.text_size)
		text_surface_obj = font_obj.render(text_to_print, True, (230,230,230))
		text_coords = tuple(map(sum, zip(self.shape.topleft, (10,12))))
		screen.blit(text_surface_obj, text_coords)
