from django.contrib.auth.models import AnonymousUser

def ensure_perms(user, perm_codename):
    if isinstance(user, AnonymousUser):
        raise PermissionError("Not logged in")

def get_my_leave_balance(user):
    ensure_perms(user, "leave.view_leaveallocation")
    return {"annual_balance": 10, "sick_balance": 5}

def get_my_last_payslip_summary(user):
    ensure_perms(user, "payroll.view_payslip")
    return {"period": "2025-07-31", "gross": 90000, "net": 75000}

def get_my_attendance_summary(user, days=30):
    ensure_perms(user, "attendance.view_attendance")
    return {"days_checked": days, "present": 20, "absent": 2}

def get_my_employee_id(user):
    ensure_perms(user, "employee.view_employee")
    try:
        emp = user.employee
        return {"employee_id": emp.employee_id}
    except:
        return {"employee_id": "Not assigned"}
