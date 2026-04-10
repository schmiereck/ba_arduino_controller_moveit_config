"""Launch MoveGroup + RViz for the real robot (no fake hardware).

Expects Ros2Bridge running on the Raspberry Pi (same ROS_DOMAIN_ID).
"""
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
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

    return LaunchDescription(
        [
            # MoveGroup (motion planning + trajectory execution)
            *generate_move_group_launch(moveit_config).entities,
            # RViz with MotionPlanning plugin
            *generate_moveit_rviz_launch(moveit_config).entities,
        ]
    )
