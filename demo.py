import tkinter as tk
import time
import threading

# ---------- 世界常数 ----------
W = H = 15
CELL = 40
FONT = ("Microsoft YaHei", 20, "bold")

# ---------- 关卡数据 ----------
levels = [
    # 1  9×9
    [
        "墙墙墙墙墙墙墙墙墙",
        "墙我      墙",
        "墙       墙",
        "墙       墙",
        "墙       门",
        "墙       墙",
        "墙   钥   墙",
        "墙       墙",
        "墙墙墙墙墙墙墙墙墙"
    ],
    # 2  3×20
    [
        "墙墙墙墙墙墙墙墙墙墙墙墙墙墙",
        "墙我                      ",
        "墙                     路",
        "墙灯墙墙墙墙墙墙墙墙墙墙墙墙墙"
    ],
]
needLight = [False, True]
curr_lvl = 0

# ---------- 背包 ----------
inventory = {'钥': False, '灯': False}
itemBar = None


def update_bar():
    t = [k for k, v in inventory.items() if v]
    s = '当前拥有：' + ' '.join(t) if t else '当前拥有：无'
    canvas.itemconfig(itemBar, text=s, fill='yellow' if t else 'white')


# ---------- 关卡加载（返回实际行列 + 偏移 + 玩家坐标） ----------
def load_level(n):
    raw = levels[n]
    lv = [list(row) for row in raw]
    h, w = len(lv), len(lv[0])
    px = py = 1
    for y in range(h):
        for x in range(w):
            if lv[y][x] == '我':
                lv[y][x] = ' '
                px, py = x, y
    offX = (W - w) // 2
    offY = (H - h) // 2
    return lv, w, h, offX, offY, px + offX, py + offY


level9, RW, RH, offX, offY, px, py = load_level(curr_lvl)

# ---------- Tk ----------
root = tk.Tk()
root.title("按Q启动元神")
canvas = tk.Canvas(root, width=W * CELL, height=H * CELL, bg="black", highlightthickness=0)
canvas.pack()
itemBar = canvas.create_text(5, 5, text='当前拥有：无', font=("Microsoft YaHei", 14), fill='white', anchor='nw')
text_ids = [[None] * W for _ in range(H)]

# 玩家光标（独立对象，最上层）
player_id = canvas.create_text(px * CELL + CELL // 2, py * CELL + CELL // 2,
                               text='我', font=FONT, fill='yellow')


# ---------- 光照 ----------
def in_raw(x, y):
    rx, ry = x - offX, y - offY
    return 0 <= rx < RW and 0 <= ry < RH


def get_char(x, y):
    rx, ry = x - offX, y - offY
    return level9[ry][rx] if in_raw(x, y) else ' '


def get_light_positions():
    """获取所有光源位置"""
    light_positions = []

    # 玩家位置总是光源
    light_positions.append((px, py))

    # 寻找"灯"道具的位置
    for y in range(RH):
        for x in range(RW):
            if level9[y][x] == '灯':
                light_positions.append((x + offX, y + offY))

    return light_positions


def in_light_range(x, y, has_light):
    """判断位置是否在任何光源的照亮范围内"""
    light_positions = get_light_positions()

    for lx, ly in light_positions:
        # 无灯时光源范围：半径2的菱形（5×5）
        if not has_light:
            if abs(x - lx) + abs(y - ly) <= 2:
                return True
        # 有灯时光源范围：半径4的菱形（9×9）
        else:
            if abs(x - lx) + abs(y - ly) <= 4:
                return True
    return False


def should_show(x, y, has_light):
    """判断这个位置是否应该显示"""
    if not in_raw(x, y):
        return False

    # 如果是需要光照的关卡
    if needLight[curr_lvl]:
        # 判断当前位置是否在任意光源的照亮范围内
        return in_light_range(x, y, has_light)

    # 不需要光照的关卡，始终显示
    return True


def update_light():
    """更新所有位置的可视状态"""
    has_light = inventory.get('灯', False)

    for y in range(H):
        for x in range(W):
            if text_ids[y][x]:
                if should_show(x, y, has_light):
                    ch = get_char(x, y)
                    canvas.itemconfig(text_ids[y][x], text=ch)
                else:
                    canvas.itemconfig(text_ids[y][x], text=' ')  # 黑暗外罩


