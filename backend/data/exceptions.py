class DataError(Exception):
    message = "분류되지 않은 데이터 에러"

    def __init__(self, msg: str = None):
        super().__init__(msg)
        if msg:
            self.message += f" {msg}"


class ElementDoesNotExist(DataError):
    message = "This element does not exist"


class FactorDoesNotExist(DataError):
    message = "This factor does not exist"


class LanguageNotSupported(DataError):
    message = "Language is not supported"
