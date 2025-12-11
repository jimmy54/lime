import secrets
import hashlib
import argparse
import os

KEY_FILE = os.path.join(os.path.dirname(__file__), "key.txt")


def generate_key(n_bytes: int = 32) -> str:
    """生成随机 key（URL-safe）并返回字符串。"""
    return secrets.token_urlsafe(n_bytes)


def hash_key(key: str) -> str:
    """对 key 做 SHA-256 并返回 hex 哈希。"""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def save_hash(hash_hex: str, path: str = KEY_FILE) -> None:
    """将哈希追加到文件（每行一个），如果已存在则不重复写入。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # 读取已有哈希以避免重复
    existing = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    existing.add(line)
    if hash_hex in existing:
        return
    with open(path, "a", encoding="utf-8") as f:
        f.write(hash_hex + "\n")


def verify_key(key: str, path: str = KEY_FILE) -> bool:
    """判断给定 key 的哈希是否存在于 key.txt 中。"""
    hash_hex = hash_key(key)
    if not os.path.exists(path):
        return False
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() == hash_hex:
                return True
    return False


def main():
    parser = argparse.ArgumentParser(
        description="生成随机 key 并保存其哈希，或校验给定 key。"
    )
    parser.add_argument(
        "--verify", "-v", metavar="KEY", help="校验给定的 KEY 是否在 key.txt 中"
    )
    args = parser.parse_args()

    if args.verify:
        ok = verify_key(args.verify)
        if ok:
            print("Valid: key 的哈希存在于 key.txt。")
        else:
            print("Invalid: key 的哈希不在 key.txt。")
    else:
        key = generate_key()
        print("Generated key:", key)
        h = hash_key(key)
        save_hash(h)
        print("Saved SHA-256 hash to", KEY_FILE)


if __name__ == "__main__":
    main()
