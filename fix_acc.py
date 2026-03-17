def fix():
    with open('backend/app/api/admin/accounts.py', 'r') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if 'if feature == "test" or feature in model.provider_model_name.lower() or caps.get(feature):' in line:
            lines[i] = '            cap_name = "images" if feature == "image" else feature
            if feature == "test" or feature in model.provider_model_name.lower() or caps.get(cap_name) or caps.get(feature):
'
            break
    with open('backend/app/api/admin/accounts.py', 'w') as f:
        f.writelines(lines)
fix()
