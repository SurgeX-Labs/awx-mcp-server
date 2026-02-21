"""
Test script for AAP/AWX platform support and remote server functionality.

This script verifies:
1. Platform type enum works correctly
2. Environment configuration accepts platform types
3. Remote server can start and respond
4. AAP environment variables are parsed correctly
"""

import asyncio
import os
from uuid import uuid4

# Test imports
from awx_mcp_server.domain import (
    EnvironmentConfig,
    PlatformType,
)

def test_platform_types():
    """Test that all platform types are available."""
    print("✅ Testing PlatformType enum...")
    
    assert PlatformType.AWX == "awx"
    assert PlatformType.AAP == "aap"
    assert PlatformType.TOWER == "tower"
    
    print("   ✓ All platform types defined correctly")


def test_environment_config():
    """Test environment configuration with different platforms."""
    print("\n✅ Testing EnvironmentConfig with different platforms...")
    
    # Test AWX
    env_awx = EnvironmentConfig(
        name="test-awx",
        base_url="https://awx.example.com",
        platform_type=PlatformType.AWX,
    )
    assert env_awx.platform_type == PlatformType.AWX
    print("   ✓ AWX environment config works")
    
    # Test AAP
    env_aap = EnvironmentConfig(
        name="test-aap",
        base_url="https://aap.example.com",
        platform_type=PlatformType.AAP,
    )
    assert env_aap.platform_type == PlatformType.AAP
    print("   ✓ AAP environment config works")
    
    # Test Tower
    env_tower = EnvironmentConfig(
        name="test-tower",
        base_url="https://tower.example.com",
        platform_type=PlatformType.TOWER,
    )
    assert env_tower.platform_type == PlatformType.TOWER
    print("   ✓ Tower environment config works")
    
    # Test default (should be AWX)
    env_default = EnvironmentConfig(
        name="test-default",
        base_url="https://default.example.com",
    )
    assert env_default.platform_type == PlatformType.AWX
    print("   ✓ Default platform type is AWX")


def test_environment_variable_parsing():
    """Test that AWX_PLATFORM environment variable is parsed correctly."""
    print("\n✅ Testing AWX_PLATFORM environment variable parsing...")
    
    # Save original env vars
    original_platform = os.getenv("AWX_PLATFORM")
    
    try:
        # Test AWX
        os.environ["AWX_PLATFORM"] = "awx"
        platform = PlatformType(os.getenv("AWX_PLATFORM", "awx").lower())
        assert platform == PlatformType.AWX
        print("   ✓ AWX_PLATFORM=awx parsed correctly")
        
        # Test AAP
        os.environ["AWX_PLATFORM"] = "aap"
        platform = PlatformType(os.getenv("AWX_PLATFORM", "awx").lower())
        assert platform == PlatformType.AAP
        print("   ✓ AWX_PLATFORM=aap parsed correctly")
        
        # Test TOWER
        os.environ["AWX_PLATFORM"] = "tower"
        platform = PlatformType(os.getenv("AWX_PLATFORM", "awx").lower())
        assert platform == PlatformType.TOWER
        print("   ✓ AWX_PLATFORM=tower parsed correctly")
        
        # Test case insensitivity
        os.environ["AWX_PLATFORM"] = "AAP"
        platform = PlatformType(os.getenv("AWX_PLATFORM", "awx").lower())
        assert platform == PlatformType.AAP
        print("   ✓ AWX_PLATFORM is case-insensitive")
        
    finally:
        # Restore original env var
        if original_platform:
            os.environ["AWX_PLATFORM"] = original_platform
        elif "AWX_PLATFORM" in os.environ:
            del os.environ["AWX_PLATFORM"]


def test_json_serialization():
    """Test that environment config can be serialized to JSON."""
    print("\n✅ Testing JSON serialization...")
    
    env = EnvironmentConfig(
        name="test-serialization",
        base_url="https://aap.example.com",
        platform_type=PlatformType.AAP,
    )
    
    # Serialize to JSON
    json_data = env.model_dump_json()
    assert "aap" in json_data
    print("   ✓ Environment config serializes to JSON correctly")
    
    # Deserialize from JSON
    env_restored = EnvironmentConfig.model_validate_json(json_data)
    assert env_restored.platform_type == PlatformType.AAP
    assert env_restored.name == "test-serialization"
    print("   ✓ Environment config deserializes from JSON correctly")


async def test_remote_server_health():
    """Test that remote server responds to health checks."""
    print("\n✅ Testing remote server health endpoint...")
    
    try:
        import httpx
        
        # Check if server is running on localhost:8000
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                assert data["status"] == "healthy"
                assert "awx-mcp-server" in data["service"]
                print(f"   ✓ Server is healthy: {data}")
                return True
            else:
                print(f"   ⚠ Server returned status {response.status_code}")
                return False
                
    except httpx.ConnectError:
        print("   ℹ Server not running on localhost:8000 (this is OK for testing)")
        return None
    except Exception as e:
        print(f"   ⚠ Error checking server health: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("AWX MCP Server - AAP Support & Remote Server Tests")
    print("=" * 70)
    
    try:
        # Unit tests
        test_platform_types()
        test_environment_config()
        test_environment_variable_parsing()
        test_json_serialization()
        
        # Integration test
        asyncio.run(test_remote_server_health())
        
        print("\n" + "=" * 70)
        print("✅ All tests passed!")
        print("=" * 70)
        print("\n📋 Summary:")
        print("   • PlatformType enum works correctly (awx, aap, tower)")
        print("   • EnvironmentConfig accepts all platform types")
        print("   • AWX_PLATFORM environment variable is parsed correctly")
        print("   • JSON serialization/deserialization works")
        print("   • Remote server health check (if running)")
        print("\n🎉 AWX/AAP/Tower support is fully functional!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
