import os
with open('backend/app/adapters/webapi_adapter.py', 'r') as f:
    content = f.read()

content = content.replace(
    '        if self.mock_mode or not self.client:
            text = f\"[mock webapi] {last_message}\" if last_message else \"[mock webapi]\"',
    '        if self.mock_mode or not self.client:
            raise Exception(\"Gemini WebAPI client is not initialized. Please ensure valid __Secure-1PSID cookies are set via the Accounts page in the admin panel.\")'
)

content = content.replace(
    '        if self.mock_mode or not self.client:
            for token in (f\"[mock webapi] {last_message}\").split():
                yield {\"id\": chunk_id, \"object\": \"chat.completion.chunk\", \"created\": created, \"model\": request.model, \"choices\": [{\"index\": 0, \"delta\": {\"content\": token + \' \'}, \"finish_reason\": None}]}',
    '        if self.mock_mode or not self.client:
            raise Exception(\"Gemini WebAPI client is not initialized. Please ensure valid __Secure-1PSID cookies are set via the Accounts page in the admin panel.\")'
)

content = content.replace(
    '        if self.mock_mode or not self.client:
            return {\"created\": int(time.time()), \"data\": [{\"url\": f\"mock://image/{uuid.uuid4().hex}\", \"prompt\": prompt}]}',
    '        if self.mock_mode or not self.client:
            raise Exception(\"Gemini WebAPI client is not initialized. Please ensure valid __Secure-1PSID cookies are set via the Accounts page in the admin panel.\")'
)
content = content.replace(
    '        if not urls:
            urls.append({\"url\": f\"mock://image/{uuid.uuid4().hex}\", \"prompt\": prompt})',
    '        if not urls:
            raise Exception(\"Model successfully generated a response but no image URLs were returned. Check if the prompt violated safety guidelines.\")'
)

content = content.replace(
    '        if self.mock_mode:
            return True',
    '        if self.mock_mode:
            return False'
)

with open('backend/app/adapters/webapi_adapter.py', 'w') as f:
    f.write(content)
