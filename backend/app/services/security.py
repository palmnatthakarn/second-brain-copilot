from sqlalchemy.orm import Session

from app.models.erp import User


class PermissionError(Exception):
    pass


def assert_company_scope(db: Session, user_id: int, company_id: int) -> None:
    user = db.get(User, user_id)
    if not user:
        raise PermissionError("Unknown user.")
    if user.role != "Admin" and user.company_id != company_id:
        raise PermissionError("User is not allowed to access this company.")
