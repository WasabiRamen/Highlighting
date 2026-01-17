import os
import json
import argparse


# .key 파일은 아래와 같이 json 형식으로 저장
"""
{
    "version": 1,
    "key": "base64-encoded-key-data"
}
"""


# 키 버전은 1, 2, 3 ... 순으로 관리
def get_next_key_version(path: str) -> int:
    if not os.path.exists(path):
        return 1  # 첫 번째 키 버전

    existing_files = os.listdir(path)
    versions = []
    for filename in existing_files:
        if filename.endswith(".key"):
            try:
                with open(os.path.join(path, filename), "r") as f:
                    data = json.load(f)
                    versions.append(int(data.get("version", 0)))
            except ValueError:
                continue

    if not versions:
        return 1
    
    return max(versions) + 1


def generate_master_key(path: str):
    # AES-256 키 생성
    master_key = os.urandom(32)  # 256-bit
    next_key_version = get_next_key_version(os.path.dirname(path))

    # 디렉토리 없으면 생성
    dir_path = os.path.dirname(path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

    # 파일로 저장
    with open(path, "w") as f:
        json.dump({
            "version": next_key_version,
            "key": master_key.hex()
        }, f)
    print(f"Master key generated and saved as {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate AES-256 master key")
    parser.add_argument("--path", type=str, default="./master.key",
                        help="Path to save the master key")
    args = parser.parse_args()

    generate_master_key(args.path)
