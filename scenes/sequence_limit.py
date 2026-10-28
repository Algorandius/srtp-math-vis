# -*- coding: utf-8 -*-
"""
概念动画：数列极限的 ε-N 定义

教学意图：
    让学生理解 ε 与 N 的依赖关系——ε 每缩小一次，N 被迫右移一次；
    且一旦越过 N，后续所有项永不出界。

结构（基准时长约 10.5 分钟）：
    ch00 片头          ch05 ε 带            ch10 反例 (-1)^n
    ch01 直觉          ch06 门              ch11 N 不唯一
    ch02 青蛙游戏      ch07 ε 缩小核心     ch11b 定义的三句话
    ch03 坐标系        ch08 通式            ch12 ε-N 定义
    ch04 逐项展开      ch09 振荡数列

镜头策略（全片统一）：
    采用「分度值动态变化 + 镜头跟随」而非「直接拉近」：
    镜头只做"跟随焦点推拉 + 平移"，横轴的数据范围与分度值随焦点动态变化
    （焦点右移 → 横轴拉长、分度值增大；镜头推近 → 分度值变细），
    使坐标轴分度始终合理、可见区域恒有 6~8 个分度。
    文字大小恒定：字幕 / 角标 / 公式类用 updater 固定在画面上；
    门与 ε 的标注按目标镜头缩放预补偿（创建时先除以缩放），
    因此镜头拉近时"只缩放图形，不放大文字"，也不会出现文字超出屏幕。

节奏总控（在文件顶部）：
    MOTION —— 所有动画 run_time 的倍率
    PAUSE  —— 所有 self.wait 的倍率

视觉规范（全片统一，禁止一帧内出现两种语义的同色）：
    C_TERM 橙 = 数列项
    C_EPS  绿 = 极限位置与 ε 带
    C_FAIL 红 = 不合格的项（在带外）
    C_N    蓝 = N 与 n 轴
    C_DIM 灰 = 已淡出、当前不关心的项
    FROG_A / FROG_B = 第 2 章两只青蛙的道具色（该章无 N，不冲突）

注意：Text 字幕中避免使用下标/上标字符（字体可能不渲染），
      数学符号一律交给 MathTex（走 LaTeX）。
"""
import re

from manim import *

# ══════════════════════════════════════════════════════════
# 节奏总控：全片想快/想慢，只改这两个数（1.0 = 各章基准值）
# ══════════════════════════════════════════════════════════
MOTION = 0.75   # 所有动画 run_time 的倍率
PAUSE = 0.75    # 所有 self.wait 的倍率

# ══════════════════════════════════════════════════════════
# 视觉规范
# ══════════════════════════════════════════════════════════
C_TERM = ORANGE
C_EPS = GREEN
C_FAIL = RED
C_N = BLUE
C_DIM = GREY_B
FROG_A = BLUE       # 青蛙 A（第 2 章道具）
FROG_B = PURPLE     # 青蛙 B（第 2 章道具）
FONT = "Microsoft YaHei"

MAX_N = 30                  # 主视图横轴上界（收到 0~30，点才铺得开）
X_LEN = 12.0                # 横轴长度（拉长）
Y_LEN = 5.5                 # 纵轴长度（拉长）
AXES_BUFF = 1.25            # 坐标轴距画面底边距离（给大括号 / all n > N 留边距）
X_STEP = 3                  # 横轴分度：取 3，则点间距 1 = 恰好 1/3 个刻度间距
GATE_LEN = 5.5              # 门（N 蓝线）的固定长度（世界单位），不随放大变化
Y_LO, Y_HI, Y_STEP = -1.2, 1.2, 0.6   # 纵轴范围与分度
TARGET_A = 3

# 分度值 / 横轴上界的"整齐数"候选，供 plan_view 挑选
NICE_STEPS = [1, 2, 4, 5, 8, 10, 20, 40, 50, 100, 200, 400, 500,
              1000, 2000, 4000, 5000, 10000, 20000]
NICE_XMAX = [80, 100, 150, 200, 400, 500, 1000, 2000, 5000,
             10000, 15000, 20000, 50000]


def a(n):
    return 1.0 / n


def a_alt(n):
    """振荡数列：(-1)^n / n，上下摆动但幅度趋于 0"""
    return (-1) ** n / n


def a_pm(n):
    """反例数列：(-1)^n，永远在 ±1 之间跳"""
    return float((-1) ** n)


