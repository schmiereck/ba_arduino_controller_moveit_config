"""Launch MoveGroup + RViz for the real robot (no fake hardware).

Expects Ros2Bridge running on the Raspberry Pi (same ROS_DOMAIN_ID).
"""
from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import (
    generate_move_group_launch,
    generate_moveit_rviz_launch,
)


def generate_launch_description():
    moveit_config = (
        MoveItConfigsBuilder("bracket_arm", package_name="ba_arduino_controller_moveit_config")
        .to_moveit_configs()
    )

    ld = LaunchDescription()

    # MoveGroup (motion planning + trajectory execution)
    # We build the move_group node explicitly instead of using
    # generate_move_group_launch, so we can set publish_planning_scene
    # parameters. Without these, /monitored_planning_scene is never
    # published and RViz's <current> start state becomes stale after
    # trajectory execution — causing reversed trajectories on re-plans.
    move_group_params = [
        moveit_config.to_dict(),
        {
            "publish_robot_description_semantic": True,
            "allow_trajectory_execution": True,
            # Planning scene publishing — the fix for stale RViz state
            "publish_planning_scene": True,
            "publish_geometry_updates": True,
            "publish_state_updates": True,
            "publish_transforms_updates": True,
            "monitor_dynamics": False,
            # Periodic publishing rate (Hz) for /monitored_planning_scene.
            # PlanningSceneMonitor reads this with namespace prefix.
            "planning_scene_monitor.publish_planning_scene_hz": 4.0,
        },
    ]

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=move_group_params,
    )
    ld.add_action(move_group_node)

    # RViz with MotionPlanning plugin
    for entity in generate_moveit_rviz_launch(moveit_config).entities:
        ld.add_action(entity)

    return ld
