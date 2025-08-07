import pulp
import math
from utils.system import timer
from loguru import logger
from modules.const import AppData


@timer
@logger.catch(reraise=True)
def solve_layout(
    apps: list[AppData],
    weights: dict,
    rows: int,
    cols: int,
    dock_size: int,
    color_penalty_val: int = 0,
) -> tuple[dict[int, AppData | None] | None, str]:
    """
    与えられたアプリデータとパラメータで最適配置を計算する関数
    """
    num_main_locations = rows * cols
    locations = list(range(1, num_main_locations + dock_size + 1))
    location_coords = {}
    # Main grid
    for i in range(num_main_locations):
        row = i // cols
        col = i % cols
        location_coords[i + 1] = (row, col)
    # Dock
    for i in range(dock_size):
        location_coords[i + num_main_locations + 1] = (
            rows,
            i,
        )

    # 距離の計算
    distances = {}
    for i in locations:
        for k in locations:
            if i < k:
                (r1, c1) = location_coords[i]
                (r2, c2) = location_coords[k]
                dist = math.sqrt((r1 - r2) ** 2 + (c1 - c2) ** 2)
                distances[(i, k)] = dist if dist > 0 else 1e-9

    # --- PuLPモデルの構築 ---
    app_map = {app.name: app for app in apps}
    app_names = list(app_map.keys())
    app_usage = {app.name: app.usage for app in apps}
    app_color = {app.name: app.color for app in apps}

    prob = pulp.LpProblem("AppLayoutOptimization", pulp.LpMaximize)
    x = pulp.LpVariable.dicts("AppAtLocation", (app_names, locations), cat="Binary")

    # --- 目的関数 ---
    # 重みが定義されていないロケーションはデフォルト値1を割り当てる
    safe_weights = {loc: weights.get(loc, 1) for loc in locations}
    base_value = pulp.lpSum(
        safe_weights[i] * app_usage[j] * x[j][i] for j in app_names for i in locations
    )
    prob += base_value

    # 色のペナルティ
    if color_penalty_val > 0:
        app_indices = {name: i for i, name in enumerate(app_names)}
        pair_vars = pulp.LpVariable.dicts(
            "PairVar",
            (
                (i, k, j, l_app)
                for i in locations
                for k in locations
                if i < k
                for j in app_names
                for l_app in app_names
                if app_indices[j] < app_indices[l_app]
            ),
            cat="Binary",
        )

        for i in locations:
            for k in locations:
                if i < k:
                    for j in app_names:
                        for l_app in app_names:
                            if app_indices[j] < app_indices[l_app]:
                                idx = (i, k, j, l_app)
                                prob += pair_vars[idx] <= x[j][i]
                                prob += pair_vars[idx] <= x[l_app][k]
                                prob += pair_vars[idx] >= x[j][i] + x[l_app][k] - 1

        color_penalty = pulp.lpSum(
            color_penalty_val
            * (1 / distances.get((i, k), 1e-9))
            * pair_vars[(i, k, j, l_app)]
            for i, k, j, l_app in pair_vars
            if app_color.get(j) == app_color.get(l_app)
        )
        prob += -color_penalty

    # 制約条件
    # 各アプリは1つのロケーションにのみ配置
    for j in app_names:
        prob += pulp.lpSum(x[j][i] for i in locations) <= 1
    # 各ロケーションには最大1つ以下のアプリを配置
    for i in locations:
        prob += pulp.lpSum(x[j][i] for j in app_names) <= 1

    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[prob.status]
    if status != "Optimal":
        return None, status

    layout: dict[int, AppData | None] = {i: None for i in locations}
    for i in locations:
        for j in app_names:
            if pulp.value(x[j][i]) > 0.5:
                layout[i] = app_map[j]

    return layout, status
