import pulp

from utils.system import timer
from loguru import logger


@timer
@logger.catch(reraise=True)
def solve_layout(apps_data, folder_penalty_val):
    """
    与えられたアプリデータとパラメータで最適配置を計算する関数
    """
    locations = list(range(1, 29))
    weights = {
        1: 50,
        2: 55,
        3: 55,
        4: 50,
        5: 45,
        6: 45,
        7: 45,
        8: 45,
        9: 35,
        10: 25,
        11: 25,
        12: 35,
        13: 25,
        14: 60,
        15: 60,
        16: 25,
        17: 25,
        18: 60,
        19: 60,
        20: 25,
        21: 35,
        22: 25,
        23: 25,
        24: 35,
        25: 45,
        26: 40,
        27: 40,
        28: 45,
    }
    apps = list(apps_data.keys())
    app_usage = {j: data["usage"] for j, data in apps_data.items()}
    app_genre = {j: data["genre"] for j, data in apps_data.items()}
    folders = list(set(app_genre.values()))
    folder_capacity = 9
    M = len(apps)

    # PuLPモデルの構築
    prob = pulp.LpProblem("AppLayoutOptimization", pulp.LpMaximize)
    x = pulp.LpVariable.dicts("AppAtLocation", (apps, locations), cat="Binary")
    y = pulp.LpVariable.dicts("FolderAtLocation", (folders, locations), cat="Binary")
    z = pulp.LpVariable.dicts("AppInFolder", (apps, folders), cat="Binary")
    q = pulp.LpVariable.dicts("AuxiliaryVar", (apps, folders, locations), cat="Binary")

    direct_placement_value = pulp.lpSum(
        weights[i] * app_usage[j] * x[j][i] for j in apps for i in locations
    )
    folder_placement_value = pulp.lpSum(
        (weights[i] - folder_penalty_val) * app_usage[j] * q[j][f][i]
        for j in apps
        for f in folders
        for i in locations
    )
    prob += direct_placement_value + folder_placement_value

    # --- 制約条件 ---
    for j in apps:
        prob += (
            pulp.lpSum(x[j][i] for i in locations)
            + pulp.lpSum(z[j][f] for f in folders)
            == 1
        )
    for i in locations:
        prob += (
            pulp.lpSum(x[j][i] for j in apps) + pulp.lpSum(y[f][i] for f in folders)
            <= 1
        )
    for f in folders:
        prob += pulp.lpSum(z[j][f] for j in apps) <= M * pulp.lpSum(
            y[f][i] for i in locations
        )
        prob += pulp.lpSum(z[j][f] for j in apps) <= folder_capacity
        prob += pulp.lpSum(y[f][i] for i in locations) <= 1
        prob += pulp.lpSum(y[f][i] for i in locations) <= pulp.lpSum(
            z[j][f] for j in apps
        )
    for j in apps:
        for f in folders:
            if app_genre[j] != f:
                prob += z[j][f] == 0
    for j in apps:
        for f in folders:
            for i in locations:
                prob += q[j][f][i] <= y[f][i]
                prob += q[j][f][i] <= z[j][f]
                prob += q[j][f][i] >= y[f][i] + z[j][f] - 1
    prob.solve()

    status = pulp.LpStatus[prob.status]
    if status != "Optimal":
        return None, None, status

    layout = {i: "___(空)___" for i in locations}
    folders_content = {f: [] for f in folders}
    for i in locations:
        for j in apps:
            if pulp.value(x[j][i]) > 0.5:
                layout[i] = j
        for f in folders:
            if pulp.value(y[f][i]) > 0.5:
                layout[i] = f"F:{f}"
    for j in apps:
        for f in folders:
            if pulp.value(z[j][f]) > 0.5:
                folders_content[f].append(j)

    return layout, folders_content, status
