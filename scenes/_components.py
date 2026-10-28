# -*- coding: utf-8 -*-
"""
数学概念动画 · 公共组件库

供 scenes/ 下各概念动画共用，避免每支动画重写坐标系、字幕混排、
镜头补偿这些通用部件。

分两类：

    一、通用
        BaseScene        节奏控制 MOTION/PAUSE、字幕 caption、镜头补偿
        rich_text        中文 Text 与数学 MathTex 混排（含基线对齐）
        make_axes        建立坐标系并摆到指定位置
        xticks           横轴刻度数字（用 Text 实现，不依赖 LaTeX）

    二、按题材
        数列类： lollipop / eps_band / eps_labels / gate
        函数类： func_curve / hband / vstrip / open_dot / clip_bad

配色规范
    C_TERM 橙 = 被检验的对象（数列的项 / 函数曲线）
    C_EPS  绿 = 极限值 A 与 ε 带
    C_FAIL 红 = 不合格的部分（跑到带外）
    C_N    蓝 = 门 N / δ 竖带这类阈值结构
    C_DIM  灰 = 已淡出或不重要的辅助信息

一个颜色只对应一个含义，全片不变。
"""
import re
from pathlib import Path

import numpy as np
from manim import *

# ══════════════════════════════════════════════════════════
# 视觉规范
# ══════════════════════════════════════════════════════════
C_TERM = ORANGE
C_EPS = GREEN
C_FAIL = RED
C_N = BLUE
C_DIM = GREY_B
FONT = "Microsoft YaHei"
BG = "#1c1c1c"          # 深色背景（与参考视频一致）

# ══════════════════════════════════════════════════════════
# 中文 / 数学混排
# ══════════════════════════════════════════════════════════
# 判定「这段字该交给 Text 还是 MathTex」。
# 除了汉字与全角标点，还必须把中文排印常用的这批字符算作文字：
#   U+2010–201F  连字符、破折号 ——、引号 “ ” ‘ ’
#   U+2026       省略号 …
#   U+00B7       间隔号 ·
# 漏掉它们，破折号会被送进 LaTeX，渲染成两竖线（本片实拍踩到过）。
CJK_RE = re.compile(
    r"[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef"
    r"\u2010-\u201f\u2026\u00b7]"
)

# 字幕里的数学片段做规范化：符号换成 LaTeX，除号换成分数线。
# 顺序有意义：长串在前，单字符在后（"1/ε" 必须先于 "ε" 命中）。
# Unicode 上下标单独一组，先于 MATH_FIX 应用。
SUB_SUP = [
    ("₀", "_{0}"), ("₁", "_{1}"), ("₂", "_{2}"), ("₃", "_{3}"), ("₄", "_{4}"),
    ("₅", "_{5}"), ("₆", "_{6}"), ("₇", "_{7}"), ("₈", "_{8}"), ("₉", "_{9}"),
    ("ₙ", "_{n}"), ("ₖ", "_{k}"),
    ("²", "^{2}"), ("³", "^{3}"),
]

