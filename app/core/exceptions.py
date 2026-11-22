class AppError(Exception):
    """Base error that is converted into a consistent JSON response."""

    def __init__(self, status_code: int, detail: str, code: str) -> None:
        self.status_code = status_code
        self.detail = detail
        self.code = code
        super().__init__(detail)


class NotFoundError(AppError):
    def __init__(self, detail: str = "资源不存在") -> None:
        super().__init__(404, detail, "not_found")


class ConflictError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(409, detail, "conflict")


class BadRequestError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(400, detail, "bad_request")


class AuthenticationError(AppError):
    def __init__(self, detail: str = "登录状态无效或已过期") -> None:
        super().__init__(401, detail, "authentication_error")