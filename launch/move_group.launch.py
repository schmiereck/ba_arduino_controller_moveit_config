from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_move_group_launch


def generate_launch_description():
    moveit_config = (
        MoveItConfigsBuilder("bracket_arm", package_name="ba_arduino_controller_moveit_config")
        .trajectory_execution(file_path="config/trajectory_execution.yaml")
        .to_moveit_configs()
    )
    return generate_move_group_launch(moveit_config)
