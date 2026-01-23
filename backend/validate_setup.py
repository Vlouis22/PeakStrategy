#!/usr/bin/env python3
"""
Validate PeakStrategy Firebase setup.
"""
import os
import sys
import json
from pathlib import Path

def validate_setup():
    print("🔍 Validating PeakStrategy Firebase Setup")
    print("=" * 60)
    
    backend_dir = Path(__file__).parent
    all_good = True
    
    # 1. Check service account file exists
    service_account_path = backend_dir / 'service-account-key.json'
    print(f"1. Service account file: {service_account_path.name}")
    
    if not service_account_path.exists():
        print("   ❌ File does not exist")
        print("   💡 Download from: Firebase Console → Project Settings → Service Accounts")
        all_good = False
    else:
        print("   ✅ File exists")
        
        # Check file size
        size = service_account_path.stat().st_size
        print(f"   📏 File size: {size} bytes")
        
        if size < 100:
            print("   ⚠️  File seems too small (should be ~2-3KB)")
            all_good = False
    
    # 2. Check JSON is valid
    print(f"\n2. JSON Validation:")
    try:
        with open(service_account_path, 'r') as f:
            data = json.load(f)
        
        print("   ✅ Valid JSON structure")
        
        # Check required fields
        required = {
            'type': 'service_account',
            'project_id': 'peakstrategy-7a0fb',
            'private_key': 'BEGIN PRIVATE KEY',
            'client_email': 'firebase-adminsdk'
        }
        
        for field, expected in required.items():
            if field in data:
                value = str(data[field])
                if expected.lower() in value.lower():
                    print(f"   ✅ {field}: OK")
                else:
                    print(f"   ⚠️  {field}: Unexpected value")
                    print(f"      Got: {value[:50]}...")
            else:
                print(f"   ❌ Missing field: {field}")
                all_good = False
        
    except json.JSONDecodeError as e:
        print(f"   ❌ Invalid JSON: {e}")
        all_good = False
    
    # 3. Check .env configuration
    print(f"\n3. Environment Configuration:")
    env_path = backend_dir / '.env'
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        if 'FIREBASE_SERVICE_ACCOUNT_PATH' in env_content:
            print("   ✅ FIREBASE_SERVICE_ACCOUNT_PATH is set in .env")
            
            # Check it's not the JSON blob
            for line in env_content.split('\n'):
                if line.startswith('FIREBASE_SERVICE_ACCOUNT_PATH='):
                    value = line.split('=', 1)[1].strip()
                    if value.endswith('.json'):
                        print(f"   ✅ Points to file: {value}")
                    elif '{' in value:
                        print("   ❌ Contains JSON instead of file path!")
                        print("   💡 Remove JSON from .env, save to separate file")
                        all_good = False
        else:
            print("   ❌ FIREBASE_SERVICE_ACCOUNT_PATH not in .env")
            all_good = False
    else:
        print("   ❌ .env file not found")
        all_good = False
    
    # 4. Test actual initialization
    print(f"\n4. Firebase Initialization Test:")
    if all_good:
        try:
            # Test minimal Firebase init
            import firebase_admin
            from firebase_admin import credentials
            
            with open(service_account_path, 'r') as f:
                config = json.load(f)
            
            cred = credentials.Certificate(config)
            # Don't actually initialize, just test credential creation
            print("   ✅ Credentials can be created")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            all_good = False
    
    print(f"\n" + "=" * 60)
    
    if all_good:
        print("🎉 Setup is CORRECT!")
        print("Run: python run.py")
    else:
        print("❌ Setup needs fixing.")
        print("\n📋 Next steps:")
        print("1. Delete any JSON from .env file")
        print("2. Ensure you have actual service-account-key.json file")
        print("3. .env should contain: FIREBASE_SERVICE_ACCOUNT_PATH=service-account-key.json")
    
    return all_good

if __name__ == '__main__':
    sys.exit(0 if validate_setup() else 1)