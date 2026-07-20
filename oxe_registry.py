"""
Open X-Embodiment 数据集登记表（跨源深化）
=============================================

数据来自 OXE 官方发布的数据集配置（octo 仓库 oxe_dataset_configs.py，
Apache-2.0，事实数据、非 AI 编造）。每个 OXE 数据集记录：
  - 相机键（primary/secondary/wrist RGB）
  - 深度键（是否含 depth）
  - proprio 本体状态编码（POS_EULER / POS_QUAT / JOINT / JOINT_BIMANUAL / POS_NAV / NONE）
  - action 动作编码（EEF_POS / JOINT_POS / JOINT_POS_BIMANUAL / NAV_2D / ...）

由这些**可靠地推导**出：模态、本体类型、相机数、自由度、action_convention。
这样 OXE（GCS 上的 RLDS，非 HF）就能被归一化到和 HF 数据集一样的 schema。

每条格式：name -> (cam_keys[list], has_depth[bool], proprio, action)
proprio/action 用字符串枚举名。
"""

# ---------------- 原始登记表（转自 OXE 官方配置）----------------
OXE = {
    "fractal20220817_data": (["image"], False, "POS_QUAT", "EEF_POS"),
    "kuka": (["image"], False, "POS_QUAT", "EEF_POS"),
    "bridge_dataset": (["image_0", "image_1"], False, "POS_EULER", "EEF_POS"),
    "taco_play": (["rgb_static", "rgb_gripper"], True, "POS_EULER", "EEF_POS"),
    "jaco_play": (["image", "image_wrist"], False, "POS_EULER", "EEF_POS"),
    "berkeley_cable_routing": (["image", "top_image", "wrist45_image"], False, "JOINT", "EEF_POS"),
    "roboturk": (["front_rgb"], False, "NONE", "EEF_POS"),
    "nyu_door_opening_surprising_effectiveness": (["image"], False, "NONE", "EEF_POS"),
    "viola": (["agentview_rgb", "eye_in_hand_rgb"], False, "JOINT", "EEF_POS"),
    "berkeley_autolab_ur5": (["image", "hand_image"], True, "POS_QUAT", "EEF_POS"),
    "toto": (["image"], False, "JOINT", "EEF_POS"),
    "language_table": (["rgb"], False, "POS_EULER", "EEF_POS"),
    "columbia_cairlab_pusht_real": (["image", "wrist_image"], False, "POS_EULER", "EEF_POS"),
    "stanford_kuka_multimodal_dataset_converted_externally_to_rlds": (["image"], True, "POS_QUAT", "EEF_POS"),
    "nyu_rot_dataset_converted_externally_to_rlds": (["image"], False, "POS_EULER", "EEF_POS"),
    "stanford_hydra_dataset_converted_externally_to_rlds": (["image", "wrist_image"], False, "POS_EULER", "EEF_POS"),
    "austin_buds_dataset_converted_externally_to_rlds": (["image", "wrist_image"], False, "JOINT", "EEF_POS"),
    "nyu_franka_play_dataset_converted_externally_to_rlds": (["image", "image_additional_view"], True, "POS_EULER", "EEF_POS"),
    "maniskill_dataset_converted_externally_to_rlds": (["image", "wrist_image"], True, "POS_QUAT", "EEF_POS"),
    "furniture_bench_dataset_converted_externally_to_rlds": (["image", "wrist_image"], False, "POS_QUAT", "EEF_POS"),
    "cmu_franka_exploration_dataset_converted_externally_to_rlds": (["highres_image"], False, "NONE", "EEF_POS"),
    "ucsd_kitchen_dataset_converted_externally_to_rlds": (["image"], False, "JOINT", "EEF_POS"),
    "ucsd_pick_and_place_dataset_converted_externally_to_rlds": (["image"], False, "POS_EULER", "EEF_POS"),
    "austin_sailor_dataset_converted_externally_to_rlds": (["image", "wrist_image"], False, "POS_QUAT", "EEF_POS"),
    "austin_sirius_dataset_converted_externally_to_rlds": (["image", "wrist_image"], False, "POS_QUAT", "EEF_POS"),
    "bc_z": (["image"], False, "POS_EULER", "EEF_POS"),
    "utokyo_pr2_opening_fridge_converted_externally_to_rlds": (["image"], False, "POS_EULER", "EEF_POS"),
    "utokyo_pr2_tabletop_manipulation_converted_externally_to_rlds": (["image"], False, "POS_EULER", "EEF_POS"),
    "utokyo_xarm_pick_and_place_converted_externally_to_rlds": (["image", "image2", "hand_image"], False, "POS_EULER", "EEF_POS"),
    "utokyo_xarm_bimanual_converted_externally_to_rlds": (["image"], False, "POS_EULER", "EEF_POS"),
    "robo_net": (["image", "image1"], False, "POS_EULER", "EEF_POS"),
    "berkeley_mvp_converted_externally_to_rlds": (["hand_image"], False, "POS_QUAT", "JOINT_POS"),
    "berkeley_rpt_converted_externally_to_rlds": (["hand_image"], False, "JOINT", "JOINT_POS"),
    "kaist_nonprehensile_converted_externally_to_rlds": (["image"], False, "POS_QUAT", "EEF_POS"),
    "stanford_mask_vit_converted_externally_to_rlds": (["image"], False, "POS_EULER", "EEF_POS"),
    "tokyo_u_lsmo_converted_externally_to_rlds": (["image"], False, "POS_EULER", "EEF_POS"),
    "dlr_sara_pour_converted_externally_to_rlds": (["image"], False, "POS_EULER", "EEF_POS"),
    "dlr_sara_grid_clamp_converted_externally_to_rlds": (["image"], False, "POS_EULER", "EEF_POS"),
    "dlr_edan_shared_control_converted_externally_to_rlds": (["image"], False, "POS_EULER", "EEF_POS"),
    "asu_table_top_converted_externally_to_rlds": (["image"], False, "POS_EULER", "EEF_POS"),
    "stanford_robocook_converted_externally_to_rlds": (["image_1", "image_2"], True, "POS_EULER", "EEF_POS"),
    "imperialcollege_sawyer_wrist_cam": (["image", "wrist_image"], False, "NONE", "EEF_POS"),
    "iamlab_cmu_pickup_insert_converted_externally_to_rlds": (["image", "wrist_image"], False, "JOINT", "EEF_POS"),
    "uiuc_d3field": (["image_1", "image_2"], True, "NONE", "EEF_POS"),
    "utaustin_mutex": (["image", "wrist_image"], False, "JOINT", "EEF_POS"),
    "berkeley_fanuc_manipulation": (["image", "wrist_image"], False, "JOINT", "EEF_POS"),
    "cmu_playing_with_food": (["image", "finger_vision_1"], False, "POS_EULER", "EEF_POS"),
    "cmu_play_fusion": (["image"], False, "JOINT", "EEF_POS"),
    "cmu_stretch": (["image"], False, "POS_EULER", "EEF_POS"),
    "gnm_dataset": (["image"], False, "POS_NAV", "NAV_2D"),
    "aloha_static_dataset": (["cam_high", "cam_low", "cam_right_wrist"], False, "JOINT_BIMANUAL", "JOINT_POS_BIMANUAL"),
    "aloha_dagger_dataset": (["cam_high", "cam_low", "cam_right_wrist"], False, "JOINT_BIMANUAL", "JOINT_POS_BIMANUAL"),
    "aloha_mobile_dataset": (["cam_high", "cam_right_wrist"], False, "JOINT_BIMANUAL", "JOINT_POS_BIMANUAL_NAV"),
    "fmb_dataset": (["image_side_1", "image_side_2", "image_wrist_1"], True, "POS_EULER", "EEF_POS"),
    "dobbe": (["wrist_image"], False, "POS_EULER", "EEF_POS"),
    "roboset": (["image_left", "image_right", "image_wrist"], False, "JOINT", "JOINT_POS"),
    "rh20t": (["image_front", "image_side_right", "image_wrist"], False, "POS_EULER", "EEF_POS"),
    "mujoco_manip": (["image"], False, "POS_EULER", "EEF_POS"),
}

