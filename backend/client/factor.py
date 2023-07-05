from typing import Callable

import xarray as xr

from backend.client.translate import Multilingual


class Factor:
    """
    - factor definition
    - Factor는 데이터를 가져오는 get함수를 가지며 Multilingual로 name과 note를 가진다.
    """

    def __init__(self, get: Callable[[], xr.Dataset], name: str, note: str):
        """name과 note는 영어여야 합니다."""
        self.get = get
        self.name = Multilingual(name)
        self.note = Multilingual(note)

    def __call__(self):
        return self.get()

    def __repr__(self) -> str:
        return f"<Factor: {self.name.text}>"
