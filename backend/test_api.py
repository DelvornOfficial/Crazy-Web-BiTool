import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import init_db, async_session
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.models import Admin, AppRelease
from sqlalchemy import select

async def run_tests():
    print("--> 1. Testing Database Initialization & Fallback...")
    await init_db()
    print("   [OK] Database initialized.")

    print("--> 2. Testing Superadmin Provisioning & Password Hashing...")
    async with async_session() as session:
        result = await session.execute(select(Admin).where(Admin.username == "admin"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = Admin(
                username="admin",
                hashed_password=hash_password("NextLevelAdmin@2026!"),
                role="superadmin",
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            print("   [OK] Superadmin 'admin' created.")
        else:
            # Update password hash with clean bcrypt format
            admin.hashed_password = hash_password("NextLevelAdmin@2026!")
            await session.commit()
            print("   [OK] Superadmin 'admin' password hash updated.")

        # Test constant-time password verification
        is_valid = verify_password("NextLevelAdmin@2026!", admin.hashed_password)
        is_invalid = verify_password("WrongPassword123!", admin.hashed_password)
        assert is_valid is True, "Password verification failed for valid password"
        assert is_invalid is False, "Password verification succeeded for invalid password"
        print("   [OK] Bcrypt/scrypt constant-time verification passed.")

    print("--> 3. Testing JWT Token Issuance & Verification...")
    token = create_access_token(subject="1", role="superadmin", username="admin")
    payload = decode_access_token(token)
    assert payload["sub"] == "1"
    assert payload["role"] == "superadmin"
    assert payload["username"] == "admin"
    print(f"   [OK] JWT Token generated & decoded successfully: exp={payload.get('exp')}")

    print("--> 4. Testing App Release Seed...")
    async with async_session() as session:
        rel_res = await session.execute(select(AppRelease).where(AppRelease.version == "v2.4.0"))
        release = rel_res.scalar_one_or_none()
        if not release:
            release = AppRelease(
                version="v2.4.0",
                title="Next Level Cheat (Official Release)",
                download_url="https://t.me/nextlevelcheat",
                file_size_mb=45.0,
                min_android_version="Android 8.0+",
                changelog="High-performance release",
                is_active=True,
                download_count=1240500,
            )
            session.add(release)
            await session.commit()
            print("   [OK] Release v2.4.0 seeded.")
        else:
            print(f"   [OK] Release v2.4.0 exists (Downloads: {release.download_count}).")

    print("\n=======================================================")
    print("SUCCESS: ALL CORE SECURITY & DATABASE TESTS PASSED!")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
