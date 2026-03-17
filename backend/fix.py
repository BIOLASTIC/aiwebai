import re

with open('app/api/admin/accounts.py', 'r') as f:
    text = f.read()

text = text.replace('        for model in models:
            caps = model.capabilities or {}
            if feature == \"test\" or feature in model.provider_model_name.lower() or caps.get(feature):', '        for model in models:
            caps = model.capabilities or {}
            cap_name = \"images\" if feature == \"image\" else feature
            if feature == \"test\" or feature in model.provider_model_name.lower() or caps.get(cap_name) or caps.get(feature):')

with open('app/api/admin/accounts.py', 'w') as f:
    f.write(text)
