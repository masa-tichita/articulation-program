import pulp
import math
from utils.system import timer
from loguru import logger
from modules.const import AppData

# Define location coordinates (assuming 4 columns)
location_coords = {}
# Main grid: 6 rows, 4 columns
for i in range(24):
    row = i // 4
    col = i % 4
    location_coords[i + 1] = (row, col)
# Dock: 1 row, 4 columns, placed below the main grid
for i in range(4):
    location_coords[i + 25] = (6, i)

# Calculate distances
distances = {}
locations_list = list(range(1, 29))
for i in locations_list:
    for k in locations_list:
        if i < k:
            (r1, c1) = location_coords[i]
            (r2, c2) = location_coords[k]
            dist = math.sqrt((r1 - r2) ** 2 + (c1 - c2) ** 2)
            distances[(i, k)] = dist if dist > 0 else 1e-9 # Avoid division by zero


@timer
@logger.catch(reraise=True)
def solve_layout(apps: list[AppData], weights: dict, color_penalty_val: int = 0):
    """
    与えられたアプリデータとパラメータで最適配置を計算する関数
    """
    locations = list(range(1, 29))
    # PuLPモデルの構築
    # weights = {i: 1 for i in locations} # Uniform weights
    app_map = {app.name: app for app in apps}
    app_names = list(app_map.keys())
    app_usage = {app.name: app.usage for app in apps}
    app_color = {app.name: app.color for app in apps}

    prob = pulp.LpProblem("AppLayoutOptimization", pulp.LpMaximize)
    x = pulp.LpVariable.dicts("AppAtLocation", (app_names, locations), cat="Binary")

    # --- 目的関数 ---
    base_value = pulp.lpSum(
        weights[i] * app_usage[j] * x[j][i] for j in app_names for i in locations
    )
    prob += base_value

    # --- 色のペナルティ ---
    if color_penalty_val > 0:
        app_indices = {name: i for i, name in enumerate(app_names)}
        pair_vars = pulp.LpVariable.dicts(
            "PairVar",
            (
                (i, k, j, l)
                for i in locations for k in locations if i < k
                for j in app_names for l in app_names if app_indices[j] < app_indices[l]
            ),
            cat="Binary",
        )

        for i in locations:
            for k in locations:
                if i < k:
                    for j in app_names:
                        for l in app_names:
                            if app_indices[j] < app_indices[l]:
                                idx = (i, k, j, l)
                                prob += pair_vars[idx] <= x[j][i]
                                prob += pair_vars[idx] <= x[l][k]
                                prob += pair_vars[idx] >= x[j][i] + x[l][k] - 1

        color_penalty = pulp.lpSum(
            color_penalty_val * (1 / distances.get((i, k), 1e-9)) * pair_vars[(i, k, j, l)]
            for i, k, j, l in pair_vars
            if app_color.get(j) == app_color.get(l)
        )
        prob += -color_penalty

    # --- 制約条件 ---
    for j in app_names:
        prob += pulp.lpSum(x[j][i] for i in locations) == 1
    for i in locations:
        prob += pulp.lpSum(x[j][i] for j in app_names) <= 1

    prob.solve()
    status = pulp.LpStatus[prob.status]
    if status != "Optimal":
        return None, status

    layout = {i: None for i in locations}
    for i in locations:
        for j in app_names:
            if pulp.value(x[j][i]) > 0.5:
                layout[i] = app_map[j]

    return layout, status