MATH_FIX = [
    ("(-1)^n/n", r"\frac{(-1)^n}{n}"),
    ("1/n", r"\frac{1}{n}"),
    ("1/ε", r"\frac{1}{\varepsilon}"),
    ("1/\\varepsilon", r"\frac{1}{\varepsilon}"),
    # 分数一律走 \frac，不要留成 "a/b" 的斜杠形式。
    # 顺序：带分母的整段必须排在单字符替换（"ε"→"\varepsilon"）之前。
    ("ε/3", r"\frac{\varepsilon}{3}"),
    ("ε/2", r"\frac{\varepsilon}{2}"),
    ("ε/4", r"\frac{\varepsilon}{4}"),
    ("δ/2", r"\frac{\delta}{2}"),
    ("δ/3", r"\frac{\delta}{3}"),
    ("ε", r"\varepsilon"),
    ("δ", r"\delta"),
    ("Δ", r"\Delta"),
    ("∞", r"\infty"),
    ("∀", r"\forall"),
    ("∃", r"\exists"),
    ("⇒", r"\Rightarrow"),
    ("⇔", r"\Leftrightarrow"),
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
    """量一次「汉字字面高度」与「数学大写字母高度」（scale=1），供混排换算。"""
    if not _TEXT_METRICS:
        _TEXT_METRICS["cn"] = Text("国", font=FONT).height
        _TEXT_METRICS["cap"] = MathTex(r"\mathrm{N}").height
    return _TEXT_METRICS


def _auto_frac(s):
    """把剩下的简单 "a/b" 自动转成 \\frac{a}{b}。

    只处理「分子分母都是短记号」的情形（如 1/3、x/2、ε/δ），
    复杂表达式留给调用方自己写 LaTeX，免得把语义改错。
    """
    tok = r"[0-9A-Za-z\\{}()\s\+\-\u0370-\u03ff]{1,12}"
    pat = re.compile(rf"(?<![\\A-Za-z])({tok}?)\s*/\s*({tok})")

    def rep(m):
        a, b = m.group(1).strip(), m.group(2).strip()
        if not a or not b:
            return m.group(0)
        # 已经是 \frac 的一部分就别再套一层
        if "frac" in a or "frac" in b:
            return m.group(0)
        return rf"\frac{{{a}}}{{{b}}}"

    # 反复替换，处理 1/2/3 这类连写（少见）；最多 3 轮避免死循环
    for _ in range(3):
        new = pat.sub(rep, s)
        if new == s:
            break
        s = new
    return s


def _auto_pow(s):
    """把 "x^2" 这类写法规范成上标 x^{2}（已是花括号的原样保留）。"""
    return re.sub(r"\^(\w)(?!\{)", r"^{\1}", s)


# 形如 x0 / x1 / a1 / n0 的写法：第二个字符若是数字，按「下标」解释。
# 学生与稿子里都习惯敲 x0，字幕里不该出现这种半吊子记号。
_AUTO_SUB = re.compile(r"(?<![\\A-Za-z0-9])([A-Za-z])(\d)(?![0-9])")


def _auto_sub(s):
    return _AUTO_SUB.sub(r"\1_{\2}", s)


def _math_expr(s):
    """把字幕里的数学片段转成 LaTeX。先去掉除号两侧空格，让写法统一。

    Unicode 上下标先转成 LaTeX 语法：字幕里可以直接写 x₀、aₙ、ε²，
    不必在手写字符串里記 "_0" 这种别扭写法。
    最后再做「x0→x_{0}」「^2→^{2}」「a/b→\\frac{a}{b}」的兜底规范，
    保证数学内容一律以真下标、真上标、竖式分数呈现。
    """
    s = re.sub(r"\s*/\s*", "/", s)
    for old, new in SUB_SUP:
        s = s.replace(old, new)
    for old, new in MATH_FIX:
        s = s.replace(old, new)
    s = _auto_pow(s)
    s = _auto_frac(s)
    s = _auto_sub(s)
    return s


def rich_text(text, color=WHITE, scale=0.5, math_ratio=0.92, buff=0.08,
              max_width=None):
    """把一句字幕拆成「中文 → Text」「数学 → MathTex」两类片段拼起来。

    - 数学片段按实测字高归一化，两者视觉大小一致；
    - 垂直方向按基线对齐，数学片段扣掉分数线/下标的下伸量；
    - 全部使用世界坐标单位，与渲染分辨率无关；
    - max_width 给定时，整句超宽就等比缩到该宽度（字幕必须留得住，
      宁可小一点也不能被画面边缘切掉）。

    注意：中文里的 ①②③、上标 ²、下标 ₙ 这类字符属于非 CJK 区段，
    会被判成数学片段送进 LaTeX 而报错——字幕里不要用。
    """
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
    if max_width is not None and group.width > max_width:
        group.scale(max_width / group.width)
    return group


# ══════════════════════════════════════════════════════════
# 文案表：字幕全部来自 captiontext.md，改字不用改代码
# ══════════════════════════════════════════════════════════
_CAPTION_FILE = Path(__file__).with_name("captiontext.md")
_CAPTION_KEYS = Path(__file__).with_name("caption_keys.json")
_CAPTION_CACHE = {}
_KEY_OF_LITERAL = {}


def load_captions(path=None):
    """解析 captiontext.md，返回 {key: 文案}。

    格式约定：
        [key]                  ← 单独一行，方括号包住标识
        这一句字幕的正文         ← 紧接的下一行非空行
        （空行）
        # 注释                 ← 忽略

    找不到文件时返回空字典，代码里的字面量兜底，不会因此崩溃。
    """
    p = Path(path) if path else _CAPTION_FILE
    out = {}
    if not p.exists():
        return out
    key = None
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.fullmatch(r"\[([A-Za-z0-9_]+)\]", line)
        if m:
            key = m.group(1)
            continue
        if key is not None:
            out[key] = line
            key = None
    return out


def _load_key_map():
    """读 caption_keys.json：{代码里的原句: md 里的 key}。

    这张表是**锚点**，作用是让代码里现成的 38 句字幕不必逐句改成 T("key")。
    改文案时只动 captiontext.md 即可 —— 原句仍然能通过这张表找到新文案。
    """
    if _KEY_OF_LITERAL:
        return _KEY_OF_LITERAL
    try:
        import json
        data = json.loads(_CAPTION_KEYS.read_text(encoding="utf-8"))
    except Exception:
        return _KEY_OF_LITERAL
    for lit, key in data.items():
        if lit.startswith("_"):
            continue
        _KEY_OF_LITERAL[lit] = key
    return _KEY_OF_LITERAL


def T(key, fallback=""):
    """直接按 key 取文案。"""
    if not _CAPTION_CACHE:
        _CAPTION_CACHE.update(load_captions())
    return _CAPTION_CACHE.get(key, fallback)


def resolve_caption(text):
    """把代码里传进来的字符串解析成 md 里的最新文案。

    三种传入方式都支持：
        1. 传 key            → T("ch01_gate")
        2. 传代码里的原句      → 通过 caption_keys.json 反查 key
        3. 传一个 md 里没有的句子 → 原样返回（临时改字不改文件也能跑）

    这样字幕文案的唯一来源就是 captiontext.md，改字不必碰代码。
    """
    if not _CAPTION_CACHE:
        _CAPTION_CACHE.update(load_captions())
    # 1) 直接是 key
    if text in _CAPTION_CACHE:
        return _CAPTION_CACHE[text]
    # 2) 是代码里的原句
    k = _load_key_map().get(text)
    if k is not None and k in _CAPTION_CACHE:
        return _CAPTION_CACHE[k]
    # 3) 兜底：原样
    return text


# ══════════════════════════════════════════════════════════
# 基类：节奏总控 + 常驻字幕
# ══════════════════════════════════════════════════════════
class BaseScene(MovingCameraScene):
    """所有概念动画的基类。

    继承 MovingCameraScene 而不是 Scene：本片用固定机位，不需要镜头运动，
    但基类保留 fix_scale / fix_in_frame / fix_top_center 三件套，
    日后做需要推拉的动画时可直接用，不必重写。
    """

    MOTION = 0.85      # 所有动画 run_time 的倍率
    PAUSE = 0.80       # 所有 self.wait 的倍率

    # ---------------- 节奏总控 ----------------
    def play(self, *args, **kwargs):
        """所有动画统一乘 MOTION 倍率；不足一帧的按一帧算。"""
        if not getattr(self, "_in_wait", False):
            rt = kwargs.get("run_time", 1.0) * self.MOTION
            kwargs["run_time"] = max(rt, 1.0 / config.frame_rate)
        super().play(*args, **kwargs)

    def wait(self, duration=1.0, **kwargs):
        """所有停顿统一乘 PAUSE 倍率（绕开 play 的 MOTION 倍率）。"""
        self._in_wait = True
        try:
            super().wait(duration * self.PAUSE, **kwargs)
        finally:
            self._in_wait = False

    # ---------------- 镜头推拉 ----------------
    def zoom_to(self, focus, scale=1.0, aux=(), run_time=2.6,
                keep=(), ease=rate_functions.ease_in_out_sine):
        """把镜头推到 focus（世界坐标），同时把画面放大 1/scale 倍。

        实现方式是直接改 MovingCameraScene 的 camera.frame，
        而不是重画一套坐标轴再把旧轴变换过去。重画的做法有三个毛病：
        刻度、标注、曲线都要跟着重建，容易留下残影；放大是瞬间的结构替换，
        看不出镜头在移动；倍率一变，所有文字和线宽的世界尺寸都跟着变，
        要逐个补偿。

        改用 camera.frame 之后，世界坐标不动，图形自己就被放大了；
        缩放是连续插值，镜头是推过去的。需要在屏幕上保持固定大小的元素
        （字幕、状态牌、公式）传进 aux/keep，内部会挂 fix_in_frame。

        参数
            focus  要推到画面中心的点（世界坐标）
            scale  画面高度的倍率：小于 1 放大，大于 1 缩小，1 不变
            aux    跟着一起缩放、但要保持屏幕大小的附属物件
            keep   同上，语义化别名

        注意：已经用 pin_to_screen 钉住的物件（例如字幕）不要再传进来，
        否则它会挂上两个尺寸补偿 updater，尺寸会被连缩两次。
        """
        frame = self.camera.frame
        anim = frame.animate.move_to(focus).set(width=frame.width * scale)

        for m in list(aux) + list(keep):
            if m is None:
                continue
            if getattr(m, "_pin_state", None) is not None:
                continue          # 已被 pin_to_screen 接管，别重复挂
            self.fix_in_frame(m)

        return anim

    def zoom_play(self, focus, scale=1.0, aux=(), run_time=2.6, **kw):
        """zoom_to 的即用版：直接播放。

        字幕不用传：它身上已挂 pin_to_screen，镜头推拉时自动保持
        屏幕位置与尺寸。这里反而不能把它塞进 aux，否则双重补偿。
        """
        return self.play(self.zoom_to(focus, scale, aux=aux, run_time=run_time, **kw),
                         run_time=run_time)

    def reset_zoom(self, run_time=2.0):
        """镜头复位：回到原点、恢复原始画面宽度。

        不在这里挪字幕。字幕位置一旦变化，必须走「先撤旧的、再在新位置
        新建」的流程（见 caption），否则旧字幕会在画面上瞬移到新位置，
        看起来就是"闪了一下"。
        """
        frame = self.camera.frame
        self.play(
            frame.animate.move_to(ORIGIN).set(width=config.frame_width),
            run_time=run_time)

    def pin_to_screen(self, mob, pos=None):
        """把 mob 钉在屏幕上的固定位置，且尺寸恒定 —— 推镜头时它纹丝不动。

        与 fix_in_frame 的区别：
            fix_in_frame 记下「相对画面中心」的偏移并随之平移，
                         所以镜头**平移**时它会跟着走（适合挂在某个物体旁边）。
            pin_to_screen 记的是**屏幕归一化位置**（-0.5~0.5），
                         镜头怎么推、怎么移，它都停在屏幕同一处。
                         字幕、状态牌要的就是这个行为。

        pos: (u, v)，单位是「画面宽 / 画面高」的倍数，
             所以 u=±0.5 是左右缘、v=±0.5 是上下缘，v=0.38 靠近顶部但留了余量。
             省略时按 mob 当前屏幕位置反推。
        """
        frame = self.camera.frame

        # 世界坐标 → 屏幕归一化坐标（-0.5 左/下缘，+0.5 右/上缘）
        def to_uv(m):
            dx = m.get_center()[0] - frame.get_center()[0]
            dy = m.get_center()[1] - frame.get_center()[1]
            return (dx / frame.width, dy / frame.height)

        state = {"u": None if pos is None else pos[0],
                 "v": None if pos is None else pos[1],
                 "s": 1.0}

        if pos is None:
            u, v = to_uv(mob)
            state["u"], state["v"] = u, v

        # 记下「建这个物件时的世界尺寸」，之后每次都用绝对值重设，
        # 而不是逐帧乘一个因子 —— 逐帧乘会在多次推拉后累积误差。
        base_size = {"w": mob.width, "h": mob.height}
        state["base_w"] = base_size["w"]
        state["base_h"] = base_size["h"]
        state["s"] = 1.0

        def keep(m):
            # 屏幕放大倍数 k = config.frame_width / frame.width
            # 想让屏幕尺寸恒定，世界尺寸应恒为 base / k。
            # 这里用绝对值而非增量，避免多次推拉后漂移。
            k = config.frame_width / max(frame.width, 1e-9)
            if abs(k - state["s"]) > 1e-9:
                want = state["base_w"] / k
                if m.width > 1e-9:
                    m.scale(want / m.width)
                state["s"] = k
            m.move_to(frame.get_center()
                      + RIGHT * (state["u"] * frame.width)
                      + UP * (state["v"] * frame.height))

        # 建的时候镜头是 1 倍，所以 state["s"] 从 1.0 起算，
        # 不做任何初始缩放（此时 cur_s == 1，补偿量为 0）。
        mob.move_to(frame.get_center()
                    + RIGHT * (state["u"] * frame.width)
                    + UP * (state["v"] * frame.height))

        # 把状态挂到 mobject 上，方便 refresh_caption_pos 只改位置、
        # 不重挂 updater（重挂会把尺寸补偿再执行一遍，字幕会被缩两次）。
        mob._pin_state = state
        mob.add_updater(keep)
        return mob

    # ---------------- 镜头补偿三件套 ----------------
    def fix_scale(self, mob):
        """让 mob 的屏幕大小不随镜头推拉变化。只能对单个 mobject 调用。"""
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
        """固定在画面上：位置与大小都不随镜头变化。只能对单个 mobject 调用。"""
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

    def fix_top_center(self, mob):
        """把 mob 钉在屏幕正上方居中：横向跟随镜头中心线，纵向固定。"""
        frame = self.camera.frame
        y = mob.get_center()[1]

        def keep(m):
            c = frame.get_center()
            m.move_to(np.array([c[0], y, 0.0]))

        mob.add_updater(keep)
        return mob

    # ---------------- 常驻字幕 ----------------
    def _cap_v(self):
        """字幕在屏幕上的纵向归一化位置（0.5 = 画面顶缘）。

        默认放顶部（与第一支视频一致）。但推镜头时中上部全是放大的图形，
        字幕会压上去，所以允许用 self._cap_v_override 临时改到别处
        （例如 ch05 推近时挪到底部空白区）。"""
        ov = getattr(self, "_cap_v_override", None)
        if ov is not None:
            return ov
        return 0.425

    def refresh_caption_pos(self):
        """镜头倍率变化后，把字幕重新定位到对应位置。

        这里只改位置，不改尺寸。尺寸由 pin_to_screen 的 updater 负责，
        两边同时缩放会让字幕被连缩两次，越推越小。
        """
        cap = getattr(self, "_cap", None)
        if cap is None:
            return
        st = getattr(cap, "_pin_state", None)
        if st is None:
            return
        st["u"] = 0.0
        st["v"] = self._cap_v()
        fw, fh = self.camera.frame.width, self.camera.frame.height
        cap.move_to(self.camera.frame.get_center()
                    + RIGHT * (st["u"] * fw)
                    + UP * (st["v"] * fh))
        return cap

    def caption(self, text, write_time=2.0):
        """字幕：换句时先撤掉旧的，再在目标位置写入新的。

        上下位置切换的处理：
            如果先把新字幕建好再整体移到新位置，新字幕会先在旧位置出现、
            然后跳到下面，屏幕上能看出一次跳变。
            所以顺序固定为：旧字幕 Unwrite 退场，退干净之后新字幕才 Write。
            两步之间没有重叠帧，看不到位置跳变。

        节奏：
            Unwrite 用 write_time * 0.6
            Write   用 write_time，上下位置一致
        """
        fw = self.camera.frame.width
        v = self._cap_v()

        # 文案统一从 captiontext.md 取（传 key 或传原句都行）
        text = resolve_caption(text)

        # 先在目标位置建好（尚未加入场景）
        new = rich_text(text, max_width=fw * 0.78)
        new.move_to(np.array([0.0, self.camera.frame.height * v, 0.0]))
        self.pin_to_screen(new, pos=(0.0, v))

        old = getattr(self, "_cap", None)
        if old is not None:
            # 旧字幕退场（此时新字幕还没进场景，不会出现位置跳变）
            self.play(Unwrite(old), run_time=max(write_time * 0.6, 0.9))
            self.remove(old)

        # 新字幕在目标位置 Write 进来
        self.play(Write(new), run_time=write_time)
        self._cap = new
        return new

    def drop_caption(self, run_time=1.0):
        old = getattr(self, "_cap", None)
        if old is not None:
            self.play(Unwrite(old), run_time=run_time)
            self._cap = None

    # ---------------- 常用动作 ----------------
    def fade(self, *mobs, run_time=2.0):
        live = [m for m in mobs if m is not None]
        if live:
            self.play(*[FadeOut(m) for m in live], run_time=run_time)

    def bad_fade(self, run_time=1.0):
        """淡出当前记在 self._bad 上的「跑出带外」红色片段"""
        bad = getattr(self, "_bad", None)
        if bad is not None and len(bad) > 0:
            self.play(FadeOut(bad), run_time=run_time)
        self._bad = None


# ══════════════════════════════════════════════════════════
# 通用图元
# ══════════════════════════════════════════════════════════
def make_axes(x_range, y_range, x_length=9.5, y_length=4.6,
              color=C_N, stroke_width=2, center=None):
    """建坐标系；center 给定时整体移到该位置（世界坐标）。"""
    axes = Axes(x_range=x_range, y_range=y_range,
                x_length=x_length, y_length=y_length,
                color=color, stroke_width=stroke_width)
    if center is not None:
        axes.move_to(center)
    return axes


def xticks(axes, values, size=0.4, color=WHITE, buff=0.16, skip_zero=True):
    """横轴刻度数字（Text 实现，免得为几个数字反复调 LaTeX）。"""
    g = VGroup()
    for v in values:
        if skip_zero and abs(v) < 1e-9:
            continue
        t = Text(f"{v:g}", font=FONT, color=color).scale(size)
        t.next_to(axes.c2p(v, 0), DOWN, buff=buff)
        g.add(t)
    return g


def open_dot(point, color=C_TERM, radius=0.085, bg=BG):
    """空心圆：表示「这个点被挖掉了 / 不在定义域」"""
    return Circle(radius=radius, stroke_color=color, stroke_width=3.2,
                  fill_color=bg, fill_opacity=1.0).move_to(point)


# ══════════════════════════════════════════════════════════
# 数列类零件（端口自 sequence_limit.py）
# ══════════════════════════════════════════════════════════
def lollipop(axes, n, seq, color=C_TERM):
    """棒棒糖式画项：点 + 垂直茎线到 n 轴。茎线长度就是该项的误差。"""
    y = seq(n)
    d = Dot(axes.c2p(n, y), color=color, radius=0.055)
    stem = Line(axes.c2p(n, 0), axes.c2p(n, y), color=color, stroke_width=2.2)
    return VGroup(stem, d)


def eps_band(axes, eps, x_max, color=C_EPS, opacity=0.13):
    """数列的 ε 带：上下虚线 + 半透明填充（对称于 0）"""
    left, right = axes.c2p(0, -eps), axes.c2p(x_max, eps)
    rect = Rectangle(width=right[0] - left[0], height=right[1] - left[1],
                     fill_color=color, fill_opacity=opacity, stroke_width=0)
    rect.move_to(axes.c2p(x_max / 2, 0))
    top = DashedLine(axes.c2p(0, eps), axes.c2p(x_max, eps),
                     color=color, stroke_width=1.8, dash_length=0.14)
    bot = DashedLine(axes.c2p(0, -eps), axes.c2p(x_max, -eps),
                     color=color, stroke_width=1.8, dash_length=0.14)
    return VGroup(rect, top, bot)


def gate(axes, N, y_lo=-1.2, y_hi=1.2, x_max=30, gate_len=5.5,
         brace=True, color=C_N):
    """数列的「门」：蓝色竖线 + N 标注 + 底部大括号 all n > N"""
    foot = axes.c2p(N, 0)
    line = Line(foot + DOWN * (gate_len / 2), foot + UP * (gate_len / 2),
                color=color, stroke_width=2.5)
    lab = MathTex(f"N={N}", color=color).scale(0.6)
    lab.next_to(line.get_top(), UP, buff=0.1)
    if N <= 5:
        lab.shift(RIGHT * 0.45)
    if not brace:
        return VGroup(line, lab)
    brace_dy = (y_hi - y_lo) * 0.02
    seg = Line(axes.c2p(N, y_lo + brace_dy), axes.c2p(x_max, y_lo + brace_dy))
    br = Brace(seg, direction=DOWN, color=color)
    btext = Text("all n > N", font=FONT, color=color).scale(0.5)
    br.put_at_tip(btext)
    return VGroup(line, lab, br, btext)


# ══════════════════════════════════════════════════════════
# 函数类零件
# ══════════════════════════════════════════════════════════
def func_curve(axes, f, x_range, color=C_TERM, stroke_width=5):
    """把函数画成曲线"""
    return axes.plot(f, x_range=x_range, color=color, stroke_width=stroke_width)


def hband(axes, level, half, xlo, xhi, color=C_EPS, opacity=0.13, dash_len=0.14):
    """水平 ε 带：以 level 为中心、半高 half，横跨 [xlo, xhi]。
    返回 VGroup(填充块, 上虚线, 下虚线, 中心实线)。"""
    p_l = axes.c2p(xlo, level - half)
    p_u = axes.c2p(xhi, level + half)
    rect = Rectangle(width=p_u[0] - p_l[0], height=p_u[1] - p_l[1],
                     fill_color=color, fill_opacity=opacity, stroke_width=0)
    rect.move_to(np.array([(p_l[0] + p_u[0]) / 2,
                           (p_l[1] + p_u[1]) / 2, 0.0]))
    top = DashedLine(axes.c2p(xlo, level + half), axes.c2p(xhi, level + half),
                     color=color, stroke_width=1.8, dash_length=dash_len)
    bot = DashedLine(axes.c2p(xlo, level - half), axes.c2p(xhi, level - half),
                     color=color, stroke_width=1.8, dash_length=dash_len)
    mid = Line(axes.c2p(xlo, level), axes.c2p(xhi, level),
               color=color, stroke_width=1.6, stroke_opacity=0.55)
    return VGroup(rect, top, bot, mid)


def vstrip(axes, center, half, ylo, yhi, color=C_N, opacity=0.075,
           gap_ratio=0.22, hole=True):
    """竖直 δ 带 —— 本片的核心新图元。

    与数列的「门」不同，它是**双开门**：一条竖带夹住 x0。
    当 hole=True 时，竖带在 x = x0 处**挖空一条缝**，
    对应定义里的 0 < |x - x0| < δ —— 那个 0 就是说 x 不许等于 x0。

    返回 VGroup(左块, 右块, 左虚线, 右虚线, 中缝虚线)。
    """
    xl = axes.c2p(center - half, 0)[0]
    xr = axes.c2p(center + half, 0)[0]
    xc = axes.c2p(center, 0)[0]
    yb = axes.c2p(0, ylo)[1]
    yt = axes.c2p(0, yhi)[1]

    g = min((xr - xl) * gap_ratio, (xr - xl) * 0.30) if hole else 0.0

    def block(a, b):
        r = Rectangle(width=max(b - a, 1e-3), height=yt - yb,
                      fill_color=color, fill_opacity=opacity, stroke_width=0)
        r.move_to(np.array([(a + b) / 2, (yb + yt) / 2, 0.0]))
        return r

    if g > 1e-3:
        left = block(xl, xc - g / 2)
        right = block(xc + g / 2, xr)
    else:
        left = block(xl, xc)
        right = block(xc, xr)

    lft = DashedLine(axes.c2p(center - half, ylo), axes.c2p(center - half, yhi),
                     color=color, stroke_width=2.0, dash_length=0.13)
    rgt = DashedLine(axes.c2p(center + half, ylo), axes.c2p(center + half, yhi),
                     color=color, stroke_width=2.0, dash_length=0.13)
    if hole:
        mid = DashedLine(axes.c2p(center, ylo), axes.c2p(center, yhi),
                         color=C_DIM, stroke_width=1.5, dash_length=0.10)
    else:
        mid = Line(axes.c2p(center, ylo), axes.c2p(center, ylo),
                   color=C_DIM, stroke_width=0)
    return VGroup(left, right, lft, rgt, mid)


def clip_bad(axes, f, x0, half, level, eps,
             color=C_FAIL, stroke_width=13, n=900):
    """找出 δ 邻域里「冲出 ε 带」的那些曲线段，画成红色。

    定义要求：0 < |x - x0| < δ 时必须有 |f(x) - level| < eps。
    凡是违反的采样点，连成一段红色折线盖在原曲线上 —— 一眼看出 δ 给大了。

    线宽取得比原曲线粗（13 vs 5），否则红段会被橙线吞掉，学生看不到。
    """
    xs = np.linspace(x0 - half * 0.995, x0 + half * 0.995, n)
    xs = xs[np.abs(xs - x0) > 1e-9]
    bad_mask = np.abs(f(xs) - level) >= eps

    runs, cur = [], []
    for x, bad in zip(xs, bad_mask):
        if bad:
            cur.append(x)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)

    pieces = VGroup()
    for run in runs:
        if len(run) < 2:
            run = [run[0] - 1e-3, run[0] + 1e-3]
        # 两端各外扩一点，让红段压住相邻的橙色缝
        pts = [axes.c2p(x, f(x)) for x in run]
        m = VMobject(color=color, stroke_width=stroke_width)
        m.set_points_as_corners([np.array([p[0], p[1], 0.0]) for p in pts])
        pieces.add(m)
    return pieces


def info_panel(eps=None, delta=None, corner=UL, buff=0.55, size=0.62):
    """左上角状态牌：当前 ε / δ 的数值。"""
    parts = []
    if eps is not None:
        parts.append(MathTex(r"\varepsilon = " + f"{eps:g}",
                             color=C_EPS).scale(size))
    if delta is not None:
        parts.append(MathTex(r"\delta = " + f"{delta:g}",
                             color=C_N).scale(size))
    g = VGroup(*parts).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
    g.to_corner(corner, buff=buff)
    return g
