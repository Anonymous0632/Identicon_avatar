# restore_text.py

from PIL import Image
from Crypto.Cipher import AES
import hashlib
from Crypto.Util.Padding import unpad

def decrypt_text_ctr(encrypted, key):
    """
    使用 AES CTR 模式解密密文，恢复原始文本。
    
    参数：
      encrypted: 包含 nonce（前8字节）+ 密文 的字节串。
      key: 与加密时相同的密钥（字符串）。
    
    返回：
      解密后的原始文本（字符串）。
    """
    key_bytes = hashlib.sha256(key.encode('utf-8')).digest()
    nonce = encrypted[:8]
    ciphertext = encrypted[8:]
    cipher = AES.new(key_bytes, AES.MODE_CTR, nonce=nonce)
    plaintext = cipher.decrypt(ciphertext)
    return plaintext.decode('utf-8')

def main():
    # 提示用户输入图像文件路径
    filename = input("请输入包含嵌入密文的图像文件路径（例如 avatar.png）：")
    user_key = input("请输入加密密钥：")
    
    try:
        image = Image.open(filename)
    except Exception as e:
        print("无法打开图像文件：", e)
        return
    
    # 从 PNG 元数据中提取嵌入的加密数据
    enc_hex = image.info.get("encrypted")
    if not enc_hex:
        print("图像中未找到嵌入的密文。")
        return
    encrypted = bytes.fromhex(enc_hex)
    
    try:
        original_text = decrypt_text_ctr(encrypted, user_key)
        print("还原的原始文本为：", original_text)
    except Exception as e:
        print("解密出错：", e)

if __name__ == '__main__':
    main()
