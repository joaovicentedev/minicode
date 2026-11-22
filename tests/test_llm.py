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
    schema = requests[0]["response_format"]["json_schema"]["schema"]
    assert schema == FileChanges.model_json_schema()
    http_client.close()


def test_optional_planning_model_environment():
    from minicode.llm import planning_model_from_environment

    assert planning_model_from_environment({}) is None
    try:
        planning_model_from_environment({"MINICODE_PLAN_BASE_URL": "http://localhost:8000/v1"})
    except ValueError as error:
        assert "MINICODE_PLAN_MODEL" in str(error)
    else:
        assert False
    model = planning_model_from_environment(
        {
            "MINICODE_PLAN_BASE_URL": "http://localhost:8000/v1",
            "MINICODE_PLAN_MODEL": "qwen",
            "MINICODE_PLAN_API_KEY": "key",
        }
    )
    assert model.model == "qwen"
    assert str(model.client.base_url) == "http://localhost:8000/v1/"
