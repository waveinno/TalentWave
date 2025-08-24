import os
from . import fetchers

USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")

def system_prompt():
    return (
        "You are BL AI HR Assistant. "
        "Answer concisely and only about the logged-in user."
    )

TOOLS = {
    "get_my_leave_balance": fetchers.get_my_leave_balance,
    "get_my_attendance_summary": fetchers.get_my_attendance_summary,
    "get_my_last_payslip_summary": fetchers.get_my_last_payslip_summary,
}

def call_tool(user, name, args):
    fn = TOOLS.get(name)
    if not fn:
        return {"error": f"Unknown tool {name}"}
    return fn(user, **args)

def complete_openai(messages):
    if not USE_OPENAI:
        # Fallback: echo last user message
        return type("Resp", (), {"choices":[type("Choice", (), {"message":type("Msg", (), {"content":messages[-1]['content']})})()]})()
    from openai import OpenAI
    client = OpenAI()
    return client.chat.completions.create(
        model=AI_MODEL,
        messages=messages,
        temperature=0.2,
    )
