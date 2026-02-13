"""Test AWX connection and fetch resources"""
import os
import httpx
import urllib3

# Disable SSL warnings for local testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
AWX_BASE_URL = "http://localhost:30080"
AWX_TOKEN = "kMs3gDlZk3XI1tcpoiSbPvtYf14GfS"

headers = {
    "Authorization": f"Bearer {AWX_TOKEN}",
    "Content-Type": "application/json"
}

def test_connection():
    print("\n" + "="*60)
    print("   AWX MCP SERVER - CONNECTION TEST")
    print("="*60)
    print(f"\n📍 AWX URL: {AWX_BASE_URL}")
    print(f"🔑 Token: ****{AWX_TOKEN[-4:]}")
    
    try:
        # Test ping
        print("\n🔍 Testing connection...")
        response = httpx.get(
            f"{AWX_BASE_URL}/api/v2/ping/",
            headers=headers,
            verify=False,
            timeout=10.0
        )
        
        if response.status_code == 200:
            print("✅ Connection successful!")
            data = response.json()
            print(f"   Version: {data.get('version', 'Unknown')}")
            print(f"   Active Node: {data.get('active_node', 'Unknown')}")
        else:
            print(f"❌ Connection failed: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False
    
    return True

def fetch_job_templates():
    print("\n" + "-"*60)
    print("📋 FETCHING JOB TEMPLATES")
    print("-"*60)
    
    try:
        response = httpx.get(
            f"{AWX_BASE_URL}/api/v2/job_templates/",
            headers=headers,
            verify=False,
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            count = data['count']
            print(f"✅ Found {count} job template(s):")
            
            for item in data['results']:
                print(f"   • {item['name']}")
                print(f"     ID: {item['id']} | Type: {item['type']} | Last Job: {item.get('last_job_run', 'Never')}")
            
            return True
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def fetch_jobs():
    print("\n" + "-"*60)
    print("🔧 FETCHING RECENT JOBS")
    print("-"*60)
    
    try:
        response = httpx.get(
            f"{AWX_BASE_URL}/api/v2/jobs/?order_by=-finished",
            headers=headers,
            verify=False,
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            count = data['count']
            print(f"✅ Found {count} job(s) (showing first 4):")
            
            for item in data['results'][:4]:
                print(f"   • Job {item['id']}: {item['name']}")
                print(f"     Status: {item['status']} | Type: {item.get('type', 'N/A')}")
                print(f"     Started: {item.get('started', 'N/A')} | Finished: {item.get('finished', 'N/A')}")
            
            return True
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def fetch_projects():
    print("\n" + "-"*60)
    print("📦 FETCHING PROJECTS")
    print("-"*60)
    
    try:
        response = httpx.get(
            f"{AWX_BASE_URL}/api/v2/projects/",
            headers=headers,
            verify=False,
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            count = data['count']
            print(f"✅ Found {count} project(s):")
            
            for item in data['results']:
                print(f"   • {item['name']}")
                print(f"     Status: {item['status']} | Type: {item['scm_type']} | Revision: {item.get('scm_revision', 'N/A')[:7]}")
            
            return True
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def fetch_inventories():
    print("\n" + "-"*60)
    print("📊 FETCHING INVENTORIES")
    print("-"*60)
    
    try:
        response = httpx.get(
            f"{AWX_BASE_URL}/api/v2/inventories/",
            headers=headers,
            verify=False,
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            count = data['count']
            print(f"✅ Found {count} inventor(ies):")
            
            for item in data['results']:
                print(f"   • {item['name']}")
                print(f"     Kind: {item['kind']} | Total Hosts: {item.get('total_hosts', 0)} | Groups: {item.get('total_groups', 0)}")
            
            return True
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def fetch_hosts():
    print("\n" + "-"*60)
    print("🖥️  FETCHING HOSTS")
    print("-"*60)
    
    try:
        response = httpx.get(
            f"{AWX_BASE_URL}/api/v2/hosts/",
            headers=headers,
            verify=False,
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            count = data['count']
            print(f"✅ Found {count} host(s):")
            
            for item in data['results']:
                desc = item.get('description', 'N/A')
                print(f"   • {item['name']}")
                print(f"     Description: {desc if desc else '(none)'} | Inventory: {item.get('summary_fields', {}).get('inventory', {}).get('name', 'N/A')}")
            
            return True
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def fetch_credentials():
    print("\n" + "-"*60)
    print("🔐 FETCHING CREDENTIALS")
    print("-"*60)
    
    try:
        response = httpx.get(
            f"{AWX_BASE_URL}/api/v2/credentials/",
            headers=headers,
            verify=False,
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            count = data['count']
            print(f"✅ Found {count} credential(s):")
            
            for item in data['results']:
                cred_type = item.get('summary_fields', {}).get('credential_type', {}).get('name', 'Unknown')
                print(f"   • {item['name']}")
                print(f"     Type: {cred_type}")
            
            return True
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def fetch_schedules():
    print("\n" + "-"*60)
    print("📅 FETCHING SCHEDULES")
    print("-"*60)
    
    try:
        response = httpx.get(
            f"{AWX_BASE_URL}/api/v2/schedules/",
            headers=headers,
            verify=False,
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            count = data['count']
            print(f"✅ Found {count} schedule(s) (showing first 4):")
            
            for item in data['results'][:4]:
                print(f"   • {item['name']}")
                print(f"     Next Run: {item.get('next_run', 'N/A')} | Enabled: {item.get('enabled', False)}")
            
            return True
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    # Test connection first
    if not test_connection():
        print("\n❌ Connection test failed. Please check your AWX URL and token.")
        exit(1)
    
    # Fetch all resources
    results = {
        "Job Templates": fetch_job_templates(),
        "Jobs": fetch_jobs(),
        "Projects": fetch_projects(),
        "Inventories": fetch_inventories(),
        "Hosts": fetch_hosts(),
        "Credentials": fetch_credentials(),
        "Schedules": fetch_schedules()
    }
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for resource, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {resource}")
    
    print(f"\n✅ Passed: {passed}/{total} tests")
    
    if passed == total:
        print("\n🎉 All tests passed! AWX MCP Server can successfully connect and fetch data.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