def sample_ns(x_max, step, skip=()):
    """按「每 1/3 个刻度一个点」取样：stride = 分度 / 3，
    点从第一个刻度右侧 1/3 刻度处开始，等距铺满整条横轴。"""
    stride = max(step // 3, 1)
    return [n for n in range(stride, x_max, stride) if n not in skip]


# 主视图取样点：X_STEP = 3 → 点间距 1 = 1/3 刻度间距，首点在 n = 1（第一个刻度右侧 1/3 处）
SEQ_NS = sample_ns(MAX_N, X_STEP)


def nice_step(target):
    """取不小于 target 的整齐分度值"""
    for s in NICE_STEPS:
        if s >= target:
            return s
    return NICE_STEPS[-1]


def nice_xmax(target):
    """取不小于 target 的整齐横轴上界"""
    for v in NICE_XMAX:
        if v >= target:
            return v
    return NICE_XMAX[-1]


def plan_view(focus_n, zoom=None):
    """按焦点规划横轴：焦点在主视图范围内就保持 0~MAX_N（点分布不动），
    超出时才按焦点拉长横轴；分度值取横轴约 1/10 且为 3 的倍数，
    使刻度数恒约 10 条、点间距恒为 1/3 刻度（zoom 仅保留旧调用签名）。"""
    if focus_n <= MAX_N * 0.85:
        x_max = MAX_N
    else:
        x_max = max(MAX_N, nice_xmax(focus_n * 1.4))
    return x_max, max(X_STEP, 3 * nice_step(x_max / 30))


# ══════════════════════════════════════════════════════════
# 组件构建（可复用的视觉零件）
# ══════════════════════════════════════════════════════════

def build_axes(x_range=None, y_range=None, x_length=X_LEN, y_length=Y_LEN):
    """坐标系；x_range / y_range 缺省用主视图的 [0, MAX_N] × [Y_LO, Y_HI]"""
    axes = Axes(
        x_range=[0, MAX_N, X_STEP] if x_range is None else x_range,
        y_range=[Y_LO, Y_HI, Y_STEP] if y_range is None else y_range,
        x_length=x_length,
        y_length=y_length,
        color=C_N,
        stroke_width=2,
    )
    axes.to_edge(DOWN, buff=AXES_BUFF)
    return axes


def lollipop(axes, n, seq=a):
    """棒棒糖式画项：点 + 垂直茎线到 n 轴。茎线长度就是该项的误差。"""
    y = seq(n)
    d = Dot(axes.c2p(n, y), color=C_TERM, radius=0.055)
    stem = Line(axes.c2p(n, 0), axes.c2p(n, y),
                color=C_TERM, stroke_width=2.2)
    return VGroup(stem, d)


def eps_band(axes, eps, x_max=MAX_N):
    """ε 带：上下虚线边界 + 半透明填充（对称于 0）"""
    left = axes.c2p(0, -eps)
    right = axes.c2p(x_max, eps)
    rect = Rectangle(
        width=right[0] - left[0],
        height=right[1] - left[1],
        fill_color=C_EPS, fill_opacity=0.13, stroke_width=0,
    )
    rect.move_to(axes.c2p(x_max / 2, 0))
    top = DashedLine(axes.c2p(0, eps), axes.c2p(x_max, eps),
                     color=C_EPS, stroke_width=1.8, dash_length=0.14)
    bot = DashedLine(axes.c2p(0, -eps), axes.c2p(x_max, -eps),
                     color=C_EPS, stroke_width=1.8, dash_length=0.14)
    return VGroup(rect, top, bot)


def eps_labels(axes, eps, x=None, x_max=MAX_N):
    """ε 标注；x 给定则贴该数据横坐标放（放大坐标系后改放到门边，避免出画）。
    标注尺寸固定，不随坐标轴缩放变化。"""
    # 默认放在轴右端略微靠里的位置，避免与横轴末端的 "n" 标签重合
    x = max(x_max - 2, 0) if x is None else x
    up = MathTex(f"+{eps}", color=C_EPS).scale(0.6)
    dn = MathTex(f"-{eps}", color=C_EPS).scale(0.6)
    up.next_to(axes.c2p(x, eps), UP, buff=0.05)
    dn.next_to(axes.c2p(x, -eps), DOWN, buff=0.05)
    return VGroup(up, dn)


def gate(axes, N, y_lo=Y_LO, y_hi=Y_HI, x_max=MAX_N, brace_dy=None,
         label_y=None, brace=True):
    """门：蓝色竖线 + N 标注 + 底部大括号。
    竖线长度固定为 GATE_LEN（以 x 轴为中心上下对称），坐标系放大时不再变长；
    N 标注字号适中、贴在竖线顶端上方，避免与竖线及其他元素重叠。
    brace=False 时只画竖线与标注（底部改由引导箭头表达）。"""
    foot = axes.c2p(N, 0)
    line = Line(foot + DOWN * (GATE_LEN / 2), foot + UP * (GATE_LEN / 2),
                color=C_N, stroke_width=2.5)
    lab = MathTex(f"N={N}", color=C_N).scale(0.6)
    lab.next_to(line.get_top(), UP, buff=0.1)
    if N <= 5:
        lab.shift(RIGHT * 0.45)         # 靠左的门，标签右移避开 y 轴 a_n

    if not brace:
        return VGroup(line, lab)

    if brace_dy is None:
        brace_dy = (y_hi - y_lo) * 0.02     # 按量程取 2%，量程收窄后仍贴着轴底
    seg = Line(axes.c2p(N, y_lo + brace_dy), axes.c2p(x_max, y_lo + brace_dy))
    brace = Brace(seg, direction=DOWN, color=C_N)
    btext = Text("all n > N", font=FONT, color=C_N).scale(0.5)
    brace.put_at_tip(btext)
    return VGroup(line, lab, brace, btext)


CJK_RE = re.compile(r"[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]")
# 字幕里的数学片段做规范化：下标交给 LaTeX、除号换成分数线
MATH_FIX = [
    ("(-1)^n/n", r"\frac{(-1)^n}{n}"),
    ("1/n", r"\frac{1}{n}"),
    ("1/ε", r"\frac{1}{\varepsilon}"),
    ("1/\\varepsilon", r"\frac{1}{\varepsilon}"),
    ("ε", r"\varepsilon"),
    ("±", r"\pm"),
    ("×", r"\times"),
    ("~", r"\sim"),
    ("→", r"\to"),
    ("≥", r"\geq"),
    ("≤", r"\leq"),
    ("≠", r"\neq"),
]


_TEXT_METRICS = {}


def _text_metrics():
    """量一次「汉字字面高度」与「数学大写字母高度」（scale=1），供混排换算。
    两者都取自同一套 manim 单位，因此换算结果与输出分辨率无关。"""
    if not _TEXT_METRICS:
        _TEXT_METRICS["cn"] = Text("国", font=FONT).height
        _TEXT_METRICS["cap"] = MathTex(r"\mathrm{N}").height
    return _TEXT_METRICS


def _math_expr(s):
    """把字幕里的数学片段转成 LaTeX（下标交给 LaTeX、除号换成分数线）。
    先统一去掉除号两侧的空格，`(-1)^n / n` 与 `(-1)^n/n` 才会走同一条规则。"""
    s = re.sub(r"\s*/\s*", "/", s)
    for old, new in MATH_FIX:
        s = s.replace(old, new)
    return s


def rich_text(text, color=WHITE, scale=0.5, math_ratio=0.92, buff=0.08):
    """把一句字幕拆成「中文 → Text」「数学 → MathTex」两类片段拼起来。

    - 数学片段按实测字高归一化：大写字母高 = 0.92 × 汉字字面高，
      因此两者视觉大小一致（不再用经验系数，换字号 / 换环境都成立）；
    - 垂直方向按基线对齐：汉字底边为基线，数学片段去掉分数线 / 下标
      带来的下伸量后再对齐，避免上下错位；
    - 全部使用世界坐标单位，与渲染分辨率无关。"""
    chunks, buf, buf_cjk = [], "", None
    for ch in text:
        is_cjk = bool(CJK_RE.match(ch))
        if ch == " " and buf_cjk is not None:
            is_cjk = buf_cjk                 # 空格跟随当前片段
        if buf_cjk is None or is_cjk == buf_cjk:
            buf, buf_cjk = buf + ch, is_cjk
        else:
            chunks.append((buf, buf_cjk))
            buf, buf_cjk = ch, is_cjk
    if buf:
        chunks.append((buf, buf_cjk))

    metrics = _text_metrics()
    s_math = scale * math_ratio * metrics["cn"] / metrics["cap"]
    cap_h = metrics["cap"] * s_math

    items = []
    for s, is_cjk in chunks:
        if is_cjk:
            mob, depth = Text(s, font=FONT, color=color).scale(scale), 0.0
        else:
            try:
                mob = MathTex(_math_expr(s), color=color).scale(s_math)
            except Exception:
                mob, depth = Text(s, font=FONT, color=color).scale(scale), 0.0
            else:
                # 分数线 / 上下标会让片段底部低于基线，扣掉下伸量再对齐
                depth = max(0.0, (mob.height - cap_h) / 2)
        items.append((mob, depth))

    group = VGroup(*[mob for mob, _ in items])
    cursor = 0.0
    for mob, depth in items:
        mob.move_to(ORIGIN)
        mob.shift(UP * (-depth - mob.get_bottom()[1]))   # 底边对齐到基线
        mob.shift(RIGHT * (cursor + mob.width / 2))
        cursor += mob.width + buff
    group.move_to(ORIGIN)
    return group


def band_piece(axes, eps, x_lo, x_hi):
    """ε 带在 [x_lo, x_hi] 区间的单独一小块（用于闪烁强调门后的带）"""
    left, right = axes.c2p(x_lo, -eps), axes.c2p(x_hi, eps)
    rect = Rectangle(width=right[0] - left[0], height=right[1] - left[1],
                     fill_color=C_EPS, fill_opacity=0.4, stroke_width=0)
    rect.move_to(np.array([(left[0] + right[0]) / 2,
                           (left[1] + right[1]) / 2, 0.0]))
    top = Line(axes.c2p(x_lo, eps), axes.c2p(x_hi, eps),
               color=C_EPS, stroke_width=2.5)
    bot = Line(axes.c2p(x_lo, -eps), axes.c2p(x_hi, -eps),
               color=C_EPS, stroke_width=2.5)
    return VGroup(rect, top, bot)


def frog(color):
    """简笔青蛙：椭圆身体 + 两只眼睛（第 2 章道具）"""
    body = Ellipse(width=1.2, height=0.95, color=color,
                   fill_color=color, fill_opacity=0.85, stroke_width=2)
    eye_l = Circle(radius=0.17, color=WHITE, fill_color=WHITE,
                   fill_opacity=1, stroke_width=1.5)
    eye_r = eye_l.copy()
    eye_l.move_to(body.get_top() + LEFT * 0.3 + UP * 0.02)
    eye_r.move_to(body.get_top() + RIGHT * 0.3 + UP * 0.02)
    pup_l = Dot(eye_l.get_center() + UP * 0.04, radius=0.06, color=BLACK)
    pup_r = Dot(eye_r.get_center() + UP * 0.04, radius=0.06, color=BLACK)
    return VGroup(body, eye_l, eye_r, pup_l, pup_r)


def speech_bubble(text, color):
    """对话气泡：圆角框 + 文字 + 朝下的小尾巴（指向青蛙）"""
    txt = Text(text, font=FONT, color=WHITE).scale(0.42)
    box = RoundedRectangle(
        width=txt.width + 0.9, height=txt.height + 0.6, corner_radius=0.22,
        color=color, fill_color=BLACK, fill_opacity=0.85, stroke_width=2.2,
    )
    box.move_to(txt)
    tail = Triangle(fill_color=BLACK, fill_opacity=0.85, color=color,
                    stroke_width=2.2).scale(0.2)
    tail.rotate(PI)                       # 尖端朝下
    tail.move_to(box.get_bottom() + DOWN * 0.1)
    return VGroup(box, txt, tail)


# ══════════════════════════════════════════════════════════
# 主场景
# ══════════════════════════════════════════════════════════

class SequenceLimit(MovingCameraScene):

    # ---------------- 节奏总控 ----------------
    def play(self, *args, **kwargs):
        """所有动画统一乘 MOTION 倍率；不足一帧的按一帧算（否则 manim 会警告）。
        注意：Scene.wait() 内部是 self.play(Wait(run_time=d))，而 play 的
        run_time 关键字会被强制写给每个动画，所以停顿必须绕开这里，
        否则所有 pause 都会被压成 MOTION 秒。"""
        if not getattr(self, "_in_wait", False):
            rt = kwargs.get("run_time", 1.0) * MOTION
            kwargs["run_time"] = max(rt, 1.0 / config.frame_rate)
        super().play(*args, **kwargs)

    def wait(self, duration=1.0, **kwargs):
        """所有停顿统一乘 PAUSE 倍率（绕开 play 的 MOTION 倍率）"""
        self._in_wait = True
        try:
            super().wait(duration * PAUSE, **kwargs)
        finally:
            self._in_wait = False

    # ---------------- 镜头 ----------------
    def cam_anim(self, center):
        """镜头只平移、不缩放：返回把镜头移到 center（世界坐标）的动画。
        放大效果改由『放大坐标系本身』实现（见 apply_view），
        这样字幕 / 刻度线 / ε 标注 / N 标注都不会被放大。"""
        return self.camera.frame.animate.move_to(center)

    def fix_scale(self, mob):
        """让 mob 的屏幕大小不随镜头推拉变化（位置仍跟随世界坐标）。
        镜头推拉是渲染期变换、不会改 mobject 的 width，必须按镜头缩放做
        增量补偿：世界缩放设为 s，屏幕大小才恒定；只能对单个 mobject 调用
        （对 VGroup 缩放会破坏内部相对位置）。"""
        frame = self.camera.frame
        state = {"f": 1.0}

        def keep(m):
            s = frame.width / config.frame_width
            target = s if s > 1e-6 else 1.0
            m.scale(target / state["f"])
            state["f"] = target

        mob.add_updater(keep)
        return mob

    def fix_in_frame(self, mob):
        """固定在画面上：位置与大小都不随镜头变化（字幕 / 角标 / 公式）。
        pos 记录的是「相对画面中心」的位置，因此镜头已经平移过之后再挂也正确；
        必须对单个 mobject 调用。"""
        frame = self.camera.frame
        pos = (mob.get_center() - frame.get_center()).copy()
        state = {"f": 1.0}

        def keep(m):
            s = frame.width / config.frame_width
            target = s if s > 1e-6 else 1.0
            m.scale(target / state["f"])
            state["f"] = target
            m.move_to(frame.get_center() + pos * s)

        mob.add_updater(keep)
        return mob

    # ---------------- 通用工具 ----------------
    # 常驻舞台的物件，换场景前由 clear_stage 统一淡出（并把镜头复位）
    STAGE_ATTRS = ("axes", "axis_labels", "axis_nums", "corner", "band",
                   "eps_labs", "gate", "formulas")

    def clear_stage(self, run_time=2.5):
        """清理当前舞台上的常驻物件（公式用 Unwrite 退场），并把镜头复位"""
        formulas = getattr(self, "formulas", None)
        mobs = []
        for name in self.STAGE_ATTRS:
            mob = getattr(self, name, None)
            if mob is not None and mob is not formulas:
                mobs.append(mob)
            setattr(self, name, None)
        for _, m in getattr(self, "terms", []):
            mobs.append(m)
        self.terms = []
        self.failed = set()
        self.passed = set()

        anims = [FadeOut(m) for m in mobs]
        if formulas is not None:
            anims.append(Unwrite(formulas))     # 公式退场用 unwrite
        frame = self.camera.frame
        if (abs(frame.width - config.frame_width) > 1e-6
                or np.linalg.norm(frame.get_center()) > 1e-6):
            anims.append(frame.animate
                         .scale(config.frame_width / frame.width)
                         .move_to(ORIGIN))
        if anims:
            self.play(*anims, run_time=run_time)

    def fix_top_center(self, mob):
        """把 mob 钉在屏幕正上方居中：横向跟随镜头中心线，纵向固定在顶部。
        与镜头是否缩放无关，因此字幕不会随放大左右偏移。"""
        frame = self.camera.frame
        y = mob.get_center()[1]

        def keep(m):
            c = frame.get_center()
            m.move_to(np.array([c[0], y, 0.0]))

        mob.add_updater(keep)
        return mob

    def caption(self, text, write_time=2.0):
        """顶部字幕：换字幕前先淡出旧的。
        中文段用 Text、数学段用 MathTex（a_n 走下标、1/n 走分数），
        字幕始终固定在屏幕正上方居中；updater 在 Write 之前就挂上，
        否则写入过程中它会停在以世界原点为中心的位置（放大/平移后看起来
        先偏到一侧、写完又跳回中间，形成闪现）。"""
        new = rich_text(text).to_edge(UP, buff=0.28)
        cam_x = self.camera.frame.get_center()[0]
        new.move_to(np.array([cam_x, new.get_center()[1], 0.0]))
        self.fix_top_center(new)
        old = getattr(self, "_cap", None)
        if old is None:
            self.play(Write(new), run_time=write_time)
        else:
            self.play(Unwrite(old), run_time=0.8)   # 字幕退场统一用 unwrite
            self.play(Write(new), run_time=write_time)
        self._cap = new
        return new

    def fade(self, *mobs, run_time=2.0):
        self.play(*[FadeOut(m) for m in mobs], run_time=run_time)

    def mark_fail(self, eps):
        """把所有画出的项中，误差 >= eps 的标红（标过红的不会褪回）。
        同时记下这些 n，供 apply_view 重建项时保留红色。"""
        seq = getattr(self, "seq", a)
        failed = self.failed
        anims = []
        for n, mob in self.terms:
            if n in self.passed:
                continue                 # 已按 N 分到右侧（黄色）的，不再被判红
            if abs(seq(n)) >= eps - 1e-12:
                anims.append(mob.animate.set_color(C_FAIL))
                failed.add(n)
        if anims:
            self.play(*anims, run_time=3.5)

    def add_terms(self, seq, ns, run_time=0.6, gap=0.0):
        """追加画若干项（保留已有项），结果并入 self.terms 供 mark_fail 使用"""
        drawn = []
        for n in ns:
            m = lollipop(self.axes, n, seq)
            drawn.append((n, m))
            self.play(Create(m), run_time=run_time)
            if gap:
                self.wait(gap)
        self.terms.extend(drawn)
        return drawn

    def draw_terms(self, seq, ns, run_time=0.6, gap=0.0):
        """逐项画棒棒糖（替换 self.terms）。
        前 5 个慢速生成（看清“一项一个数”），其余快速带出，避免整体耗时过长。"""
        self.terms = []
        self.failed = set()
        self.passed = set()
        ns = list(ns)
        head, tail = ns[:5], ns[5:]
        if head:
            self.add_terms(seq, head, max(run_time, 0.55), gap)
        if tail:
            self.add_terms(seq, tail, min(run_time, 0.12))
        return self.terms

    def drop_terms(self, ns):
        """把指定项淡出并从 self.terms 移除（不再需要时调用，禁止残留）"""
        gone = [(n, m) for n, m in self.terms if n in ns]
        if gone:
            self.fade(*[m for _, m in gone])
        self.terms = [(n, m) for n, m in self.terms if n not in ns]

    def axis_numbers(self, axes=None, every=2):
        """横轴刻度数字：每 every 个刻度标一个数，密度适中；
        横轴拉长时分度值同步变大，数字个数保持稳定。"""
        axes = self.axes if axes is None else axes
        interval = axes.x_range[2] * every
        vals, x = [], 0.0
        while x <= axes.x_range[1] + 1e-9:
            vals.append(x)
            x += interval
        vals = [v for v in vals if abs(v) > 1e-9]   # 不标 0
        if vals:
            vals = vals[:-1]                        # 不标最靠近轴尾的那个
        nums = VGroup()
        for v in vals:
            t = Text(f"{int(round(v))}", font=FONT, color=WHITE).scale(0.4)
            t.next_to(axes.c2p(v, 0), DOWN, buff=0.16)
            nums.add(t)
        return nums

    def blink_gate(self, times=3, out_time=0.6, in_time=0.6, gap=0.4):
        """门（蓝线 + N 标注）停稳后闪烁：先消失再出现，重复 times 次。"""
        if self.gate is None:
            return
        part = VGroup(self.gate[0], self.gate[1])
        for _ in range(times):
            self.play(FadeOut(part), run_time=out_time)
            self.play(FadeIn(part), run_time=in_time)
            self.wait(gap)

    def blink_band_right(self, times=2, out_time=0.9, in_time=0.9, gap=1.0):
        """门闪烁后，让 N 线右侧那段绿带闪两次：先消失、再出现（间隔适中）。
        用与底色同色的遮罩实现，遮罩压在绿带之上、点与坐标轴之下，
        所以不会把绿带“加深”，也不会盖住点。"""
        if self.gate_n is None or getattr(self, "gate_eps", None) is None:
            return
        x_max = self.axes.x_range[1]
        left = self.axes.c2p(self.gate_n, -self.gate_eps)
        right = self.axes.c2p(x_max, self.gate_eps)
        mask = Rectangle(width=right[0] - left[0] + 0.06,
                         height=right[1] - left[1] + 0.06,
                         fill_color=BLACK, fill_opacity=1.0, stroke_width=0)
        mask.move_to(np.array([(left[0] + right[0]) / 2,
                               (left[1] + right[1]) / 2, 0.0]))
        self.band.set_z_index(-2)
        mask.set_z_index(-1)
        for _ in range(times):
            self.play(FadeIn(mask), run_time=out_time)    # 右侧绿带消失
            self.play(FadeOut(mask), run_time=in_time)    # 再出现
            self.wait(gap)

    def mark_sides(self, N=None, run_time=2.5):
        """N 线左侧（n ≤ N）的点一律红、右侧（n > N）的点一律黄。
        以当前 N 为准重新判色（例如 N=25 之后回到 N=20 时，
        原来偏红的那一段必须重新变黄），不做单向累积。"""
        N = self.gate_n if N is None else N
        if N is None:
            return
        anims = []
        for n, mob in self.terms:
            if n <= N:
                if n in self.failed:
                    continue
                self.failed.add(n)
                self.passed.discard(n)
                anims.append(mob.animate.set_color(C_FAIL))
            else:
                if n in self.passed:
                    continue
                self.passed.add(n)
                self.failed.discard(n)
                anims.append(mob.animate.set_color(YELLOW))
        if anims:
            self.play(*anims, run_time=run_time)

    def draw_band(self, eps, x_max=MAX_N, run_time=3.0):
        """平滑绘制 ε 带：色块自左向右展开，上下虚线段同步逐段长出，
        最终与坐标轴对齐；随后淡入 ±ε 标注。"""
        axes = self.axes
        top = DashedLine(axes.c2p(0, eps), axes.c2p(x_max, eps),
                         color=C_EPS, stroke_width=1.8, dash_length=0.14)
        bot = DashedLine(axes.c2p(0, -eps), axes.c2p(x_max, -eps),
                         color=C_EPS, stroke_width=1.8, dash_length=0.14)
        self.add(top, bot)
        # 虚线先缩成一个点，稍后自左向右逐段长出
        jobs = []
        for line in (top, bot):
            for d in line.submobjects:
                left, w = d.get_left(), d.width
                d.stretch_to_fit_width(0.001, about_point=left)
                jobs.append((d, left, w))
        jobs.sort(key=lambda j: j[1][0])      # 按横坐标排序，上下两段交替推进
        # 色块自左端展开
        left_pt, right_pt = axes.c2p(0, -eps), axes.c2p(x_max, eps)
        rect = Rectangle(width=right_pt[0] - left_pt[0],
                         height=right_pt[1] - left_pt[1],
                         fill_color=C_EPS, fill_opacity=0.13, stroke_width=0)
        rect.move_to(axes.c2p(x_max / 2, 0))
        anchor = axes.c2p(0, 0)
        rect.stretch_to_fit_width(0.001, about_point=anchor)
        self.add(rect)
        n_dash = max(len(jobs), 1)
        self.play(
            rect.animate.stretch_to_fit_width(right_pt[0] - anchor[0],
                                              about_point=anchor),
            LaggedStart(*[d.animate(run_time=run_time / n_dash * 1.2)
                          .stretch_to_fit_width(w, about_point=lp)
                          for d, lp, w in jobs],
                        lag_ratio=1.0),
            run_time=run_time,
        )
        self.band = VGroup(rect, top, bot)
        labs = eps_labels(self.axes, eps, x_max=x_max)
        self.play(Write(labs), run_time=1.5)
        self.eps_labs = labs
        return self.band

    def apply_view(self, x_max, x_step, eps=None, N=None, zoom=None,
                   cam_y=0.0, lab_x=None, label_y=None, run_time=3.0,
                   extra_anims=(), new_ns=(), y_zoom=None, brace=True):
        """统一视角策略：放大的是『坐标系本身』而不是镜头。

        zoom 在这里是放大倍率：坐标轴及其上的项 / 色带 / 门按 1/zoom 变长，
        数据原点 (0,0) 位置保持不变；镜头只平移到 N 处跟随，不做缩放。
        因此刻度线、±ε 标注、N 标注、字幕都保持原始大小、不被放大。"""
        # 放大坐标系时，横轴右端的 "n" 会离开轴线残留在屏幕里，直接淡出
        if zoom is not None and self.axis_labels is not None \
                and len(self.axis_labels) > 0:
            x_lab = self.axis_labels[0]
            self.play(FadeOut(x_lab), run_time=0.6)
            self.axis_labels.remove(x_lab)

        old = self.axes
        y_lo, y_hi, y_step = self.y_range
        z = 1.0 if zoom is None else zoom
        yz = z if y_zoom is None else y_zoom   # 竖向放大可与横向不同
        new_axes = Axes(
            x_range=[0, x_max, x_step],
            y_range=[y_lo, y_hi, y_step],
            x_length=X_LEN / z, y_length=Y_LEN / yz,
            color=C_N, stroke_width=2,
        )
        # 锚定数据原点，让坐标轴从原位置向右上方伸展开
        new_axes.shift(old.c2p(0, 0) - new_axes.c2p(0, 0))

        # 色带与门的括号都要铺到新横轴右端，不能拿门的位置 N 当右端
        # （否则色带只剩 0~N 一小段，括号退化成 N→N 的零长度线段而消失）
        anims = [ReplacementTransform(old, new_axes)]
        if eps is not None:
            if self.band is not None:
                anims.append(Transform(self.band,
                                       eps_band(new_axes, eps,
                                                x_max=x_max)))
            if self.eps_labs is not None:
                anims.append(Transform(
                    self.eps_labs,
                    eps_labels(new_axes, eps, x=lab_x, x_max=x_max)))
        # 门可能在大括号 / 箭头两种结构间切换，必须用 ReplacementTransform
        # （Transform 要求两端结构一致，否则残留退化图形）
        new_gate = None
        if N is not None and self.gate is not None:
            new_gate = gate(new_axes, N, y_lo=y_lo, y_hi=y_hi, x_max=x_max,
                            label_y=label_y, brace=brace)
            anims.append(ReplacementTransform(self.gate, new_gate))
        if getattr(self, "axis_nums", None) is not None:
            anims.append(Transform(self.axis_nums,
                                   self.axis_numbers(new_axes)))
        # 项按新坐标轴重建（长度 / 间距随之放大），已标红的重建后仍是红色。
        # 用 ReplacementTransform：茎线两端各自对齐，不会在插值时甩到别处。
        # 同时把 self.terms 换成新对象——否则列表里仍留着已被移出场景的旧对象，
        # 下一轮动画会把它重新加回画面，看起来就是“残留的点”。
        rebuilt = []
        for n, mob in self.terms:
            target = lollipop(new_axes, n, self.seq)
            if n in self.failed:
                target.set_color(C_FAIL)
            anims.append(ReplacementTransform(mob, target))
            rebuilt.append((n, target))
        # 新补的项直接建在新坐标轴上、只播 Create（不能同时再 Transform，
        # 否则同一 mobject 挂两个动画，Create 会把它留在旧位置）
        new_terms = [(n, lollipop(new_axes, n, self.seq)) for n in new_ns]
        anims.extend(Create(m) for _, m in new_terms)
        if N is not None or zoom is not None:
            # 镜头只平移到 N（横向跟随），纵向保持在 x 轴高度，避免内容被推出画面
            anims.append(self.cam_anim(new_axes.c2p(N or 0, 0)))
        self.play(*anims, *extra_anims, run_time=run_time)
        self.terms = rebuilt + new_terms
        if new_gate is not None:
            self.gate = new_gate
        if N is not None:
            self.gate_n = N
        if eps is not None:
            self.gate_eps = eps
        self.axes = new_axes

    # ---------------- 章 0：片头 ----------------
    def ch00_title(self):
        title = Text("数列极限的 ε-N 定义", font=FONT).scale(0.85)
        sub = Text("ε 每缩小一次，N 就被迫往右挪一次",
                   font=FONT, color=GREY).scale(0.45)
        sub.next_to(title, DOWN, buff=0.45)
        self.play(Write(title), run_time=2.5)
        self.play(Write(sub), run_time=1.5)
        self.wait(3.0)
        self.play(FadeOut(title), FadeOut(sub), run_time=1.5)

    # ---------------- 章 1：直觉 ----------------
    def ch01_intuition(self):
        self.caption("首先，当我们发现 1/n 越来越大……", write_time=2.0)
        nl = NumberLine(x_range=[0, 1, 0.25], length=12.0,
                        include_numbers=True, font_size=26,
                        label_direction=DOWN).shift(DOWN * 0.8)
        zmark = Dot(nl.n2p(0), color=C_EPS, radius=0.08)
        self.play(Create(nl), FadeIn(zmark), run_time=2.5)

        dots, labs = [], []
        for v in [1, 0.5, 0.333, 0.1, 0.01]:
            nd = Dot(nl.n2p(v), color=C_TERM, radius=0.09)
            lab = Text(f"{v}", font=FONT, color=C_TERM).scale(0.38)
            lab.next_to(nd, UP, buff=0.18)
            self.play(FadeIn(nd, scale=0.6), Write(lab), run_time=1.5)
            dots.append(nd)
            labs.append(lab)
            self.wait(1.2)

        self.caption("……看起来越来越接近 0。但这严谨吗？", write_time=2.0)
        self.wait(10.0)
        # 全部橙色点与数值标注一并淡出，禁止残留到后续章节
        self.fade(nl, zmark, *dots, *labs)

    # ---------------- 章 2：青蛙游戏 ----------------
    def ch02_frog_game(self):
        self.caption("我们更该考量的是「距离」。先从一个游戏说起", write_time=2.0)
        # 数轴置于画面中间偏上
        nl = NumberLine(x_range=[0, 4, 0.5], length=7.5).shift(UP * 1.0)
        tdot = Dot(nl.n2p(TARGET_A), color=C_EPS, radius=0.09)
        tlab = Text(f"目标 {TARGET_A}", font=FONT, color=C_EPS).scale(0.45)
        tlab.next_to(tdot, UP, buff=0.45)
        self.play(Create(nl), FadeIn(tdot), Write(tlab), run_time=2.5)

        # 左右两只青蛙，报数改成对话形式
        frogA = frog(FROG_A).move_to(LEFT * 5.3 + DOWN * 1.1)
        frogB = frog(FROG_B).move_to(RIGHT * 5.3 + DOWN * 1.1)
        tagA = Text("青蛙 A", font=FONT, color=FROG_A).scale(0.4)
        tagB = Text("青蛙 B", font=FONT, color=FROG_B).scale(0.4)
        tagA.next_to(frogA, DOWN, buff=0.25)
        tagB.next_to(frogB, DOWN, buff=0.25)
        self.play(FadeIn(frogA, scale=0.7), FadeIn(frogB, scale=0.7),
                  Write(tagA), Write(tagB), run_time=2.0)

        guesses = [(2, FROG_A, "我猜 2，误差 1"),
                   (2.5, FROG_B, "我猜 2.5，误差 0.5"),
                   (2.9, FROG_A, "2.9！误差 0.1"),
                   (2.95, FROG_B, "2.95！误差 0.05")]
        bubble, dots = None, []
        for v, color, line in guesses:
            d = Dot(nl.n2p(v), color=C_TERM, radius=0.075)
            b = speech_bubble(line, color)
            anchor = frogA if color == FROG_A else frogB
            b.next_to(anchor, UP, buff=0.3)
            anims = [FadeIn(d, scale=0.6), FadeIn(b, scale=0.85)]
            if bubble is not None:
                anims.append(FadeOut(bubble))       # 上一句对话退场
            self.play(*anims, run_time=1.8)
            bubble = b
            dots.append(d)
            self.wait(1.2)

        # 对话结束：先收起最后一只青蛙的气泡，再做误差回顾
        if bubble is not None:
            self.fade(bubble)

        errline = MathTex(r"1 \to 0.5 \to 0.1 \to 0.05 \to \cdots \to 0",
                          color=C_TERM).scale(0.6)
        errline.to_edge(UP, buff=1.5)
        self.play(Write(errline), run_time=2.0)
        self.wait(3.0)

        self.caption("一轮轮报下去，没完没了：越来越近，误差越来越小",
                     write_time=2.0)
        self.wait(8.0)
        # 青蛙、气泡、数轴、点全部清理，不带入下一章
        self.fade(nl, tdot, tlab, frogA, frogB, tagA, tagB, errline, *dots)

    # ---------------- 章 3：坐标系登场 ----------------
    def ch03_axes(self):
        self.caption("把游戏换成一个数列：a_n = 1/n，目标改成 0", write_time=2.0)
        self.axes = build_axes()
        self.y_range = [Y_LO, Y_HI, Y_STEP]
        labels = self.axes.get_axis_labels(x_label="n", y_label="a_n")
        corner = MathTex("a_n \\rightarrow 0 \\ ?", color=C_EPS).scale(0.7)
        corner.to_corner(UR, buff=0.6)
        self.play(Create(self.axes), Write(labels), Write(corner), run_time=4.0)
        for lab in labels:
            self.fix_scale(lab)       # 轴名逐个固定大小（不能对 VGroup 缩放）               # 轴名大小不随镜头变
        self.fix_in_frame(corner)            # 右上角问题固定在画面
        self.axis_labels = labels
        self.corner = corner
        self.wait(7.0)

    # ---------------- 章 4：逐项展开 ----------------
    def ch04_terms(self):
        self.caption("数列的每一项，就像青蛙报的一个数", write_time=2.0)
        # 前三项单独画，强调"一项一个数"
        self.draw_terms(a, [1, 2, 3], run_time=1.2, gap=0.8)
        # 其余项按 SEQ_NS 等距铺满整条横轴（点间距 = 1 个数据单位 = 1/3 个刻度）
        # 第 4、5 项仍慢速，之后的项快速带出
        tail = [n for n in SEQ_NS if n > 3]
        self.add_terms(a, tail[:2], run_time=0.55)
        self.add_terms(a, tail[2:], run_time=0.12)
        self.wait(4.0)
        self.caption("越往后，所有项都挤向 0", write_time=2.0)
        self.wait(6.0)
        # 前三项保留在画面上，直接进入第 5 章（不淡出、不重画，避免闪烁）

    # ---------------- 章 5：ε 带 ----------------
    def ch05_eps_band(self):
        self.caption("先定一个误差上限：比如 ε = 0.5", write_time=2.0)
        # 前三个点沿用第 4 章的，不再重画，保证过渡全程连续可见
        self.draw_band(0.5)                  # 平滑绘制：色块随虚线向右延伸
        self.mark_fail(0.5)                  # n = 1、2 在带外
        self.wait(5.0)
        self.caption("n = 1、2 掉出了带外", write_time=2.0)
        self.wait(5.0)

    # ---------------- 章 6：门 ----------------
    def ch06_gate(self):
        self.caption("从第几项起，后面全都合格？", write_time=2.0)
        g = gate(self.axes, 2)               # 标签自动右移，避开 y 轴 a_n
        self.play(Create(g), run_time=4.0)
        self.wait(4.0)
        self.caption("这个 N 就是一道门：门后必须全部合格", write_time=2.0)
        self.wait(7.0)
        self.caption("N = 2，就是能满足 ε = 0.5 的那道门", write_time=2.0)
        self.wait(6.0)
        self.gate = g

    # ---------------- 章 7：ε 缩小，N 右移 ----------------
    def ch07_shrink_eps(self):
        """
        ε 走 0.5 → 0.2 → 0.1 → 0.04 → 0.05(互动) → 0.01 六档。
        每档：带变窄、项标红、门右移；同时横轴分度值随镜头推近变细，
        镜头跟随门 N 平移；每放大一档补几个点提高密度。
        """
        self.caption("现在提高要求：如果 ε 变小，还能满足吗？", write_time=2.0)
        # 本章横轴加刻度数字（每 2 个刻度标一个数，密度适中），便于看出 N 在右移
        self.axis_nums = self.axis_numbers()
        self.play(FadeIn(self.axis_nums), run_time=1.5)

        # eps / N / 镜头缩放 / 焦点高度 / N标注高度 / ±ε标注横坐标 /
        # 补充的点 / 纵轴量程 / 竖向放大（后两项非空时启用"纵向单独放大"）
        # SEQ_NS 已覆盖 1~29 每个整数，各轮不再额外补点（补了会和已有点重合）
        rounds = [
            (0.2,  5,  0.55, 0.35, None,  7,  [], None, None,
             "ε = 0.2：第 1~5 项都在带外，门退到 N = 5"),
            (0.1,  10, 0.40, 0.30, 0.30,  13, [], None, None,
             "ε = 0.1：第 1~10 项不合格，门退到 N = 10"),
            (0.04, 25, 0.26, 0.22, 0.22,  28, [], (-0.08, 0.08, 0.02), 0.859,
             "ε = 0.04：第 20 项还在带外，门退到 N = 25"),
        ]
        for (eps, N, zoom, cam_y, label_y, lab_x, extra,
             y_rng, y_zoom, note) in rounds:
            if y_rng is not None:
                self.y_range = list(y_rng)
            x_max, x_step = plan_view(N, zoom)
            # 纵向放大的档位不画大括号，改在门闪烁后补引导箭头
            self.apply_view(x_max, x_step, eps=eps, N=N, zoom=zoom,
                            cam_y=cam_y, label_y=label_y, lab_x=lab_x,
                            run_time=7.0, new_ns=extra, y_zoom=y_zoom,
                            brace=(y_rng is None))
            self.blink_gate()             # 门停稳后闪三下（先消失再出现）
            if y_rng is not None:
                self.blink_band_right()   # 门后那段绿带闪两次
                self.mark_sides()          # N 左侧点变红、右侧点变黄
            self.mark_fail(eps)
            self.caption(note)
            self.wait(8.0)

        # ---- 互动节拍：轮到观众 ----
        self.caption("轮到你了：如果 ε = 0.05，N 至少是多少？", write_time=2.0)
        self.wait(10.0)
        self.caption("要让 1/n < 0.05，就要 n > 20，所以 N = 20", write_time=2.0)
        # 同样做纵向放大：量程收到 ±0.1，绿带占画面高度一半，100% 一眼看出谁在带内
        self.y_range = [-0.1, 0.1, 0.02]
        self.apply_view(MAX_N, X_STEP, eps=0.05, N=20, zoom=0.4, y_zoom=0.859,
                        cam_y=0.3, label_y=0.3, lab_x=23, run_time=6.0,
                        brace=False)
        self.blink_gate()
        self.blink_band_right()   # 门后那段绿带闪两次
        self.mark_sides()          # N 左侧点变红、右侧点变黄
        self.mark_fail(0.05)
        self.wait(4.0)

        # ---- ε = 0.01：门退到 N = 100，坐标系再放大一档，看清 100 之后全在带内 ----
        self.caption("ε = 0.01 呢？门要退到 N = 100，再放大一档看",
                     write_time=2.0)
        self.wait(3.0)
        # 横轴 0~150、分度 3 → 点间距 1 = 1/3 刻度；门前后每个整数补一个点（更密）。
        # 纵轴量程同时收到 ±0.02，让绿带占满画面高度的一半，
        # 100 之后的点明显躺在带里（竖向放大与横向解耦，可见的 n 范围仍是 ~20 个点）
        self.y_range = [-0.02, 0.02, 0.005]
        self.apply_view(150, 3, eps=0.01, N=100, zoom=0.112, y_zoom=0.859,
                        cam_y=0.02, label_y=0.02, lab_x=104, run_time=6.0,
                        new_ns=range(85, 118), brace=False)
        self.blink_gate()
        self.blink_band_right()   # 门后那段绿带闪两次
        self.mark_sides()          # N 左侧点变红、右侧点变黄
        self.mark_fail(0.01)          # n = 100 正好卡在带上，之后全部落入带内
        self.caption("n = 100 正好卡在带上，从 n = 101 起全部落进带内",
                     write_time=2.0)
        self.wait(8.0)

        self.clear_stage()
        self.caption("ε 每缩小一次，N 就被迫往右挪一次", write_time=2.0)
        self.wait(8.0)

    # ---------------- 章 8：通式 ----------------
    def ch08_formula_N(self):
        # 与第 7 章平滑衔接：居中的提示先柔和淡入（此时顶部总结句还在），
        # 再把总结句用 unwrite 撤掉，随后提示收回、接公式，不出现硬切
        hint = rich_text("N 能算：要让 1/n < ε，只要 n > 1/ε", scale=0.6)
        hint.move_to(ORIGIN)
        self.play(FadeIn(hint, shift=UP * 0.12), run_time=2.5)
        self.wait(3.0)
        old_cap = getattr(self, "_cap", None)
        if old_cap is not None:
            self.play(Unwrite(old_cap), run_time=1.5)
            self._cap = None
        self.wait(3.0)
        self.play(Unwrite(hint), run_time=1.5)

        step1 = MathTex(r"\frac{1}{n} < \varepsilon "
                        r"\Leftrightarrow n > \frac{1}{\varepsilon}",
                        color=WHITE).scale(0.95)
        step2 = MathTex(r"N = \left\lfloor \frac{1}{\varepsilon} \right\rfloor",
                        color=C_EPS).scale(1.05)
        group = VGroup(step1, step2).arrange(DOWN, buff=0.5)
        group.move_to(ORIGIN).shift(UP * 0.5)        # 置于屏幕中心
        self.play(Write(step1), run_time=3.0)
        self.wait(6.0)
        self.play(Write(step2), run_time=3.5)
        for s in (step1, step2):
            self.fix_in_frame(s)
        self.wait(7.0)
        self.caption("你给多小的 ε，我都能找到对应的 N", write_time=2.0)
        self.wait(6.0)
        self.caption("比如 ε = 0.04 时，N = 25", write_time=2.0)
        self.wait(5.0)
        self.formulas = group

    # ---------------- 章 9：振荡数列 ----------------
    def ch09_oscillating(self):
        self.seq = a_alt
        self.caption("换个不安分的：a_n = (-1)^n / n", write_time=2.0)
        self.clear_stage()
        self.axes = build_axes()
        self.y_range = [Y_LO, Y_HI, Y_STEP]
        labels = self.axes.get_axis_labels(x_label="n", y_label="a_n")
        self.play(Create(self.axes), Write(labels), run_time=4.0)
        for lab in labels:
            self.fix_scale(lab)       # 轴名逐个固定大小（不能对 VGroup 缩放）
        self.axis_labels = labels

        # 横轴标度值：随视角动态增删，密度适中
        self.axis_nums = self.axis_numbers()
        self.play(FadeIn(self.axis_nums), run_time=1.2)

        # 点按 SEQ_NS 取样，稀疏均匀铺满整条横轴
        self.draw_terms(a_alt, SEQ_NS, run_time=0.35)
        self.wait(2.0)

        self.draw_band(0.5)
        self.mark_fail(0.5)          # n = 1、2 在带外
        self.wait(4.0)

        g = gate(self.axes, 2)
        self.play(Create(g), run_time=3.0)
        self.gate = g
        self.caption("虽然上下摆动，但幅度 1/n 一样趋于 0", write_time=2.0)
        self.wait(6.0)

        # ---- 与章 7 相同的节奏：ε 收窄 → 门右移，纵向单独放大 + 引导箭头 ----
        self.caption("把要求提高：ε = 0.2", write_time=2.0)
        self.y_range = [-0.5, 0.5, 0.1]
        self.apply_view(MAX_N, X_STEP, eps=0.2, N=5, zoom=0.55, y_zoom=0.859,
                        lab_x=8, run_time=7.0, brace=False)
        self.blink_gate()
        self.blink_band_right()   # 门后那段绿带闪两次
        self.mark_sides()          # N 左侧点变红、右侧点变黄
        self.mark_fail(0.2)
        self.caption("ε = 0.2：门退到 N = 5，摆动被压进带里", write_time=2.0)
        self.wait(7.0)

        self.caption("再高一点：ε = 0.1，门退到 N = 10", write_time=2.0)
        self.y_range = [-0.25, 0.25, 0.05]
        self.apply_view(MAX_N, X_STEP, eps=0.1, N=10, zoom=0.40, y_zoom=0.859,
                        lab_x=14, run_time=7.0, brace=False)
        self.blink_gate()
        self.blink_band_right()   # 门后那段绿带闪两次
        self.mark_sides()          # N 左侧点变红、右侧点变黄
        self.mark_fail(0.1)
        self.caption("上下跳得再欢，门后也全部落在带内", write_time=2.0)
        self.wait(8.0)

    # ---------------- 章 10：反例 ----------------
    def ch10_counterexample(self):
        self.seq = a_pm
        self.caption("a_n = (-1)^n 呢？门后总有点跑出去", write_time=2.0)
        self.clear_stage()
        # 纵轴范围放到 ±2.4：ε = 2 时两条虚线（±2）也落在可视区域内
        self.y_range = [-2.4, 2.4, 0.6]
        self.axes = build_axes(y_range=self.y_range)
        labels = self.axes.get_axis_labels(x_label="n", y_label="a_n")
        self.play(Create(self.axes), Write(labels), run_time=4.0)
        for lab in labels:
            self.fix_scale(lab)       # 轴名逐个固定大小（不能对 VGroup 缩放）
        self.axis_labels = labels

        # 横轴标度值：随视角动态增删，密度适中
        self.axis_nums = self.axis_numbers()
        self.play(FadeIn(self.axis_nums), run_time=1.2)

        # 两排 ±1 按 SEQ_NS 取样，稀疏均匀铺满整条横轴
        self.draw_terms(a_pm, SEQ_NS, run_time=0.35)
        self.wait(2.0)

        # ---- ε 走 2 → 1 → 0.5：不用章 7 的放大方式，只换带与门 ----
        # 本章起不再画门底的大括号与 all n > N 标注
        self.draw_band(2.0)
        g = gate(self.axes, 2, brace=False)
        self.play(Create(g), run_time=3.0)
        self.gate, self.gate_n = g, 2
        self.caption("ε = 2：带很宽，±1 全在里面，N = 2 就够", write_time=2.0)
        self.wait(5.0)

        self.caption("把 ε 收到 1：±1 正好压在带边上", write_time=2.0)
        self.apply_view(MAX_N, X_STEP, eps=1.0, N=10, run_time=6.0,
                        brace=False)
        self.blink_gate()
        self.mark_fail(1.0)          # |a_n| = 1 >= 1，全部不合格
        self.caption("门推到 N = 10，照样有点在带外", write_time=2.0)
        self.wait(5.0)

        self.caption("再收到 ε = 0.5，门推到 N = 28", write_time=2.0)
        self.apply_view(MAX_N, X_STEP, eps=0.5, N=28, run_time=6.0,
                        brace=False)
        self.blink_gate()
        self.mark_fail(0.5)
        self.caption("门再往右也没用：总有项在带外", write_time=2.0)
        self.wait(7.0)

        # 收尾：色带连同其他物件全部清理，不带入下一章
        self.clear_stage()

    # ---------------- 章 11：N 不唯一 ----------------
    def ch11_N_not_unique(self):
        self.seq = a
        self.caption("顺便说一句：这个 N 不是唯一的", write_time=2.0)
        self.clear_stage()
        self.axes = build_axes()
        self.y_range = [Y_LO, Y_HI, Y_STEP]
        labels = self.axes.get_axis_labels(x_label="n", y_label="a_n")
        self.play(Create(self.axes), Write(labels), run_time=3.0)
        for lab in labels:
            self.fix_scale(lab)       # 轴名逐个固定大小（不能对 VGroup 缩放）
        self.axis_labels = labels

        # 横轴标度值：随视角动态增删，密度适中
        self.axis_nums = self.axis_numbers()
        self.play(FadeIn(self.axis_nums), run_time=1.2)

        self.draw_terms(a, SEQ_NS, run_time=0.5)
        self.draw_band(0.1)
        self.mark_fail(0.1)          # n ≤ 10 的项不合格

        g = gate(self.axes, 10, brace=False)     # 本章起不画下方大括号与标注
        self.play(Create(g), run_time=3.0)
        self.gate = g
        self.caption("ε = 0.1 时，N = 10 就行", write_time=2.0)
        self.wait(4.0)

        # ---- N = 100：按章 7 标准做纵向解耦放大 ----
        # 量程取 ±2.5/N，保证门后那些项的垂线仍然看得见（1/n 随 N 变小，
        # 若沿用 ±2.5ε 的量程，n≈100 附近的点会全部贴在轴上、看不到垂线）
        self.caption("取 N = 100 呢？坐标系放大到 N = 100 附近", write_time=2.0)
        x_max, x_step = plan_view(100, 0.35)
        self.y_range = [-2.5 / 100, 2.5 / 100, 0.5 / 100]
        self.apply_view(x_max, x_step, eps=0.1, N=100, zoom=0.35,
                        y_zoom=0.859, lab_x=104, run_time=4.5,
                        new_ns=sample_ns(x_max, x_step, skip=SEQ_NS),
                        brace=False)
        self.blink_gate()
        self.blink_band_right()   # 门后那段绿带闪两次
        self.mark_sides()          # N 左侧点变红、右侧点变黄
        self.mark_fail(0.1)
        self.caption("取 N = 100，当然也成立", write_time=2.0)
        self.wait(5.0)

        # ---- N = 10000：量程继续跟着 1/N 收，垂线仍然可见 ----
        self.caption("N = 10000 也行，量程再收一档", write_time=2.0)
        x_max, x_step = plan_view(10000, 0.14)
        self.y_range = [-2.5 / 10000, 2.5 / 10000, 0.5 / 10000]
        self.apply_view(x_max, x_step, eps=0.1, N=10000, zoom=0.14,
                        y_zoom=0.859, lab_x=10400, run_time=4.5,
                        new_ns=sample_ns(x_max, x_step, skip=SEQ_NS),
                        brace=False)
        self.blink_gate()
        self.blink_band_right()   # 门后那段绿带闪两次
        self.mark_sides()          # N 左侧点变红、右侧点变黄
        self.mark_fail(0.1)
        self.caption("N 从来不唯一，够用就行", write_time=2.0)
        self.wait(6.0)
        self.clear_stage()

    # ---------------- 章 11b：定义其实是三句话 ----------------
    def ch11b_quantifiers(self):
        """把 ε-N 定义拆成 ∀ε / ∃N / ∀n>N 三层；N 线随句子动态右移，镜头跟随"""
        self.seq = a
        self.caption("这个定义，其实是三句话", write_time=2.0)
        self.clear_stage()
        self.axes = build_axes()
        self.y_range = [Y_LO, Y_HI, Y_STEP]
        labels = self.axes.get_axis_labels(x_label="n", y_label="a_n")
        self.play(Create(self.axes), Write(labels), run_time=3.0)
        for lab in labels:
            self.fix_scale(lab)       # 轴名逐个固定大小（不能对 VGroup 缩放）
        self.axis_labels = labels

        self.draw_terms(a, SEQ_NS, run_time=0.5)
        self.draw_band(0.2)
        self.mark_fail(0.2)          # n ≤ 5 的项不合格
        g = gate(self.axes, 5, brace=False)      # 本章起不画下方大括号与标注
        self.play(Create(g), run_time=2.5)
        self.gate = g

        l1 = MathTex(r"\forall \varepsilon > 0", color=C_EPS).scale(0.72)
        l2 = MathTex(r"\exists N", color=C_N).scale(0.72)
        l3 = MathTex(r"\forall n > N:\ |a_n - L| < \varepsilon",
                     color=WHITE).scale(0.72)
        lines = VGroup(l1, l2, l3).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        lines.to_edge(UP, buff=0.8)

        self.caption("第一句：误差上限 ε 随便你给", write_time=2.0)
        self.play(Write(l1), run_time=2.5)
        self.wait(5.0)

        # 第二句：N 线右移，镜头跟随；公式先固定在画面上，不随视角移出屏幕
        self.caption("第二句：我总能找到一道门 N", write_time=2.0)
        self.play(Write(l2), run_time=2.0)
        for l in (l1, l2):
            self.fix_in_frame(l)
        self.apply_view(MAX_N, X_STEP, eps=0.2, N=20, zoom=0.5, cam_y=0.25,
                        lab_x=23, run_time=4.0, brace=False)
        self.blink_gate()
        self.blink_band_right()
        self.mark_sides()
        # 门线缩短一半（避免挡住上方公式），同时把 N=20 标签挪到线底下方
        line = self.gate[0]
        line_center = line.get_center()
        bottom_after = line_center + DOWN * (line.height * 0.55 / 2)
        self.play(line.animate.scale(0.55),
                  self.gate[1].animate.next_to(bottom_after, DOWN, buff=0.12),
                  run_time=1.5)

        # 第三句：逐字写出（镜头到此不再移动）
        self.caption("第三句：门后的每一项，都必须落进带里", write_time=2.0)
        l3.shift(self.camera.frame.get_center())    # 搬到当前画面位置
        self.fix_in_frame(l3)
        self.play(Write(l3), run_time=4.0)
        self.wait(6.0)
        self.formulas = lines

    # ---------------- 章 12：定义 ----------------
    def ch12_definition(self):
        self.caption("对任意的 ε 大于 0，都存在一个 N", write_time=2.0)
        self.clear_stage()

        lineA = MathTex(r"\forall \varepsilon > 0,\ \exists N,").scale(0.95)
        part1 = MathTex(r"n > N :").scale(0.95)
        part2 = MathTex(r"|a_n - L| < \varepsilon",
                        color=C_EPS).scale(0.95)
        lineB = VGroup(part1, part2).arrange(RIGHT, buff=0.35)
        eq = VGroup(lineA, lineB).arrange(DOWN, buff=0.5)
        eq.move_to(ORIGIN).shift(UP * 0.4)          # 置于屏幕中心

        self.play(Write(lineA), run_time=2.5)
        self.wait(4.0)
        self.play(Write(part1), run_time=2.0)
        self.wait(3.0)
        self.play(Write(part2), run_time=2.5)
        self.wait(6.0)

        self.caption("|a_n - L| 就是我们从头到尾在说的那个「距离」", write_time=2.0)
        self.wait(6.0)
        box = SurroundingRectangle(part2, color=C_EPS, buff=0.18)
        self.play(Create(box), run_time=1.5)
        for m in (lineA, part1, part2):
            self.fix_in_frame(m)
        self.wait(5.0)

        self.caption("你给的每道误差要求，我都能找到一道门：门后永远达标",
                     write_time=2.0)
        self.wait(10.0)
        self.caption("这就是数列极限的 ε-N 定义", write_time=2.0)
        self.wait(6.0)
        self.formulas = VGroup(lineA, part1, part2, box)

    # ---------------- 入口 ----------------
    def construct(self):
        self.seq = a
        self.terms = []
        self.failed = set()
        self.passed = set()
        self.axis_nums = None
        self.gate_n = None
        self.gate_eps = None
        self.ch00_title()
        self.ch01_intuition()
        self.ch02_frog_game()
        self.ch03_axes()
        self.ch04_terms()
        self.ch05_eps_band()
        self.ch06_gate()
        self.ch07_shrink_eps()      # 核心章节，节奏与镜头在此调
        self.ch08_formula_N()
        self.ch09_oscillating()
        self.ch10_counterexample()
        self.ch11_N_not_unique()
        self.ch11b_quantifiers()
        self.ch12_definition()
