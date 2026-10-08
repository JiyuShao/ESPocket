# AI Chatbot Credentials

Copy the matching `.example` file to the real file name, then replace the
placeholder values with your credentials:

- `openai.json.example` -> `openai.json`
- `coze.json.example` -> `coze.json`
- `coze_private_key.pem.example` -> `coze_private_key.pem`

The app only reads `openai.json`, `coze.json`, and `coze_private_key.pem`;
`.example` files are templates only.

OpenAI requires `model` and `api_key`. `voice` may be left as a known OpenAI
voice such as `alloy`.

Coze requires `authorization.app_id`, `authorization.public_key`, a private key
from either `authorization.private_key` or `coze_private_key.pem`, and at least
one robot with `name`, `bot_id`, and `voice_id`.
