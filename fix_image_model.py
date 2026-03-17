import re
with open("backend/app/adapters/webapi_adapter.py", "r") as f:
    text = f.read()

text = text.replace("output = await self.client.generate_content(prompt, model=request.model)", "output = await self.client.generate_content(prompt, model=\\"gemini-3.0-flash\\")")
with open("backend/app/adapters/webapi_adapter.py", "w") as f:
    f.write(text)
