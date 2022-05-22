import pygame
import config
import sys
import math
import time

pygame.font.init()


class Line:
    def __init__(self, x0, y0, x1, y1) -> None:
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1

    def point_at_t(self, t):
        x = self.x0 + t*(self.x1 - self.x0)
        y = self.y0 + t*(self.y1 - self.y0)
        return x, y

class Vehicle:
    def __init__(self) -> None:
        self.x = config.vehicle_x0_px
        self.y = config.vehicle_y0_px
        self.v = 0 # dm/s
        self.theta = config.vehicle_theta_deg # deg
        self.omega = 0 #deg/s
        self.size = config.vehicle_size_px

    def draw(self):
        size = width, height = (300, 300)
        surface = pygame.Surface(size)
        pygame.draw.polygon(surface, GREEN, ((0, 100), (0, 200), (200, 200), (200, 300), (300, 150), (200, 0), (200, 100)))
        surface = pygame.transform.rotate(surface, self.theta)
        surface = pygame.transform.scale(surface, (self.size, self.size))
        p = pos_to_pix(self.x, self.y)
        p = (p[0] - self.size/2, p[1] - self.size/2 )
        screen.blit(surface, p)

    def update(self):
        self.theta += self.omega
        self.x += math.cos(math.radians(self.theta))*self.v
        self.y += math.sin(math.radians(self.theta))*self.v



class Lidar:
    def __init__(self) -> None:
        self.scan_n = config.lidar_scan_n
        self.dtheta_ang = 360 / config.lidar_scan_n
        self.scan_res = {} # Dict with ang as keys and d and line  as values
        self.scan_d_dm = config.lidar_scan_d_dm
        self.t_start = time.time()
        self.n = 0

    def scan(self):
        self.scan_res = {}

        for ang in range(0, 360, math.ceil(360/self.scan_n)):
            x = vehicle.x + math.cos(math.radians(ang + vehicle.theta))*self.scan_d_dm
            y = vehicle.y + math.sin(math.radians(ang + vehicle.theta))*self.scan_d_dm
            l = Line(vehicle.x, vehicle.y, x, y)
            for map_l in map:
                t1, t2 = intersection(l, map_l)

                if t1 <= 1 and t1 >= 0 and t2 <= 1 and t2 >= 0:
                    p = l.point_at_t(t1)
                    d = ((p[0] - vehicle.x)**2 + (p[1] - vehicle.y)**2)**0.5
                else:
                    p = None
                    d = None

                if ang not in self.scan_res:
                    self.scan_res[ang] = (d, l, p)
                else:
                    if d is not None :
                        if ang in self.scan_res:
                            d0,_,_ = self.scan_res[ang]
                            if d0 is None  or d < d0:
                                self.scan_res[ang] = (d, l, p)
                        else:
                            self.scan_res[ang] = (d, l, p)

    def iter_scans(self):
        return self

    def __next__(self):
        self.n+=1
        if self.n%60 == 0:
            print(f"hz: {self.n/(time.time() - self.t_start)}")
            self.t_start = time.time()
            self.n = 0

        screen.fill(WHITE)
        
        lidar.scan()
        lidar.draw()
        vehicle.draw()

        for l in map:
            draw_line(l)
        
        # draw_map_intersections()

        # pygame.display.flip()
        pygame.display.update()
        for events in pygame.event.get():
            if events.type == pygame.QUIT:
                sys.exit(0)
            elif events.type == pygame.KEYDOWN:
                if events.dict['unicode'] == 'w':
                    vehicle.v = 1
                elif events.dict['unicode'] == 'a':
                    vehicle.omega = 1
                elif events.dict['unicode'] == 'd':
                    vehicle.omega = -1
                elif events.dict['unicode'] == 's':
                    vehicle.v = -1
            elif events.type == pygame.KEYUP:
                if events.dict['unicode'] == 'w':
                    vehicle.v = 0
                elif events.dict['unicode'] == 'a':
                    vehicle.omega = 0
                elif events.dict['unicode'] == 'd':
                    vehicle.omega = 0
                elif events.dict['unicode'] == 's':
                    vehicle.v = -0

        vehicle.update()

        res = []
        for ang in self.scan_res:
            d, l, p = self.scan_res[ang]
            res.append((1, ang, d))
        
        return res


    def draw(self):
        for key in self.scan_res:
            d, l, p = self.scan_res[key]
            if config.lidar_lines_draw:
                draw_line(l)

        for key in self.scan_res:
            d, l, p = self.scan_res[key]
            if p is not None:
                draw_circle(*p, text=False)
        
def intersection(l1:Line, l2:Line):
    xa0 = round(l1.x0, 9)
    ya0 = round(l1.y0, 9)
    xa1 = round(l1.x1, 9)
    ya1 = round(l1.y1, 9)

    xb0 = round(l2.x0, 9)
    yb0 = round(l2.y0, 9)
    xb1 = round(l2.x1, 9)
    yb1 = round(l2.y1, 9)

    dxa = xa1 - xa0
    dya = ya1 - ya0
    dxb = xb1 - xb0
    dyb = yb1 - yb0

    t1, t2 = -1, -1
    div = dxb*dya - dyb*dxa
    if div != 0:
        t2 = ((yb0 - ya0)*dxa - (xb0 - xa0)*dya) / div

    if dxa != 0:
        t1 = (xb0 - xa0 + dxb*t2)/dxa
    return t1, t2

def draw_line(l:Line):
    p0 = pos_to_pix(l.x0, l.y0)
    p1 = pos_to_pix(l.x1, l.y1)
    pygame.draw.line(screen, BLACK, p0, p1)

def draw_circle(x, y, text=False):
    p = pos_to_pix(x, y)
    pygame.draw.circle(screen, RED, p, radius=5)
    if text:
        text_surface = my_font.render(f'{(x,y)}', False, BLACK)
        screen.blit(text_surface, p)

def pos_to_pix(x, y):
    x += width/2
    y = height - y - 1
    y -= height/2
    return x, y

def draw_map_intersections():
    for i in range(len(map)):
        l1, l2 = map[i], map[(1+i)%len(map)]
        t1, t2 = intersection(l1, l2)

        if t1 <=1  and t1 >= 0:
            p = l1.point_at_t(t1)
        elif t2 <=1  and t2 >= 0:
            p = l2.point_at_t(t2)

        draw_circle(*p, text=True)




width, height = (480, 480)
WHITE = (0,0,0)
BLACK = (255,255,255)
RED = (255, 0 ,0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

screen=pygame.display.set_mode((width,height))
my_font = pygame.font.SysFont('Comic Sans MS', 10)

l1 = Line(-100,-100,-100,100)
l2 = Line(-100,100,0,150)
l3 = Line(0,150,100,100)
l4 = Line(100,100,100,-100)
l5 = Line(100,-100,-100,-100)

map = [l1, l2, l3, l4, l5]

vehicle = Vehicle()

lidar = Lidar()
iterator = lidar.iter_scans()
# First scan is crap, so ignore it
next(iterator)


if __name__ == '__main__':
    while True:
        next(iterator)
