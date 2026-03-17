with open('backend/app/adapters/webapi_adapter.py', 'r') as f: text = f.read()
text = text.replace('text = f\"[mock webapi] {last_message}\" if last_message else \"[mock webapi]\"', 'raise Exception(\"Gemini WebAPI client is not initialized. Please ensure valid __Secure-1PSID cookies are set via the Accounts page in the admin panel.\")')
text = text.replace('            for token in (f\"[mock webapi] {last_message}\").split():
                yield {\"id\": chunk_id, \"object\": \"chat.completion.chunk\", \"created\": created, \"model\": request.model, \"choices\": [{\"index\": 0, \"delta\": {\"content\": token + \' \'}, \"finish_reason\": None}]}', '            raise Exception(\"Gemini WebAPI client is not initialized. Please ensure valid __Secure-1PSID cookies are set via the Accounts page in the admin panel.\")')
text = text.replace('return {\"created\": int(time.time()), \"data\": [{\"url\": f\"mock://image/{uuid.uuid4().hex}\", \"prompt\": prompt}]}', 'raise Exception(\"Gemini WebAPI client is not initialized. Please ensure valid __Secure-1PSID cookies are set via the Accounts page in the admin panel.\")')
text = text.replace('urls.append({\"url\": f\"mock://image/{uuid.uuid4().hex}\", \"prompt\": prompt})', 'raise Exception(\"Model successfully generated a response but no image URLs were returned. Check if the prompt violated safety guidelines.\")')
text = text.replace('        if self.mock_mode:
            return True', '        if self.mock_mode:
            return False')
with open('backend/app/adapters/webapi_adapter.py', 'w') as f: f.write(text)
