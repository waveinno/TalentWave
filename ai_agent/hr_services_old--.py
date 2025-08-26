from employee.models import Employee
from leave.models import LeaveRequest, LeaveType
from attendance.models import Attendance
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.db.models import Sum

def ensure_perms(user, perm):
    if not user.has_perm(perm):
        raise PermissionDenied(f"User lacks {perm}")

def get_my_employee(user: User):
    try:
        return Employee.objects.get(employee_user_id=user)
    except Employee.DoesNotExist:
        return None

def get_my_employee_name(user: User):
    employee = get_my_employee(user)
    return employee.get_full_name() if employee else "Not assigned"


def isReportingManager(user: User):
    manager = Employee.objects.filter(employee_user_id=user).first()
    queryset = Employee.objects.filter(employee_work_info__reporting_manager_id=manager)
    return queryset.exists()

 

def getEmployInformation(user: User):
    """
    Returns a detailed dictionary of the employee's personal, work, and bank information.
    """
    try:
        employee = Employee.objects.get(employee_user_id=user)
    except Employee.DoesNotExist:
        return None   

    work_info = getattr(employee, "employee_work_info", None)
    bank_info = getattr(employee, "employee_bank_details", None)

    # All available leave types with balances
    leave_types = LeaveType.objects.all()
    leave_balances = {}
    for leave_type in leave_types:
        # print("==================")
        # print(leave_type.name)

        employee_data = {
        "name": employee.get_full_name(),
        "badge_id": employee.badge_id,
        "email": employee.get_email(),
        "phone": employee.phone,
        "address": employee.address,
        "city": employee.city,
        "state": employee.state,
        "country": employee.country,
        "zip": employee.zip,
        "dob": employee.dob.strftime("%Y-%m-%d") if employee.dob else None,
        "gender": employee.gender,
        "marital_status": employee.marital_status,
        "children": employee.children,
        "profile_image": employee.get_avatar(),
        "employee_type": work_info.employee_type_id if work_info and work_info.employee_type_id else None,
        "department": work_info.department_id.department if work_info and work_info.department_id else None,
        "job_position": work_info.job_position_id if work_info and work_info.job_position_id else None,
        "job_role": work_info.job_role_id if work_info and work_info.job_role_id else None,
        "work_type": work_info.work_type_id if work_info and work_info.work_type_id else None,
        "shift": work_info.shift_id if work_info and work_info.shift_id else None,
        "isReportingManager": isReportingManager(user),
        "reporting_manager": work_info.reporting_manager_id.get_full_name() if work_info and work_info.reporting_manager_id else None,
        "date_joining": work_info.date_joining.strftime("%Y-%m-%d") if work_info and work_info.date_joining else None,
        "contract_end_date": work_info.contract_end_date.strftime("%Y-%m-%d") if work_info and work_info.contract_end_date else None,
        "basic_salary": work_info.basic_salary if work_info else None,
        "company_name": work_info.company_id if work_info else None,
        "teams":{"total_members": 0, "members": []},
        "bank_details": {
            "bank_name": bank_info.bank_name if bank_info else None,
            "account_number": bank_info.account_number if bank_info else None,
            "branch": bank_info.branch if bank_info else None,
            "bank_address": bank_info.address if bank_info else None,
            "country": bank_info.country if bank_info else None,
            "state": bank_info.state if bank_info else None,
            "city": bank_info.city if bank_info else None,
        } if bank_info else None,
    }

    return employee_data


def get_employee_personal_info(employee:Employee):
    """
    Returns the personal information of an employee.
    """
    return {
        "name": employee.get_full_name(),
        "badge_id": employee.badge_id,
        "email": employee.get_email(),
        "phone": employee.phone,
        "address": employee.address,
        "city": employee.city,
        "state": employee.state,
        "country": employee.country,
        "zip": employee.zip,
        "dob": employee.dob.strftime("%Y-%m-%d") if employee.dob else None,
        "gender": employee.gender,
        "marital_status": employee.marital_status,
        "children": employee.children,
        "profile_image": employee.get_avatar(),
    }

