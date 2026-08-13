#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json
import hashlib
import uuid
import time
from urllib.parse import quote
import sys

# Config PESDATA
PESDATA_API_BASE = "https://www.pesdata.net/api/player/detail"
PESDATA_API_VERSION = "1.9.0"
PESDATA_API_TOKEN = "null"
PESDATA_API_SECRET = "777888"

test_player_id = "88045755866499"

def build_pesdata_signature(params):
    clean_params = {k: str(v) for k, v in params.items() if v is not None and str(v) != ''}
    sorted_keys = sorted(clean_params.keys())
    query = '&'.join(f"{k}={quote(str(clean_params[k]), safe="'")}" for k in sorted_keys)
    timestamp = str(int(time.time()))
    nonce = uuid.uuid4().hex[:13]
    payload = f"{timestamp}{nonce}{PESDATA_API_SECRET}{query}"
    signature = hashlib.md5(payload.encode('utf-8')).hexdigest()
    return {
        'timestamp': timestamp,
        'nonce': nonce,
        'signature': signature,
    }

output = []
output.append(f"🔍 Testing PESDATA API")
output.append(f"Player ID: {test_player_id}")
output.append(f"Endpoint: {PESDATA_API_BASE}")
output.append("")

try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
    }
    
    params = {'id': test_player_id}
    sig = build_pesdata_signature(params)
    headers.update({
        'version': PESDATA_API_VERSION,
        'token': PESDATA_API_TOKEN,
        'x-timestamp': sig['timestamp'],
        'x-nonce': sig['nonce'],
        'x-signature': sig['signature'],
        'Referer': f'https://www.pesdata.net/player/detail/{test_player_id}',
    })
    
    output.append("Sending request...")
    resp = requests.get(PESDATA_API_BASE, headers=headers, params=params, timeout=20)
    
    output.append(f"✅ Status Code: {resp.status_code}")
    output.append("")
    
    if resp.status_code == 200:
        try:
            data = resp.json()
            output.append("="*80)
            output.append("📊 FULL JSON RESPONSE:")
            output.append("="*80)
            output.append(json.dumps(data, indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            output.append(f"Response text (first 2000 chars):\n{resp.text[:2000]}")
    else:
        output.append(f"❌ Status {resp.status_code}")
        output.append(f"Response:\n{resp.text[:1000]}")
        
except Exception as e:
    output.append(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    output.append(traceback.format_exc())

# Write to file
with open('pesdata_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

# Also print
for line in output:
    print(line)

print("\n✅ Result saved to pesdata_result.txt")