# 已知含自然语言指令的数据集（保守：只标确定的）
_HAS_LANGUAGE = {"language_table", "bc_z", "fractal20220817_data", "taco_play"}

# 已知为仿真的数据集（其余无信号者标 unknown，不假装 teleop）
_SIMULATION = {"mujoco_manip", "maniskill_dataset_converted_externally_to_rlds"}

# 动作编码 -> (action_convention, 自由度粗估)
_ACTION_SPEC = {
    "EEF_POS":              ({"space": "cartesian", "abs_or_delta": "delta", "gripper": True}, 7),
    "JOINT_POS":            ({"space": "joint", "abs_or_delta": "delta", "gripper": True}, 8),
    "JOINT_POS_BIMANUAL":   ({"space": "joint", "arms": 2, "gripper": True}, 14),
    "NAV_2D":               ({"space": "navigation_2d", "abs_or_delta": "delta"}, 2),
    "JOINT_POS_BIMANUAL_NAV": ({"space": "joint+base", "arms": 2, "gripper": True}, 16),
}


def has(name: str) -> bool:
    return name in OXE


def cameras(name: str):
    return list(OXE[name][0]) if name in OXE else []


def modalities(name: str):
    if name not in OXE:
        return []
    cams, depth, proprio, _ = OXE[name]
    mods = ["rgb"] if cams else []
    if depth:
        mods.append("depth")
    if proprio and proprio != "NONE":
        mods.append("state")
    if name in _HAS_LANGUAGE:
        mods.append("language")
    return mods


def embodiment(name: str) -> str:
    if name not in OXE:
        return ""
    _, _, proprio, action = OXE[name]
    if "BIMANUAL" in action or "bimanual" in name or "aloha" in name:
        return "bimanual"
    if action == "NAV_2D" or proprio == "POS_NAV" or "mobile" in name or name == "gnm_dataset":
        return "mobile"
    return "single_arm"


def action_convention(name: str):
    if name not in OXE:
        return {}, 0
    action = OXE[name][3]
    conv, dof = _ACTION_SPEC.get(action, ({}, 0))
    return dict(conv), dof


def provenance(name: str) -> str:
    return "simulation" if name in _SIMULATION else "unknown"


def all_names():
    return list(OXE.keys())
