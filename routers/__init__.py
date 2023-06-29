import importlib.util

from system import ROOT_PATH


def regist(app):
    """
    - routers 안에 정의된 모든 fastapi.APIRouter를 app에 등록합니다.
    - routers 내부 모든 모듈에 각각 fastapi.APIRouter 객체가 "router" 변수로 정의되어 있어야 합니다.
    """
    module_list = []
    for py_file in (ROOT_PATH / "routers").rglob("*.py"):
        if py_file.name != "__init__.py":
            module_name = py_file.stem  # remove '.py'
            module_spec = importlib.util.spec_from_file_location(module_name, py_file)
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
            module_list.append(module)
    for module in module_list:
        try:
            app.include_router(module.router)
        except AttributeError:
            raise NotImplementedError(f"{module.__file__} 모듈에 router가 없습니다.")