def get_my_employee_full_info(user: User):
    """
    Returns a detailed dictionary of the employee's personal, work, and bank information.
    """
    return getEmployInformation(user)


def get_team_employees_info(user: User):
    keys_to_remove = ["basic_salary", "reporting_manager","teams"]

    manager = Employee.objects.filter(employee_user_id=user).first()
    queryset = Employee.objects.filter(employee_work_info__reporting_manager_id=manager)
    if not queryset.exists():
        return {"total_members": 0, "members": []}

    members = []
    for emp in queryset:
        user_instance = emp.employee_user_id  
        employee_data = getEmployInformation(user_instance)

        for key in keys_to_remove:
            employee_data.pop(key, None)

        # Calculate leave balance
        leaves = LeaveRequest.objects.filter(
            employee_id=emp, 
            status="approved"
        ).aggregate(total_days=Sum("requested_days"))
        employee_data["leave_balance"] = leaves["total_days"] or 0

        # # Calculate attendance %
        # attendance_records = Attendance.objects.filter(employee_id=emp)
        # total_days = attendance_records.count()
        # present_days = attendance_records.filter(status="present").count()

        # employee_data["attendance_percentage"] = (
        #     (present_days / total_days) * 100 if total_days > 0 else 0
        # )

        members.append(employee_data)

    return {
        "total_members": len(members),
        "members": members
    }

# def get_team_employees_info(user: User):
#     """
#     Returns a list of subordinate employees as plain dictionaries.
#     Removes any Django model objects, optionally removes dynamic keys,
#     and includes leave balance and attendance percentage.
    
#     :param keys_to_remove: List of keys to remove from each employee dictionary
#     """
#     keys_to_remove = ["basic_salary","reporting_manager"]  # default keys to remove
  
#     manager = Employee.objects.filter(employee_user_id=user).first()
#     queryset = Employee.objects.filter(employee_work_info__reporting_manager_id=manager)
#     if not queryset.exists():
#         return []
 
#     team_info = [] 
#     for emp in queryset:
#         user_instance = emp.employee_user_id  
#         employee_data = getEmployInformation(user_instance)
#         # Remove sensitive/dynamic keys
#         for key in keys_to_remove:
#             employee_data.pop(key, None)
        
#         team_info.append(employee_data)

#     team_info["total_members"] = len(team_info)
#     return team_info
   
    # print("Team Members:")
    # for member in team_members:
    #     print(f" - {member.get_full_name()}")

    # return team_info

    # for emp in team_members:
    #     # Get object-free employee info
    #     employee_data = getEmployInformation(emp)

    #     # Remove dynamic keys
    #     for key in keys_to_remove:
    #         employee_data.pop(key, None)

    #     # Calculate leave balance
    #     # leaves = LeaveRequest.objects.filter(employee_id=emp, status="approved")
    #     # total_leave = leaves.aggregate(total_days_sum=models.Sum('requested_days'))['total_days_sum'] or 0
    #     # employee_data["leave_balance"] = total_leave

    #     # # Calculate attendance %
    #     # attendance_records = Attendance.objects.filter(employee_id=emp)
    #     # if attendance_records.exists():
    #     #     total_days = attendance_records.count()
    #     #     present_days = attendance_records.filter(status="Present").count()
    #     #     attendance_pct = round((present_days / total_days) * 100, 2)
    #     # else:
    #     #     attendance_pct = None
    #     # employee_data["attendance_pct"] = attendance_pct

    #     team_info.append(employee_data)
    # print("Team Members:")
    # for member in team_members:
    #     print(f" - {member.get_full_name()}")
    # return team_info

# def get_my_leave_balance(user):
#     """
#     Returns the total approved leave balance for the logged-in user.
#     """
#     try:
#         # employee = Employee.objects.get(user=user)
#         # leaves = LeaveRequest.objects.filter(employee_id=employee, status="approved")
#         # total_balance = sum([l.approved_available_days + l.approved_carryforward_days for l in leaves])
#         return 10
#     except Employee.DoesNotExist:
#         return "Employee not found."