# ---------- 生成 ----------
def spawn_border():
    for y in range(H):
        for x in range(W):
            if not in_raw(x, y):
                text_ids[y][x] = canvas.create_text(
                    x * CELL + CELL // 2, y * CELL + CELL // 2,
                    text=' ', font=FONT, fill="white")


gen_x = gen_y = 0


def spawn_next():
    global gen_x, gen_y
    if gen_y >= RH:
        update_light()  # 生成完刷新光照
        return
    x = gen_x + offX
    y = gen_y + offY
    if 0 <= x < W and 0 <= y < H:  # 保险越界
        ch = level9[gen_y][gen_x]
        # 初始生成时检查是否应该显示
        if should_show(x, y, False):  # 初始没有灯
            show_ch = ch
        else:
            show_ch = ' '
        text_ids[y][x] = canvas.create_text(
            x * CELL + CELL // 2, y * CELL + CELL // 2,
            text=show_ch, font=FONT, fill="white")
    gen_x += 1
    if gen_x == RW:
        gen_x, gen_y = 0, gen_y + 1
    root.after(30, spawn_next)


# ---------- 关卡切换 ----------
def next_level():
    global curr_lvl, level9, RW, RH, offX, offY, px, py, gen_x, gen_y, inventory
    inventory = {'钥': False, '灯': False}
    update_bar()
    curr_lvl += 1
    if curr_lvl >= len(levels):
        curr_lvl = 0
    # 清屏
    for y in range(H):
        for x in range(W):
            if text_ids[y][x]:
                canvas.delete(text_ids[y][x])
    text_ids[:] = [[None] * W for _ in range(H)]
    # 加载新关
    level9, RW, RH, offX, offY, px, py = load_level(curr_lvl)
    gen_x = gen_y = 0
    spawn_border()
    # 把玩家光标移到新起点
    canvas.coords(player_id, px * CELL + CELL // 2, py * CELL + CELL // 2)
    root.after(100, spawn_next)


# ---------- 游戏逻辑 ----------
def can_go(x, y):
    if not (0 <= x < W and 0 <= y < H):
        return False
    if not in_raw(x, y):
        return False
    rx, ry = x - offX, y - offY
    return level9[ry][rx] not in ('墙', '门')


def move(dx, dy):
    global px, py
    nx, ny = px + dx, py + dy
    if can_go(nx, ny):
        # 擦旧：恢复地图字符
        old_ch = get_char(px, py)
        canvas.itemconfig(text_ids[py][px], text=old_ch)

        px, py = nx, ny
        rx, ry = px - offX, py - offY
        here = level9[ry][rx]

        # 拾取道具
        if here == '钥':
            level9[ry][rx] = ' '
            canvas.itemconfig(text_ids[py][px], text=' ')
            inventory['钥'] = True
            update_bar()
            for iy in range(RH):
                for ix in range(RW):
                    if level9[iy][ix] == '门':
                        level9[iy][ix] = '路'
                        canvas.itemconfig(text_ids[iy + offY][ix + offX], text='路')

        if here == '灯':
            level9[ry][rx] = ' '
            canvas.itemconfig(text_ids[py][px], text=' ')
            inventory['灯'] = True
            update_bar()
            # 拾取灯后立即更新光照
            update_light()

        # 胜利条件
        if here == '路':
            root.after(300, next_level)
            return

        # 移动玩家光标
        canvas.coords(player_id, px * CELL + CELL // 2, py * CELL + CELL // 2)
        # 更新光照显示
        update_light()


# ---------- 键盘 ----------
dirs = {'w': (0, -1), 'a': (-1, 0), 's': (0, 1), 'd': (1, 0)}
pressed = set()


def on_key_down(e):
    c = e.char
    if c == 'q':
        root.quit()
        return
    if c in dirs:
        pressed.add(c)


def on_key_up(e):
    pressed.discard(e.char)


def game_loop():
    while True:
        time.sleep(0.08)
        if pressed:
            for c in sorted(pressed):
                move(*dirs[c])


root.bind("<KeyPress>", on_key_down)
root.bind("<KeyRelease>", on_key_up)
threading.Thread(target=game_loop, daemon=True).start()

# ---------- 启动 ----------
root.focus_set()
spawn_border()
root.after(100, spawn_next)
root.mainloop()