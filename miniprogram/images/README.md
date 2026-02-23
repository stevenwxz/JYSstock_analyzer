# 小程序图标资源

## 📋 需要准备的图标

### TabBar 图标 (必需)

小程序底部导航栏需要以下图标,每个图标需要**普通状态**和**选中状态**两个版本:

#### 1. 首页图标
- **文件名**:
  - `home.png` (普通状态)
  - `home_active.png` (选中状态)
- **尺寸**: 81px × 81px
- **格式**: PNG (透明背景)
- **颜色**:
  - 普通: 灰色 (#666666)
  - 选中: 绿色 (#1aad19)
- **图标建议**: 房子、主页、仪表盘等

#### 2. 历史记录图标
- **文件名**:
  - `history.png` (普通状态)
  - `history_active.png` (选中状态)
- **尺寸**: 81px × 81px
- **格式**: PNG (透明背景)
- **颜色**:
  - 普通: 灰色 (#666666)
  - 选中: 绿色 (#1aad19)
- **图标建议**: 时钟、日历、列表等

---

## 🎨 图标设计规范

### 尺寸要求
- **TabBar图标**: 81px × 81px (推荐)
- **小程序图标**: 144px × 144px (发布时需要)

### 设计风格
- 扁平化设计
- 线条清晰
- 识别度高
- 与品牌色调一致

### 配色方案
- **主色**: #1aad19 (绿色,代表涨)
- **辅助色**: #666666 (灰色)
- **强调色**: #ee4747 (红色,代表跌)

---

## 🛠️ 制作图标的方法

### 方法1: 使用在线图标库 (推荐)

**IconFont (阿里巴巴矢量图标库)**
1. 访问: https://www.iconfont.cn/
2. 搜索关键词: "首页"、"历史"
3. 选择喜欢的图标加入购物车
4. 下载PNG格式 (81px × 81px)
5. 使用在线工具更改颜色:
   - https://www.photopea.com/ (免费在线PS)
   - 调整颜色为 #666666 (普通) 和 #1aad19 (选中)

**Font Awesome**
1. 访问: https://fontawesome.com/
2. 搜索图标
3. 下载PNG格式

### 方法2: 使用设计工具

**Figma (免费)**
1. 访问: https://www.figma.com/
2. 创建 81px × 81px 画布
3. 使用形状工具绘制图标
4. 导出为PNG

**Canva (免费)**
1. 访问: https://www.canva.com/
2. 创建自定义尺寸 81px × 81px
3. 搜索图标元素
4. 下载为PNG

### 方法3: AI生成 (快速)

使用AI工具生成简单图标:
- DALL-E
- Midjourney
- 稳定扩散 (Stable Diffusion)

**提示词示例**:
```
"simple flat icon of a home, minimalist, green color,
transparent background, 81x81 pixels"
```

---

## 📁 文件组织

图标文件应放置在此目录下:

```
miniprogram/images/
├── home.png              (首页-普通)
├── home_active.png       (首页-选中)
├── history.png           (历史-普通)
└── history_active.png    (历史-选中)
```

---

## ✅ 临时解决方案 (开发阶段)

如果暂时没有图标,可以:

1. **使用纯色方块代替**
   - 创建 81px × 81px 的纯色PNG图片
   - 普通状态: 灰色方块
   - 选中状态: 绿色方块

2. **使用文字图标**
   - 在小程序中使用文字代替图标
   - 修改 `app.json` 中的 TabBar 配置

3. **暂时隐藏TabBar**
   - 注释掉 `app.json` 中的 `tabBar` 配置
   - 使用顶部导航代替

---

## 🎯 快速生成图标脚本 (Python)

使用Python PIL库快速生成占位符图标:

```python
from PIL import Image, ImageDraw

def create_icon(filename, color, size=81):
    """创建简单的圆形图标"""
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # 绘制圆形
    draw.ellipse([10, 10, size-10, size-10], fill=color)

    # 保存
    img.save(filename)
    print(f"已创建: {filename}")

# 创建首页图标
create_icon('home.png', (102, 102, 102))  # 灰色
create_icon('home_active.png', (26, 173, 25))  # 绿色

# 创建历史图标
create_icon('history.png', (102, 102, 102))  # 灰色
create_icon('history_active.png', (26, 173, 25))  # 绿色

print("图标创建完成!")
```

**使用方法**:
```bash
pip install Pillow
cd miniprogram/images
python create_icons.py
```

---

## 📞 需要帮助?

如果需要专业设计师设计图标:
- **猪八戒网**: https://www.zbj.com/
- **Fiverr**: https://www.fiverr.com/
- **淘宝**: 搜索"小程序图标设计"

预算参考: 50-200元可获得一套完整小程序图标

---

**当前状态**: ⚠️ 图标未添加

**下一步**: 根据上述方法准备图标,并放置在此目录下
