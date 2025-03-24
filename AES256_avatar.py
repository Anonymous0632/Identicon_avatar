from PIL import Image, ImageDraw, PngImagePlugin
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import hashlib
import random

# ------------------ AES 加密部分 ------------------
def derive_nonce(text, key):
    """
    将文本和密钥拼接后计算 MD5 哈希，取前 8 字节作为 CTR 模式的 nonce（确定性）。
    """
    combined = (text + key).encode('utf-8')
    md5_hash = hashlib.md5(combined).digest()
    return md5_hash[:8]

def encrypt_text_ctr(text, key):
    """
    使用 AES CTR 模式对文本进行加密。
    
    参数：
      text: 待加密的文本（字符串）。
      key: 用户自定义的密钥（字符串）。
      
    返回：
      字节串：nonce（8 字节） + 密文
    """
    # 使用 SHA256 将密钥扩展为 32 字节（AES-256）
    key_bytes = hashlib.sha256(key.encode('utf-8')).digest()
    nonce = derive_nonce(text, key)
    cipher = AES.new(key_bytes, AES.MODE_CTR, nonce=nonce)
    ciphertext = cipher.encrypt(text.encode('utf-8'))
    return nonce + ciphertext

# ------------------ 预设调色板选择 ------------------
def get_palette(seed_bytes):
    """
    根据 AES 加密后种子（16 字节）最后一个字节取模 4 选择预设调色板：
      - 0：蓝橙调：背景：深蓝 (0, 51, 102)；填充：橙色 (255, 153, 51)
      - 1：赛博朋克调：背景：洋红 (255, 0, 255)；填充：青蓝 (0, 153, 204)
      - 2：互补色调：背景：紫色 (128, 0, 128)；填充：黄色 (255, 255, 0)
      - 3：柔和中性色调：背景：低饱和蓝绿 (102, 153, 153)；填充：温暖灰 (192, 192, 192)
    """
    mod_val = seed_bytes[-1] % 4
    if mod_val == 0:
        return ((0, 51, 102), (255, 153, 51))
    elif mod_val == 1:
        return ((255, 0, 255), (0, 153, 204))
    elif mod_val == 2:
        return ((128, 0, 128), (255, 255, 0))
    else:
        return ((102, 153, 153), (192, 192, 192))

# ------------------ 头像生成函数 ------------------
def generate_identicon_aes(text, key, image_size=5500, cell_size=500, fill_threshold=0.5, cell_gap=10):
    """
    使用 AES CTR 模式加密输入文本，并利用加密结果作为种子生成 Identicon 头像图像，
    美学设计如下：
      - 图像总尺寸为 5500×5500 像素，划分为 11×11 个网格（每网格 500×500 像素）。
      - 每个网格内部预留 cell_gap 像素（默认10像素）作为留白，实际绘制区域为 (cell_size - 2*cell_gap) 的正方形。
      - 整个图像仅使用两种颜色：背景色和填充色，均来源于预设调色板（根据 AES 种子选择）。
      - 对于每个网格，随机值小于 fill_threshold（默认0.5）时，在该网格内部绘制一个正方形（填充色）；否则保持背景色。
      - 不添加任何外部边框。
      - 将 AES 加密后的完整数据（以十六进制字符串形式）嵌入 PNG 元数据中。
    
    参数：
      text: 用于生成头像的文本（如邮箱或用户名）。
      key: AES 加密使用的自定义密钥（字符串）。
      image_size: 图像总尺寸，默认为5500 像素。
      cell_size: 每个网格单元的尺寸，默认为500 像素。
      fill_threshold: 填充网格的概率（0～1），默认0.5。
      cell_gap: 每个网格内部预留的留白边距（像素），默认10。
      
    返回：
      (image, metadata)
         image: 生成的 PIL Image 对象。
         metadata: 包含嵌入 AES 加密数据的 PNG 元数据对象。
    """
    # 1. 使用 AES CTR 模式加密文本
    encrypted = encrypt_text_ctr(text, key)
    # 2. 取加密结果的前 16 字节作为种子数据
    seed_bytes = encrypted[:16]
    
    # 3. 根据种子选择预设调色板：背景色和填充色
    palette = get_palette(seed_bytes)
    bg_color = palette[0]
    fill_color = palette[1]
    
    # 4. 计算网格数量（5500/500 = 11）
    grid_count = image_size // cell_size
    
    # 5. 使用种子数据初始化随机数生成器，确保相同输入生成相同图案
    seed_int = int.from_bytes(seed_bytes, byteorder='big')
    random.seed(seed_int)
    
    # 6. 创建图像（无外边框），尺寸为 image_size x image_size，填充背景色
    image = Image.new('RGB', (image_size, image_size), bg_color)
    draw = ImageDraw.Draw(image)
    
    # 7. 遍历每个网格，随机决定是否绘制正方形填充
    for row in range(grid_count):
        for col in range(grid_count):
            if random.random() < fill_threshold:
                x0 = col * cell_size
                y0 = row * cell_size
                # 内部绘制区域，预留 cell_gap 边距
                inner_rect = (x0 + cell_gap, y0 + cell_gap,
                              x0 + cell_size - cell_gap, y0 + cell_size - cell_gap)
                draw.rectangle(inner_rect, fill=fill_color)
    
    # 8. 将完整的 AES 加密数据（以十六进制字符串形式）嵌入 PNG 元数据中
    meta = PngImagePlugin.PngInfo()
    meta.add_text("encrypted", encrypted.hex())
    
    return image, meta

def main():
    # 提示用户输入生成头像的文本和加密密钥
    user_text = input("请输入用于生成头像的文本（例如邮箱或用户名）：")
    user_key = input("请输入加密密钥（任意字符串）：")
    
    img, meta = generate_identicon_aes(user_text, user_key)
    output_filename = "aes_avatar_square.png"
    img.save(output_filename, "PNG", pnginfo=meta)
    print(f"生成的头像图像已保存为 {output_filename}")
    img.show()

if __name__ == '__main__':
    main()
