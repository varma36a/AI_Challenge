from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from typing import Dict, Any
import json

from .llm import client, AZURE_OPENAI_DEPLOYMENT, SYSTEM, DEVELOPER, tool_schemas
from .tools import get_stat, predict_customer
from .schemas import ChatRequest

app = FastAPI(title="Week21 — Azure OpenAI Orchestrator")

@app.post("/api/chat")
def chat(req: ChatRequest) -> Dict[str, Any]:
    # seed the conversation
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "developer", "content": DEVELOPER},
        {"role": "user", "content": req.message},
    ]

    actions_result = []
    tools = tool_schemas()

    while True:
        resp = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        msg = resp.choices[0].message

        # If the model wants to call tools, run them and return results to the model
        if getattr(msg, "tool_calls", None):
            # Add the assistant's tool call message to the conversation
            messages.append(
                {
                    "role": "assistant",
                    "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
                }
            )
            for tc in msg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments or "{}")

                try:
                    if name == "get_stat":
                        result = get_stat(args.get("key", ""))
                    elif name == "predict_customer":
                        result = predict_customer(args)
                    else:
                        result = {"error": f"Unknown tool {name}"}
                except ValidationError as ve:
                    raise HTTPException(400, f"Invalid payload: {ve}")

                # record for API response
                actions_result.append({"tool": name, "result": result})

                # send tool result back to the model
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": name,
                        "content": json.dumps(result),
                    }
                )
            # loop again; the next turn should contain the final assistant text
            continue

        # No tool calls => final assistant message
        content = msg.content or ""
        # Try to parse JSON (if your prompt asks the model to return JSON). Fallback to plain text.
        try:
            plan = json.loads(content)
            intent = plan.get("intent", "answer")
            answer_md = plan.get("answer_md", "")
        except Exception:
            intent = "answer"
            answer_md = content

        return {
            "intent": intent,
            "answer_md": answer_md,
            "actions_result": actions_result,
        }
