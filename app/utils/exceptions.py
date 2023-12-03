
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


class MessageDuplicationError(Exception):
    def __init__(self,
                 message_id: int,
                 status_code: int = 422):
        self.status_code = status_code
        self.error = f"Message with id {message_id} already exists"

    def __str__(self):
        return f"status code: {self.status_code}; error: {self.error}"

    def __repr__(self):
        return f"status code: {self.status_code}\nerror: {self.error}"


class ReadOnlyException(Exception):
    def __init__(self,
                 status_code: int = 500):
        self.status_code = status_code
        self.error = f"There is no healthy servers registered on master"

    def __str__(self):
        return f"status code: {self.status_code}; error: {self.error}"

    def __repr__(self):
        return f"status code: {self.status_code}\nerror: {self.error}"


class NotToRetryException(Exception):
    def __init__(self,
                 error: str):
        self.error = error

    def __str__(self):
        return f"Error: {self.error}"

    def __repr__(self):
        return f"Error: {self.error}"
