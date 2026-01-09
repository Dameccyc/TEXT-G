import tkinter as tk
import time
import threading
from tkinter import simpledialog

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
    # 2
    [
        "墙门墙墙墙门墙墙墙墙墙门墙门墙墙墙墙门墙墙墙墙墙墙墙墙墙墙墙墙墙门墙",
        "墙我                               墙",
        "墙                                墙",
        "墙 盒                              墙",
        "墙灯墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙墙"
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
    # 找到最长行的长度
    max_len = max(len(row) for row in raw)

    # 统一所有行的长度
    lv = []
    for row in raw:
        if len(row) < max_len:
            # 填充空格到最长长度
            row = row + ' ' * (max_len - len(row))
        lv.append(list(row))

    h, w = len(lv), max_len
    px = py = 1
    for y in range(h):
        for x in range(w):
            if lv[y][x] == '我':
                lv[y][x] = ' '
                px, py = x, y
    return lv, w, h, px, py


# 游戏世界数据
world_world = []  # 完整游戏世界
world_w = 0  # 世界宽度
world_h = 0  # 世界高度
px = 0  # 玩家世界坐标x
py = 0  # 玩家世界坐标y
view_x = 0  # 视图左上角世界坐标x
view_y = 0  # 视图左上角世界坐标y

# 加载初始关卡
level_data, world_w, world_h, px, py = load_level(curr_lvl)
world_world = level_data

# ---------- Tk ----------
root = tk.Tk()
root.title("按Q启动元神")
canvas = tk.Canvas(root, width=W * CELL, height=H * CELL, bg="black", highlightthickness=0)
canvas.pack()
itemBar = canvas.create_text(5, 5, text='当前拥有：无', font=("Microsoft YaHei", 14), fill='white', anchor='nw')
text_ids = [[None] * W for _ in range(H)]

# 玩家光标（独立对象，最上层）
player_id = canvas.create_text(W // 2 * CELL + CELL // 2, H // 2 * CELL + CELL // 2,
                               text='我', font=FONT, fill='yellow')


# ---------- 密码输入逻辑 ----------
def open_password_dialog():
    """打开密码输入对话框"""
    password = simpledialog.askstring("密码", "请输入密码：", parent=root)
    if password == "351413":
        # 找到第一个门并变成路
        first_door_found = False
        for y in range(world_h):
            for x in range(world_w):
                if world_world[y][x] == '门' and not first_door_found:
                    world_world[y][x] = '路'
                    first_door_found = True
                    # 移除盒子
                    world_world[py][px] = ' '
                    # 显示成功消息
                    show_message("密码正确！第一个门已打开！")
                    # 更新视图显示
                    update_view()
                    return
    elif password is not None:  # 用户输入了但密码错误
        show_message("密码错误！")
        # 密码错误，不删除盒子，玩家可以重新尝试


def show_message(msg):
    """显示消息框"""
    simpledialog.messagebox.showinfo("提示", msg, parent=root)


# ---------- 光照 ----------
def in_world(x, y):
    return 0 <= x < world_w and 0 <= y < world_h


def get_char(x, y):
    if in_world(x, y):
        return world_world[y][x]
    return ' '


def get_light_positions():
    """获取所有光源位置"""
    light_positions = []

    # 玩家位置总是光源
    light_positions.append((px, py))

    # 寻找"灯"道具的位置
    for y in range(world_h):
        row = world_world[y]
        for x in range(min(len(row), world_w)):  # 确保不超出行的实际长度
            if row[x] == '灯':
                light_positions.append((x, y))

    return light_positions


def in_light_range(world_x, world_y, has_light):
    """判断世界坐标是否在任何光源的照亮范围内"""
    light_positions = get_light_positions()

    for lx, ly in light_positions:
        # 计算曼哈顿距离
        distance = abs(world_x - lx) + abs(world_y - ly)

        if not has_light:
            # 无灯时光源范围：半径2的菱形（5×5）
            if distance <= 2:
                return True
        else:
            # 有灯时光源范围：半径4的菱形（9×9）
            if distance <= 4:
                return True
    return False


def should_show(world_x, world_y, has_light):
    """判断这个位置是否应该显示"""
    if not in_world(world_x, world_y):
        return False

    # 如果是需要光照的关卡
    if needLight[curr_lvl]:
        # 判断当前位置是否在任意光源的照亮范围内
        return in_light_range(world_x, world_y, has_light)

    # 不需要光照的关卡，始终显示
    return True


def update_view():
    """更新视图显示"""
    has_light = inventory.get('灯', False)

    for screen_y in range(H):
        for screen_x in range(W):
            world_x = view_x + screen_x
            world_y = view_y + screen_y

            if text_ids[screen_y][screen_x]:
                if in_world(world_x, world_y):
                    if should_show(world_x, world_y, has_light):
                        ch = get_char(world_x, world_y)
                        canvas.itemconfig(text_ids[screen_y][screen_x], text=ch)
                    else:
                        canvas.itemconfig(text_ids[screen_y][screen_x], text=' ')
                else:
                    canvas.itemconfig(text_ids[screen_y][screen_x], text=' ')


def update_view_position():
    """更新视图位置以玩家为中心"""
    global view_x, view_y

    # 如果世界比视图小，居中显示
    if world_w <= W:
        # 世界居中显示
        view_x = (world_w - W) // 2
    else:
        # 玩家保持在中心
        target_view_x = px - W // 2
        # 确保视图不会超出世界边界
        view_x = max(0, min(target_view_x, world_w - W))

    if world_h <= H:
        # 世界居中显示
        view_y = (world_h - H) // 2
    else:
        # 玩家保持在中心
        target_view_y = py - H // 2
        # 确保视图不会超出世界边界
        view_y = max(0, min(target_view_y, world_h - H))


def update_player_position():
    """更新玩家在屏幕上的位置"""
    screen_x = px - view_x
    screen_y = py - view_y
    canvas.coords(player_id, screen_x * CELL + CELL // 2, screen_y * CELL + CELL // 2)


# ---------- 生成 ----------
def spawn_level():
    """生成整个视图区域"""
    # 更新视图位置
    update_view_position()

    for screen_y in range(H):
        for screen_x in range(W):
            world_x = view_x + screen_x
            world_y = view_y + screen_y

            if in_world(world_x, world_y):
                ch = get_char(world_x, world_y)
                if not needLight[curr_lvl] or should_show(world_x, world_y, False):
                    show_ch = ch
                else:
                    show_ch = ' '
            else:
                show_ch = ' '

            text_ids[screen_y][screen_x] = canvas.create_text(
                screen_x * CELL + CELL // 2, screen_y * CELL + CELL // 2,
                text=show_ch, font=FONT, fill="white")

    # 更新玩家位置
    update_player_position()
    update_view()


# ---------- 关卡切换 ----------
def next_level():
    global curr_lvl, world_world, world_w, world_h, px, py, view_x, view_y, inventory
    inventory = {'钥': False, '灯': False}
    update_bar()
    curr_lvl += 1
    if curr_lvl >= len(levels):
        # 如果到达最后一关，回到第一关
        curr_lvl = 0

    # 清屏
    for screen_y in range(H):
        for screen_x in range(W):
            if text_ids[screen_y][screen_x]:
                canvas.delete(text_ids[screen_y][screen_x])
    text_ids[:] = [[None] * W for _ in range(H)]

    # 加载新关
    level_data, world_w, world_h, px, py = load_level(curr_lvl)
    world_world = level_data

    # 重新生成
    spawn_level()


# ---------- 游戏逻辑 ----------
def can_go(x, y):
    if not (0 <= x < world_w and 0 <= y < world_h):
        return False
    return world_world[y][x] not in ('墙', '门')


def move(dx, dy):
    global px, py, view_x, view_y

    nx, ny = px + dx, py + dy
    if can_go(nx, ny):
        # 更新玩家位置
        old_px, old_py = px, py
        px, py = nx, ny
        here = world_world[py][px]

        # 拾取道具
        if here == '钥':
            world_world[py][px] = ' '
            inventory['钥'] = True
            update_bar()
            for y in range(world_h):
                for x in range(world_w):
                    if world_world[y][x] == '门':
                        world_world[y][x] = '路'
            # 更新视图显示
            update_view()

        if here == '灯':
            world_world[py][px] = ' '
            inventory['灯'] = True
            update_bar()
            # 更新视图显示
            update_view()

        # 遇到盒子
        if here == '盒':
            # 打开密码输入对话框
            root.after(100, open_password_dialog)  # 延迟一点显示，避免卡顿
            # 注意：这里不立即移除盒子，等待密码验证结果
            # 盒子是否移除在 open_password_dialog 中根据密码正确性决定

        # 检查是否需要更新视图位置
        old_view_x, old_view_y = view_x, view_y
        update_view_position()

        # 如果视图位置有变化，重新生成整个视图
        if view_x != old_view_x or view_y != old_view_y:
            # 清除旧的显示
            for screen_y in range(H):
                for screen_x in range(W):
                    if text_ids[screen_y][screen_x]:
                        canvas.delete(text_ids[screen_y][screen_x])

            # 重新生成视图
            for screen_y in range(H):
                for screen_x in range(W):
                    world_x = view_x + screen_x
                    world_y = view_y + screen_y

                    if in_world(world_x, world_y):
                        ch = get_char(world_x, world_y)
                        has_light = inventory.get('灯', False)
                        if not needLight[curr_lvl] or should_show(world_x, world_y, has_light):
                            show_ch = ch
                        else:
                            show_ch = ' '
                    else:
                        show_ch = ' '

                    text_ids[screen_y][screen_x] = canvas.create_text(
                        screen_x * CELL + CELL // 2, screen_y * CELL + CELL // 2,
                        text=show_ch, font=FONT, fill="white")
        else:
            # 视图位置没变化，只更新显示
            update_view()

        # 更新玩家显示位置
        update_player_position()

        # 胜利条件
        if here == '路':
            root.after(300, next_level)
            return


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
spawn_level()
root.mainloop()