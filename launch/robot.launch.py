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
        .robot_description(file_path="config/bracket_arm.urdf.xacro")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .planning_pipelines(pipelines=["ompl", "pilz_industrial_motion_planner", "chomp"])
        # Inject tolerances for WSL2/Pi clock drift
        .planning_scene_monitor(
            publish_planning_scene=True,
            publish_geometry_updates=True,
            publish_state_updates=True,
            publish_transforms_updates=True,
        )
        .to_moveit_configs()
    )

    # Set parameters for OMPL tolerance
    moveit_config.planning_pipelines["ompl"]["arm"].update({
        "start_state_max_bounds_error": 0.5,
        "start_state_max_dt": 2.0,
    })

    ld = LaunchDescription()

    # Static virtual joint transformations (e.g., world -> base_link)
    for entity in generate_static_virtual_joint_tfs_launch(moveit_config).entities:
        ld.add_action(entity)

    # Robot State Publisher (publishes /robot_description)
    for entity in generate_rsp_launch(moveit_config).entities:
        ld.add_action(entity)

    # MoveGroup (motion planning + trajectory execution)
    move_group_node = generate_move_group_launch(moveit_config).entities[0] # Usually the Node
    # We add custom parameters to handle the WSL2/Pi time sync issues
    move_group_params = [
        {'ompl.start_state_max_bounds_error': 0.5}, # High tolerance for start state deviation
        {'ompl.start_state_max_dt': 2.0},           # 2s instead of 0.5s for time drift
        {'jiggle_fraction': 0.1},
    ]

    for entity in generate_move_group_launch(moveit_config).entities:
        # If it's a Node, we can append parameters. Since these are launch entities, 
        # it's cleaner to just add them via the builder or as a separate action.
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
