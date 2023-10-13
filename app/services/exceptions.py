
class AuthorizationError(Exception):
    def __init__(self,
                 service: str,
                 status_code: int = 403,
                 error: str = "Authorization Error: Access Denied!"):
        self.service = service
        self.status_code = status_code
        self.error = error

    def __str__(self):
        return f"service: {self.service}; status code: {self.status_code}; error: {self.error}"

    def __repr__(self):
        return f"service: {self.service}\nstatus code: {self.status_code}\nerror: {self.error}"


class UnexpectedResponse(Exception):
    def __init__(self,
                 service: str,
                 status_code: int = 422,
                 error: str = "Unprocessed Entity"):
        self.service = service
        self.status_code = status_code
        self.error = error

    def __str__(self):
        return f"service: {self.service}; status code: {self.status_code}; error: {self.error}"

    def __repr__(self):
        return f"service: {self.service}\nstatus code: {self.status_code}\nerror: {self.error}"
