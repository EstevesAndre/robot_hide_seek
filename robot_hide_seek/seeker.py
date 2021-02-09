from math import radians, degrees, isinf, pi, inf

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from std_msgs.msg import String
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist

from robot_hide_seek.utils import *
from robot_hide_seek import deepqlearn

class Seeker(Node):
    follow_id = inf
    follow_distance = inf
    follow_angle = inf
    angles = []
    distances = []
    time = -1
    gameover = True
    
    def __init__(self, id=None):
        if id==None:
            super().__init__('seeker')
            self.declare_parameter('id')
            id = self.get_parameter('id').value

        else:
            super().__init__('seeker_' + str(id))

        self.node_topic = '/seeker_' + str(id)

        self.game_sub = self.create_subscription(
            String,
            self.node_topic + '/game',
            self.game_callback,
            10
        )
        self.seeker_coord_sub = self.create_subscription(
            String,
            '/seekers',
            self.coord_callback,
            10
        )
        self.seeker_coord_pub = self.create_publisher(
            String,
            '/seekers',
            10
        )
        self.clock_sub = self.create_subscription(
            Clock, 
            '/clock', 
            self.clock_callback,
            10
        )
        self.vel_pub = self.create_publisher(
            Twist,
            self.node_topic + '/cmd_vel',
            10
        )
        self.lidar_sub = self.create_subscription(
            LaserScan, 
            self.node_topic + '/scan', 
            self.lidar_callback,
            qos_profile_sensor_data
        )

        if GAME_USES_TRAINING:
            self.deepQ = deepqlearn.DeepQ(11, 5, save_path='./training_results/seeker')
            self.deepQ.initPlay()

    def reset(self):
        self.follow_id = inf
        self.follow_distance = inf
        self.follow_angle = inf
        self.angles = []
        self.distances = []

    def clock_callback(self, msg):
        if int(msg.clock.sec) < self.time:
            self.gameover = False
            self.reset()

        self.time = int(msg.clock.sec)

    def game_callback(self, msg):
        if msg.data == START_MSG:
            return

        elif msg.data == GAMEOVER_MSG:
            self.endgame()

        message = msg.data.rstrip().split('\n\n')

        if message[0] == POSITIONS_MSG_HEADER:
            self.angles = [float(pos.split('\n')[0][7:]) for pos in message[1:]]
            self.distances = [float(pos.split('\n')[1][10:]) for pos in message[1:]]

            if self.seeker_coord_pub:
                self.share_distances()

    def share_distances(self):
        msg = String()

        for dist in self.distances:
            msg.data += str(dist) + '\n'

        self.seeker_coord_pub.publish(msg)

    def coord_callback(self, msg):
        if self.time < SECONDS_SEEKER_START:
            return
        other_distances = msg.data.rstrip().split('\n')

        if len(other_distances) > len(self.distances):
            return
        
        min_difference = (inf, inf)

        for i, distance in enumerate(other_distances):
            diff = self.distances[i] - float(distance)

            if diff < min_difference[1]:
                min_difference = (i, diff)

        if not isinf(min_difference[0]):
            self.follow_id = min_difference[0]
            self.follow_angle = self.angles[min_difference[0]]
            self.follow_distance = self.distances[min_difference[0]]

    def lidar_callback(self, msg):
        if self.time < SECONDS_SEEKER_START or self.gameover:
            return

        if GAME_USES_TRAINING:
            observation = [msg.ranges[0], msg.ranges[45], msg.ranges[90], msg.ranges[135], msg.ranges[180], msg.ranges[225], msg.ranges[270], msg.ranges[315]]

            observation.append(self.follow_angle)
            observation.append(self.follow_distance)
            observation.append(self.time)

            action = self.deepQ.predict(observation)
            vel = Twist()

            if action == 0: #Forward
                vel.linear.x = SEEKER_LINEAR_SPEED
                vel.angular.z = 0.0
            elif action == 1: #Rotate left
                vel.linear.x = 0.0
                vel.angular.z = ROBOT_ANGULAR_SPEED
            elif action == 2: #Rotate right
                vel.linear.x = 0.0
                vel.angular.z = -ROBOT_ANGULAR_SPEED
            elif action == 3: #Stop
                vel.linear.x = 0.0
                vel.angular.z = 0.0
            elif action == 4: #Back
                vel.linear.x = -SEEKER_LINEAR_SPEED
                vel.angular.z = 0.0
            
            self.vel_pub.publish(vel)

            return

        min_range = msg.ranges[0]
        min_angle = msg.angle_min

        for i in range(1, len(msg.ranges)):
            angle = degrees(msg.angle_min + (i* msg.angle_increment))

            if msg.ranges[i] < min_range:
                min_range = msg.ranges[i]
                min_angle = radians(angle)

        if isinf(min_range):
            return

        vel = Twist()
        vel.linear.x = SEEKER_LINEAR_SPEED

        #Temporary
        if min_range <= MIN_DISTANCE_TO_WALL:
            if min_angle < 5 * pi / 8:
                if min_angle < pi / 8:
                    vel.linear.x = -SPEED_NEAR_WALL
                elif min_angle < 3 * pi / 8:
                    vel.linear.x = SPEED_NEAR_WALL

                if not isinf(self.follow_angle):
                    if self.follow_angle >= 0:
                        min_angle -= 5 * pi / 8
                    else:
                        min_angle += 5 * pi / 8

            elif min_angle > 11 * pi / 8:
                if min_angle > 15 * pi / 8:
                    vel.linear.x = -SPEED_NEAR_WALL
                elif min_angle > 13 * pi / 8:
                    vel.linear.x = SPEED_NEAR_WALL
                min_angle -= 11 * pi / 8

                if not isinf(self.follow_angle):
                    if self.follow_angle >= 0:
                        min_angle -= 11 * pi / 8
                    else:
                        min_angle += 11 * pi / 8
        else:
            if not isinf(self.follow_angle):
                min_angle = self.follow_angle / TURN_RATIO

        vel.angular.z = min_angle * TURN_RATIO

        self.vel_pub.publish(vel)

    def endgame(self):
        self.gameover = True
        self.vel_pub.publish(Twist())

def main(args=None):
    rclpy.init(args=args)

    seeker = Seeker()

    rclpy.spin(seeker)

    seeker.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