# def get_last_payslip(user):
#     """
#     Returns the last payslip of the logged-in user.
#     """
#     try:
#         employee = Employee.objects.get(user=user)
#         payslip = Payslip.objects.filter(employee_id=employee).order_by("-date").first()
#         if payslip:
#             return f"Payslip Date: {payslip.date}, Net Salary: {payslip.net_salary}"
#         else:
#             return "No payslip found."
#     except Employee.DoesNotExist:
#         return "Employee not found."

# def get_attendance_summary(user):
#     """
#     Returns a summary of attendance for the logged-in user.
#     """
#     try:
#         employee = Employee.objects.get(user=user)
#         attendance = Attendance.objects.filter(employee_id=employee).order_by("-date")
#         if attendance.exists():
#             summary = f"Total Records: {attendance.count()}, Last Entry: {attendance.first().date}"
#             return summary
#         else:
#             return "No attendance records found."
#     except Employee.DoesNotExist:
#         return "Employee not found."

# def get_assigned_assets(user):
#     """
#     Returns a list of assets assigned to the logged-in user.
#     """
#     try:
#         employee = Employee.objects.get(user=user)
#         assets = AssetAssignment.objects.filter(assigned_to_employee_id=employee)
#         if assets.exists():
#             return ", ".join([str(a.asset_id) for a in assets])
#         else:
#             return "No assets assigned."
#     except Employee.DoesNotExist:
#         return "Employee not found."

# def get_my_asset_requests(user):
#     """
#     Returns asset requests made by the logged-in user.
#     """
#     try:
#         employee = Employee.objects.get(user=user)
#         requests = AssetRequest.objects.filter(requested_employee_id=employee)
#         if requests.exists():
#             return ", ".join([f"{r.asset_category_id.asset_category_name} ({r.asset_request_status})" for r in requests])
#         else:
#             return "No asset requests found."
#     except Employee.DoesNotExist:
#         return "Employee not found."

# def get_available_asset_categories():
#     """
#     Returns all available asset categories.
#     """
#     categories = AssetCategory.objects.all()
#     if categories.exists():
#         return ", ".join([c.asset_category_name for c in categories])
#     else:
#         return "No asset categories found."

# def get_employee_info(user):
#     ensure_perms(user, "employee.view_employee")
#     try:
#         emp = user.employee
#         return {
#             "employee_id": emp.employee_id,
#             "full_name": emp.get_full_name,
#             "email": emp.user.email,
#             "department": emp.department.name if emp.department else "N/A",
#             "designation": emp.designation.name if emp.designation else "N/A",
#             "reporting_manager": emp.reporting_manager.get_full_name() if emp.reporting_manager else "N/A",
#         }
#     except:
#         return {"employee_id": "Not assigned"}
 
        

# def get_my_last_payslip_summary(user):
#     ensure_perms(user, "payslip.view_payslip")
#     try:
#         emp = user.employee
#         last_payslip = Payslip.objects.filter(employee_id=emp).order_by("-date").first()
#         if last_payslip:
#             return {
#                 "month": last_payslip.month,
#                 "gross": float(last_payslip.gross_salary),
#                 "net": float(last_payslip.net_salary),
#             }
#         else:
#             return {"Error": "No payslip found."}
#     except:
#         return {"Error": "Not assigned"}
    
# def get_my_attendance_summary(user):
#     ensure_perms(user, "attendance.view_attendance")
#     try:
#         emp = user.employee
#         attendance = Attendance.objects.filter(employee_id=emp).order_by("-date")
#         if attendance.exists():
#             return {
#                 "total_days": attendance.count(),
#                 "present_days": attendance.filter(status="present").count(),
#                 "absent_days": attendance.filter(status="absent").count(),
#             }
#         else:
#             return {"Error": "No attendance records found."}
#     except:
#         return {"Error": "Not assigned"}