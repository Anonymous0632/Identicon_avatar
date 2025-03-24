from PIL import Image, ImageDraw, PngImagePlugin
import hashlib
import random

# ------------------ 预设调色板 ------------------
def get_palette(hash_bytes):
    """
    根据 MD5 哈希的最后一个字节取模 4 选择预设调色板：
      - 0：蓝橙调：背景：深蓝 (0,51,102)；填充：橙色 (255,153,51)
      - 1：赛博朋克调：背景：洋红 (255,0,255)；填充：青蓝 (0,153,204)
      - 2：互补色调：背景：紫色 (128,0,128)；填充：黄色 (255,255,0)
      - 3：柔和中性色调：背景：低饱和蓝绿 (102,153,153)；填充：温暖灰 (192,192,192)
    """
    mod_val = hash_bytes[-1] % 4
    if mod_val == 0:
        return ((0, 51, 102), (255, 153, 51))
    elif mod_val == 1:
        return ((255, 0, 255), (0, 153, 204))
    elif mod_val == 2:
        return ((128, 0, 128), (255, 255, 0))
    else:
        return ((102, 153, 153), (192, 192, 192))

# ------------------ 头像生成函数 ------------------
def generate_identicon_hash_tone(text, image_size=5500, cell_size=500, fill_threshold=0.5,
                                  cell_gap=10):
    """
    使用 MD5 哈希对输入文本进行哈希，并以此为种子生成一个两色方案的 Identicon 头像图像。
    
    美学设计：
      - 图像总尺寸：image_size x image_size（默认为5500×5500 像素）
      - 网格：每个网格 cell_size x cell_size（默认为500×500 像素），共 image_size/cell_size 个网格（5500/500=11）
      - 每个网格内部预留 cell_gap 像素作为留白，实际绘制区域为 (cell_size - 2*cell_gap) 的正方形
      - 整个头像仅使用两种颜色（来自预设调色板）：背景色与填充色
      - 对于每个网格，若随机值小于 fill_threshold，则在该网格内部绘制一个正方形（填充色）；否则保持背景色
      - 不在头像最外圈添加任何边框
      - 同时将 MD5 哈希值（十六进制字符串）嵌入 PNG 元数据中
      
    参数：
      text: 用于生成头像的文本（例如邮箱或用户名）。
      image_size: 图像的总尺寸（正方形），默认 5500 像素。
      cell_size: 每个网格的尺寸，默认 500 像素。
      fill_threshold: 每个网格填充颜色的概率（0～1），默认 0.5。
      cell_gap: 每个网格内部留白边距（像素），默认 10。
      
    返回：
      (image, metadata)
         image：生成的 PIL Image 对象（最终头像图像）。
         metadata：包含嵌入 MD5 哈希（十六进制字符串）的 PNG 元数据对象。
    """
    # 1. 计算 MD5 哈希
    hash_obj = hashlib.md5(text.encode('utf-8'))
    hash_bytes = hash_obj.digest()
    hash_hex = hash_obj.hexdigest()
    
    # 2. 根据哈希选择预设调色板
    palette = get_palette(hash_bytes)
    bg_color = palette[0]
    fill_color = palette[1]
    
    # 3. 计算网格数量（例如：5500/500 = 11）
    grid_count = image_size // cell_size
    
    # 4. 使用 MD5 哈希作为种子，确保相同输入生成相同图案
    seed_int = int.from_bytes(hash_bytes, byteorder='big')
    random.seed(seed_int)
    
    # 5. 创建图像，尺寸为 image_size x image_size，填充背景色（不添加外边框）
    image = Image.new('RGB', (image_size, image_size), bg_color)
    draw = ImageDraw.Draw(image)
    
    # 6. 遍历每个网格
    for row in range(grid_count):
        for col in range(grid_count):
            if random.random() < fill_threshold:
                # 网格左上角坐标
                x0 = col * cell_size
                y0 = row * cell_size
                # 定义内部绘制区域（预留 cell_gap 作为留白）
                inner_rect = (x0 + cell_gap, y0 + cell_gap,
                              x0 + cell_size - cell_gap, y0 + cell_size - cell_gap)
                # 绘制方形（直接填充矩形区域）
                draw.rectangle(inner_rect, fill=fill_color)
    
    # 7. 将 MD5 哈希嵌入 PNG 元数据
    meta = PngImagePlugin.PngInfo()
    meta.add_text("hash", hash_hex)
    
    return image, meta

def main():
    user_text = input("请输入用于生成头像的文本（例如邮箱或用户名）：")
    img, meta = generate_identicon_hash_tone(user_text)
    output_filename = "hash_avatar_square.png"
    img.save(output_filename, "PNG", pnginfo=meta)
    print(f"生成的头像图像已保存为 {output_filename}")
    img.show()

if __name__ == '__main__':
    main()

