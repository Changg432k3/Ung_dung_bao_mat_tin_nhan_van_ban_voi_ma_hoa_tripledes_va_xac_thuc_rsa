from cryptography.hazmat.primitives import hashes, ciphers, padding
# Sửa lỗi ở đây:
from cryptography.hazmat.primitives.ciphers import algorithms # Thay thế deprecated_algorithms
from cryptography.hazmat.primitives.ciphers import modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
import os

# 1. Tạo cặp khóa RSA
def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

# 2. Mã hóa khóa TripleDES bằng RSA
def encrypt_3des_key(plaintext_3des_key, public_key):
    encrypted_key = public_key.encrypt(
        plaintext_3des_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(encrypted_key).decode('utf-8')

# 3. Tạo chữ ký RSA
def sign_data(data, private_key):
    signature = private_key.sign(
        data,
        asym_padding.PSS(
            mgf=asym_padding.MGF1(hashes.SHA256()),
            salt_length=asym_padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode('utf-8')

# 4. Mã hóa tin nhắn bằng TripleDES (CBC mode)
def encrypt_message(message, key, iv):
    padder = padding.PKCS7(64).padder()
    padded_data = padder.update(message) + padder.finalize()
    # Sửa lỗi ở đây:
    cipher = ciphers.Cipher(algorithms.TripleDES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(ciphertext).decode('utf-8')

# 5. Tạo giá trị băm SHA-256 (Đã điều chỉnh theo yêu cầu IV || ciphertext)
def create_hash_from_iv_ciphertext(iv_bytes, ciphertext_bytes):
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(iv_bytes)
    digest.update(ciphertext_bytes)
    return digest.finalize().hex()

# 6. Giải mã khóa TripleDES
def decrypt_3des_key(encrypted_key_b64, private_key):
    decoded_key = base64.b64decode(encrypted_key_b64)
    plaintext_key = private_key.decrypt(
        decoded_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return plaintext_key

# 7. Giải mã tin nhắn
def decrypt_message(ciphertext_b64, key, iv):
    # Sửa lỗi ở đây:
    cipher = ciphers.Cipher(algorithms.TripleDES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(base64.b64decode(ciphertext_b64)) + decryptor.finalize()
    unpadder = padding.PKCS7(64).unpadder()
    return unpadder.update(padded_data) + unpadder.finalize()

# 8. Xác thực chữ ký
def verify_signature(data, signature_b64, public_key):
    try:
        public_key.verify(
            base64.b64decode(signature_b64),
            data,
            asym_padding.PSS(
                mgf=asym_padding.MGF1(hashes.SHA256()),
                salt_length=asym_padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        return False

# Hàm tiện ích để serialize/deserialize khóa công khai
def serialize_public_key(public_key):
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

def deserialize_public_key(pem_key_data):
    return serialization.load_pem_public_key(
        pem_key_data.encode('utf-8'),
        backend=default_backend()
    )

# Hàm tiện ích để serialize/deserialize khóa riêng tư (chỉ để lưu trữ nếu cần, không nên truyền qua mạng)
def serialize_private_key(private_key):
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

def deserialize_private_key(pem_key_data):
    return serialization.load_pem_private_key(
        pem_key_data.encode('utf-8'),
        password=None,
        backend=default_backend()
    )