import numpy as np
import config
import sys
import math
import time
import numba

headless = config.headless
if not headless:
    import pygame


class Line:
    def __init__(self, x0, y0, x1, y1) -> None:
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1


    def point_at_t(self, t):
        return point_at_t_numba(self.x0, self.y0, self.x1, self.y1, t)

    def points_get(self):
        return self.x0, self.y0, self.x1, self.y1

@numba.njit
def point_at_t_numba(x0, y0, x1, y1, t):
    x = x0 + t*(x1 - x0)
    y = y0 + t*(y1 - y0)
    return x, y

def draw_line(l:Line):
    p0 = pos_to_pix(l.x0, l.y0)
    p1 = pos_to_pix(l.x1, l.y1)
    pygame.draw.line(screen, BLACK, p0, p1)

class Vehicle:
    def __init__(self) -> None:
        self.x = config.vehicle_x0_px * config.sim_scale
        self.y = config.vehicle_y0_px * config.sim_scale
        self.v = config.vehicle_v0_px # cm/s * config.sim_scale
        self.theta = config.vehicle_theta0_deg * config.sim_scale# deg
        self.omega = config.vehcile_omega0_deg * config.sim_scale#deg/s
        self.size = config.vehicle_size_px * config.sim_scale
        self.enc_left = 0
        self.enc_right = 0
        self.t_update_prev = time.time()

    def draw(self):
        size = (300, 300)
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

        enc_per_cm = config.vehicle_enc_per_rot / (config.vehicle_wheel_r_cm*2*math.pi)
        # This is pretty bad. It doesn't account for rotation of the robot 
        self.enc_left += enc_per_cm*self.v
        self.enc_right += enc_per_cm*self.v

    def enc_get(self):
        return int(self.enc_right), int(self.enc_left)

class Lidar:
    def __init__(self) -> None:
        self.scan_n = config.lidar_scan_n
        self.scan_res = {} # Dict with ang as keys and d and line  as values
        self.scan_d_cm = config.lidar_scan_d_cm * config.sim_scale
        self.t_start = time.time()
        self.n = 0

    @staticmethod
    @numba.njit
    def scan_numba(scan_n, theta, vehicle_x, vehicle_y, scan_d_cm, map_lines):
        scan_res = {}
        for ang in np.linspace(0, 360, scan_n):
            x = vehicle_x + np.cos(np.deg2rad(ang + theta))*scan_d_cm
            y = vehicle_y + np.sin(np.deg2rad(ang + theta))*scan_d_cm
            l = vehicle_x, vehicle_y, x, y
            for map_l in map_lines:
                t1, t2 = intersection_numba(vehicle_x, vehicle_y, x, y, map_l[0], map_l[1], map_l[2], map_l[3])

                if t1 <= 1 and t1 >= 0 and t2 <= 1 and t2 >= 0:
                    p = point_at_t_numba(vehicle_x, vehicle_y, x, y, t1)
                    d = ((p[0] - vehicle_x)**2 + (p[1] - vehicle_y)**2)**0.5
                else:
                    p = None
                    d = None

                if ang not in scan_res:
                    scan_res[ang] = (d, l, p)
                else:
                    if d is not None :
                        if ang in scan_res:
                            d0,_,_ = scan_res[ang]
                            if d0 is None  or d < d0:
                                scan_res[ang] = (d, l, p)
                        else:
                            scan_res[ang] = (d, l, p)

        return scan_res


    def scan(self):
        self.scan_res = self.scan_numba(self.scan_n, vehicle.theta, vehicle.x, vehicle.y, self.scan_d_cm, map_points)

    def iter_scans(self):
        return self

    def __next__(self):
        self.n+=1
        if self.n%60 == 0:
            print(f"simulator frequency: {self.n/(time.time() - self.t_start)} hz")
            self.t_start = time.time()
            self.n = 0

        
        self.scan()
        if not headless:
            screen.fill(WHITE)
            self.draw()

            vehicle.draw()

            for l in map_lines:
                draw_line(l)
        
            draw_map_intersections()

            pygame.display.update()
            for events in pygame.event.get():
                if events.type == pygame.QUIT:
                    sys.exit(0)
                elif events.type == pygame.KEYDOWN:
                    if events.dict['unicode'] == 'w':
                        vehicle.v = 1 * config.sim_scale
                    elif events.dict['unicode'] == 'a':
                        vehicle.omega = 2 * config.sim_scale
                    elif events.dict['unicode'] == 'd':
                        vehicle.omega = -2 * config.sim_scale
                    elif events.dict['unicode'] == 's':
                        vehicle.v = -1 * config.sim_scale
                    elif events.dict['unicode'] == '\x1b': # esc
                        exit(0)
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
            if d is not None:
                res.append((1, ang, d*10 / config.sim_scale))  
        
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
    xa0 = l1.x0
    ya0 = l1.y0
    xa1 = l1.x1
    ya1 = l1.y1

    xb0 = l2.x0
    yb0 = l2.y0
    xb1 = l2.x1
    yb1 = l2.y1

    return intersection_numba(xa0, ya0, xa1, ya1, xb0, yb0, xb1, yb1)

