import math
import sys

import numpy as np
import pygame

pygame.init()
scr_w, scr_h = 600, 400
screen = pygame.display.set_mode((scr_w, scr_h))
pygame.display.set_caption('3d engine')
pygame.mouse.set_visible(False)
pygame.mouse.set_pos(scr_w / 2, scr_h / 2)
clock = pygame.time.Clock()


class Engine:

  def __init__(self):
    self.camera = Camera()
    self.points = [Point(0, 0, 0, (255, 255, 255), 2)]
    self.cubes = [
        Cube(i1 * 30, i2 * 30, i3 * 30, (255, 255, 255), 30) for i1 in range(5)
        for i2 in range(5) for i3 in range(5)
    ]

  def render(self, screen):
    cam_dir_x = math.radians(self.camera.rot[0])
    cam_dir_y = math.radians(self.camera.rot[1])
    rot_mat_x = np.array([[1, 0, 0],
                          [0, np.cos(cam_dir_x), -np.sin(cam_dir_x)],
                          [0, np.sin(cam_dir_x),
                           np.cos(cam_dir_x)]])
    rot_mat_y = np.array([[np.cos(cam_dir_y), 0,
                           np.sin(cam_dir_y)], [0, 1, 0],
                          [-np.sin(cam_dir_y), 0,
                           np.cos(cam_dir_y)]])
    for point in self.points:
      point.draw(screen, self.camera.fov, self.camera.zclip_dist,
                 self.camera.pos, rot_mat_x, rot_mat_y)
    for cube in self.cubes:
      cube.draw(screen, self.camera.fov, self.camera.zclip_dist,
                self.camera.pos, rot_mat_x, rot_mat_y)
    pygame.draw.rect(screen, (0, 255, 0), (scr_w / 2 - 1, scr_h / 2 - 1, 2, 2))

  def update(self):
    self.camera.update()


class Camera:

  def __init__(self):
    self.pos = np.array([0, -15, 0], dtype='float64')
    self.rot = np.array([0, 0, 0])
    self.fov = 240
    self.speed = 4
    self.zclip_dist = 1

  def move(self):
    keys = pygame.key.get_pressed()
    direction = np.array([0, 0, 0], dtype='float64')
    if keys[pygame.K_w]:
      direction += self.rotate_2d(0, self.speed)
    elif keys[pygame.K_s]:
      direction -= self.rotate_2d(0, self.speed)
    if keys[pygame.K_a]:
      direction -= self.rotate_2d(self.speed, 0)
    elif keys[pygame.K_d]:
      direction += self.rotate_2d(self.speed, 0)
    if keys[pygame.K_q]:
      direction[1] -= self.speed
    elif keys[pygame.K_e]:
      direction[1] += self.speed
    self.pos += direction

  def rotate_2d(self, x, y):
    dir = math.radians(self.rot[1])
    rx = math.cos(dir) * x - math.sin(dir) * y
    ry = math.sin(dir) * x + math.cos(dir) * y
    return np.array([rx, 0, ry])

  def rotate(self):
    move_x, move_y = pygame.mouse.get_rel()
    self.rot[1] -= move_x * 0.4
    self.rot[0] += move_y * 0.4

  def update(self):
    self.rotate()
    self.move()


class Cube:

  def __init__(self, x, y, z, color, width):
    self.vertecies = [(-1, 1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1),
                      (-1, 1, 1), (1, 1, 1), (1, -1, 1), (-1, -1, 1)]
    self.edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7),
                  (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
    self.faces = [(0, 1, 2, 3), (4, 5, 6, 7), (4, 9, 0, 8), (6, 10, 2, 11),
                  (7, 8, 3, 11), (5, 9, 1, 10)]
    self.center = np.array([x, y, z])
    self.color = color
    self.width = width

  def draw_one_line(self, vertex_1, vertex_2, screen, color, fov, zclip_dist,
                    cam_pos, rot_mat_x, rot_mat_y):
    t_v1 = vertex_1 - cam_pos
    t_v2 = vertex_2 - cam_pos
    r_v1 = np.dot(rot_mat_y, np.dot(rot_mat_x, t_v1))
    r_v2 = np.dot(rot_mat_y, np.dot(rot_mat_x, t_v2))
    if r_v1[2] > zclip_dist or r_v2[2] > zclip_dist:
      clip_v1, clip_v2 = self.zclip(r_v1, r_v2, zclip_dist)
      v1_x = fov * clip_v1[0] / clip_v1[2] + scr_w / 2
      v1_y = fov * clip_v1[1] / clip_v1[2] + scr_h / 2
      v2_x = fov * clip_v2[0] / clip_v2[2] + scr_w / 2
      v2_y = fov * clip_v2[1] / clip_v2[2] + scr_h / 2
      pygame.draw.line(screen, color, (v1_x, v1_y), (v2_x, v2_y))

  def zclip(self, p1, p2, zclip_dist):
    percent = (zclip_dist - p1[2]) / (p2[2] - p1[2])
    clip_p1 = p1
    clip_p2 = p2
    if p1[2] < zclip_dist:
      clip_p1 = p1 + percent * (p2 - p1)
      clip_p1[2] = zclip_dist
    if p2[2] < zclip_dist:
      clip_p2 = p1 + percent * (p2 - p1)
      clip_p2[2] = zclip_dist
    return clip_p1, clip_p2

  def draw(self, screen, fov, zclip_dist, cam_pos, rot_mat_x, rot_mat_y):
    for edge in self.edges:
      vertex_1 = self.center + np.array(self.vertecies[edge[0]]) * self.width
      vertex_2 = self.center + np.array(self.vertecies[edge[1]]) * self.width
      self.draw_one_line(vertex_1, vertex_2, screen, self.color, fov,
                         zclip_dist, cam_pos, rot_mat_x, rot_mat_y)


class Point:

  def __init__(self, x, y, z, color, r):
    self.pos = np.array([x, y, z])
    self.color = color
    self.r = r

  def transform(self, pos, cam_pos):
    return pos - cam_pos

  def rotate(self, pos, rot_mat_x, rot_mat_y):
    return np.dot(rot_mat_x, np.dot(rot_mat_y, pos))

  def projection(self, pos, fov, zclip_dist, cam_pos, rot_mat_x, rot_mat_y):
    t_pos = self.transform(pos, cam_pos)
    r_pos = self.rotate(t_pos, rot_mat_x, rot_mat_y)
    draw, x, y = False, 0, 0
    if r_pos[2] > zclip_dist:
      draw = True
      x = r_pos[0] * fov / r_pos[2] + scr_w / 2
      y = r_pos[1] * fov / r_pos[2] + scr_h / 2
    return draw, (x, y)

  def draw(self, screen, fov, zclip_dist, cam_pos, rot_mat_x, rot_mat_y):
    draw, pos = self.projection(self.pos, fov, zclip_dist, cam_pos, rot_mat_x,
                                rot_mat_y)
    if draw:
      pygame.draw.circle(screen, self.color, (int(pos[0]), int(pos[1])),
                         self.r)


engine = Engine()

while True:
  pygame.display.set_caption(str(clock.get_fps()))
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      pygame.quit()
      sys.exit()
  screen.fill((0, 0, 0))
  engine.update()
  engine.render(screen)
  pygame.display.update()
  clock.tick(30)
