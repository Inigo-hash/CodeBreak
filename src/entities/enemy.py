import pygame

class Enemy:
	def __init__(self, screen, map_width, map_height, world_x=None, world_y=None):
		self.screen = screen

		# Load backward walking frames from the duwende_mandurug folder
		# There are 3 frames in this asset set
		raw_frames = [pygame.image.load(f"assets/images/frames/duwende_mandurug/walking/walking_backward/frame_{i}.png").convert_alpha() for i in range(8)]

		# Scale them down so they appear reasonably sized next to the player
		self.frames = [pygame.transform.scale(f, (f.get_width() // 4, f.get_height() // 4)) for f in raw_frames]

		# Position in world coordinates (unscaled)
		if world_x is None:
			self.center_x = map_width // 2 - 100
		else:
			self.center_x = world_x

		if world_y is None:
			self.center_y = map_height // 2
		else:
			self.center_y = world_y

		self.current = 0
		self.timer = 0

	def draw_frames(self, ZOOM, camera_x, camera_y):
		# advance animation
		self.timer += 1
		if self.timer >= 10:
			self.timer = 0
			self.current = (self.current + 1) % len(self.frames)

		frame = self.frames[self.current]
		draw_x = self.center_x * ZOOM - camera_x - frame.get_width() // 2
		draw_y = self.center_y * ZOOM - camera_y - frame.get_height() // 2
		self.screen.blit(frame, (draw_x, draw_y))
