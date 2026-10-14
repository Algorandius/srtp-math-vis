from manim import *


class RiemannSum(Scene):
    """概念动画：定积分的黎曼和逼近

    教学意图：让学生看到「细分越密，矩形面积之和越接近曲线下的真实面积」
    """

    def construct(self):
        # ---------- 1. 坐标系与曲线 ----------
        axes = Axes(
            x_range=[0, 4, 1],
            y_range=[0, 6, 1],
            x_length=8,
            y_length=5,
        )
        labels = axes.get_axis_labels(x_label="x", y_label="y")

        # 中文用 Text（LaTeX 不支持中文），数学符号才用 MathTex
        title = Text("定积分：矩形逼近曲线下面积", font="Microsoft YaHei")
        title.scale(0.55).to_edge(UP)

        curve = axes.plot(lambda x: x**2 / 3, x_range=[0, 4], color=YELLOW)

        self.play(Create(axes), Write(labels))
        self.play(Write(title))
        self.wait(0.4)
        self.play(Create(curve), run_time=2)
        self.wait(0.4)

        # ---------- 2. 逐步细分：dx 越来越小 ----------
        for dx in [1.0, 0.5, 0.25]:
            rects = axes.get_riemann_rectangles(
                curve,
                x_range=[0, 4],
                dx=dx,
                stroke_width=0.5,
                stroke_color=WHITE,
                fill_opacity=0.6,
            )
            n = int(4 / dx)
            tag = MathTex(f"n={n}").to_corner(UR)

            self.play(Create(rects), run_time=1.5)
            self.play(FadeIn(tag))
            self.wait(0.6)
            self.play(FadeOut(rects), FadeOut(tag))
            self.wait(0.2)

        self.wait(1)
