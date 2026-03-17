with open('app/adapters/webapi_adapter.py', 'r') as f:
    lines = f.readlines()

with open('app/adapters/webapi_adapter.py', 'w') as f:
    i = 0
    while i < len(lines):
        line = lines[i]
        if 'text = f"[mock webapi] {last_message}" if last_message else "[mock webapi]"' in line:
            f.write('            raise Exception(\"Gemini WebAPI client is not initialized. Please ensure valid __Secure-1PSID cookies are set via the Accounts page in the admin panel.\")
')
        elif 'for token in (f"[mock webapi] {last_message}").split():' in line:
            f.write('            raise Exception(\"Gemini WebAPI client is not initialized. Please ensure valid __Secure-1PSID cookies are set via the Accounts page in the admin panel.\")
')
            i += 1
        elif 'return {\"created\": int(time.time()), \"data\": [{\"url\": f\"mock://image/{uuid.uuid4().hex}\", \"prompt\": prompt}]}' in line:
            f.write('            raise Exception(\"Gemini WebAPI client is not initialized. Please ensure valid __Secure-1PSID cookies are set via the Accounts page in the admin panel.\")
')
        elif 'urls.append({\"url\": f\"mock://image/{uuid.uuid4().hex}\", \"prompt\": prompt})' in line:
            f.write('            raise Exception(\"Model successfully generated a response but no image URLs were returned. Check if the prompt violated safety guidelines.\")
')
        elif 'if self.mock_mode:
' in line and 'return True
' in lines[i+1]:
            f.write(line)
            f.write('            return False
')
            i += 1
        else:
            f.write(line)
        i += 1
