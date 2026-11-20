# -*- coding: utf-8 -*-
"""PATHFINDER: four-algorithm visual comparison. Python 3.9+, standard library only."""
import csv
import heapq
import random
import statistics
import time
import tkinter as tk
from collections import deque
from tkinter import filedialog, messagebox, ttk

ROWS = COLS = 19
START = (9, 0)
GOAL = (9, 18)
CELL = 27
BOARD = CELL * COLS
COLORS = {'BFS': '#3f6cf5', 'DFS': '#9462df', 'Dijkstra': '#e8a33e', 'A*': '#41af83'}
BG = '#f4f6fa'
INK = '#20283a'
MUTED = '#768196'
WHITE = '#ffffff'


def neighbors(p, blocked):
    r, c = p
    for nr, nc in ((r-1, c), (r, c+1), (r+1, c), (r, c-1)):
        if 0 <= nr < ROWS and 0 <= nc < COLS and (nr, nc) not in blocked:
            yield nr, nc


def solve(name, blocked, start=START, goal=GOAL):
    """Return path, visit order, and elapsed milliseconds. All edges cost 1."""
    t0 = time.perf_counter_ns()
    came = {start: None}
    visited = []
    if name == 'BFS':
        frontier = deque([start])
        while frontier:
            node = frontier.popleft()
            visited.append(node)
            if node == goal:
                break
            for nxt in neighbors(node, blocked):
                if nxt not in came:
                    came[nxt] = node
                    frontier.append(nxt)
    elif name == 'DFS':
        frontier = [start]
        while frontier:
            node = frontier.pop()
            visited.append(node)
            if node == goal:
                break
            for nxt in neighbors(node, blocked):
                if nxt not in came:
                    came[nxt] = node
                    frontier.append(nxt)
    else:
        def heuristic(p):
            return abs(p[0]-goal[0]) + abs(p[1]-goal[1]) if name == 'A*' else 0
        heap = [(heuristic(start), 0, 0, start)]
        best = {start: 0}
        closed = set()
        serial = 0
        while heap:
            _, cost, _, node = heapq.heappop(heap)
            if node in closed or cost != best[node]:
                continue
            closed.add(node)
            visited.append(node)
            if node == goal:
                break
            for nxt in neighbors(node, blocked):
                nc = cost + 1
                if nc < best.get(nxt, float('inf')):
                    best[nxt] = nc
                    came[nxt] = node
                    serial += 1
                    heapq.heappush(heap, (nc + heuristic(nxt), nc, serial, nxt))
    ms = (time.perf_counter_ns() - t0) / 1_000_000
    path = []
    if goal in came:
        p = goal
        while p is not None:
            path.append(p)
            p = came[p]
        path.reverse()
    return {'name': name, 'visited': visited, 'path': path, 'length': len(path)-1 if path else -1, 'ms': ms}


