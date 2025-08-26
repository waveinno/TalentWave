from employee.filters import EmployeeFilter
from employee.models import Employee
from leave.models import LeaveRequest, LeaveType
from attendance.models import Attendance
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.contrib.auth.models import User

class EmployeeInfoService:
    """
    A class to represent and fetch an employee's details including personal, work, and bank information.
    """

    def __init__(self, user: User):
        try:
            self.employee = Employee.objects.get(employee_user_id=user)
        except Employee.DoesNotExist:
            self.employee = None

    def ensure_perms(self, user, perm):
        """
        Check if the user has the necessary permissions.
        """
        if not user.has_perm(perm):
            raise PermissionDenied(f"User lacks {perm}")

    def getMyName(self):
        """
        Returns the full name of the employee.
        """
        return self.employee.get_full_name() if self.employee else "Not assigned"

    def is_reporting_manager(self):
        """
        Checks if the employee is a reporting manager.
        """
        if self.employee:
            manager = Employee.objects.filter(employee_user_id=self.employee.employee_user_id).first()
            return Employee.objects.filter(employee_work_info__reporting_manager_id=manager).exists()
        return False

    def get_personal_info(self):
        """
        Returns the personal information of the employee.
        """
        if not self.employee:
            return None
        
        return {
            "name": self.employee.get_full_name(),
            "badge_id": self.employee.badge_id,
            "employee_id": self.employee.badge_id,
            "email": self.employee.get_email(),
            "phone": self.employee.phone,
            "address": self.employee.address,
            "city": self.employee.city,
            "state": self.employee.state,
            "country": self.employee.country,
            "qualification":self.employee.qualification,
            "zip": self.employee.zip,
            "dob": self.employee.dob.strftime("%Y-%m-%d") if self.employee.dob else None,
            "gender": self.employee.gender,
            "marital_status": self.employee.marital_status,
            "emergency_contact":{"name":self.employee.emergency_contact_name,"phone":self.employee.emergency_contact,"relation":self.employee.emergency_contact_relation},
            "children": self.employee.children,
        }

    def get_work_info(self):
        """
        Returns the work-related information of the employee.
        """
        work_info = getattr(self.employee, "employee_work_info", None)
        if work_info:
 
            company_info = {
                "name": work_info.company_id.company if work_info.company_id else None,
                "address": work_info.company_id.address if work_info.company_id else None,
                "is_headquarter": work_info.company_id.hq if work_info.company_id else False,
                "country": work_info.company_id.country if work_info.company_id else None,
                "city": work_info.company_id.city if work_info.company_id else None,
            }

            return {
                "employee_type": work_info.employee_type_id if work_info.employee_type_id else None,
                "department": work_info.department_id.department if work_info.department_id else None,
                "job_position": work_info.job_position_id.job_position if work_info.job_position_id else None,
                "job_role": work_info.job_role_id.job_role if work_info.job_role_id else None,
                "work_type": work_info.work_type_id.work_type if work_info.work_type_id else None,
                "shift": work_info.shift_id.employee_shift if work_info.shift_id else None,
                "isReportingManager": self.is_reporting_manager(),
                "reporting_manager": work_info.reporting_manager_id.get_full_name() if work_info.reporting_manager_id else None,
                "date_joining": work_info.date_joining.strftime("%Y-%m-%d") if work_info.date_joining else None,
                "contract_end_date": work_info.contract_end_date.strftime("%Y-%m-%d") if work_info.contract_end_date else None,
                "basic_salary": work_info.basic_salary if work_info.basic_salary else None,
                "company": company_info if company_info else None,
            }
        return {}

    def get_bank_info(self):
        """
        Returns the bank details of the employee.
        """
        bank_info = getattr(self.employee, "employee_bank_details", None)
        if bank_info:
            return {
                "bank_name": bank_info.bank_name,
                "account_number": bank_info.account_number,
                "branch": bank_info.branch,
                "bank_address": bank_info.address,
                "country": bank_info.country,
                "state": bank_info.state,
                "city": bank_info.city,
            }
        return None

    def get_leave_balances(self):
        """
        Returns the leave balances for the employee.
        """
        leave_types = LeaveType.objects.all()
        leave_balances = {}
        for leave_type in leave_types:
            leave_request = LeaveRequest.objects.filter(
                employee_id=self.employee, leave_type=leave_type, status="approved"
            ).aggregate(total_days=Sum("requested_days"))
            leave_balances[leave_type.name] = leave_request["total_days"] or 0
        return leave_balances

    def get_teams_info(self):
        """
        Returns the information of the employee's subordinates.
        """
        team_info = {"total_members": 0, "members": []}
        keys_to_remove = ["basic_salary","reporting_manager"]
        team = Employee.objects.filter(employee_work_info__reporting_manager_id=self.employee)
        if team.exists():
            for member in team:
                 
                member_info = self.get_personal_info_for_member(member)
                for key in keys_to_remove:
                    member_info.pop(key, None)
   
                team_info["members"].append(member_info)
            team_info["total_members"] = len(team_info["members"])

        return team_info


    def get_personal_info_for_member(self, member):
        """
        Helper to get detailed information of a team member.
        """
        employee_info = self.get_personal_info()
        employee_info.update(self.get_work_info())  # Include both personal and work info
        # employee_info["leave_balance"] = self.get_leave_balances()

        return employee_info

    def get_employee_information(self):
        """
        Returns a detailed dictionary of the employee's personal, work, and bank information, including team information.
        """
        if not self.employee:
            return None

        # Combine all sections
        employee_data = self.get_personal_info()

        employee_data.update(self.get_work_info())
        employee_data["bank_details"] = self.get_bank_info()
        employee_data["teams"] = self.get_teams_info()
        # employee_data["leave_balances"] = self.get_leave_balances()

        return employee_data
    
    def get_employees_mock(self):
        employees = Employee.objects.filter(is_active=True)
        employee_list = []
        for emp in employees:
            # today_attendance = emp.get_today_attendance()
            # if today_attendance:
            #     attendance_status = today_attendance if today_attendance else "Present"
            # else:
            #     attendance_status = "Absent"

            employee_list.append({
                "name": emp.get_full_name(),
                "email": emp.get_email(),
                "phone": emp.phone,
                "department": str(emp.get_department()) if emp.get_department() else None,
                "job_position": str(emp.get_job_position()) if emp.get_job_position() else None,
                "employee_type": str(emp.get_employee_type()) if emp.get_employee_type() else None,
                "work_type": str(emp.get_work_type()) if emp.get_work_type() else None,
                "reporting_manager": str(emp.get_reporting_manager()) if emp.get_reporting_manager() else None,
                # "today_attendance": attendance_status
            })
        
        return {"employee":employee_list, "total_employee":employees.count()}

