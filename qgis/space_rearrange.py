from qgis.core import *
from qgis.utils import iface
from qgis.PyQt.QtCore import QVariant
from collections import defaultdict, Counter, deque
import itertools
import math

# ✅ 레이어 이름
layer_name = "joined_layer"
layer = QgsProject.instance().mapLayersByName(layer_name)[0]

# ✅ 원본 데이터 수집
original_total_a2 = 0
original_a3_distribution = Counter()
cell_to_records = defaultdict(list)
original_a2_set = set()

for f in layer.getFeatures():
    r = f["row_index"]
    c = f["col_index"]
    a2 = str(f["A2"])
    a3 = str(f["A3"])
    original_total_a2 += 1
    original_a3_distribution[a3] += 1
    cell_to_records[(r, c)].append((a3, a2))
    original_a2_set.add(a2)

# ✅ 유틸 함수
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1),
              (-1, -1), (-1, 1), (1, -1), (1, 1)]
MAX_INDEX = 22

def in_bounds(cell):
    r, c = cell
    return 0 <= r <= MAX_INDEX and 0 <= c <= MAX_INDEX

def get_neighbors(cell):
    return [(cell[0] + dr, cell[1] + dc) for dr, dc in DIRECTIONS if in_bounds((cell[0] + dr, cell[1] + dc))]

def calculate_distance(cell1, cell2):
    return math.sqrt((cell1[0] - cell2[0])**2 + (cell1[1] - cell2[1])**2)

def push_until_empty(start_cell, direction, final_assignment, confirmed_a3_per_cell):
    dr, dc = direction
    path = []
    r, c = start_cell
    while in_bounds((r, c)):
        if (r, c) not in final_assignment:
            break
        path.append((r, c))
        r += dr
        c += dc
    else:
        return None
    for i in reversed(range(len(path))):
        from_cell = path[i]
        to_cell = (from_cell[0] + dr, from_cell[1] + dc)
        final_assignment[to_cell] = final_assignment.pop(from_cell)
        confirmed_a3_per_cell[to_cell] = confirmed_a3_per_cell.pop(from_cell)
    return start_cell

# ✅ 1단계: dominant A3 확정
confirmed_a3_per_cell = {}
final_assignment = {}
remaining_data = []

for cell, records in cell_to_records.items():
    a3_counts = Counter([a3 for a3, _ in records])
    dominant_a3 = max(a3_counts.items(), key=lambda x: x[1])[0]
    confirmed_a3_per_cell[cell] = dominant_a3
    final_assignment[cell] = []
    for a3, a2 in records:
        if a3 == dominant_a3:
            final_assignment[cell].append((a3, a2))
        else:
            remaining_data.append((cell, a3, a2))

# ✅ 3단계: 주변 셀로 이동
successfully_moved = 0
failed_to_move = []
moved_data = []

for orig_cell, a3, a2 in remaining_data:
    moved = False
    for neighbor in get_neighbors(orig_cell):
        if confirmed_a3_per_cell.get(neighbor) == a3:
            final_assignment[neighbor].append((a3, a2))
            moved_data.append((orig_cell, neighbor, a3, a2))
            successfully_moved += 1
            moved = True
            break
    if not moved:
        failed_to_move.append((orig_cell, a3, a2))

# ✅ 5단계: 확장 불가시 셀 밀기
unresolvable = []
distance_moved = 0

failed_grouped = defaultdict(list)
for orig_cell, a3, a2 in failed_to_move:
    failed_grouped[a3].append((orig_cell, a2))

for a3, group in failed_grouped.items():
    orig_cells = [cell for cell, _ in group]
    a2_list = [a2 for _, a2 in group]

    matching_cells = [cell for cell, ca3 in confirmed_a3_per_cell.items() if ca3 == a3]
    if matching_cells:
        best_cell = min(matching_cells, key=lambda c: min(calculate_distance(c, oc) for oc in orig_cells))
        final_assignment[best_cell].extend([(a3, a2) for a2 in a2_list])
        for orig_cell, a2 in group:
            moved_data.append((orig_cell, best_cell, a3, a2))
        distance_moved += len(a2_list)
    else:
        found = False
        for base_cell in orig_cells:
            for dr, dc in DIRECTIONS:
                pushed_cell = push_until_empty(base_cell, (dr, dc), final_assignment, confirmed_a3_per_cell)
                if pushed_cell:
                    confirmed_a3_per_cell[pushed_cell] = a3
                    final_assignment[pushed_cell] = [(a3, a2) for a2 in a2_list]
                    for orig_cell, a2 in group:
                        moved_data.append((orig_cell, pushed_cell, a3, a2))
                    distance_moved += len(a2_list)
                    found = True
                    break
            if found:
                break
        if not found:
            print(f"❌ 무결성 오류: A3 {a3} 배정 실패")
            for orig_cell, a2 in group:
                unresolvable.append((orig_cell, a3, a2))

# ✅ 무결성 검증
final_total_a2 = sum(len(v) for v in final_assignment.values())
final_a3_distribution = Counter(a3 for records in final_assignment.values() for a3, _ in records)

final_a2_set = set()
for records in final_assignment.values():
    for _, a2 in records:
        final_a2_set.add(a2)

missing_a2s = original_a2_set - final_a2_set
extra_a2s = final_a2_set - original_a2_set

print("\n📊 무결성 검증 결과:")
print(f"- 원본 A2 수: {original_total_a2}")
print(f"- 최종 A2 수: {final_total_a2}")
print(f"- 이동 실패 및 무결성 위배 A2 수: {len(unresolvable)}")

if missing_a2s:
    print(f"❌ 누락된 A2 수: {len(missing_a2s)} → 예: {list(missing_a2s)[:5]}")
else:
    print("✅ 모든 A2가 정확히 포함됨")

if extra_a2s:
    print(f"⚠️ 예기치 않은 A2 포함: {len(extra_a2s)} → 예: {list(extra_a2s)[:5]}")

missing_a3s = [a3 for a3 in original_a3_distribution if final_a3_distribution.get(a3, 0) == 0]
if missing_a3s:
    print("❌ A3가 전혀 배정되지 않은 경우:", missing_a3s)
else:
    print("✅ 모든 A3 최소 1셀에 배정됨")

mixed_cells = [cell for cell, records in final_assignment.items() if len(set(a3 for a3, _ in records)) > 1]
if mixed_cells:
    print(f"❌ 혼합 A3 셀 {len(mixed_cells)}개 존재 → 무결성 위반")
else:
    print("✅ 모든 셀 단일 A3 유지")

# ✅ 결과 레이어 생성
fields = QgsFields()
fields.append(QgsField("row_index", QVariant.Int))
fields.append(QgsField("col_index", QVariant.Int))
fields.append(QgsField("A3", QVariant.String))
fields.append(QgsField("A2_list", QVariant.String))
fields.append(QgsField("A2_count", QVariant.Int))

result_layer = QgsVectorLayer("Point?crs=EPSG:4326", "A3_distributed_final", "memory")
prov = result_layer.dataProvider()
prov.addAttributes(fields)
result_layer.updateFields()

for (r, c), records in final_assignment.items():
    a3 = confirmed_a3_per_cell.get((r, c), "")
    a2_list = [a2 for _, a2 in records]
    f = QgsFeature()
    f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(c, -r)))
    f.setAttributes([r, c, a3, ",".join(a2_list), len(a2_list)])
    prov.addFeature(f)

QgsProject.instance().addMapLayer(result_layer)
print("✅ 결과 레이어가 QGIS에 추가되었습니다.")
