from enum import Enum


class BasePermission(Enum):
    CREATE = "create"
    READ = "read"
    EDIT = "edit"
    DELETE = "delete"
