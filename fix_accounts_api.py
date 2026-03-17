import os
with open('backend/app/api/admin/accounts.py', 'r') as f:
    text = f.read()

new_text = text.replace(
    '        for model in models:
            caps = model.capabilities or {}
            if feature == \"test\" or feature in model.provider_model_name.lower() or caps.get(feature):',
    '        for model in models:
            caps = model.capabilities or {}
            # Normalize image feature to check for images cap and video to check for video cap
            cap_name = \"images\" if feature == \"image\" else feature
            if feature == \"test\" or feature in model.provider_model_name.lower() or caps.get(cap_name):'
)

with open('backend/app/api/admin/accounts.py', 'w') as f:
    f.write(new_text)
