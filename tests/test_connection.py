"""Test AWX connection with detailed error output."""
import asyncio
import httpx

async def test_rest_connection():
    """Test REST API connection."""
    print("Testing REST API connection...")
    token = "kMs3gDlZk3XI1tcpoiSbPvtYf14GfS"
    
    async with httpx.AsyncClient(verify=False) as client:
        try:
            # Test ping endpoint
            response = await client.get(
                "http://localhost:30080/api/v2/ping/",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            print(f"✓ Ping Status: {response.status_code}")
            print(f"✓ Response: {response.json()}")
            
            # Test me endpoint (requires auth)
            response = await client.get(
                "http://localhost:30080/api/v2/me/",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            print(f"✓ Auth Status: {response.status_code}")
            if response.status_code == 200:
                print(f"✓ User: {response.json()['results'][0]['username']}")
            else:
                print(f"✗ Auth failed: {response.text}")
                
        except Exception as e:
            print(f"✗ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_rest_connection())
