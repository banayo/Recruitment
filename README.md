# Context: Project Master Blueprint
You are an expert Full-Stack Python/Django Developer. I am building an **Internal Recruitment System (Phase 1)**. 
Please read and memorize this entire architectural blueprint and business logic before generating any code.

## 1. Tech Stack Overview
- **Framework:** Django (Monolithic, Server-Side Rendering)
- **Database:** PostgreSQL
- **Authentication:** Authentik (OpenID Connect - OIDC) via `mozilla-django-oidc`. NO local password management.
- **Frontend/UI:** Django Templates + Tailwind CSS + HTMX (for dynamic interactions).
- **Storage:** Cloud Data Storage for Candidate Resumes (storing URLs in DB).
- **Infrastructure:** Docker & Docker Compose.

## 2. Business Workflow (Phase 1)
1. **Request:** Employee creates a "Manpower Requisition" form.
2. **Approve:** Manager approves the requisition based on the reporting line logic.
3. **Map:** HR maps the approved requisition to an official `JobPosition`.
4. **Source:** HR inputs Candidate details and links them to the Requisition (`Application`).
5. **Interview:** HR schedules a single-round interview. Interviewer logs the result.
6. **Offer:** If passed, HR creates a `HiringOffer`. Requisition auto-closes when headcount is met.

## 3. User Authentication & SSO Claims Mapping
We use Just-In-Time (JIT) provisioning. Users log in via Authentik. The OIDC token contains custom claims. 
The Custom `User` model must extend `AbstractUser` and include these fields mapped from the claims:
- `authentik_sub` (CharField, unique)
- `person_unid` (CharField, unique) - The true primary identifier of the employee.
- `approve_code` (CharField) - The `person_unid` of this user's direct manager.
- `gender` (CharField)
- `division` (CharField)
- `department` (CharField)
- `location` (CharField)
- `nickname` (CharField)
- `company_code` (CharField) - e.g., 'KMHQ'

*Role Management:* Roles (HR, Manager, Employee) will be passed via the `groups` claim from Authentik and checked dynamically in memory during the active session.

## 4. Crucial Business Logic: Auto-Routing Approvals
When an employee (Requester) creates a Requisition, they DO NOT manually select an approver.
Instead, the system uses the Requester's `approve_code` to identify the manager.
Because the manager might not have logged into this Django system yet (due to JIT provisioning), the `Requisition` model must store the approver as a string, NOT a ForeignKey.
- Field: `approver_unid = models.CharField(max_length=50)`
- Logic: `Requisition.approver_unid = Requester.approve_code`
When a Manager logs in (and their `person_unid` is known), they will see all Requisitions where `approver_unid == self.person_unid`.

## 5. Database Schema Models (Core Entities)
- **User:** (Described in section 3)
- **JobPosition:** `job_code`, `title`, `description`
- **Requisition:** `requester` (FK User), `approver_unid` (CharField), `position` (FK JobPosition, nullable), `required_headcount`, `fulfilled_headcount`, `status` (pending, approved, rejected, in_progress, closed), `required_date`.
- **Candidate:** `first_name`, `last_name`, `email`, `phone`, `resume_url`.
- **Application:** Links `Candidate` to `Requisition`. Status choices: new, interviewing, passed, failed, hired.
- **Interview:** Links to `Application`. `interviewer` (FK User), `scheduled_date`, `location`, `result`, `comments`.
- **HiringOffer:** OneToOne with `Application`. `agreed_salary`, `start_date`, `status`.

## Your First Task:
Acknowledge that you have read, understood, and memorized this blueprint. Then, generate the initial `models.py` including the Custom User model and the Requisition model with the `approver_unid` logic. Wait for my confirmation before creating the Custom OIDC Authentication Backend."# Recruitment" 
