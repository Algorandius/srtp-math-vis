from manim import *


class DemoScene(Scene):
    """冒烟测试：验证坐标系、函数图像、LaTeX 公式、动画均可用"""

    def construct(self):
        # 1. 建立坐标系
        axes = Axes(x_range=[-3, 3, 1], y_range=[-1, 8, 1])
        self.play(Create(axes))
        self.wait(0.5)

        # 2. 画出抛物线 + LaTeX 公式
        graph = axes.plot(lambda x: x**2, color=BLUE)
        label = MathTex("y = x^2").to_corner(UL)
        self.play(Create(graph), Write(label), run_time=2)
        self.wait(0.5)

        # 3. 在曲线上放一个点
        dot = Dot(axes.c2p(2, 4), color=RED)
        self.play(FadeIn(dot, scale=0.5))
        self.wait(0.5)

        # 4. 让点沿曲线移动到另一侧
        self.play(dot.animate.move_to(axes.c2p(-2, 4)), run_time=2)
        self.wait(1)
