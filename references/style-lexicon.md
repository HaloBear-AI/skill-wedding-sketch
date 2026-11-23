# 手绘风格词库

从每组挑选能在成品上明确看见的词，用于 [提示词模板](prompt-templates.md) 的画风与媒介段。优先从参考图提取设计特征，再用词库确定笔触、上色和标注方式。

## 表现媒介

| 元素 | 中文 | English | 画面用法 |
| --- | --- | --- | --- |
| 纸底 | 米白轻做旧水彩纸 | warm ivory, lightly aged watercolor paper | 让淡纹理贯穿整页，淡化纸边和脏渍，给标题与小字留干净区域。 |
| 纸纹 | 轻微冷压颗粒 | subtle cold-pressed paper grain | 保留笔端擦过纸面的细颗粒，控制在近看才明显的程度。 |
| 主轮廓 | 针管笔细线勾轮廓 | thin technical-pen contours | 主结构轮廓清楚，笔画略有轻重变化。 |
| 次级线 | 轻量排线与淡阴影 | light hatching and soft cast shadows | 只在布褶内侧、花丛深处及落地接触处表现体积。 |
| 水彩 | 透明薄染、局部叠色 | transparent watercolor washes with selective glazing | 主花以薄染叠层，暖纸作为高光，轮廓处保留少量自然晕开。 |
| 马克笔 | 淡马克笔铺色 | light marker blocking | 用在框架、台面和前后层面的浅色区块，沿材质纹理或结构方向走笔。 |
| 留白 | 纸白高光、疏朗留白 | reserved paper highlights and open negative space | 用干净底纸表现纱的透光、浅花边缘和文字区。 |

## 文字、引线与视图

| 元素 | 中文 | English | 画面用法 |
| --- | --- | --- | --- |
| 标题 | 手写标题配一笔下划线 | hand-lettered title with a single hand-drawn underline | 标题笔画比正文略重，下划线轻细，独立留空。 |
| 中文字 | 清晰端正的简体手写字 | legible upright Simplified Chinese hand lettering | 字形完整、字距均匀、深墨落在浅底，并复现清单里的精确文字。 |
| 英文字 | 清晰短词手写，易读数字 | legible English hand lettering with clear numerals | 仅在选择英文图内文字时使用英文标注。数字写全，单位按清单放置。 |
| 引线 | 细引线与明确端点 | fine leader lines with clear endpoints | 从短标注连到具体构件，优先用简单折线，绕开其他引线与文字。 |
| 三视图 | 对应位置的正交投影小图 | aligned orthographic thumbnails | 按同一正面方向与比例关系画正视、侧视和俯视，弱化辅助线。 |
| 尺寸线 | 细尺寸界线、短箭头、毫米数字 | fine extension lines, small dimension arrows, millimeter values | 两端对齐同一外包络，数字居中，按尺寸清单逐字标写。 |
| 分解图 | 轻量轴测分解示意 | lightly rendered exploded axonometric sketch | 拉开主要构件并沿原安装方向对位，保持与三视图的结构关系一致。 |
| 细节圈 | 淡墨椭圆或圆形放大窗 | fine-ink oval or circular detail insets | 每窗聚焦一个部位的褶、纹、花层或底座轮廓。 |

默认用 3:4 竖版，米白轻做旧水彩纸、针管笔线稿、水彩薄染配淡马克笔。标题贴近上缘并配手绘下划线，上区约 55%、中下区约 35%、底区约 10%。类型 B 优先沿用可辨认的版式与笔触。模块的详细排位与变体见 [方案板版式](board-layout-spec.md)。

将图内文字集中在按位置分组的清单，逐字放在引号内。引线主词最多 8 个汉字，副词最多 6 个汉字，单块说明最多 3 行，默认全图最多 28 个字块。字形不稳时用最少文字模式保留关键信息，或生成无字底图并按完整清单后期加字。

## 可直接采用的画风句

中文

> 使用米白轻做旧水彩纸。以针管笔细线勾出轮廓，用透明水彩薄染和淡马克笔叠出材质层次。用清晰端正的手写字、细引线及简洁的毫米标注呈现婚礼设计。

English

> Use warm ivory, lightly aged watercolor paper. Draw thin technical-pen contours and layer transparent watercolor washes with light marker accents. Present the wedding design with legible hand lettering, fine leader lines, and clear millimeter dimensions.
