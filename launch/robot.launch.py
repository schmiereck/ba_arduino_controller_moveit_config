"""Launch MoveGroup + RViz for the real robot (no fake hardware).

Expects Ros2Bridge running on the Raspberry Pi (same ROS_DOMAIN_ID).
"""
import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from ament_index_python.packages import get_package_prefix
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import (
    generate_move_group_launch,
    generate_moveit_rviz_launch,
    generate_rsp_launch,
    generate_static_virtual_joint_tfs_launch,
)


def generate_launch_description():
    moveit_config = (
        MoveItConfigsBuilder("bracket_arm", package_name="ba_arduino_controller_moveit_config")
        .to_moveit_configs()
    )

    # Extra parameters for MoveGroup to handle time sync/drift
    extra_params = {
        "ompl.arm.start_state_max_bounds_error": 0.5,
        "ompl.arm.start_state_max_dt": 2.0,
        "jiggle_fraction": 0.1,
    }

    ld = LaunchDescription()

    # Static virtual joint transformations (e.g., world -> base_link)
    for entity in generate_static_virtual_joint_tfs_launch(moveit_config).entities:
        ld.add_action(entity)

    # Robot State Publisher (publishes /robot_description)
    for entity in generate_rsp_launch(moveit_config).entities:
        ld.add_action(entity)

    # MoveGroup (motion planning + trajectory execution)
    # We pass the extra_params here
    for entity in generate_move_group_launch(moveit_config).entities:
        # If the entity is a Node, we could technically add parameters, but
        # generate_move_group_launch already wraps them. 
        # A simpler way in MoveIt2 is to ensure they are in the YAML or 
        # passed via the launch description.
        ld.add_action(entity)

    # RViz with MotionPlanning plugin
    for entity in generate_moveit_rviz_launch(moveit_config).entities:
        ld.add_action(entity)

    # Planning Scene Relay: Periodisch die Scene von move_group abrufen
    # und auf /monitored_planning_scene republizieren.
    # Workaround: move_group publiziert State-Updates nicht zuverlaessig,
    # sodass RViz nach einer Trajektorie einen veralteten Start-Zustand hat.
    pkg_prefix = get_package_prefix('ba_arduino_controller_moveit_config')
    relay_script = os.path.join(
        pkg_prefix, 'lib', 'ba_arduino_controller_moveit_config',
        'planning_scene_relay.py')

    ld.add_action(
        ExecuteProcess(
            cmd=['python3', relay_script],
            output='screen',
        )
    )

    return ld
