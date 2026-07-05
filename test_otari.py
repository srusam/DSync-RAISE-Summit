"""
Run this to test Otari:  python test_otari.py

Install SDK first:  pip install otari
"""

import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OTARI_API_KEY")
model = os.getenv("OTARI_MODEL", "mzai:moonshotai/Kimi-K2.6")

print("=" * 50)
print("OTARI TEST")
print("=" * 50)
print(f"API key set: {'YES (starts with ' + key[:6] + '...)' if key else 'NO — add OTARI_API_KEY to .env'}")
print(f"Model: {model}")
print()

if not key:
    print("STOP: Add your tk_ key to .env first.")
    raise SystemExit(1)

try:
    from otari import OtariClient
except ImportError:
    print("STOP: Run this first →  pip install otari")
    raise SystemExit(1)

client = OtariClient(platform_token=key)

models_to_try = [model, "mzai:moonshotai/Kimi-K2.6", "mzai:Qwen/Qwen3-32B"]

for m in models_to_try:
    print(f"Trying model: {m}")
    try:
        response = client.completion(
            model=m,
            messages=[{"role": "user", "content": "Say hello in one short sentence."}],
        )
        print("SUCCESS!")
        print("Reply:", response.choices[0].message.content)
        print()
        print(f"→ Use this in .env:  OTARI_MODEL={m}")
        break
    except Exception as e:
        print(f"FAILED: {e}")
        print()
