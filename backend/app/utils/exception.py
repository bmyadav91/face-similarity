import sys

def error_message_details(error, error_details=None):
    exc_type, exc_value, exc_tb = sys.exc_info() if error_details is None else error_details.exc_info()
    if exc_tb:
        file_name = exc_tb.tb_frame.f_code.co_filename
        error_message = f"Error occurred in script [{file_name}] at line [{exc_tb.tb_lineno}] with message [{str(error)}]"
    else:
        error_message = f"Error occurred: {str(error)}"

    return error_message

class CustomException(Exception):
    def __init__(self, error_message, error_details=None):
        super().__init__(error_message)
        self.error_message = error_message_details(error_message, error_details)

    def __str__(self):
        return self.error_message


