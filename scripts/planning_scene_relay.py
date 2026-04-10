#!/usr/bin/env python3
"""Periodisch die Planning Scene von move_group abrufen und auf
/monitored_planning_scene republizieren.

Workaround: move_group publiziert /monitored_planning_scene nicht bei
State-Updates von /joint_states, daher hat RViz nach einer Trajektorie
einen veralteten <current>-Zustand.
"""
import rclpy
from rclpy.node import Node
from moveit_msgs.srv import GetPlanningScene
from moveit_msgs.msg import PlanningScene, PlanningSceneComponents


class PlanningSceneRelay(Node):
    def __init__(self):
        super().__init__('planning_scene_relay')
        self.cli = self.create_client(GetPlanningScene, '/get_planning_scene')
        self.pub = self.create_publisher(PlanningScene, '/monitored_planning_scene', 10)
        # 2 Hz reicht, damit RViz den aktuellen Zustand bekommt
        self.timer = self.create_timer(0.5, self.poll)
        self.get_logger().info('Planning Scene Relay gestartet (2 Hz)')

    def poll(self):
        if not self.cli.service_is_ready():
            return
        req = GetPlanningScene.Request()
        req.components.components = (
            PlanningSceneComponents.ROBOT_STATE
            | PlanningSceneComponents.WORLD_OBJECT_NAMES
            | PlanningSceneComponents.WORLD_OBJECT_GEOMETRY
            | PlanningSceneComponents.ROBOT_STATE_ATTACHED_OBJECTS
            | PlanningSceneComponents.TRANSFORMS
            | PlanningSceneComponents.ALLOWED_COLLISION_MATRIX
            | PlanningSceneComponents.LINK_PADDING_AND_SCALING
            | PlanningSceneComponents.OBJECT_COLORS
        )
        future = self.cli.call_async(req)
        future.add_done_callback(self.on_response)

    def on_response(self, future):
        try:
            result = future.result()
            if result:
                self.pub.publish(result.scene)
        except Exception as e:
            self.get_logger().warn(f'get_planning_scene fehlgeschlagen: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = PlanningSceneRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
