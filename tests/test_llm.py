import json

import httpx

from minicode.agent import FileChanges
from minicode.llm import OpenAIChatModel


def test_openai_adapter_sends_pydantic_schema_for_structured_turn():
    requests = []

    def respond(request):
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-test",
                "object": "chat.completion",
                "created": 1,
                "model": "test-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": '{"files":[{"path":"main.py","content":"print(1)"}]}',
                        },
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(respond))
    model = OpenAIChatModel("https://example.test/v1", "test-key", "test-model", http_client)

    response = model.complete("Crie um arquivo", response_model=FileChanges)

    assert '"files"' in response
    assert requests[0]["response_format"]["type"] == "json_schema"
    assert requests[0]["response_format"]["json_schema"]["schema"] == FileChanges.model_json_schema()
    http_client.close()
