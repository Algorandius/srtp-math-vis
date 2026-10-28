# srtp-math-vis

数学核心概念可视化动画库。每支动画是一个独立的 manim 场景，共用一套配色与组件。

## 环境

- Python 3.14
- manim 0.22.0
- LaTeX（MiKTeX），用于渲染公式

安装依赖：

```
pip install -r requirements.txt
```

## 目录结构

```
scenes/      动画场景源码
  _components.py      公共组件：配色、坐标系、字幕混排、ε 带、δ 竖带
  sequence_limit.py   数列极限的 ε-N 定义
  function_limit.py   函数的极限 ε-δ 定义
  captiontext.md      字幕文案，改字只改这里
  caption_keys.json   文案索引，供代码定位，不必手动修改
docs/        技术说明
reference/   试验性脚本，不作为正式内容
tools/       辅助工具
assets/      素材（背景音乐）
media/       渲染产物，不入库
```

## 渲染

预览用 480p15，几十秒即可出片；确定效果后再上高画质。

```
python -m manim -ql scenes/function_limit.py FunctionLimit    # 480p15
python -m manim -qh scenes/function_limit.py FunctionLimit    # 1080p60
python -m manim -qk scenes/function_limit.py FunctionLimit    # 2160p60
```

数列极限那支同理，把文件名与场景名换成 `sequence_limit.py` / `SequenceLimit`。

## 修改字幕

`scenes/captiontext.md` 是字幕的唯一来源，格式为一行 key、下一行正文：

```
[ch02_distance]
x 越靠近 1，纵坐标就越靠近 1——还是「距离」那件事
```

改完直接重新渲染即可，不需要改代码。数学部分直接写 `x_0`、`ε`、`x^2`、`ε/3`，
程序会自动转换成下标、上标与分数。

`[key]` 那一行是索引，改动会导致找不到文案，需要与 `caption_keys.json` 保持一致。

## 加背景音乐

```
python tools/add_bgm.py "media/videos/xxx/yyy.mp4" -18
```

输出在 `media/with_bgm/`，不覆盖原视频。视频流直接复制，不重新编码。

## 配色约定

| 颜色 | 含义 |
|---|---|
| 橙 | 被检验的对象（数列的项 / 函数曲线） |
| 绿 | 极限值与 ε 带 |
| 红 | 落在带外的不合格部分 |
| 蓝 | 门 N / δ 竖带 |
| 灰 | 辅助线与已淡出的元素 |

一个颜色只对应一个含义，全片不变。
