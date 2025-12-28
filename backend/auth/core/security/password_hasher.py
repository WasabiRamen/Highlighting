import re
import bcrypt
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

# 1️⃣ bcrypt 전용 thread pool 생성
def get_bcrypt_pool():
    cpu_count = os.cpu_count() or 1
    max_workers = max(1, cpu_count * 2)  # CPU-bound용 적정 스레드 수
    return ThreadPoolExecutor(max_workers=max_workers)

bcrypt_pool = get_bcrypt_pool()


class PasswordHasher:
    """
    비밀번호 검증 및 해싱 유틸리티
    """
    def __init__(self, bcrypt_rounds: int = 16):
        self.__BCRYPT_ROUNDS: int = bcrypt_rounds
        self.__password_regex: str = r"^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{8,16}$"
    
    class passwordValidationError(Exception):
        """비밀번호 정규식 실패 예외"""
        pass

    class passwordVerificationError(Exception):
        """비밀번호 검증 실패 예외"""
        pass

    def validate_password(self, plain_password: str) -> None:
        """비밀번호 정책(정규식) 검증"""
        if not re.fullmatch(self.__password_regex, plain_password):
            raise PasswordHasher.passwordValidationError("비밀번호 정책에 맞지 않습니다.")

    async def verify_password(self, plain_password: str, hashed_password: str) -> None:
        """평문 비밀번호와 해시를 비교"""
        loop = asyncio.get_running_loop()

        def _verify():
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        
        if not await loop.run_in_executor(bcrypt_pool, _verify):
            raise PasswordHasher.passwordVerificationError("비밀번호가 일치하지 않습니다.")

    async def hash_password(self, plain_password: str) -> str:
        """비밀번호를 bcrypt로 해싱"""
        loop = asyncio.get_running_loop()

        def _hash():
            salt = bcrypt.gensalt(rounds=self.__BCRYPT_ROUNDS)
            hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        
        return await loop.run_in_executor(bcrypt_pool, _hash)