class Pathfinder:
    def __init__(self, root):
        self.root = root
        root.title('PATHFINDER | 알고리즘 경로 탐색 비교')
        root.geometry('1130x790')
        root.minsize(1020, 740)
        root.configure(bg=BG)
        self.blocked = set()
        self.active = tk.StringVar(value='BFS')
        self.tool = tk.StringVar(value='wall')
        self.speed = tk.IntVar(value=12)
        self.status = tk.StringVar(value='격자를 클릭하여 장애물을 설치하거나 제거하세요.')
        self.results = {}
        self.visit_shown = set()
        self.path_shown = set()
        self.anim_id = None
        self.anim_steps = []
        self.anim_pos = 0
        self.draw_board_base = None
        self.chart_metric = tk.StringVar(value='nodes')
        self.race_window = None
        self.race_job = None
        self.setup_ui()
        self.preset()

    def panel(self, parent, **kwargs):
        return tk.Frame(parent, bg=WHITE, highlightbackground='#e6eaf1', highlightthickness=1, **kwargs)

    def label(self, parent, text, size=10, color=INK, bold=False, bg=WHITE, **kwargs):
        return tk.Label(parent, text=text, font=('Malgun Gothic', size, 'bold' if bold else 'normal'),
                        fg=color, bg=bg, **kwargs)

    def button(self, parent, text, command, accent=False, width=None):
        return tk.Button(parent, text=text, command=command, cursor='hand2',
                         font=('Malgun Gothic', 9, 'bold' if accent else 'normal'),
                         bg='#3f6cf5' if accent else '#f3f5f9',
                         fg='white' if accent else INK, activebackground='#3155cc' if accent else '#e5eaf2',
                         activeforeground='white' if accent else INK, relief='flat', bd=0,
                         padx=12, pady=8, width=width)

    def setup_ui(self):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill='both', expand=True, padx=23, pady=18)
        top = tk.Frame(outer, bg=BG)
        top.pack(fill='x', pady=(0, 16))
        self.label(top, '●  Pathfinder', 17, INK, True, BG).pack(side='left')
        self.label(top, '게임 속 길찾기 알고리즘 비교 분석', 10, MUTED, bg=BG).pack(side='left', padx=16)
        self.label(top, 'BFS  ●    DFS  ●    Dijkstra  ●    A*', 9, MUTED, bg=BG).pack(side='right')

        content = tk.Frame(outer, bg=BG)
        content.pack(fill='both', expand=True)
        left = self.panel(content)
        left.pack(side='left', fill='y', padx=(0, 14))
        right = tk.Frame(content, bg=BG)
        right.pack(side='left', fill='both', expand=True)

        left_head = tk.Frame(left, bg=WHITE)
        left_head.pack(fill='x', padx=17, pady=(15, 8))
        self.label(left_head, '경로 탐색 맵', 12, bold=True).pack(side='left')
        self.label(left_head, '19 × 19', 9, MUTED).pack(side='right')
        self.canvas = tk.Canvas(left, width=BOARD, height=BOARD, bg='#fff', highlightthickness=0,
                                cursor='crosshair')
        self.canvas.pack(padx=17, pady=(0, 12))
        self.canvas.bind('<Button-1>', self.on_click)
        legend = tk.Frame(left, bg=WHITE)
        legend.pack(fill='x', padx=17, pady=(0, 12))
        for symbol, txt, color in [('●','출발','#3f6cf5'), ('●','도착','#f06a74'),
                                   ('■','장애물','#303748'), ('■','방문','#b9cdfa'), ('■','경로','#3f6cf5')]:
            self.label(legend, symbol, 10, color).pack(side='left')
            self.label(legend, txt, 8, MUTED).pack(side='left', padx=(2, 11))
        toolrow = tk.Frame(left, bg=WHITE)
        toolrow.pack(fill='x', padx=17, pady=(0, 12))
        for value, text in [('wall','장애물'), ('start','출발점'), ('goal','도착점')]:
            tk.Radiobutton(toolrow, text=text, value=value, variable=self.tool, bg=WHITE,
                           activebackground=WHITE, selectcolor=WHITE,
                           font=('Malgun Gothic', 9)).pack(side='left', padx=(0, 10))
        actions = tk.Frame(left, bg=WHITE)
        actions.pack(fill='x', padx=17, pady=(0, 12))
        for text, func in [('▶ 시작',self.start), ('기록 초기화',self.reset_view),
                           ('랜덤 맵',self.random_map), ('맵 비우기',self.clear_map)]:
            self.button(actions, text, func, accent=text.startswith('▶')).pack(side='left', padx=(0, 5))
        lower = tk.Frame(left, bg=WHITE)
        lower.pack(fill='x', padx=17, pady=(0, 14))
        self.label(lower, '애니메이션 속도', 9, MUTED).pack(side='left')
        tk.Scale(lower, from_=1, to=30, orient='horizontal', variable=self.speed,
                 bg=WHITE, highlightthickness=0, showvalue=0, length=160).pack(side='right')

        summary = self.panel(right)
        summary.pack(fill='x', pady=(0, 12))
        self.label(summary, '알고리즘 선택', 11, bold=True).pack(anchor='w', padx=18, pady=(15, 8))
        tabs = tk.Frame(summary, bg=WHITE)
        tabs.pack(fill='x', padx=18, pady=(0, 13))
        self.tab_buttons = {}
        for name in COLORS:
            b = self.button(tabs, name, lambda n=name: self.choose(n), width=9)
            b.pack(side='left', padx=(0, 7))
            self.tab_buttons[name] = b
        self.refresh_tabs()
        statrow = tk.Frame(summary, bg=WHITE)
        statrow.pack(fill='x', padx=18, pady=(0, 17))
        self.stat_labels = {}
        for key, title in [('time','탐색 시간'), ('nodes','방문 노드'), ('length','경로 길이')]:
            part = tk.Frame(statrow, bg=WHITE)
            part.pack(side='left', expand=True, fill='x')
            self.label(part, title, 9, MUTED).pack(anchor='w')
            val = self.label(part, '—', 19, INK, True)
            val.pack(anchor='w', pady=(3, 0))
            self.stat_labels[key] = val

        chartpanel = self.panel(right)
        chartpanel.pack(fill='both', expand=True, pady=(0, 12))
        self.label(chartpanel, '성능 비교', 12, bold=True).pack(anchor='w', padx=18, pady=(15, 0))
        self.chart_hint = self.label(chartpanel, '동일한 맵 · 방문 노드 수 (낮을수록 효율적)', 9, MUTED)
        self.chart_hint.pack(anchor='w', padx=18, pady=(2, 5))
        metric_row = tk.Frame(chartpanel, bg=WHITE)
        metric_row.pack(anchor='w', padx=18, pady=(0, 3))
        for key, title in [('nodes', '방문 노드'), ('length', '경로 길이'), ('ms', '탐색 시간')]:
            tk.Radiobutton(metric_row, text=title, value=key, variable=self.chart_metric,
                           command=self.draw_chart, bg=WHITE, activebackground=WHITE,
                           selectcolor=WHITE, font=('Malgun Gothic', 9)).pack(side='left', padx=(0, 8))
        self.chart = tk.Canvas(chartpanel, height=210, bg=WHITE, highlightthickness=0)
        self.chart.pack(fill='x', padx=16, pady=(0, 10))
        self.chart.bind('<Configure>', lambda e: self.draw_chart())
        self.label(chartpanel, '알고리즘별 결과', 10, bold=True).pack(anchor='w', padx=18, pady=(0, 5))
        columns = ('alg', 'nodes', 'ms', 'length')
        self.table = ttk.Treeview(chartpanel, columns=columns, show='headings', height=4)
        for key, title, width in [('alg','알고리즘',90),('nodes','방문 노드',75),
                                  ('ms','시간(ms)',100),('length','경로 길이',75)]:
            self.table.heading(key, text=title)
            self.table.column(key, anchor='center', width=width, stretch=True)
        self.table.pack(fill='x', padx=18, pady=(0, 13))
        foot = self.panel(right)
        foot.pack(fill='x')
        row = tk.Frame(foot, bg=WHITE)
        row.pack(fill='x', padx=14, pady=11)
        self.button(row, '동시 탐색 ▶', self.start_race, accent=True).pack(side='left', padx=(0, 7))
        self.button(row, '결과 비교', self.compare_all).pack(side='left', padx=(0, 7))
        self.button(row, 'CSV 저장', self.save_csv).pack(side='left')
        self.label(foot, '동시 탐색은 관찰용 애니메이션입니다. 실제 계산 시간은 별도 측정값입니다.',
                   8, MUTED, justify='left', wraplength=450).pack(anchor='w', padx=16, pady=(0, 12))
        self.label(outer, '', 9, MUTED, bg=BG).pack_forget()
        self.status_label = self.label(outer, '', 9, MUTED, bg=BG, anchor='w')
        self.status_label.pack(fill='x', pady=(10, 0))
        self.status.trace_add('write', lambda *_: self.status_label.config(text=self.status.get()))
        self.status_label.config(text=self.status.get())

    def refresh_tabs(self):
        for name, b in self.tab_buttons.items():
            selected = self.active.get() == name
            b.config(bg=COLORS[name] if selected else '#f3f5f9', fg='white' if selected else INK,
                     activebackground=COLORS[name] if selected else '#e5eaf2')

    def choose(self, name):
        self.stop_animation()
        self.active.set(name)
        self.refresh_tabs()
        if name in self.results:
            self.visit_shown = set(self.results[name]['visited'])
            self.path_shown = set(self.results[name]['path'])
        else:
            self.visit_shown.clear()
            self.path_shown.clear()
        self.draw()
        self.update_stats()

    def stop_animation(self):
        if self.anim_id is not None:
            self.root.after_cancel(self.anim_id)
            self.anim_id = None
        self.anim_steps = []

    def reset_view(self):
        self.stop_animation()
        self.results.clear()
        self.visit_shown.clear()
        self.path_shown.clear()
        self.refresh_results()
        self.status.set('분석 기록을 초기화했습니다. 장애물은 유지됩니다.')

    def clear_map(self):
        self.blocked.clear()
        self.reset_view()
        self.status.set('맵을 비웠습니다. 출발점과 도착점은 유지됩니다.')

    def preset(self):
        self.blocked.clear()
        for r in range(4, 15):
            if r != 5:
                self.blocked.add((r, 8))
        for p in [(2,4),(3,14),(5,3),(6,15),(12,3),(14,14),(16,5),(16,12),(3,11),(12,13)]:
            self.blocked.add(p)
        self.reset_view()
        self.status.set('예시 맵이 준비됐습니다. 시작을 눌러 탐색을 확인하세요.')

    def random_map(self):
        self.blocked = {(r,c) for r in range(ROWS) for c in range(COLS)
                        if (r,c) not in (START, GOAL) and random.random() < .20}
        # A reachable map makes demonstrations easier.
        for _ in range(40):
            if solve('BFS', self.blocked)['path']:
                break
            self.blocked = {(r,c) for r in range(ROWS) for c in range(COLS)
                            if (r,c) not in (START, GOAL) and random.random() < .16}
        self.reset_view()
        self.status.set('랜덤 장애물 맵을 생성했습니다.')

    def on_click(self, event):
        r, c = event.y // CELL, event.x // CELL
        if not (0 <= r < ROWS and 0 <= c < COLS):
            return
        p = (r, c)
        global START, GOAL
        if self.tool.get() == 'start':
            if p != GOAL and p not in self.blocked:
                START = p
        elif self.tool.get() == 'goal':
            if p != START and p not in self.blocked:
                GOAL = p
        elif p not in (START, GOAL):
            if p in self.blocked:
                self.blocked.remove(p)
            else:
                self.blocked.add(p)
        self.reset_view()
        self.status.set('맵이 변경되었습니다. 같은 조건에서 알고리즘을 다시 비교하세요.')

    def draw(self):
        c = self.canvas
        c.delete('all')
        for r in range(ROWS):
            for col in range(COLS):
                p = (r, col)
                color = '#ffffff' if (r+col)%2 == 0 else '#fafbfe'
                if p in self.visit_shown:
                    color = '#dce7ff'
                if p in self.path_shown:
                    color = COLORS[self.active.get()]
                if p in self.blocked:
                    color = '#303748'
                x, y = col*CELL, r*CELL
                c.create_rectangle(x+1, y+1, x+CELL-1, y+CELL-1,
                                   fill=color, outline='#e9edf4', width=1)
        for p, color, text in [(START, '#3f6cf5', 'S'), (GOAL, '#ef6978', 'G')]:
            r, col = p
            x, y = col*CELL+CELL/2, r*CELL+CELL/2
            c.create_oval(x-10, y-10, x+10, y+10, fill=color, outline='white', width=2)
            c.create_text(x, y, text=text, fill='white', font=('Arial', 9, 'bold'))

    def update_stats(self):
        r = self.results.get(self.active.get())
        if r:
            self.stat_labels['time'].config(text=f"{r['ms']:.3f} ms")
            self.stat_labels['nodes'].config(text=str(len(r['visited'])))
            self.stat_labels['length'].config(text=str(r['length']) if r['length'] >= 0 else '경로 없음')
        else:
            for label in self.stat_labels.values():
                label.config(text='—')

    def refresh_results(self):
        for item in self.table.get_children():
            self.table.delete(item)
        for name in COLORS:
            if name in self.results:
                r = self.results[name]
                self.table.insert('', 'end', values=(name, len(r['visited']), f"{r['ms']:.3f}",
                                                      r['length'] if r['length'] >= 0 else '없음'))
        self.update_stats()
        self.draw_chart()
        self.draw()

    def draw_chart(self):
        c = self.chart
        c.delete('all')
        width = max(c.winfo_width(), 400)
        metric = self.chart_metric.get()
        self.chart_hint.config(text={'nodes': '동일한 맵 · 방문 노드 수 (적을수록 효율적)',
                                     'length': '동일한 맵 · 목적지까지의 경로 길이 (짧을수록 좋음)',
                                     'ms': '동일한 맵 · 탐색 계산 시간(ms) (작을수록 빠름)'}[metric])
        def value_of(r):
            return len(r['visited']) if metric == 'nodes' else (r['length'] if metric == 'length' else r['ms'])
        values = [max(0, value_of(self.results[n])) for n in COLORS if n in self.results]
        maximum = max(values, default=1) or 1
        for idx, (name, color) in enumerate(COLORS.items()):
            y = 25 + idx*50
            c.create_text(16, y+10, text=name, anchor='w', font=('Arial', 10, 'bold'), fill=INK)
            left = 102
            available = max(100, width-left-64)
            c.create_rectangle(left, y, left+available, y+20, fill='#eef1f5', outline='')
            if name in self.results:
                value = value_of(self.results[name])
                if self.results[name]['length'] < 0:
                    display = '경로 없음' if metric == 'length' else (f'{value:.3f}' if metric == 'ms' else str(value))
                else:
                    display = f'{value:.3f}' if metric == 'ms' else str(value)
                c.create_rectangle(left, y, left+available*(max(0, value)/maximum), y+20,
                                   fill=color, outline='')
                c.create_text(left+available+12, y+10, text=display, anchor='w',
                              font=('Arial', 9, 'bold'), fill=INK)
            else:
                c.create_text(left+available+12, y+10, text='—', anchor='w', fill=MUTED)

    def start(self):
        self.stop_animation()
        name = self.active.get()
        result = solve(name, self.blocked)
        self.results[name] = result
        self.visit_shown.clear()
        self.path_shown.clear()
        self.refresh_results()
        self.anim_steps = [('visit', p) for p in result['visited']] + [('path', p) for p in result['path']]
        self.anim_pos = 0
        self.status.set(f'{name} 탐색 애니메이션 실행 중…')
        self.animate()

    def animate(self):
        if self.anim_pos >= len(self.anim_steps):
            self.anim_id = None
            name = self.active.get()
            r = self.results.get(name)
            self.status.set(f"{name}: 경로 {r['length']}칸, 방문 노드 {len(r['visited'])}개, "
                            f"탐색 시간 {r['ms']:.3f}ms (애니메이션 시간 제외)" if r else '완료')
            return
        count = max(1, self.speed.get() // 3)
        for _ in range(count):
            if self.anim_pos >= len(self.anim_steps):
                break
            kind, p = self.anim_steps[self.anim_pos]
            (self.visit_shown if kind == 'visit' else self.path_shown).add(p)
            self.anim_pos += 1
        self.draw()
        self.anim_id = self.root.after(25, self.animate)

    def compare_all(self):
        self.stop_animation()
        self.results = {name: solve(name, self.blocked) for name in COLORS}
        name = self.active.get()
        self.visit_shown = set(self.results[name]['visited'])
        self.path_shown = set(self.results[name]['path'])
        self.refresh_results()
        self.status.set('4가지 알고리즘 비교 완료. 상단 알고리즘을 선택하면 각 경로를 볼 수 있습니다.')


    def start_race(self):
        """Show all four search processes on independent miniature maps, in lockstep."""
        self.stop_animation()
        if self.race_window is not None and self.race_window.winfo_exists():
            self.race_window.destroy()
        self.results = {name: solve(name, self.blocked) for name in COLORS}
        self.refresh_results()
        win = tk.Toplevel(self.root)
        self.race_window = win
        win.title('동시 경로 탐색 | BFS · DFS · Dijkstra · A*')
        win.geometry('1220x870')
        win.minsize(1160, 820)
        win.configure(bg=BG)
        self.label(win, '4가지 알고리즘 동시 탐색', 17, INK, True, BG).pack(pady=(14, 3))
        self.label(win, '동일한 맵 · 동일한 출발점/도착점 · 같은 애니메이션 간격으로 탐색 단계를 표시',
                   9, MUTED, bg=BG).pack(pady=(0, 9))
        workspace = tk.Frame(win, bg=BG)
        workspace.pack(fill='both', expand=True, padx=12)
        area = tk.Frame(workspace, bg=BG)
        area.pack(side='left', expand=True)
        graph_panel = self.panel(workspace)
        graph_panel.pack(side='right', fill='y', padx=(12, 0), pady=7)
        self.label(graph_panel, '목적지까지 이동 거리', 13, INK, True).pack(anchor='w', padx=16, pady=(16, 3))
        self.label(graph_panel, '알고리즘별 경로 길이 (칸)', 9, MUTED).pack(anchor='w', padx=16, pady=(0, 10))
        self.race_distance_chart = tk.Canvas(graph_panel, width=335, height=270, bg=WHITE,
                                             highlightthickness=0)
        self.race_distance_chart.pack(padx=12)
        self.draw_race_distance_chart()
        self.label(graph_panel, '동일한 맵에서 찾은 경로를 비교합니다.\n막대가 짧을수록 이동 거리가 짧습니다.\n(탐색 계산 시간과는 별개)',
                   9, MUTED, justify='left').pack(anchor='w', padx=16, pady=(4, 12))
        self.race_canvases = {}
        self.race_labels = {}
        self.race_states = {}
        self.race_blocked = set(self.blocked)
        self.race_start = START
        self.race_goal = GOAL
        self.race_cell = 18
        for i, name in enumerate(COLORS):
            card = self.panel(area)
            card.grid(row=i//2, column=i%2, padx=7, pady=7)
            header = tk.Frame(card, bg=WHITE)
            header.pack(fill='x', padx=11, pady=(8, 4))
            self.label(header, name, 12, COLORS[name], True).pack(side='left')
            stat = self.label(header, '탐색 준비', 9, MUTED)
            stat.pack(side='right')
            board = tk.Canvas(card, width=COLS*18, height=ROWS*18, bg=WHITE,
                              highlightthickness=0)
            board.pack(padx=10, pady=(0, 10))
            self.race_canvases[name] = board
            self.race_labels[name] = stat
            result = self.results[name]
            self.race_states[name] = {'visits': set(), 'path': set(), 'phase': 'visit',
                                      'pos': 0, 'result': result, 'done': False}
            self.draw_race_board(name)
        controls = tk.Frame(win, bg=BG)
        controls.pack(pady=(3, 12))
        self.race_info = self.label(controls, '각 알고리즘의 탐색 순서를 동시에 표시합니다.', 9, MUTED, bg=BG)
        self.race_info.pack(side='left', padx=12)
        self.button(controls, '다시 재생', self.start_race).pack(side='left', padx=5)
        self.button(controls, '닫기', win.destroy).pack(side='left', padx=5)
        self.race_job = None
        win.protocol('WM_DELETE_WINDOW', win.destroy)
        self.race_tick()
        self.status.set('동시 탐색 창을 열었습니다. 경로 길이 그래프도 선택할 수 있습니다.')

    def draw_race_distance_chart(self):
        """Draw distance bars directly beside the four simultaneous animations."""
        canvas = self.race_distance_chart
        canvas.delete('all')
        lengths = [r['length'] for r in self.results.values() if r['length'] >= 0]
        maximum = max(lengths, default=1) or 1
        for i, (name, color) in enumerate(COLORS.items()):
            y = 22 + i * 58
            result = self.results[name]
            distance = result['length']
            canvas.create_text(10, y, text=name, anchor='w', fill=INK,
                               font=('Arial', 10, 'bold'))
            canvas.create_rectangle(95, y-10, 270, y+10, fill='#eef1f5', outline='')
            if distance >= 0:
                canvas.create_rectangle(95, y-10, 95 + 175 * distance / maximum, y+10,
                                        fill=color, outline='')
                label = f'{distance}칸'
            else:
                label = '경로 없음'
            canvas.create_text(280, y, text=label, anchor='w', fill=INK,
                               font=('Arial', 9, 'bold'))

    def draw_race_board(self, name):
        board = self.race_canvases[name]
        board.delete('all')
        state = self.race_states[name]
        z = self.race_cell
        for r in range(ROWS):
            for col in range(COLS):
                p = (r, col)
                color = '#ffffff' if (r+col)%2 == 0 else '#fafbfe'
                if p in state['visits']:
                    color = '#dce7ff'
                if p in state['path']:
                    color = COLORS[name]
                if p in self.race_blocked:
                    color = '#303748'
                board.create_rectangle(col*z+1, r*z+1, (col+1)*z, (r+1)*z,
                                       fill=color, outline='#e9edf4')
        for p, color, char in [(self.race_start, '#3f6cf5', 'S'), (self.race_goal, '#ef6978', 'G')]:
            r, col = p
            x, y = col*z+z/2, r*z+z/2
            board.create_oval(x-7, y-7, x+7, y+7, fill=color, outline='white')
            board.create_text(x, y, text=char, fill='white', font=('Arial', 7, 'bold'))

    def race_tick(self):
        if self.race_window is None or not self.race_window.winfo_exists():
            return
        all_done = True
        for name, state in self.race_states.items():
            if state['done']:
                continue
            all_done = False
            result = state['result']
            items = result['visited'] if state['phase'] == 'visit' else result['path']
            for _ in range(max(1, self.speed.get() // 5)):
                if state['pos'] < len(items):
                    target = state['visits'] if state['phase'] == 'visit' else state['path']
                    target.add(items[state['pos']])
                    state['pos'] += 1
                if state['pos'] >= len(items):
                    if state['phase'] == 'visit' and result['path']:
                        state['phase'], state['pos'] = 'path', 0
                        break
                    state['done'] = True
                    break
            self.draw_race_board(name)
            if state['done']:
                length = result['length']
                self.race_labels[name].config(text=(f'완료 · {length}칸' if length >= 0 else '경로 없음'))
            else:
                self.race_labels[name].config(text=f"방문 {len(state['visits'])} / {len(result['visited'])}")
        if all_done or all(s['done'] for s in self.race_states.values()):
            self.race_info.config(text='4가지 탐색 완료 · 오른쪽에 이동 거리 그래프가 표시됩니다.')
            self.race_job = None
            return
        self.race_job = self.race_window.after(30, self.race_tick)

    def save_csv(self):
        if not self.results:
            messagebox.showinfo('결과 없음', '먼저 시작 또는 네 알고리즘 비교를 실행하세요.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv',
                                            filetypes=[('CSV 파일', '*.csv')],
                                            initialfile='pathfinder_results.csv')
        if not path:
            return
        with open(path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['algorithm','path_length','visited_nodes','search_time_ms',
                             'start','goal','obstacles'])
            for name in COLORS:
                if name in self.results:
                    r = self.results[name]
                    writer.writerow([name, r['length'], len(r['visited']), f"{r['ms']:.6f}",
                                     START, GOAL, ';'.join(f'{x}:{y}' for x,y in sorted(self.blocked))])
        self.status.set('CSV 저장 완료: '+path)


def self_test():
    assert solve('BFS', set())['length'] == 18
    assert solve('Dijkstra', set())['length'] == 18
    assert solve('A*', set())['length'] == 18
    blocked = {(9, c) for c in range(1, 18)}
    for name in COLORS:
        result = solve(name, blocked)
        assert result['path'] and result['path'][0] == START and result['path'][-1] == GOAL
        for a, b in zip(result['path'], result['path'][1:]):
            assert abs(a[0]-b[0])+abs(a[1]-b[1]) == 1 and b not in blocked
    assert solve('BFS', blocked)['length'] == solve('Dijkstra', blocked)['length'] == solve('A*', blocked)['length']


if __name__ == '__main__':
    import sys
    if '--test' in sys.argv:
        self_test()
        print('Algorithm tests passed.')
    else:
        root = tk.Tk()
        Pathfinder(root)
        root.mainloop()
