from ..console import Console

class HCaptchaError(Exception):
    pass#Console.debug(f"RAISED ERROR : {Exception}")

class ApiError(HCaptchaError):
    pass#Console.debug(f"RAISED ERROR : {HCaptchaError}")

class SolveFailed(HCaptchaError):
    pass#Console.debug(f"RAISED ERROR : {HCaptchaError}")