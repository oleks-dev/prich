from pathlib import Path

from faker import Faker
from prich.models.file_scope import FileScope

from prich.models.template import TemplateModel, VariableDefinition, PythonStep, LLMStep, PromptFields

faker = Faker()

def generate_template(prich_path: Path = ".", template_id: str=None, isolated_venv: bool = False, global_location: bool = False):
    tpl_name = faker.company()
    tpl_description = faker.text(max_nb_chars=100)
    if not template_id:
        template_id = faker.company()
    tpl_id = template_id.lower().replace(", ", "-").replace(". ", "-").replace(" ", "-")

    tpl = TemplateModel(
        schema_version="1.0",
        version="1.0",
        id=tpl_id,
        author=faker.name(),
        name=tpl_name,
        description=tpl_description,
        tags=[faker.word(ext_word_list=tpl_description.replace(",", "").replace(".", "").split(" ")).lower()],
        variables=[
            VariableDefinition(
                name="name",
                type="str",
                default="Assistant",
                required=False
            )
        ],
        venv="shared" if not isolated_venv else "isolated",
        steps=[
            PythonStep(
                name="Preprocess",
                call="test.py",
                type="python",
                args=[],
                output_variable="test_output"
            ),
            LLMStep(
                name="LLM Step",
                type="llm",
                prompt=PromptFields(
                    system=f"You are {{ name }}, {faker.text(80)}",
                    user=f"Analyse `{{ test_output }}`, {faker.text(40)}"
                )
            )
        ],
        source=FileScope.LOCAL if not global_location else FileScope.GLOBAL,
        folder=str(prich_path / "templates"),
        file=str(prich_path / "templates" / f"{tpl_id}.yaml"),
    )
    return tpl

def templates(count: int = 1, isolated_venv: bool = False, global_location: bool = False, tag_first_n: int = None):
    templates_list = []
    index = 0
    tag_group_index = 1
    tag_name = f"{faker.word()}{tag_group_index}".lower()
    for i in range(0, count):
        index += 1
        if tag_first_n and index > tag_first_n:
            tag_group_index = +1
            tag_name = f"{faker.word()}{tag_group_index}".lower()
        tpl = generate_template(prich_path=Path("."), isolated_venv=isolated_venv, global_location=global_location)
        tpl.id = f"{tpl.id}{index}"
        if tag_first_n:
            tpl.tags.append(tag_name)
        templates_list.append(tpl)
    return templates_list
