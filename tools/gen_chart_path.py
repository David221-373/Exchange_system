import random

random.seed(42)
w, h = 1200, 72
n = 120
step = w / (n - 1)
pts: list[tuple[float, float]] = []

for i in range(n):
    x = round(i * step, 1)
    trend = 66 - (66 - 4) * (i / (n - 1))
    jitter = random.uniform(-10, 10)
    if i % 2 == 0:
        jitter += random.uniform(-6, 6)
    if 18 <= i <= 24:
        jitter += 16 if i < 21 else -12
    if 40 <= i <= 52:
        jitter -= random.uniform(2, 12)
    if 70 <= i <= 90:
        jitter += random.uniform(-8, 8)
    y = trend + jitter
    y = max(3.0, min(69.0, y))
    pts.append((x, round(y, 1)))

pts[0] = (0.0, 66.0)
pts[-1] = (1200.0, 4.0)

for i in range(1, n):
    prev_y = pts[i - 1][1]
    cur_y = pts[i][1]
    if cur_y > prev_y + 18:
        pts[i] = (pts[i][0], round(prev_y + random.uniform(8, 16), 1))
    if cur_y < prev_y - 22:
        pts[i] = (pts[i][0], round(prev_y - random.uniform(10, 18), 1))

def fmt(v: float) -> str:
    return str(int(v)) if v == int(v) else f"{v:.1f}"

line = f"M{fmt(pts[0][0])},{fmt(pts[0][1])}" + "".join(f" L{fmt(x)},{fmt(y)}" for x, y in pts[1:])
area = f"{line} L1200,{h} L0,{h} Z"
print(line)
print("---")
print(area)