@numba.njit
def intersection_numba(xa0, ya0, xa1, ya1, xb0, yb0, xb1, yb1):
    xa0 = np.round(xa0, 9)
    ya0 = np.round(ya0, 9)
    xa1 = np.round(xa1, 9)
    ya1 = np.round(ya1, 9)

    xb0 = np.round(xb0, 9)
    yb0 = np.round(yb0, 9)
    xb1 = np.round(xb1, 9)
    yb1 = np.round(yb1, 9)

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


def draw_circle(x, y, text=False):
    p = pos_to_pix(x, y)
    pygame.draw.circle(screen, RED, p, radius=config.intersection_size_r)
    if text:
        text_surface = my_font.render(f'{(x,y)}', False, BLACK)
        screen.blit(text_surface, p)

def pos_to_pix(x, y):
    x += width/2
    y = height - y - 1
    y -= height/2
    return x, y

def draw_map_intersections():
    for i in range(len(map_lines)):
        l1, l2 = map_lines[i], map_lines[(1+i)%len(map_lines)]
        t1, t2 = intersection(l1, l2)

        if t1 <=1  and t1 >= 0:
            p = l1.point_at_t(t1)
        elif t2 <=1  and t2 >= 0:
            p = l2.point_at_t(t2)
        else:
            continue

        draw_circle(*p, text=False)



if not headless:
    width, height = (config.width, config.height)
    WHITE = (0,0,0)
    BLACK = (255,255,255)
    RED = (255, 0 ,0)
    BLUE = (0, 0, 255)
    GREEN = (0, 255, 0)

    screen = pygame.display.set_mode((width,height))
    pygame.font.init()
    my_font = pygame.font.SysFont('Comic Sans MS', 10)

def lines_from_points(points):
    lines = []
    for i in range(len(points)-1):
        p0 = points[i]
        p1 = points[i+1]
        lines.append(Line(*p0, *p1))

    return lines

def scale_points(points , dp, scale):
    return (points - dp) * scale


points1 = ((0,0), 
                    (0, 4.1),
                    (2.1, 4.1),
                    (2.1, 5.2),
                    (2.1, 4.1),
                    (0, 4.1),
                    (0, 7),
                    (2.1, 7),
                    (2.1, 6.2),
                    (2.3, 10),
                    (3.8 , 10),
                    (4, 7),
                    (11.1, 7),
                    (11.1, 1.8),
                    (8.1, 1.8),
                    (11.1, 1.8),
                    (11.1, -2.6),
                    (8.1, -2.6),
                    (8.1, 1),
                    (8.1, -2.6),
                    (5.9, -2.6),
                    (5.9, 0.4),
                    (5.2, 0.4),
                    (5.2, 0),
                    (3.5, 0),
                    (3.5, 3.3),
                    (4.4, 3.3),
                    (3, 3.3),
                    (3.5, 3.3),
                    (3.5, 0),
                    (2.2, 0),
                    (2.2, 3.3),
                    (2.1, 3.3),
                    (2.1, 0),
                    (0,0),
)
points1 = scale_points(np.array(points1), np.array([3,3]), 100*config.sim_scale)

points2 = ((5.2, 3.3),
            (6.2, 3.3),
            (5.9, 1.3),
            (5.2, 1.3),
            (5.2, 3.3),
)
points2 = scale_points(np.array(points2), np.array([3,3]), 100*config.sim_scale)

lines1 = lines_from_points(points1)
lines2 = lines_from_points(points2)
map_lines = lines1 + lines2
map_points = np.array([line.points_get() for line in map_lines])


vehicle = Vehicle()

lidar = Lidar()
iterator = lidar.iter_scans()


if __name__ == '__main__':
    while True:
        next(iterator)
