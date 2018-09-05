#-*-coding:utf-8-*-
"""
建築用ホバリングスクリプト

コマンド：
	/hover
		ホバリングモードのON/OFF切り替え
		ホバリングモードONの時にジャンプしたら、自動的にホバリング開始
"""
from twisted.internet import reactor
from pyspades.constants import *
from pyspades.common import Vertex3
from commands import add, admin

import math

HOVER_SPEED = 0.2
HIGHER_SPEED = 0.6

@admin
def hover(connection):
	print(connection.hover_right)
	connection.hover_right = not connection.hover_right
	if connection.hover_right:
		connection.send_chat("Hover ON")
	else:
		connection.send_chat("Hover OFF")
	print(connection.hover_right)
add(hover)


def apply_script(protocol, connection, config):
	class HoverProtocol(protocol):
		def on_map_change(self, map):
			for player in self.players.values():
				player.hover_right = False
				player.hover = False
			protocol.on_map_change(self, map)
	
	class HoverConnection(connection):
		#飛行中判定
		hover = False
		
		#ホバリングモード
		hover_right = False
		
		#入力された移動方向
		fw = False
		bw = False
		le = False
		ri = False
		up = False
		dw = False
		
		#移動スピード
		speed = HOVER_SPEED
		
		def hovering(self, x, y, z):
			if isinstance(self.world_object, type(None)):
				return
			if self.hover:
				if  self.fw or self.bw or self.le or self.ri or self.up or self.dw:
					ox, oy, oz = self.world_object.orientation.get()
					n = math.pow(oz, 2)
					m = 1 - n
					
					x2 = ox * self.speed
					y2 = oy * self.speed
					z2 = oz * self.speed
					
					x3 = ox * oz / math.sqrt(m) * self.speed
					y3 = oy * oz / math.sqrt(m) * self.speed
					z3 = math.sqrt(m) * self.speed
					
					dx = x
					dy = y
					dz = z
					
					if self.fw:
						dx += x2
						dy += y2
						dz += z2
					if self.bw:
						dx -= x2
						dy -= y2
						dz -= z2
					if self.le:
						dx += y2 / math.sqrt(m)
						dy -= x2 / math.sqrt(m)
					if self.ri:
						dx -= y2 / math.sqrt(m)
						dy += x2 / math.sqrt(m)
					if self.up:
						dx += x3
						dy += y3
						dz -= z3
					if self.dw:
						dx -= x3
						dy -= y3
						dz += z3
					dx = (dx + 511) % 511
					dy = (dy + 511) % 511
					
					ddx = math.floor(dx + 0.5)
					ddy = math.floor(dy + 0.5)
					ddz = math.floor(dz + 0.5)
					if self.protocol.map.get_solid(ddx, ddy, ddz):
						dx = x
						dy = y
						dz = z
					elif self.protocol.map.get_solid(ddx, ddy, ddz+1):
						dz -= 1
						self.hover = False
						
					if dz < -90:
						dz = z
				
				else:
					dx = x
					dy = y
					dz = z
				self.set_location((dx, dy, dz))
				reactor.callLater(0.01, self.hovering, dx, dy, dz)
		
		"""
		shiftキー（上昇）、ctrlキー（下降）の入力を受け取ってホバリング用の情報に変換
		"""
		def on_animation_update(self,jump,crouch,sneak,sprint):
			if not self.hover and self.hover_right and jump:
				self.hover = True
				x, y, z = self.world_object.position.get()
				self.hovering(x, y, z)
			if self.hover:
				if sprint:
					self.up = True
				else:
					self.up = False
				if crouch:
					self.dw = True
				else:
					self.dw = False
			return connection.on_animation_update(self,jump,crouch,sneak,sprint)
		
		"""
		WASDによる移動を受け取ってホバリング用の情報に変換
		"""
		def on_walk_update(self, fw, bw, le, ri):
			if fw:
				self.fw = True
			else:
				self.fw = False
			if bw:
				self.bw = True
			else:
				self.bw = False
			if le:
				self.le = True
			else:
				self.le = False
			if ri:
				self.ri = True
			else:
				self.ri = False
			return connection.on_walk_update(self, fw, bw, le, ri)
		
		"""
		移動速度の変更
		"""
		def on_secondary_fire_set(self, secondary):
			if secondary:
				self.speed = HIGHER_SPEED
				self.send_chat("SPEED UP")
			else:
				self.speed = HOVER_SPEED
				self.send_chat("SPEED DOWN")
			return connection.on_secondary_fire_set(self, secondary)
		
		
		"""
		この下はホバリングモードを強制解除する条件を設定
		"""
		def on_team_leave(self):
			self.hover = False
			self.hover_right = False
			return connection.on_team_leave(self)
	
		def on_fall(self, damage):
			if self.hover_right:
				return False
			else:
				return connection.on_fall(self, damage)

		def on_disconnect(self):
			self.hover = False
			self.hover_right = False
			return connection.on_disconnect(self)
	
	return HoverProtocol, HoverConnection