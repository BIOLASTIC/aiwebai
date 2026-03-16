#!/usr/bin/env python3
"""
Test script for Chrome profile import and UTF-8 validation.
This script tests the fix for the encryption utility UTF-8 encoding issue.
"""

import asyncio
from backend.app.db.engine import get_db
from backend.app.db.models import Account, User, AccountAuthMethod
from backend.app.utils.encryption import encrypt, decrypt
from backend.app.accounts.manager import account_manager
from fastapi import HTTPException


async def test_encryption():
    """Test that encryption/decryption works with UTF-8 characters."""
    print("=" * 60)
    print("Testing UTF-8 Encryption Utility")
    print("=" * 60)

    test_strings = [
        "Simple text",
        "Text with emoji 🎉",
        "Text with special characters: !@#$%^&*()",
        "Unicode: 日本語 中文 العربية",
        "Mixed content: Test123 ABC",
    ]

    for test_str in test_strings:
        try:
            encrypted = encrypt(test_str)
            decrypted = decrypt(encrypted)
            assert test_str == decrypted, (
                f"Encryption/decryption failed: {test_str} != {decrypted}"
            )
            print(f"✓ Test passed: '{test_str}'")
        except Exception as e:
            print(f"✗ Test failed: '{test_str}' - {str(e)}")
            return False

    print("\n✓ All encryption tests passed!")
    return True


async def test_chrome_import():
    """Test Chrome profile import functionality."""
    print("\n" + "=" * 60)
    print("Testing Chrome Profile Import")
    print("=" * 60)

    async for db in get_db():
        try:
            # Create a test account with special characters in credentials
            test_label = "Test Account with UTF-8"
            test_credentials = "Test_Credentials_123|Test_TS_456"

            account = Account(
                label=test_label,
                provider="webapi",
                owner_user_id=1,  # Default admin user
                status="active",
                health_status="unknown",
            )
            db.add(account)
            await db.flush()

            auth_method = AccountAuthMethod(
                account_id=account.id,
                auth_type="cookie",
                encrypted_credentials=encrypt(test_credentials),
            )
            db.add(auth_method)
            await db.commit()

            print(f"✓ Created test account: {test_label} (ID: {account.id})")

            # Verify the credentials were encrypted/decrypted correctly
            decrypted_credentials = decrypt(auth_method.encrypted_credentials)
            assert decrypted_credentials == test_credentials, "Decryption failed!"
            print(
                f"✓ Credentials encrypted/decrypted correctly: {decrypted_credentials}"
            )

            # Refresh account manager to pick up the new account
            await account_manager.refresh_accounts()
            print("✓ Account manager refreshed successfully")

            return True

        except Exception as e:
            print(f"✗ Test failed: {str(e)}")
            import traceback

            traceback.print_exc()
            return False


async def test_validation():
    """Test account validation functionality."""
    print("\n" + "=" * 60)
    print("Testing Account Validation")
    print("=" * 60)

    async for db in get_db():
        try:
            # Try to validate an account
            await account_manager.refresh_accounts()
            adapter = account_manager.get_adapter_for_account(1)

            if adapter:
                print("✓ Adapter retrieved successfully")
                is_healthy = await adapter.health_check()
                print(f"✓ Health check completed: {is_healthy}")
                return True
            else:
                print("✗ No adapter found for account")
                return False

        except Exception as e:
            print(f"✗ Validation test failed: {str(e)}")
            import traceback

            traceback.print_exc()
            return False


async def main():
    """Run all tests."""
    print("\n🚀 Starting Chrome Import & UTF-8 Validation Tests")
    print("=" * 60)

    results = []

    # Test 1: Encryption utility
    results.append(("Encryption Utility", await test_encryption()))

    # Test 2: Chrome import
    results.append(("Chrome Import", await test_chrome_import()))

    # Test 3: Validation
    results.append(("Account Validation", await test_validation()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✅ All tests passed! The UTF-8 issue has been fixed.")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
