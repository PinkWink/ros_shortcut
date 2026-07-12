import threading
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

CART_JOINT = 'slider_joint'
POLE_JOINT = 'pole_joint'
BUFFER_LEN = 2000
DECIMATION = 10  # gazebo publishes at ~1 kHz; keep every 10th sample


class JointStatePlotter(Node):

    def __init__(self):
        super().__init__('joint_state_plotter')
        self.lock = threading.Lock()
        self.time = deque(maxlen=BUFFER_LEN)
        self.cart_pos = deque(maxlen=BUFFER_LEN)
        self.cart_vel = deque(maxlen=BUFFER_LEN)
        self.pole_pos = deque(maxlen=BUFFER_LEN)
        self.pole_vel = deque(maxlen=BUFFER_LEN)
        self.msg_count = 0

        self.create_subscription(
            JointState, 'joint_states', self.joint_state_callback, 10)

    def joint_state_callback(self, msg):
        if CART_JOINT not in msg.name or POLE_JOINT not in msg.name:
            return

        self.msg_count += 1
        if self.msg_count % DECIMATION != 0:
            return

        cart_idx = msg.name.index(CART_JOINT)
        pole_idx = msg.name.index(POLE_JOINT)
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

        with self.lock:
            self.time.append(stamp)
            self.cart_pos.append(msg.position[cart_idx])
            self.cart_vel.append(msg.velocity[cart_idx])
            self.pole_pos.append(msg.position[pole_idx])
            self.pole_vel.append(msg.velocity[pole_idx])

    def run_plot(self):
        fig, axes = plt.subplots(2, 2, figsize=(10, 6), sharex=True)
        fig.canvas.manager.set_window_title('Cart-Pole Joint States')

        titles = [
            ('Cart Position [m]', 'tab:blue'),
            ('Cart Velocity [m/s]', 'tab:cyan'),
            ('Pole Angle [rad]', 'tab:red'),
            ('Pole Angular Velocity [rad/s]', 'tab:orange'),
        ]
        lines = []
        for ax, (title, color) in zip(axes.flat, titles):
            line, = ax.plot([], [], color=color)
            ax.set_title(title)
            ax.grid(True)
            lines.append(line)
        for ax in axes[1]:
            ax.set_xlabel('sim time [s]')
        fig.tight_layout()

        def update(_frame):
            with self.lock:
                t = list(self.time)
                data = [list(self.cart_pos), list(self.cart_vel),
                        list(self.pole_pos), list(self.pole_vel)]

            if t:
                for line, values, ax in zip(lines, data, axes.flat):
                    line.set_data(t, values)
                    ax.relim()
                    ax.autoscale_view()
            return lines

        anim = FuncAnimation(fig, update, interval=100, cache_frame_data=False)  # noqa: F841
        plt.show()


def main():
    rclpy.init()
    node = JointStatePlotter()

    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    try:
        node.run_plot()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
