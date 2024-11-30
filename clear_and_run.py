import os
import json

# Delete the cache file if it exists
cache_file = 'prediction_cache.json'
if os.path.exists(cache_file):
    os.remove(cache_file)
    print("Cache cleared")

# Create empty cache
with open(cache_file, 'w') as f:
    json.dump({}, f)

print("Running cost predictor...")
exec(open('cost_predictor_debug.py').read())
