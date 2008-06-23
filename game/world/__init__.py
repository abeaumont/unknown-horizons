# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

__all__ = ['island', 'player', 'settlement']

import game.main
from game.world.island import Island
from game.world.player import Player
from stablelist import stablelist

class World(object):
	def __init__(self):
		#load properties
		self.properties = {}
		for (name, value) in game.main.db("select name, value from map.map_properties"):
			self.properties[name] = value

		#load islands
		self.islands = stablelist()
		for index,(island, offset_x, offset_y) in enumerate(game.main.db("select island, x, y from map.island")):
			self.islands[index] = Island(index, offset_x, offset_y, island)

		#calculate map dimensions
		self.min_x, self.min_y, self.max_x, self.max_y = None, None, None, None
		for i in self.islands.values():
			self.min_x = i.x if self.min_x == None or i.x < self.min_x else self.min_x
			self.min_y = i.y if self.min_y == None or i.y < self.min_y else self.min_y
			self.max_x = (i.x + i.width - 1) if self.max_x == None or (i.x + i.width - 1) > self.max_x else self.max_x
			self.max_y = (i.y + i.height - 1) if self.max_y == None or (i.y + i.width - 1) > self.max_y else self.max_y
		self.min_x -= 10
		self.min_y -= 10
		self.max_x += 10
		self.max_y += 10

		#add water
		print "Filling world with water..."
		self.grounds = []
		for x in xrange(self.min_x, self.max_x):
			for y in xrange(self.min_y, self.max_y):
				for i in self.islands:
					for g in i.grounds:
						if g.x == x and g.y == y:
							break
					else: #found no instance at x,y in the island
						continue
					break
				else: #found no instance at x,y at any island
					self.grounds.append(game.main.session.entities.grounds[int(self.properties.get('default_ground', 13))](x, y))
		print "done."

		#setup players
		self.player = Player(0, "Arthus")
		self.players = stablelist()
		self.players.append(self.player)

		#add ship
		self.ships = stablelist()
		self.ships.append(game.main.session.entities.units[1](25, 25))
		self.ships.append(game.main.session.entities.units[1](29, 25))

		game.main.session.ingame_gui.status_set("gold", str(self.player.inventory.get_value(1)))

	def get_building(self, x, y):
		i = self.get_island(x, y)
		return None if i == None else i.get_building(x, y)

	def get_island(self, x, y,):
		"""Returns the island for that coordinate, if none is found, returns None.
		@param x: int x position.
		@param y: int y position. """
		for i in self.islands:
			if not (i.x <= x < i.x + i.width and i.y <= y < i.y + i.height):
				continue
			for tile in i.grounds:
				if tile.x == x and tile.y == y:
					return i
		return None

	def __del__(self):
		print 'deconstruct',self

	def save(self, db = 'savegame'):
		for player in self.players:
			player.save(db)
		for island in self.islands:
			island.save(db)
		for ship in self.ships:
			ship.save(db)
		for building in self.buildings:
			building.save(db)
