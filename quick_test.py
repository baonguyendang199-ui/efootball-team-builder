#!/usr/bin/env python3
import requests
import json

# Test 2 IDs
test_ids = [
    '88045755866499',  # P.E. Aubameyang
    '88039850287270',  # New ID
]

for player_id in test_ids:
    print(f"\n{'='*80}")
    print(f"🔍 Testing Player ID: {player_id}")
    print(f"{'='*80}")
    
    url = "https://www.pesdata.net/api/player/detail"
    params = {'id': player_id}
    
    try:
        print("Requesting...")
        resp = requests.get(url, params=params, timeout=10)
        print(f"Status: {resp.status_code}")
        
        if resp.text:
            try:
                data = resp.json()
                print("\n✅ JSON Response:")
                response_str = json.dumps(data, indent=2, ensure_ascii=False)
                print(response_str[:5000])  # Print first 5000 chars
                
                # Extract top-level keys if possible
                if isinstance(data, dict) and 'data' in data:
                    player_data = data['data']
                    if isinstance(player_data, list):
                        player_data = player_data[0] if player_data else {}
                    
                    if isinstance(player_data, dict):
                        print(f"\n📋 Available Keys in 'data':")
                        for key in sorted(player_data.keys()):
                            val = str(player_data.get(key, ''))[:50]
                            print(f"   - {key}: {val}...")
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {e}")
                print(f"Response text: {resp.text[:500]}")
        else:
            print("Empty response")
            
    except requests.exceptions.Timeout:
        print("❌ Timeout")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

