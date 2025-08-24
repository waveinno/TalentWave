from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import AiConversation, AiMessage
from .llm import system_prompt, complete_openai

@login_required
def widget_page(request):
    return render(request, "ai_agent/chat_widget.html")

@csrf_exempt
@require_POST
@login_required
def chat(request):
    user = request.user
    # HTMX sends form data, not JSON
    text = request.POST.get("message", "")
    conv_id = request.POST.get("conversation_id")

    if conv_id:
        conv = AiConversation.objects.get(id=conv_id, user=user)
    else:
        conv = AiConversation.objects.create(user=user, title=text[:60])

    msgs = [{"role": "system", "content": system_prompt()}]
    for m in conv.messages.order_by("created_at")[:10]:
        msgs.append({"role": m.role, "content": m.content})

    AiMessage.objects.create(conversation=conv, role="user", content=text)
    msgs.append({"role": "user", "content": text})

    # Call LLM safely
    try:
        resp = complete_openai(msgs)
        answer = getattr(resp.choices[0].message, "content", None) if resp.choices else None
        if not answer:
            answer = "Sorry, I could not generate a response."
    except Exception as e:
        answer = f"Error: {e}"

    AiMessage.objects.create(conversation=conv, role="assistant", content=answer)

    return JsonResponse({"conversation_id": conv.id, "answer": answer})
