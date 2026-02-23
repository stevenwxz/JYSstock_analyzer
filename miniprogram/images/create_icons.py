#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速生成小程序TabBar图标
使用PIL库创建简单的占位符图标
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    print("PIL库已安装")
except ImportError:
    print("错误: 未安装PIL库")
    print("请运行: pip install Pillow")
    exit(1)


def create_home_icon(filename, color, size=81):
    """创建首页图标(房子形状)"""
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # 绘制房子
    # 屋顶(三角形)
    roof = [(size//2, size//4), (size//4, size//2), (size*3//4, size//2)]
    draw.polygon(roof, fill=color)

    # 房身(矩形)
    house = [(size//4, size//2), (size*3//4, size*3//4)]
    draw.rectangle(house, fill=color)

    # 门(小矩形)
    door = [(size*2//5, size*3//5), (size*3//5, size*3//4)]
    draw.rectangle(door, fill=(255, 255, 255))

    img.save(filename)
    print(f"[OK] Created: {filename}")


def create_history_icon(filename, color, size=81):
    """创建历史图标(时钟形状)"""
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # 绘制圆形外框
    padding = 10
    circle_bbox = [padding, padding, size-padding, size-padding]
    draw.ellipse(circle_bbox, outline=color, width=4)

    # 绘制时针(短)
    center = size // 2
    draw.line([center, center, center, center-15], fill=color, width=3)

    # 绘制分针(长)
    draw.line([center, center, center+15, center], fill=color, width=2)

    img.save(filename)
    print(f"[OK] Created: {filename}")


def create_simple_icon(filename, color, icon_type='circle', size=81):
    """创建简单的几何图形图标"""
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    padding = 15

    if icon_type == 'circle':
        # 圆形
        draw.ellipse([padding, padding, size-padding, size-padding], fill=color)
    elif icon_type == 'square':
        # 方形
        draw.rectangle([padding, padding, size-padding, size-padding], fill=color)
    elif icon_type == 'triangle':
        # 三角形
        triangle = [
            (size//2, padding),
            (padding, size-padding),
            (size-padding, size-padding)
        ]
        draw.polygon(triangle, fill=color)

    img.save(filename)
    print(f"[OK] Created: {filename}")


def main():
    """主函数"""
    print("=" * 60)
    print("          微信小程序图标生成工具")
    print("=" * 60)
    print()

    # 定义颜色
    GRAY = (102, 102, 102)      # #666666
    GREEN = (26, 173, 25)       # #1aad19

    print("开始生成图标...")
    print()

    # 方案1: 使用形状图标(推荐)
    print("方案1: 使用形状图标")
    try:
        create_home_icon('home.png', GRAY)
        create_home_icon('home_active.png', GREEN)
        create_history_icon('history.png', GRAY)
        create_history_icon('history_active.png', GREEN)
        print()
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        print()

        # 备用方案: 使用简单几何图形
        print("使用备用方案: 简单几何图形")
        create_simple_icon('home.png', GRAY, 'square')
        create_simple_icon('home_active.png', GREEN, 'square')
        create_simple_icon('history.png', GRAY, 'circle')
        create_simple_icon('history_active.png', GREEN, 'circle')
        print()

    print("=" * 60)
    print("          图标生成完成!")
    print("=" * 60)
    print()
    print("Generated files:")
    print("  [OK] home.png")
    print("  [OK] home_active.png")
    print("  [OK] history.png")
    print("  [OK] history_active.png")
    print()
    print("提示:")
    print("  - 这些是临时占位符图标,建议使用专业工具优化")
    print("  - 可以从IconFont等网站下载更精美的图标")
    print("  - 图标尺寸: 81px × 81px")
    print()


if __name__ == '__main__':
    main()
