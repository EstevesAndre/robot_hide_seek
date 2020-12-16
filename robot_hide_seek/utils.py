from math import atan2, pi, sqrt
from transformations import euler_from_quaternion

START_MSG = 'START'
GAMEOVER_MSG = 'GAMEOVER'
HIDER_LINEAR_SPEED = 0.25
SEEKER_LINEAR_SPEED = 0.2
SECONDS_HIDER_START = 0
SECONDS_SEEKER_START = 10
TURN_RATIO = 0.75
MIN_DISTANCE_TO_WALL = 0.35
SPEED_NEAR_WALL = 0.1
MIN_DISTANCE = 0.35
WEIGHT = 1
DISTANCE_ENDGAME = 0.3
GAME_TIME_LIMIT = 60
FOV_ANGLE = pi / 3
WALLS = [\
        [[-2.5, 2.5], [2.5, 2.5]], \
        [[-2.5, -2.5], [2.5, -2.5]], \
        [[2.5, -2.5], [2.5, 2.5]], \
        [[-2.5, -2.5], [-2.5, 2.5]], \
        [[1, 0.5], [1, 2.5]], \
        [[2, 0.5], [2, 1.5]], \
        [[1, 1.5], [2, 1.5]], \
        [[1, -0.5], [1, -2.5]], \
        [[2, -0.5], [2, -1.5]], \
        [[1, -1.5], [2, -1.5]], \
        [[-2, 0.5], [-1, 0.5]], \
        [[-2, -0.5], [-1, -0.5]], \
        [[-1, -0.5], [-1, 0.5]], \
        [[-2, -0.5], [-2, -0.5]] \
        ]
# LEFT WALL
# RIGHT WALL
# UP WALl
# DOWN WALL
# LEFT EYE
# LEFT EYE
# LEFT EYE
# RIGHT EYE
# RIGHT EYE
# RIGHT EYE
# LEFT MOUTH
# RIGHT MOUTH
# UP MOUTH
# DOWN MOUTH

def get_yaw(orientation_q):
    orientation_list = [orientation_q.x, orientation_q.y, orientation_q.z, orientation_q.w]
    (yaw, pitch, roll) = euler_from_quaternion(orientation_list)
    return yaw

def calc_angle_robots(r1_pos, r1_yaw, r2_pos):
    pos_angle = atan2(r2_pos[1] - r1_pos[1], r2_pos[0] - r1_pos[0])       
    
    if pos_angle < 0:
        pos_angle = pos_angle + (2 * pi)

    pos_angle = (pos_angle - r1_yaw) % (2 * pi)
    
    if pos_angle > pi:
        return pos_angle - (2 * pi)
    elif pos_angle < -pi:
        return pos_angle + (2 * pi)
    else:
        return pos_angle

def orientation(p, q, r):
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])

    return 1 if val > 0 else 2

def doIntersect(p1, q1, p2, q2):
    o1 = orientation(p1, q1, p2) 
    o2 = orientation(p1, q1, q2) 
    o3 = orientation(p2, q2, p1) 
    o4 = orientation(p2, q2, q1)
  
    return o1 != o2 and o3 != o4

def can_see(angle, pos1, pos2):
    if not -FOV_ANGLE <= angle <= FOV_ANGLE:
        return False

    for wall in WALLS:
        if doIntersect(pos1, pos2, wall[0], wall[1]):
            return False

    return True    