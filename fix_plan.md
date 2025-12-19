# Fix Plan for Orientati Backend

## 1. Status Overview
- **Docker Services**: All services (`gateway`, `users-service`, `schools-service`, `kms-service`, `email-service`, `rabbitmq`, databases) start successfully.
- **API Availability**: All services expose their documentation endpoints (`/docs`).
- **Registration Flow**: **FIXED** and Verified.
- **Login Flow**: **FIXED** and Verified.
- **Business Logic APIs** (`Schools`, `Citta`, `Indirizzi`, `Materie`, `Users`): **FIXED** and Verified.
  - **Issue Identified**: `Schools Service` returned 500 Error when listing schools.
  - **Root Cause**: Invalid SQLAlchemy `selectinload` usage (string passed instead of class attribute).
  - **Status**: **FIXED**.

## 2. Implemented Fixes

### A. Gateway User Synchronization
The `fastapi-gateway` needs to mirror users created by `users-service` to perform authentication checks and reference users.
- **File**: `fastapi-gateway/app/services/users.py`
- **Change**: Added logic to `update_from_rabbitMQ` to handle `RABBIT_CREATE_TYPE`.

### B. Gateway Auth Service (MissingGreenlet Fix)
The `login` function caused a 500 error due to `sqlalchemy.exc.MissingGreenlet` when accessing properties of `user` and `db_session` after a commit had expired them.
- **File**: `fastapi-gateway/app/services/auth.py`
- **Change**: Modified `create_user_session_and_tokens` to extract `user.id` and `db_session.id` into variables *before* they are expired by `await db.commit()`, and used these variables for token creation.

### C. Schools Service Query Fix
The `get_schools` and `get_school_by_id` functions crashed with `sqlalchemy.exc.ArgumentError` because they used `selectinload("materie")` (string) instead of `selectinload(Indirizzo.materie)`.
- **File**: `schools-service/app/services/school.py`
- **Change**: Imported `Indirizzo` model and updated `selectinload` calls to use the class-bound attribute.

## 3. Remaining Issues & Recommendations

### A. Email Verification for Development/Testing
**Issue**: Testing the full flow (Login -> Access Protected APIs) requires email verification.
**Workaround Used**: Direct database update (`UPDATE users SET email_verified=true...`) inside `users-service_db`.
**Proposed Solutions**:
1. **Dev Mode Auto-Verification**: Configure `users-service` to auto-verify emails in `DEV` environment.
2. **Expose Verification Token**: Log the verification link in `email-service` more clearly.
3. **Admin Endpoint**: Add an endpoint in `users-service` (protected by admin secret) to manually verify a user by email/ID.

### B. Integration Test Script
**Action**: The `verify_apis.py` script (created during this session) serves as a good baseline for smoke testing. It should be integrated into the repository or CI/CD pipeline.

## 4. Next Steps for Antigravity
1. **Clean Up**: Remove temporary test credentials/scripts if needed (user requested not to save creds in committed files).
2. **Monitoring**: Keep an eye on `email-service` logs to ensure actual email delivery works when SMTP is configured.
