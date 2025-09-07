from qgis.core import *
from qgis.utils import iface
from qgis.PyQt.QtCore import QVariant
from collections import defaultdict, Counter
import math

# ✅ 레이어 이름
layer_name = "joined_layer"
layer = QgsProject.instance().mapLayersByName(layer_name)[0]

# ✅ 원본 데이터 수집
original_total_pnu = 0
original_bgd_distribution = Counter()
cell_to_records = defaultdict(list)
original_pnu_set = set()

for f in layer.getFeatures():
    r = f["row_index"]
    c = f["col_index"]
    pnu = str(f["PNU"])   # ✅ A2 → PNU
    bgd = str(f["BGD"])   # ✅ A3 → BGD
    original_total_pnu += 1
    original_bgd_distribution[bgd] += 1
    cell_to_records[(r, c)].append((bgd, pnu))
    original_pnu_set.add(pnu)

# ✅ 유틸 함수
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1),
              (-1, -1), (-1, 1), (1, -1), (1, 1)]
MAX_INDEX = 21

def in_bounds(cell):
    r, c = cell
    return 0 <= r <= MAX_INDEX and 0 <= c <= MAX_INDEX

def get_neighbors(cell):
    return [(cell[0] + dr, cell[1] + dc) for dr, dc in DIRECTIONS if in_bounds((cell[0] + dr, cell[1] + dc))]

def calculate_distance(cell1, cell2):
    return math.sqrt((cell1[0] - cell2[0])**2 + (cell1[1] - cell2[1])**2)

def push_until_empty(start_cell, direction, final_assignment, confirmed_bgd_per_cell):
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
        confirmed_bgd_per_cell[to_cell] = confirmed_bgd_per_cell.pop(from_cell)
    return start_cell

# ✅ 1단계: dominant BGD 확정
confirmed_bgd_per_cell = {}
final_assignment = {}
remaining_data = []

for cell, records in cell_to_records.items():
    bgd_counts = Counter([bgd for bgd, _ in records])
    dominant_bgd = max(bgd_counts.items(), key=lambda x: x[1])[0]
    confirmed_bgd_per_cell[cell] = dominant_bgd
    final_assignment[cell] = []
    for bgd, pnu in records:
        if bgd == dominant_bgd:
            final_assignment[cell].append((bgd, pnu))
        else:
            remaining_data.append((cell, bgd, pnu))

# ✅ 3단계: 주변 셀로 이동
successfully_moved = 0
failed_to_move = []
moved_data = []

for orig_cell, bgd, pnu in remaining_data:
    moved = False
    for neighbor in get_neighbors(orig_cell):
        if confirmed_bgd_per_cell.get(neighbor) == bgd:
            final_assignment[neighbor].append((bgd, pnu))
            moved_data.append((orig_cell, neighbor, bgd, pnu))
            successfully_moved += 1
            moved = True
            break
    if not moved:
        failed_to_move.append((orig_cell, bgd, pnu))

# ✅ 5단계: 확장 불가시 셀 밀기
unresolvable = []
distance_moved = 0

failed_grouped = defaultdict(list)
for orig_cell, bgd, pnu in failed_to_move:
    failed_grouped[bgd].append((orig_cell, pnu))

for bgd, group in failed_grouped.items():
    orig_cells = [cell for cell, _ in group]
    pnu_list = [pnu for _, pnu in group]

    matching_cells = [cell for cell, c_bgd in confirmed_bgd_per_cell.items() if c_bgd == bgd]
    if matching_cells:
        best_cell = min(matching_cells, key=lambda c: min(calculate_distance(c, oc) for oc in orig_cells))
        final_assignment[best_cell].extend([(bgd, pnu) for pnu in pnu_list])
        for orig_cell, pnu in group:
            moved_data.append((orig_cell, best_cell, bgd, pnu))
        distance_moved += len(pnu_list)
    else:
        found = False
        for base_cell in orig_cells:
            for dr, dc in DIRECTIONS:
                pushed_cell = push_until_empty(base_cell, (dr, dc), final_assignment, confirmed_bgd_per_cell)
                if pushed_cell:
                    confirmed_bgd_per_cell[pushed_cell] = bgd
                    final_assignment[pushed_cell] = [(bgd, pnu) for pnu in pnu_list]
                    for orig_cell, pnu in group:
                        moved_data.append((orig_cell, pushed_cell, bgd, pnu))
                    distance_moved += len(pnu_list)
                    found = True
                    break
            if found:
                break
        if not found:
            print(f"❌ 무결성 오류: BGD {bgd} 배정 실패")
            for orig_cell, pnu in group:
                unresolvable.append((orig_cell, bgd, pnu))

# ✅ 무결성 검증
final_total_pnu = sum(len(v) for v in final_assignment.values())
final_bgd_distribution = Counter(bgd for records in final_assignment.values() for bgd, _ in records)

final_pnu_set = set()
for records in final_assignment.values():
    for _, pnu in records:
        final_pnu_set.add(pnu)

missing_pnus = original_pnu_set - final_pnu_set
extra_pnus = final_pnu_set - original_pnu_set

print("\n📊 무결성 검증 결과:")
print(f"- 원본 PNU 수: {original_total_pnu}")
print(f"- 최종 PNU 수: {final_total_pnu}")
print(f"- 이동 실패 및 무결성 위배 PNU 수: {len(unresolvable)}")

if missing_pnus:
    print(f"❌ 누락된 PNU 수: {len(missing_pnus)} → 예: {list(missing_pnus)[:5]}")
else:
    print("✅ 모든 PNU가 정확히 포함됨")

if extra_pnus:
    print(f"⚠️ 예기치 않은 PNU 포함: {len(extra_pnus)} → 예: {list(extra_pnus)[:5]}")

missing_bgds = [bgd for bgd in original_bgd_distribution if final_bgd_distribution.get(bgd, 0) == 0]
if missing_bgds:
    print("❌ BGD가 전혀 배정되지 않은 경우:", missing_bgds)
else:
    print("✅ 모든 BGD 최소 1셀에 배정됨")

mixed_cells = [cell for cell, records in final_assignment.items() if len(set(bgd for bgd, _ in records)) > 1]
if mixed_cells:
    print(f"❌ 혼합 BGD 셀 {len(mixed_cells)}개 존재 → 무결성 위반")
else:
    print("✅ 모든 셀 단일 BGD 유지")

# ✅ 결과 레이어 생성
fields = QgsFields()
fields.append(QgsField("row_index", QVariant.Int))
fields.append(QgsField("col_index", QVariant.Int))
fields.append(QgsField("BGD", QVariant.String))
fields.append(QgsField("PNU_list", QVariant.String))
fields.append(QgsField("PNU_count", QVariant.Int))

result_layer = QgsVectorLayer("Point?crs=EPSG:4326", "PNU_distributed_final", "memory")
prov = result_layer.dataProvider()
prov.addAttributes(fields)
result_layer.updateFields()

for (r, c), records in final_assignment.items():
    bgd = confirmed_bgd_per_cell.get((r, c), "")
    pnu_list = [pnu for _, pnu in records]
    f = QgsFeature()
    f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(c, -r)))
    f.setAttributes([r, c, bgd, ",".join(pnu_list), len(pnu_list)])
    prov.addFeature(f)

QgsProject.instance().addMapLayer(result_layer)
print("✅ 결과 레이어가 QGIS에 추가되었습니다.")
