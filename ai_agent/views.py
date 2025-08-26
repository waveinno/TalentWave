#views.py
import json
import random
import re
from django.utils.timezone import localtime
from django.views import View
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from openai import OpenAI

from ai_agent.helpers import  get_follow_ups, get_greeting_patterns, get_system_prompt
from . import config
from .models import AIAgentLog
from django.utils.timezone import now, timedelta
from django.core.paginator import Paginator
from .hr_services import  EmployeeInfoService
 
client = OpenAI(api_key=config.OPENAI_API_KEY)

@method_decorator(login_required, name="dispatch")
class AdvancedAIAgentChatView(View):
    def post(self, request):
        try:
            payload = json.loads(request.body)
            user_message = payload.get("message", "").strip()
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON format.")

        if not user_message:
            return HttpResponseBadRequest("Empty message.")
        employee_info = EmployeeInfoService(request.user)
        # Get employee information
        greeting_patterns = get_greeting_patterns()
        greeting_regex = re.compile("|".join(greeting_patterns), re.IGNORECASE)

        if greeting_regex.search(user_message):
            current_hour = localtime().hour
            if 5 <= current_hour < 12:
                time_greet = "Good morning"
            elif 12 <= current_hour < 17:
                time_greet = "Good afternoon"
            else:
                time_greet = "Good evening"

            # Get follow-up messages from the helper
            follow_ups = get_follow_ups()
            reply = f"{time_greet}, {employee_info.getMyName()}! {random.choice(follow_ups)}"
            AIAgentLog.objects.create(user=request.user, question=user_message, answer=reply)
            return JsonResponse({"reply": reply})



        # Get HR context for the employee
        data = employee_info.get_employees_mock()
        hr_context = {"employees": data}
        # # Get system prompt for AI interaction
        system_prompt = get_system_prompt(hr_context)
        # 🔹 Load last N messages from log for continuity
        history_logs = AIAgentLog.objects.filter(user=request.user).order_by("-created_at")[:5]
        conversation_history = []
        for log in reversed(history_logs):  # oldest → newest
            conversation_history.append({"role": "user", "content": log.question})
            conversation_history.append({"role": "assistant", "content": log.answer})

        # Add system + current query
        messages = [{"role": "system", "content": system_prompt}] + conversation_history
        messages.append({"role": "user", "content": user_message})
        try:
            # Make a call to the OpenAI API
            completion = client.chat.completions.create(
                model=config.AGENT_AI_MODEL,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}],
                temperature=0.3
            )
            reply = completion.choices[0].message.content
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

        # Log the conversation
        AIAgentLog.objects.create(user=request.user, question=user_message, answer=reply)

        # # Return the AI response
        return JsonResponse({"reply": reply})
    
# @method_decorator(login_required, name="dispatch")
# class AdvancedAIAgentChatView(View):
#     def post(self, request):
#         try:
#             payload = json.loads(request.body)
#             user_message = payload.get("message", "").strip()
#         except Exception:
#             return HttpResponseBadRequest("Invalid JSON")

#         if not user_message:
#             return HttpResponseBadRequest("Empty message")
#          # Get employee info
#         name = get_my_employee_name(request.user)
#         employee_name = name if name else "Employee"
        
#         # # Get greeting patterns from helper
#         # greeting_patterns = get_greeting_patterns()
#         # greeting_regex = re.compile("|".join(greeting_patterns), re.IGNORECASE)

#         # if greeting_regex.search(user_message):
#         #     current_hour = localtime().hour
#         #     if 5 <= current_hour < 12:
#         #         time_greet = "Good morning"
#         #     elif 12 <= current_hour < 17:
#         #         time_greet = "Good afternoon"
#         #     else:
#         #         time_greet = "Good evening"

#         #     # Get follow-up messages from the helper
#         #     follow_ups = get_follow_ups()
#         #     reply = f"{time_greet}, {employee_name}! {random.choice(follow_ups)}"
#         #     AIAgentLog.objects.create(user=request.user, question=user_message, answer=reply)
#         #     return JsonResponse({"reply": reply})

#         # ---------------- HR context ----------------
#         employee_info = get_my_employee_full_info(request.user) or {}
#         hr_context = {
#             "employee": employee_info,
#         }

#         # team_info = None
#         # if employee_info.get("isReportingManager"):
#         #     team_info = get_team_employees_info(request.user) or []
#         #     hr_context["team"] = team_info

#         # # ---------------- Conversation memory ----------------
#         # recent_messages = _get_recent_dialog_messages(request.user, limit=8)

#         # # ---------------- Contact short-circuit ----------------
#         # if CONTACT_PAT.search(user_message):
#         #     people_index = _index_people_from_context(employee_info, team_info)
#         #     target_person = _resolve_target_person(user_message, recent_messages, people_index)
#         #     if target_person:
#         #         reply = _format_contact_reply(target_person, employee_name)
#         #         AIAgentLog.objects.create(user=request.user, question=user_message, answer=reply)
#         #         return JsonResponse({"reply": reply})

#         # # ---------------- LLM call with history ----------------
#         system_prompt = get_system_prompt(hr_context)  # Use the helper function to generate system prompt
#         # messages = [{"role": "system", "content": system_prompt}]
#         # messages.extend(recent_messages)            # <- conversation chain
#         # messages.append({"role": "user", "content": user_message})

#         # try:
#         #     completion = client.chat.completions.create(
#         #         model=config.AGENT_AI_MODEL,
#         #         messages=messages,
#         #         temperature=0.3,
#         #     )
#         #     reply = completion.choices[0].message.content
#         # except Exception as e:
#         #     return JsonResponse({"error": str(e)}, status=500)

#         # AIAgentLog.objects.create(user=request.user, question=user_message, answer=reply)
#         return JsonResponse({"reply": reply})
    
    
@method_decorator(login_required, name="dispatch")
class AIAgentChatView(View):
    def post(self, request):
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return HttpResponseBadRequest("Invalid JSON")

        user_message = (payload.get("message") or "").strip()
        if not user_message:
            return HttpResponseBadRequest("Empty message")

        try:
            completion = client.chat.completions.create(
                model=config.AGENT_AI_MODEL,
                messages=[
                    {"role": "system", "content": config.AGENT_AI_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
            )
            reply = completion.choices[0].message.content
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

        AIAgentLog.objects.create(user=request.user, question=user_message, answer=reply)

        return JsonResponse({"reply": reply})

@method_decorator(login_required, name="dispatch")
class AIAgentHistoryView(View):
    def get(self, request):
        page = int(request.GET.get("page", 1))
        per_page = 20
        since = now() - timedelta(days=1)

        logs = AIAgentLog.objects.filter(user=request.user, created_at__gte=since).order_by("-created_at")
        paginator = Paginator(logs, per_page)
        page_obj = paginator.get_page(page)

        messages = []
        # send in chronological order: user -> AI
        for log in reversed(page_obj.object_list):
            messages.append({"role": "user", "content": log.question, "time": log.created_at.isoformat()})
            messages.append({"role": "ai", "content": log.answer, "time": log.created_at.isoformat()})

        return JsonResponse({
            "messages": messages,
            "has_next": page_obj.has_next(),
            "page": page_obj.number,
        })
 