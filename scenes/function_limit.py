# -*- coding: utf-8 -*-
"""
概念动画：函数的极限 · ε-δ 定义

内容说明
    数列极限里自变量只能向一个方向增长，所以一个 N 就能划出分界。
    函数极限的自变量可以从左右两侧趋近，因此分界由一条区间带给出，
    而不是一个点；定义中 0 < |x - x0| 这一条则要求把 x0 本身排除在外。

    全片的主线是 ε 与 δ 的联动：ε 收窄一次，δ 就必须跟着收窄一次。

章节（约 6 分 30 秒）
    ch00 片头           ch05 δ 被逼窄（核心）
    ch01 从门到带       ch06 0 < 的含意
    ch02 ε 带           ch07 左右极限
    ch03 δ 带           ch08 δ 的求法
    ch04 越界标红       ch09 定义收束

视觉规范（与 _components.py 一致）
    橙 = 曲线 / 被检验的对象
    绿 = 极限高度 A 与 ε 带
    红 = 冲出 ε 带的曲线段
    蓝 = δ 竖带
    灰 = x0 中缝、辅助线

排版约定
    manim 的 Text 不支持 Unicode 上下标，会渲染成方框，所以字幕统一走
    _components.rich_text，由它拆成 Text 与 MathTex 两段再拼接。
    字幕里可以直接写 x₀、ε、x^2、ε/3，rich_text 会自动转成下标、上标与分数。
"""
import numpy as np
from manim import *

from _components import (
    BaseScene, rich_text, make_axes, xticks, open_dot,
    func_curve, hband, vstrip, clip_bad, info_panel,
    C_TERM, C_EPS, C_FAIL, C_N, C_DIM, FONT, BG,
    T, resolve_caption,
)

# ══════════════════════════════════════════════════════════
# 本片参数
# ══════════════════════════════════════════════════════════
# 主函数：f(x) = x²，在 x0 = 1 处考察，极限 A = 1
F_MAIN = lambda x: x ** 2
X0 = 1.0
A_MAIN = 1.0

# 坐标系：纵轴只取 0–3.2
# ε 最小到 0.07，若纵轴拉到 7 则 ±0.07 的带只有几个像素，
# 学生根本看不出「带在变窄」。压到 3.2 后 ε=0.07 的带仍占约 4% 画面高度。
XR = [0, 2.0, 0.5]
YR = [0, 3.2, 0.5]
AXES_CENTER = DOWN * 0.45 + LEFT * 1.15


