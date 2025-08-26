import json
import re

from base.models import Company, JobPosition, JobRole
from .models import AIAgentLog
from django.core.serializers import serialize

PRONOUN_PAT = re.compile(r"\b(his|her|their|tar|তার|তারটা| ওর |ওনার)\b", re.IGNORECASE)
CONTACT_PAT = re.compile(r"\b(contact|phone|mobile|number|নম্বর|নাম্বার)\b", re.IGNORECASE)
MANAGER_PAT = re.compile(r"\b(manager|reporting manager|supervisor|boss|ম্যানেজার)\b", re.IGNORECASE)

def _get_recent_dialog_messages(user, limit=8):
    """
    Return the last `limit` turns as Chat Completions messages.
    Keeps ordering oldest -> newest for the model.
    """
    logs = AIAgentLog.objects.filter(user=user).order_by('-created_at')[:limit]
    messages = []
    for log in reversed(logs):
        if log.question:
            messages.append({"role": "user", "content": log.question})
        if log.answer:
            messages.append({"role": "assistant", "content": log.answer})
    return messages

 
def _index_people_from_context(employee_info, team_info):
    """
    Build a simple name->person map to help match names mentioned in text.
    """
    people = {}
    if employee_info:
        rm = employee_info.get("reportingManager") or employee_info.get("manager") or employee_info.get("reporting_manager")
        if isinstance(rm, dict) and rm.get("name"):
            people[rm["name"]] = rm
            people["__reporting_manager__"] = rm

    if isinstance(team_info, list):
        for p in team_info:
            if isinstance(p, dict) and p.get("name"):
                people[p["name"]] = p

    me_name = employee_info.get("name") if isinstance(employee_info, dict) else None
    if me_name:
        me = dict(employee_info)
        people[me_name] = me
        people["__me__"] = me

    return people

def _extract_last_person_mentioned(text, people_index):
    """
    Try to find the last mentioned known person by name in a chunk of text.
    """
    best, best_pos = None, -1
    for name in people_index.keys():
        if name.startswith("__"):  # skip magic keys
            continue
        pos = text.lower().rfind(name.lower())
        if pos > best_pos:
            best, best_pos = people_index[name], pos
    return best

def _resolve_target_person(user_message, recent_messages, people_index):
    """
    Resolve who 'his/her/tar' refers to.
    """
    msg_has_pronoun = bool(PRONOUN_PAT.search(user_message))
    msg_mentions_manager = bool(MANAGER_PAT.search(user_message))

    if msg_mentions_manager:
        return people_index.get("__reporting_manager__")

    last_assistant_text = None
    for m in reversed(recent_messages):
        if m["role"] == "assistant":
            last_assistant_text = m["content"]
            break

    if last_assistant_text:
        candidate = _extract_last_person_mentioned(last_assistant_text, people_index)
        if candidate and (msg_has_pronoun or MANAGER_PAT.search(user_message)):
            return candidate

    if msg_has_pronoun:
        return people_index.get("__reporting_manager__")

    return None

def _format_contact_reply(person, employee_name="Employee"):
    """
    Format the contact reply for a given person.
    """
    name = person.get("name") or "the person"
    phone = person.get("phone") or person.get("mobile") or person.get("contactNumber")
    email = person.get("email") or person.get("workEmail")
    contact_info = []
    if phone:
        contact_info.append(f"📞 Phone: {phone}")
    if email:
        contact_info.append(f"✉️ Email: {email}")
    if not contact_info:
        return f"Sorry {employee_name}, I couldn’t find a contact number or email for {name}."
    return f"{name}’s contact details:\n" + "\n".join(contact_info)

def get_greeting_patterns():
    return [
        r'\bhi\b', r'\bhello\b', r'\bhey\b',
        r'\bgood morning\b', r'\bgood afternoon\b', r'\bgood evening\b',
        r'\bmorning\b', r'\bafternoon\b', r'\bevening\b'
    ]

   
def serialize_employee_data(employee_info):
    """
    Serialize employee data, making sure non-serializable objects are converted.
    """
    
    return employee_info

def get_system_prompt(hr_context):

  
    """
    Returns the system prompt string to be used for OpenAI API call.
    Takes in the HR context as input.
    """
    # hr_context['employee'] = serialize_employee_data(hr_context['employee'])

    return (
        "You are BL AI, a smart HR assistant. "
        "Use the provided HR data ONLY if the user has permission. "
        "Resolve pronouns like 'his/her/their/tar' to the most recently mentioned person; "
        "if the previous turn asked about the user's reporting manager, prefer that manager. "
        "If asked for a contact number, provide the phone and email if available. "
        "Be concise, friendly, and accurate.\n\n"
        f"HR DATA:\n{json.dumps(hr_context, ensure_ascii=False)}"
    )


def get_follow_ups():
    """
    Returns a list of follow-up questions for greeting responses.
    """
    return [
        "How can I assist you today?",
        "What can I do for you?",
        "Need any help with HR tasks?",
        "How may I help you today?",
        "Is there something I can assist you with?",
        "What do you need help with?",
        "How can I support you?"
    ]