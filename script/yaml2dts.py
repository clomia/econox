"""UiText.yaml에 대한 Type 정의를 생성합니다."""
import yaml
from datetime import datetime

target = "frontend/static/UiText.yaml"
output = "frontend/static/UiText.d.ts"

with open(target, "r") as file:
    yaml_data = yaml.safe_load(file)

type_definitions = []
for key, value in yaml_data.items():
    literal_values = " | ".join(
        ['"' + v.replace("\n", "") + '"' for v in list(value.values())]
    )
    type_definitions.append(f"{key}: {literal_values};")
timestring = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open(output, "w") as output_file:
    comment = f"// Automatically generated in {timestring}. Refer to rollup.config.js and script/yaml2dts.py for the relevant logic.\n\n"
    code = "export interface UiText {\n    " + "\n    ".join(type_definitions) + "\n}"
    output_file.write(comment + code)