class FunctionLimit(BaseScene):
    """函数的极限 · ε-δ"""

    # ------------------------------------------------------
    # 章 0：片头
    # ------------------------------------------------------
    def ch00_title(self):
        title = Text("函数的极限", font=FONT).scale(0.95)
        sub = Text("数列只有一道门，函数却要两边都守住",
                   font=FONT, color=GREY).scale(0.46)
        sub.next_to(title, DOWN, buff=0.45)
        self.play(Write(title), run_time=2.5)
        self.play(Write(sub), run_time=1.6)
        self.wait(3.2)
        self.play(FadeOut(title), FadeOut(sub), run_time=1.4)

    # ------------------------------------------------------
    # 章 1：从「门」到「带」
    # ------------------------------------------------------
    def ch01_from_gate_to_band(self):
        # 先回顾第一支视频的门
        self.caption("上一支视频里，数列的 N 是一道门", write_time=2.0)
        nlab = NumberLine(x_range=[0, 10, 1], length=10.0,
                          include_numbers=True, font_size=24,
                          label_direction=DOWN).shift(UP * 1.35)
        gate_line = Line(nlab.n2p(4) + DOWN * 0.55, nlab.n2p(4) + UP * 0.55,
                         color=C_N, stroke_width=3)
        gate_lab = MathTex("N", color=C_N).scale(0.6)
        gate_lab.next_to(gate_line, UP, buff=0.12)
        right_zone = Rectangle(width=nlab.n2p(10)[0] - nlab.n2p(4)[0],
                               height=1.1, fill_color=C_N, fill_opacity=0.13,
                               stroke_width=0)
        right_zone.move_to(np.array([(nlab.n2p(4)[0] + nlab.n2p(10)[0]) / 2,
                                     nlab.n2p(0)[1], 0.0]))
        self.play(Create(nlab), run_time=2.5)
        self.play(FadeIn(right_zone), Create(gate_line),
                  Write(gate_lab), run_time=1.6)
        self.wait(3.5)

        # 关键对比：n 只能往右
        arrow = Arrow(nlab.n2p(1) + UP * 0.62, nlab.n2p(9) + UP * 0.62,
                      color=C_DIM, stroke_width=3.5, buff=0)
        arrow_lab = Text("n 只能往右走", font=FONT, color=C_DIM).scale(0.42)
        arrow_lab.next_to(arrow, UP, buff=0.12)
        self.play(GrowArrow(arrow), Write(arrow_lab), run_time=1.8)
        self.caption("n 只能往右走，所以一个数就够用了", write_time=2.0)
        self.wait(4.0)

        # 转场：换成 x 轴，可以从两边来
        self.caption("但 x 可以从左边来，也可以从右边来", write_time=2.0)
        xlab = NumberLine(x_range=[0, 10, 1], length=10.0,
                          include_numbers=True, font_size=24,
                          label_direction=DOWN).shift(DOWN * 0.75)
        x0_line = Line(xlab.n2p(5) + DOWN * 0.55, xlab.n2p(5) + UP * 0.55,
                       color=C_EPS, stroke_width=3)
        x0_lab = MathTex("x_0", color=C_EPS).scale(0.62)
        # 贴在竖线左侧、轴线上方一点点：既不会和下方的刻度数字 "5" 打架，
        # 也不会因为放到更高处而被误读成属于上面那条数轴。
        x0_lab.next_to(x0_line, LEFT, buff=0.14).shift(UP * 0.40)

        left_arr = Arrow(xlab.n2p(2.2) + DOWN * 1.25, xlab.n2p(4.7) + DOWN * 1.25,
                         color=C_N, stroke_width=3.5, buff=0)
        right_arr = Arrow(xlab.n2p(7.8) + DOWN * 1.25, xlab.n2p(5.3) + DOWN * 1.25,
                          color=C_TERM, stroke_width=3.5, buff=0)
        ltag = Text("从左逼近", font=FONT, color=C_N).scale(0.4)
        rtag = Text("从右逼近", font=FONT, color=C_TERM).scale(0.4)
        ltag.next_to(left_arr, DOWN, buff=0.1)
        rtag.next_to(right_arr, DOWN, buff=0.1)

        self.play(FadeOut(right_zone), FadeOut(gate_line),
                  FadeOut(gate_lab), FadeOut(arrow), FadeOut(arrow_lab),
                  Create(xlab), run_time=1.8)
        self.play(Create(x0_line), Write(x0_lab), run_time=1.2)
        self.play(GrowArrow(left_arr), GrowArrow(right_arr),
                  Write(ltag), Write(rtag), run_time=2.0)

        self.caption("两边都得管住——这就是为什么 δ 是一条带，不是一道门",
                     write_time=2.2)
        self.wait(4.5)
        self.fade(nlab, xlab, x0_line, x0_lab, left_arr, right_arr, ltag, rtag)

    # ------------------------------------------------------
    # 章 2：ε 带登场
    # ------------------------------------------------------
    def ch02_eps_band(self):
        self.caption("先看一个具体的：f(x) = x^2，在 x_0 = 1 附近", write_time=2.2)

        self.axes = make_axes(XR, YR, center=AXES_CENTER)
        labels = self.axes.get_axis_labels(
            x_label=MathTex("x").scale(0.7),
            y_label=MathTex("y").scale(0.7))
        curve = func_curve(self.axes, F_MAIN, [0, 2.0], color=C_TERM)
        self.play(Create(self.axes), Write(labels), run_time=3.0)
        self.play(Create(curve), run_time=3.0)

        # 曲线标注 y = x^2（真上标，走 LaTeX）。
        # 位置贴在曲线右上方：曲线在 x>1.5 之后已经很陡，右侧那块
        # （约 1.8, 2.3）既在曲线右边、又落在 ε 带上方，不压任何标注。
        x2_lab = MathTex(r"y = x^{2}", color=C_TERM).scale(0.66)
        x2_lab.move_to(self.axes.c2p(1.80, 2.08))
        x2_lab.set_z_index(5)
        self.play(Write(x2_lab), run_time=1.2)

        # 只标出极限点本身，不写 (1,1) 文字标注：
        # 坐标已由 x_0、A 两处引导线与轴上刻度说清楚，
        # 再挂一个 (1,1) 反而和后面的 ε 带叠在一起。
        pt = Dot(self.axes.c2p(X0, A_MAIN), color=C_EPS, radius=0.10)
        self.play(FadeIn(pt, scale=0.5), run_time=1.2)

        # 辅助虚线：x0 到轴、A 到轴
        guide_x = DashedLine(self.axes.c2p(X0, 0), self.axes.c2p(X0, A_MAIN),
                             color=C_DIM, stroke_width=1.5, dash_length=0.1)
        guide_y = DashedLine(self.axes.c2p(0, A_MAIN), self.axes.c2p(X0, A_MAIN),
                             color=C_DIM, stroke_width=1.5, dash_length=0.1)
        x0_lab = MathTex("x_0", color=C_DIM).scale(0.55)
        x0_lab.next_to(self.axes.c2p(X0, 0), DOWN, buff=0.28)
        a_lab = MathTex("A", color=C_EPS).scale(0.6)
        a_lab.next_to(self.axes.c2p(0, A_MAIN), LEFT, buff=0.18)
        self.play(Create(guide_x), Create(guide_y),
                  Write(x0_lab), Write(a_lab), run_time=1.6)
        self.wait(2.8)

        self.caption("x 越靠近 1，纵坐标就越靠近 1——还是「距离」那件事",
                     write_time=2.2)
        self.wait(4.5)

        # ε = 0.8：两条虚线夹出一条水平带
        eps0 = 0.8
        self.caption("老规矩：先给一个误差上限 ε，比如 ε = 0.8", write_time=2.2)
        band = hband(self.axes, A_MAIN, eps0, 0, 2.0)
        up_lab, dn_lab = self._eps_labels(eps0)
        self.play(Create(band[1]), Create(band[2]),
                  FadeIn(band[0]), run_time=2.2)
        self.play(Write(up_lab), Write(dn_lab), run_time=1.2)
        self.wait(3.5)

        self.caption("要求：只要 x 离 1 够近，f(x) 就必须落在这条带里",
                     write_time=2.2)
        self.wait(4.5)

        self._store = dict(labels=labels, curve=curve, pt=pt, pt_lab=None,
                           guide_x=guide_x, guide_y=guide_y, x0_lab=x0_lab,
                           a_lab=a_lab, band=band, up_lab=up_lab, dn_lab=dn_lab)

    # ------------------------------------------------------
    # 章 3：δ 带登场（本片的核心新图元）
    # ------------------------------------------------------
    def ch03_delta_band(self):
        s = self._store
        self.caption("现在看横轴：x 要离 1 多近，才守得住？", write_time=2.2)

        # δ = 0.6：给出一个明显过宽的带，为第 4 章「两端都跑出去」做铺垫
        d0 = 0.6
        strip = vstrip(self.axes, X0, d0, 0, YR[1], gap_ratio=0.20)
        dlab = MathTex(rf"\delta = {d0:g}", color=C_N).scale(0.6)
        dlab.move_to(self.axes.c2p(0.44, YR[1] * 0.82))

        self.play(Create(strip[2]), Create(strip[3]),
                  FadeIn(strip[0]), FadeIn(strip[1]), run_time=2.4)
        # 中缝单独画出来，强调它是一条「缝」而非一条线
        self.play(FadeIn(strip[4]), Write(dlab), run_time=1.2)
        self.wait(3.2)

        self.caption("这条竖带，就是 δ：左右各伸出 δ，把 x_0 夹在正中间",
                     write_time=2.2)
        self.wait(4.0)

        # 强调「缝」：在缝上画出 x0 被挖掉的空点
        hole = open_dot(self.axes.c2p(X0, 0), color=C_DIM, radius=0.07)
        hole_lab = Text("这一格先算作空的", font=FONT, color=C_DIM).scale(0.4)
        hole_lab.next_to(hole, DOWN, buff=0.5)
        self.play(Create(hole), Write(hole_lab), run_time=1.6)
        self.caption("注意中间这条缝：x 不许等于 x_0，只能「靠近」",
                     write_time=2.2)
        self.wait(4.5)
        self.fade(hole, hole_lab)

        self._store.update(strip=strip, dlab=dlab, d=d0)

    def _eps_labels(self, eps, delta=None):
        """A±ε 两个标签。

        ε 一收窄，两条虚线之间的世界高度只剩 2ε（最小时 0.14），
        任何「贴着线放」的方案都会被挤成一团。
        所以彻底换位置：**放到坐标轴右端之外**，
        上下两条各自用一根短引导线连到对应虚线，
        纵向间距固定为 0.62，与 ε 大小完全无关 —— 永远不会叠。
        """
        s = 0.46
        up = MathTex(r"A+\varepsilon", color=C_EPS).scale(s)
        dn = MathTex(r"A-\varepsilon", color=C_EPS).scale(s)

        x_out = 2.16                       # 轴右端 2.0 之外
        y_mid = A_MAIN
        up.move_to(self.axes.c2p(x_out, y_mid) + UP * 0.31)
        dn.move_to(self.axes.c2p(x_out, y_mid) + DOWN * 0.31)
        up.align_to(dn, LEFT)

        # 引导线：从标签左缘拉回对应虚线
        tie_u = DashedLine(self.axes.c2p(1.99, A_MAIN + eps),
                           up.get_left() + LEFT * 0.03,
                           color=C_EPS, stroke_width=1.2, dash_length=0.07)
        tie_d = DashedLine(self.axes.c2p(1.99, A_MAIN - eps),
                           dn.get_left() + LEFT * 0.03,
                           color=C_EPS, stroke_width=1.2, dash_length=0.07)
        return VGroup(up, tie_u), VGroup(dn, tie_d)

    # ------------------------------------------------------
    # 章 4：初步合格 + 发现失控
    # ------------------------------------------------------
    def ch04_overshoot(self):
        """δ=0.6 太大：左右两端都冲出 ε 带，标红。

        数值：eps=0.8, delta=0.6 → sup|f-1| = 1.56
              f(1.6) = 2.56 > A+eps = 1.8    （右边冲高）
              f(0.4) = 0.16 < A-eps = 0.2    （左边掉出）
        两端同时失守，是本片「δ 太大」的第一次直观示范。
        """
        eps0, d0 = 0.8, 0.6

        self.caption("拿 δ = 0.6 去验一下：带里的曲线，是不是都在绿带里？",
                     write_time=2.2)
        bad = clip_bad(self.axes, F_MAIN, X0, d0, A_MAIN, eps0)
        self.play(Create(bad), run_time=2.0)
        self._bad = bad

        # 指出右端的越界点。
        # 文字用白色而不是红色：红色在深色背景上偏暗、且和红点叠在一起时
        # 可读性差；红色留给"失控的曲线段"这一处语义就够了。
        xr = 1.6
        yr = F_MAIN(xr)
        over = Dot(self.axes.c2p(xr, yr), color=C_FAIL, radius=0.09)
        over_lab = MathTex(r"f(1.6)=2.56 > 1.8", color=WHITE).scale(0.5)
        over_lab.next_to(self.axes.c2p(xr, yr), UR, buff=0.16)
        over_lab.set_z_index(5)
        self.play(FadeIn(over, scale=0.5), Write(over_lab), run_time=1.4)

        self.caption("右边跑出去了：f(1.6) = 2.56，比上限 1.8 高得多",
                     write_time=2.2)
        self.wait(4.0)

        xl = 0.4
        over2 = Dot(self.axes.c2p(xl, F_MAIN(xl)), color=C_FAIL, radius=0.09)
        over2_lab = MathTex(r"f(0.4)=0.16 < 0.2", color=WHITE).scale(0.5)
        over2_lab.next_to(self.axes.c2p(xl, F_MAIN(xl)), UR, buff=0.16)
        over2_lab.set_z_index(5)
        self.play(FadeIn(over2, scale=0.5), Write(over2_lab), run_time=1.4)

        self.caption("左边也跑出去了：f(0.4) = 0.16，比下限 0.2 还低",
                     write_time=2.2)
        self.wait(4.0)

        self.caption("两边同时失守——δ 必须收窄", write_time=2.2)
        self.wait(3.0)
        self.fade(over, over_lab, over2, over2_lab)
        self._store.update()

    # ------------------------------------------------------
    # 章 5：δ 被逼窄
    # ------------------------------------------------------
    def ch05_shrink(self):
        """ε 降一档，上一轮刚够用的 δ 随即失效，再收窄一次。

        每一轮的 sup|f-1| 与合格与否（数值见表中的 sup 列）：
            eps=0.8  delta=0.34  合格      0.7956
            eps=0.3  delta=0.34  不合格    0.7956
            eps=0.3  delta=0.14  合格      0.2996
            eps=0.15 delta=0.14  不合格    0.2996
            eps=0.15 delta=0.07  合格      0.1449

        每收窄一次，镜头朝 x0 推近一档。δ 带在屏幕上的宽度变化不大，
        周围的内容被推出画面，形成靠近观察的效果。
        """
        s = self._store

        # (eps, delta, 期望, 镜头缩放比例)
        rounds = [
            (0.8,  0.34, "OK",   1.00),
            (0.3,  0.34, "FAIL", 1.00),
            (0.3,  0.14, "OK",   0.78),
            (0.15, 0.14, "FAIL", 0.78),
            (0.15, 0.07, "OK",   0.60),
        ]

        self.caption("把 ε 一档档收窄，看 δ 被逼到哪里", write_time=2.2)
        self.wait(2.2)

        # 推近之后 (1,1) 这个标签会漂进 ε 带里，形成干扰；
        # 它在前面的章节已经完成使命，这里直接收掉。
        s_ptlab = s.get("pt_lab")
        if s_ptlab is not None:
            self.play(FadeOut(s_ptlab), run_time=0.8)

        cur_band = s["band"]
        cur_strip = s["strip"]
        cur_bad = self._bad
        cur_up, cur_dn = s["up_lab"], s["dn_lab"]
        cur_dlab = s["dlab"]
        cur_eps = 0.8

        for eps, d, expect, zoom in rounds:
            eps_changed = abs(eps - cur_eps) > 1e-9

            new_band = hband(self.axes, A_MAIN, eps, 0, 2.0) if eps_changed else cur_band
            new_strip = vstrip(self.axes, X0, d, 0, YR[1], gap_ratio=0.20)
            new_dlab = MathTex(rf"\delta = {d:g}", color=C_N).scale(0.6)
            new_dlab.move_to(self.axes.c2p(0.44, YR[1] * 0.82))

            anims = [ReplacementTransform(cur_strip, new_strip),
                     ReplacementTransform(cur_dlab, new_dlab)]
            if eps_changed:
                anims.append(ReplacementTransform(cur_band, new_band))
                # A±ε 标签固定在 x=2.16（轴右侧）。一旦推近，这个位置
                # 就落到画面之外，标签会被切成半截贴在右边缘。
                # 所以推近之后不再重建它们（前面已淡出），避免出画。
                if cur_up is not None:
                    n_up, n_dn = self._eps_labels(eps)
                    anims += [ReplacementTransform(cur_up, n_up),
                              ReplacementTransform(cur_dn, n_dn)]
                    cur_up, cur_dn = n_up, n_dn
            if cur_bad is not None:
                anims.append(FadeOut(cur_bad))

            self.play(*anims, run_time=2.2)

            bad = clip_bad(self.axes, F_MAIN, X0, d, A_MAIN, eps)
            cur_bad = bad if len(bad) > 0 else None
            if cur_bad is not None:
                self.play(Create(cur_bad), run_time=1.5)

            # 镜头推近：焦点取 ε 带中心 A。
            #
            # 字幕位置的切换顺序：
            #   1) 上一条字幕先退场（它此时在顶部）
            #   2) 镜头推近
            #   3) 新字幕在底部重新写入
            # 第 1 步必须排在第 2 步之前，且不能先把旧字幕挪到新位置，
            # 否则屏幕上会看到一次位置跳变。所以先 drop_caption，
            # 再设 override，让下一次 caption() 直接建在底部。
            if zoom < 1.0 and zoom < self._zoom_now - 1e-9:
                self.drop_caption(run_time=1.2)   # 1) 上字幕退场
                self.zoom_play(focus=self.axes.c2p(X0, A_MAIN),
                               scale=zoom, run_time=2.2)   # 2) 推镜头
                self._zoom_now = zoom
                self._cap_v_override = -0.455     # 3) 之后一律建在底部

                ax_x0 = s.get("x0_lab")
                if ax_x0 is not None:
                    self.play(FadeOut(ax_x0), run_time=0.6)
                    s["x0_lab"] = None

                # A±ε 标签固定在轴右端，推近后会落到画面外，因此一并撤掉，
                # 并把 cur_up/cur_dn 置空，后续轮次不再重建。
                if cur_up is not None:
                    self.play(FadeOut(cur_up), FadeOut(cur_dn), run_time=0.6)
                    cur_up, cur_dn = None, None

            chip = self._verdict(expect)
            self.play(FadeIn(chip, scale=0.8), run_time=0.55)
            self.caption(self._round_note(eps, d, expect), write_time=1.8)
            self.wait(2.6)
            self.play(FadeOut(chip), run_time=0.45)

            cur_band, cur_strip, cur_dlab = new_band, new_strip, new_dlab
            cur_eps = eps

        self.caption("ε 每降一档，δ 就被逼窄一层——上一轮刚够用的 δ 总会失效",
                     write_time=2.4)
        self.wait(3.6)

        # 收尾前把镜头拉回来，否则下一章会带着放大的画面开场
        self._cap_v_override = None
        self.reset_zoom(run_time=1.8)
        self._zoom_now = 1.0
        self.wait(1.0)

        self._store.update(band=cur_band, strip=cur_strip, dlab=cur_dlab,
                           up_lab=cur_up, dn_lab=cur_dn)
        self._bad = cur_bad

    @staticmethod
    def _round_note(eps, d, expect):
        """第 5 章每一轮的字幕。

        这几句含具体数值，所以不能靠「原句反查」自动对上 md，
        改为按 (ε, δ) 显式指定 key —— 数值一改这里跟着改，
        文案本身仍然从 captiontext.md 取。
        """
        table = {
            (0.8, 0.34): "ch05_ok_034",
            (0.3, 0.34): "ch05_fail_eps03",
            (0.3, 0.14): "ch05_ok_014",
            (0.15, 0.14): "ch05_fail_eps015",
            (0.15, 0.07): "ch05_ok_007",
        }
        key = table.get((round(eps, 4), round(d, 4)))
        if key is not None:
            return T(key)
        # 兜底：数值不在表里时现场拼一句，保证不会崩
        if expect == "FAIL":
            return f"ε 收到 {eps:g}——刚够用的 δ = {d:g} 立刻失效"
        return f"δ 收到 {d:g}，重新守住"

    def _verdict(self, expect):
        """右上角的合格 / 不合格牌子"""
        ok = expect == "OK"
        txt = Text("合格" if ok else "不合格", font=FONT,
                   color=C_EPS if ok else C_FAIL).scale(0.55)
        box = SurroundingRectangle(txt, color=C_EPS if ok else C_FAIL,
                                   buff=0.16, stroke_width=2.5)
        g = VGroup(box, txt).to_corner(UR, buff=0.5)
        return g

    # ------------------------------------------------------
    # 章 6：0 < 的深意 —— x0 被挖掉
    # ------------------------------------------------------
    def ch06_punctured(self):
        self.clear_all()

        self.caption("反过来问：为什么定义里非要写 0 < |x - x_0|？",
                     write_time=2.2)
        self.wait(2.6)

        # 换一个在 x=1 处无定义的函数
        axes = make_axes([0, 2.0, 0.5], [0, 3.2, 0.5], center=AXES_CENTER)
        labels = axes.get_axis_labels(x_label=MathTex("x").scale(0.7),
                                      y_label=MathTex("y").scale(0.7))
        # g(x) = x+1, x≠1 ；用一个空隙模拟"此处无定义"
        left_part = axes.plot(lambda x: x + 1, x_range=[0, 0.985],
                              color=C_TERM, stroke_width=5)
        right_part = axes.plot(lambda x: x + 1, x_range=[1.015, 2.0],
                               color=C_TERM, stroke_width=5)
        self.play(Create(axes), Write(labels), run_time=2.6)

        # 函数表达式用 LaTeX 写，不用 Text：
        # 用 Text 会原样显示 "x^2" 和斜杠，看着像草稿。
        # 这里直接给 MathTex 的源码，分数线与上标都是正规排法。
        gfun = MathTex(r"g(x) = \frac{x^{2} - 1}{x - 1}",
                       color=C_DIM).scale(0.72)
        # 放屏幕下方居中：右上会撞字幕，左上会撞 y 轴名。
        # buff 取 0.42 而不是 0.82 —— 分数式比单行 Text 高不少，
        # 按 0.82 摆会让分子顶穿到横轴上，看着像压线。
        gfun.to_edge(DOWN, buff=0.42)
        self.play(Write(gfun), run_time=1.4)
        self.play(Create(left_part), Create(right_part), run_time=2.4)

        self.caption("这个函数在 x = 1 处根本没有定义——分母是 0", write_time=2.2)
        hole = open_dot(axes.c2p(1, 2), color=C_TERM, radius=0.09)
        self.play(Create(hole), run_time=1.0)
        self.wait(3.4)

        # 挖掉的那个点，正落在极限高度上
        lim_line = DashedLine(axes.c2p(0, 2), axes.c2p(2.0, 2),
                              color=C_EPS, stroke_width=1.8, dash_length=0.13)
        lim_lab = MathTex("2", color=C_EPS).scale(0.6)
        lim_lab.next_to(axes.c2p(0, 2), LEFT, buff=0.18)
        self.play(Create(lim_line), Write(lim_lab), run_time=1.4)

        self.caption("但 x 从两边靠近 1 时，函数值都在靠近 2", write_time=2.2)
        self.wait(3.8)

        self.caption("所以极限看的是「靠近的过程」，不是「那一点本身」",
                     write_time=2.4)
        self.wait(3.8)

        self.caption("这就是 0 < |x - x_0| 的全部意思：x_0 那一点，不参与考核",
                     write_time=2.4)
        self.wait(3.8)
        self.fade(axes, labels, left_part, right_part, hole,
                  lim_line, lim_lab, gfun)
        self.wait(0.8)

    # ------------------------------------------------------
    # 章 7：左右极限 —— 两边都得管
    # ------------------------------------------------------
    def ch07_two_sides(self):
        self.caption("再看一件数列那里没有的事：x 从哪边来", write_time=2.2)

        # 坐标系整体右移，左侧留出一整块空白放公式——
        # 这样公式永远在画面内，不必挤到边角去。
        # x_length 收到 7.2，保证轴左端（屏幕 x≈1.9）右侧没有公式，
        # 而公式组放在 x≈-3.2 一带，两者井水不犯河水。
        axes = make_axes([0, 2.0, 0.5], [0, 4.0, 1.0],
                         x_length=7.2, y_length=3.8,
                         center=np.array([2.35, -0.10, 0.0]))
        labels = axes.get_axis_labels(x_label=MathTex("x").scale(0.7),
                                      y_label=MathTex("y").scale(0.7))
        self.play(Create(axes), Write(labels), run_time=2.2)

        # 左右极限不等的函数：h(x) = 1 (x<1) ; 3 (x>1)
        left_h = axes.plot(lambda x: 1.0, x_range=[0.04, 0.985],
                           color=C_TERM, stroke_width=5)
        right_h = axes.plot(lambda x: 3.0, x_range=[1.015, 1.94],
                            color=C_TERM, stroke_width=5)
        hl = open_dot(axes.c2p(1, 1.0), color=C_TERM, radius=0.085)
        hr = open_dot(axes.c2p(1, 3.0), color=C_TERM, radius=0.085)
        self.play(Create(left_h), Create(right_h), run_time=2.0)
        self.play(Create(hl), Create(hr), run_time=0.8)

        self.caption("这个函数，从左边过来停在 1，从右边过来停在 3",
                     write_time=2.2)

        # 两条逼近箭头：画在各自水平线之上一点点，不盖住曲线本身
        la = Arrow(axes.c2p(0.16, 1.0), axes.c2p(0.86, 1.0),
                   color=C_N, stroke_width=4, buff=0)
        ra = Arrow(axes.c2p(1.86, 3.0), axes.c2p(1.14, 3.0),
                   color=C_TERM, stroke_width=4, buff=0)
        ltag = MathTex(r"x \to 1^-", color=C_N).scale(0.55)
        rtag = MathTex(r"x \to 1^+", color=C_TERM).scale(0.55)
        ltag.next_to(la, DOWN, buff=0.16)
        rtag.next_to(ra, DOWN, buff=0.16)
        self.play(GrowArrow(la), GrowArrow(ra),
                  Write(ltag), Write(rtag), run_time=2.0)
        self.wait(3.0)

        # 两条不相等的极限值 —— 说清「极限不存在」
        # 坐标系已右移，左侧这块整片空白正好放公式，字号可以正常放大，
        # 不会再出现"挤在角落、跑出画面"的问题。
        self.caption("两个答案对不上，所以这个函数在 1 处没有极限", write_time=2.4)
        m1 = MathTex(r"\lim_{x\to1^-} h(x) = 1", color=C_N).scale(0.62)
        m2 = MathTex(r"\lim_{x\to1^+} h(x) = 3", color=C_TERM).scale(0.62)
        neq = MathTex(r"1 \neq 3", color=C_FAIL).scale(0.62)
        neq_t = Text("极限不存在", font=FONT, color=C_FAIL).scale(0.44)
        neq_g = VGroup(neq, neq_t).arrange(RIGHT, buff=0.16)

        mg = VGroup(m1, m2, neq_g).arrange(DOWN, aligned_edge=LEFT, buff=0.30)
        mg.move_to(np.array([-3.30, 0.40, 0.0]))

        self.play(Write(m1), run_time=1.4)
        self.play(Write(m2), run_time=1.4)
        self.play(Write(neq_g), run_time=1.4)
        self.wait(3.6)

        self.caption("所以 δ 带必须左右两边同时把曲线压进 ε 带——缺一边都不算",
                     write_time=2.6)
        self.wait(4.0)
        self.fade(axes, labels, left_h, right_h, hl, hr, la, ra,
                  ltag, rtag, mg)
        self.wait(0.8)

    # ------------------------------------------------------
    # 章 8：通式 —— δ 怎么找
    # ------------------------------------------------------
    def ch08_formula(self):
        # 这里原来有一句「那 δ 具体是多少？回到 f(x) = x^2 自己看」。
        # 它写在 clear_all() 之前，于是刚 Write 进来就被后面那句
        # drop_caption 撤掉了 —— 画面上只是闪一下，读者什么也没看清。
        # 既然内容也不必要，直接删掉，改成清场后直接从画面开始讲。
        self.clear_all()

        # 版面：坐标轴居中偏左（竖直方向大致居中），推导占右半屏。
        # 纵轴只画到 2.6 —— 曲线画到 x=1.60 时 y≈2.56，刚好收在框内，
        # 不会冲出坐标框、也不会顶到顶部字幕。
        axes = make_axes([0, 2.0, 0.5], [0, 2.6, 0.5],
                         x_length=5.4, y_length=2.2,
                         center=np.array([-3.85, 0.85, 0.0]))
        labels = axes.get_axis_labels(x_label=MathTex("x").scale(0.7),
                                      y_label=MathTex("y").scale(0.7))
        curve = func_curve(axes, F_MAIN, [0, 1.60], color=C_TERM)
        self.play(Create(axes), Write(labels), run_time=2.4)
        self.play(Create(curve), run_time=2.0)

        # ε 取 0.3 而不是 0.4：本章的落点是 δ = min(1, ε/3)，取 0.4 会得到
        # 0.133 这个除不尽的数，屏幕上的数值牌只能四舍五入，和右边的公式牌
        # 对不上（曾经写成 0.18，与 min(1, ε/3) 直接矛盾，学生一算就发现）。
        # 0.3 使 δ 恰好等于 0.1，与章末「ε=0.3 ⇒ δ=0.1」的数值牌一致。
        # δ 一律由公式算出，不手写常数。
        eps = 0.3
        band = hband(axes, A_MAIN, eps, 0, 2.0)
        self.play(FadeIn(band[0]), Create(band[1]), Create(band[2]),
                  run_time=1.6)
        self.wait(2.0)

        d = min(1.0, eps / 3.0)
        strip = vstrip(axes, X0, d, 0, 2.6, gap_ratio=0.20)
        self.play(FadeIn(strip[0]), FadeIn(strip[1]),
                  Create(strip[2]), Create(strip[3]), run_time=1.6)
        self.wait(1.4)

        # 曲线标注 y = x^2（真上标）。
        # 必须**画在 δ 竖带之后**：竖带是半透明填充，先画标签会被它压暗。
        # 位置贴左侧空白区（曲线在 x<0.5 时贴近横轴），避开竖带与 y 轴名。
        x2_lab = MathTex(r"y = x^{2}", color=C_TERM).scale(0.58)
        x2_lab.move_to(axes.c2p(0.56, 2.24))
        x2_lab.set_z_index(5)
        self.play(Write(x2_lab), run_time=1.0)
        self.wait(1.2)

        # δ 数值牌：放在坐标轴正下方，左栏自成一块，不去挤右半屏
        dtag = MathTex(rf"\delta = {d:g}", color=C_N).scale(0.55)
        dtag.move_to(np.array([-3.85, -0.62, 0.0]))
        self.play(Write(dtag), run_time=0.9)
        self.wait(1.2)

        self.caption("现在把 δ 算出来。目标：给定 ε，找一个 δ，"
                     "使 0 < |x-1| < δ 时必有 |x^2-1| < ε",
                     write_time=2.8)
        self.wait(2.4)

        # ------------------------------------------------------------------
        # 推导分五步，每步一句完整陈述，可以单独读通。
        # 逻辑链：拆因式 → 两个因子各自的界 → 相乘 → 反推 δ → 与前提取交集。
        #
        # 两点需要注意的地方：
        #   1) 不能写成 "|x+1| < 3 ⟹ |x²-1| < 3δ"。|x+1| 只是 |x²-1| 的一个
        #      因子，它有界推不出乘积有界，必须同时用上 |x-1| < δ，
        #      所以 |x-1| < δ 单独列成一步。
        #   2) δ 不是由 "令 3δ = ε" 得到的。方向是：要 |x²-1| < ε，
        #      只需 3δ ≤ ε，于是要求 δ ≤ ε/3；再加上 δ ≤ 1 的前提，
        #      两者取较小者才得到 min(1, ε/3)。
        # ------------------------------------------------------------------
        S_MATH = 0.56
        S_HINT = 0.44

        rows_spec = [
            (MathTex(r"|x^{2}-1| = |x-1|\cdot|x+1|",
                     color=WHITE).scale(S_MATH),
             "平方差拆开，拆出的第一个因子正是 |x-1|"),
            (MathTex(r"|x-1| < \delta", color=C_N).scale(S_MATH),
             "这是 δ 邻域本身给出的，直接可用"),
            (MathTex(r"\delta \leq 1 \ \Rightarrow\ |x+1| < 3",
                     color=WHITE).scale(S_MATH),
             "此时 x 落在 (0,2) 内，故 x+1 在 (1,3) 内"),
            (MathTex(r"|x^{2}-1| < \delta\cdot 3", color=WHITE).scale(S_MATH),
             "把上两个界相乘，得到 |x²-1| 的估计"),
            (MathTex(r"\delta = \min\left(1,\ \frac{\varepsilon}{3}\right)",
                     color=WHITE).scale(S_MATH),
             "要 3δ ≤ ε 就取 δ ≤ ε/3；又要 δ ≤ 1，故取较小者"),
        ]

        lines = []
        for expr, htext in rows_spec:
            h = rich_text(htext, color=WHITE, scale=S_HINT)
            lines.append(VGroup(expr, h).arrange(DOWN, buff=0.08))

        # 补齐高度：分式行天生更高，不补齐的话它上下的视觉空隙会偏小
        max_h = max(r.height for r in lines)
        for r in lines:
            pad = max_h - r.height
            if pad > 1e-6:
                spacer = Rectangle(width=0.01, height=pad,
                                   stroke_width=0, fill_opacity=0.0)
                spacer.move_to(r)
                r.add(spacer)

        steps = VGroup(*lines).arrange(DOWN, buff=0.30)
        if steps.width > 7.2:
            steps.scale_to_fit_width(7.2)
        if steps.height > 6.4:
            steps.scale_to_fit_height(6.4)
        steps.move_to(np.array([2.85, -0.35, 0.0]))

        # 逐行写入，每行配一句字幕，把「为什么这一步」说出来
        beats = [
            ("先把 |x²-1| 拆开。拆出来的第一个因子，正好就是 δ 管的那个距离",
             1.9),
            ("按 δ 邻域的定义，这个距离小于 δ —— 第一个因子有了界", 1.9),
            ("第二个因子 |x+1| 不是常数。但它随 x 变化，只要限制 x 的范围就能封顶",
             2.1),
            ("于是 |x²-1| 小于 δ 乘 3 —— 现在有了不含 x 的上界", 1.9),
            ("要让它小于 ε，只要 3δ ≤ ε，也就是 δ ≤ ε/3", 1.9),
        ]

        for i, line in enumerate(lines):
            text, wt = beats[i]
            self.caption(text, write_time=wt)
            self.play(Write(line), run_time=1.2)
            self.wait(1.5)

        self.caption("再加上前面 δ ≤ 1 的要求，两者取较小的那个，δ 就这么定下来了",
                     write_time=2.4)
        self.wait(2.8)

        self.fade(steps, run_time=1.0)

        # ---- 结算：把 δ 代回去，验证它确实管用 ----
        verify = MathTex(r"|x^{2}-1| < 3\delta \ \leq\ 3\cdot\frac{\varepsilon}{3}"
                         r" = \varepsilon",
                         color=C_EPS).scale(0.72)
        verify.move_to(np.array([2.85, 0.35, 0.0]))
        self.play(Write(verify), run_time=2.0)
        self.caption("代回去看：|x²-1| 一定小于 ε。δ = min(1, ε/3) 确实管用",
                     write_time=2.6)
        self.wait(3.4)

        # 数值验证牌：放在左栏、坐标轴下方，与右半屏的推导互不遮挡。
        # 字号从 0.46 提到 0.64 —— 它是「δ 由 ε 算出来」最直接的证据。
        chk = VGroup(
            MathTex(r"\varepsilon = 0.3 \ \Rightarrow\ \delta = 0.1",
                    color=C_EPS).scale(0.64),
            MathTex(r"\varepsilon = 0.03 \ \Rightarrow\ \delta = 0.01",
                    color=C_EPS).scale(0.64),
        ).arrange(DOWN, buff=0.16)
        chk.move_to(np.array([-3.85, -1.75, 0.0]))
        self.play(Write(chk), run_time=1.4)
        self.caption("ε 小 10 倍，δ 就跟着小 10 倍——同步退让", write_time=2.2)
        self.wait(3.4)

        self.fade(axes, labels, curve, band, strip, chk, dtag, verify, x2_lab)
        self.wait(0.8)

    # ------------------------------------------------------
    # 章 9：定义收束（配动态曲线）
    # ------------------------------------------------------
    def ch09_definition(self):
        """逐句讲定义，右侧用一个小窗口同步演示。

        每讲一句，右侧就更新一次 ε 与 δ，让口头讲的定义和画面上的
        图形变化保持对应。
        """
        self.caption("把刚才做的事，翻译成一句数学语言", write_time=2.2)
        self.wait(1.8)

        # ---- 左：定义三行 ----
        l1 = MathTex(r"\forall \varepsilon > 0,\ \exists \delta > 0,"
                     ).scale(0.82)
        l2 = rich_text("当 0 < |x - x₀| < δ 时", scale=0.66)
        l3 = MathTex(r"|f(x) - A| < \varepsilon", color=C_EPS).scale(0.82)
        eq = VGroup(l1, l2, l3).arrange(DOWN, buff=0.30)
        eq.move_to(np.array([-3.55, 0.75, 0.0]))

        # ---- 右：动态小窗 ----
        # 小窗坐标轴 4.6×2.7（主图 9.5×4.6）。要让同一条 ε 带在窗口里
        # 占的**相对高度**与主图一致，就按两轴 y 长度之比换算：
        #   主图带高占 2*eps/3.2，窗口里要占 2*eps'/3.2，
        #   而窗口每秒单位映射到更小的像素 → eps' 保持不变即可，
        #   真正的问题是窗口太矮、虚线太密。所以保持 eps 原值，
        #   只把虚线加粗、间距加大，让它在小尺寸下仍然读得出来。
        pan_ax = make_axes([0, 2.0, 0.5], [0, 3.2, 0.5],
                           x_length=4.6, y_length=2.7,
                           center=np.array([3.70, 0.60, 0.0]))
        pan_curve = func_curve(pan_ax, F_MAIN, [0, 2.0], color=C_TERM,
                               stroke_width=3.0)
        # 小窗里的极限点，让"在看同一个东西"一眼可读
        pan_pt = Dot(pan_ax.c2p(X0, A_MAIN), color=C_EPS, radius=0.065)
        # 小窗里同样标 y = x^2；窗口小，所以贴着曲线右上方放并适当放大。
        # z_index 抬高：竖带是半透明填充，不抬高会被压暗。
        pan_x2 = MathTex(r"y = x^{2}", color=C_TERM).scale(0.44)
        pan_x2.move_to(pan_ax.c2p(1.42, 2.90))
        pan_x2.set_z_index(5)
        self.play(Create(pan_ax), Create(pan_curve),
                  FadeIn(pan_pt), Write(pan_x2), run_time=1.9)
        PAN_SCALE = 1.0

        # ---- 第一句：ε 随便给 ----
        self.play(Write(l1), run_time=2.0)
        self.wait(1.6)
        c_eps = SurroundingRectangle(l1, color=C_EPS, buff=0.12)
        self.caption("第一句：你给多小的 ε 都行", write_time=2.0)
        self.play(Create(c_eps), run_time=1.1)
        self.wait(2.2)

        # 演示 ε 变三次：带跟着变。
        #
        # 注意必须用 **ReplacementTransform** 而不是 Transform：
        # hband / vstrip 每次按新的 ε、δ 重建，虚线段数、每段长度都不同，
        # Transform 会在新旧结构之间做点对点插值，段数不匹配时
        # 旧虚线的某些段**没有对应物可去**，就原地留在画面上 ——
        # 这正是"虚线变了、原来的虚线没被擦掉"的原因。
        # ReplacementTransform 直接把旧的整个移出场景，不留残影。
        cur_band = None
        cur_strip = None
        for eps, d in [(0.70, 0.30), (0.35, 0.15), (0.16, 0.07)]:
            nb = hband(pan_ax, A_MAIN, eps * PAN_SCALE, 0, 2.0, dash_len=0.09)
            ns = vstrip(pan_ax, X0, d * PAN_SCALE, 0, 3.2, gap_ratio=0.30)
            if cur_band is None:
                self.play(FadeIn(nb[0]), Create(nb[1]), Create(nb[2]),
                          FadeIn(ns[0]), FadeIn(ns[1]),
                          Create(ns[2]), Create(ns[3]),
                          run_time=1.3)
            else:
                self.play(ReplacementTransform(cur_band, nb),
                          ReplacementTransform(cur_strip, ns),
                          run_time=1.3)
            cur_band, cur_strip = nb, ns
            self.wait(1.4)

        # ---- 第二句：存在 δ ----
        self.play(Write(l2), run_time=1.8)
        self.wait(1.4)
        c_d = SurroundingRectangle(l2, color=C_N, buff=0.12)
        self.caption("第二句：我总能找到一条 δ 窄带", write_time=2.2)
        self.play(Create(c_d), run_time=1.1)
        self.wait(2.4)

        # ---- 第三句：带内都达标 ----
        self.play(Write(l3), run_time=1.6)
        self.wait(1.2)
        c_f = SurroundingRectangle(l3, color=C_EPS, buff=0.12)
        self.caption("第三句：窄带里的每个 x，都达标", write_time=2.2)
        self.play(Create(c_f), run_time=1.1)
        self.wait(2.4)

        # 再演示一轮：ε 继续缩小，曲线始终被压住（同样用 ReplacementTransform）
        for eps, d in [(0.09, 0.04), (0.05, 0.022)]:
            nb = hband(pan_ax, A_MAIN, eps * PAN_SCALE, 0, 2.0, dash_len=0.07)
            ns = vstrip(pan_ax, X0, d * PAN_SCALE, 0, 3.2, gap_ratio=0.30)
            self.play(ReplacementTransform(cur_band, nb),
                      ReplacementTransform(cur_strip, ns),
                      run_time=1.2)
            cur_band, cur_strip = nb, ns
            self.wait(1.2)

        self.caption("回头看，它说的和数列极限是一回事", write_time=2.2)
        self.wait(2.8)

        self.caption("只是「门」变成了「带」，「往右走」变成了「两边都来」",
                     write_time=2.4)
        self.wait(3.2)

        self.caption("你随便说多小的误差，我都能圈出够小的一块——这就是极限",
                     write_time=2.6)
        self.wait(4.0)

        self.play(FadeOut(c_eps), FadeOut(c_d), FadeOut(c_f), run_time=1.0)
        self.drop_caption(run_time=1.2)
        self.wait(1.0)

    # ------------------------------------------------------
    # 工具
    # ------------------------------------------------------
    def clear_all(self):
        """清场：把当前场景里的东西全部淡出（含字幕）。

        顺序很重要：字幕的 updater 会跟着 frame 变化做尺寸补偿，
        所以必须在**撤销字幕之后**再复位镜头，否则 updater 会在
        frame 还在变化的中间态里做一次补偿，字幕尺寸就漂了。
        """
        self.drop_caption(run_time=1.0)
        cap = getattr(self, "_cap", None)
        if self._zoom_now < 1.0 - 1e-9:
            self.reset_zoom(run_time=1.0)
            self._zoom_now = 1.0
        mobs = [m for m in self.mobjects if m is not cap]
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=1.2)
        self._bad = None
        self._store = {}

    # ------------------------------------------------------
    # 入口
    # ------------------------------------------------------
    def construct(self):
        self._store = {}
        self._bad = None
        self._cap = None
        self._zoom_now = 1.0
        self._cap_v_override = None

        self.ch00_title()
        self.ch01_from_gate_to_band()
        self.ch02_eps_band()
        self.ch03_delta_band()
        self.ch04_overshoot()
        self.ch05_shrink()          # 核心章节
        self.ch06_punctured()
        self.ch07_two_sides()
        self.ch08_formula()
        self.ch09_definition()
