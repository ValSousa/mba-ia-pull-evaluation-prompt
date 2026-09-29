"""
Testes automatizados para validação de prompts.
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data():
    """Dados do prompt otimizado (v2)."""
    data = load_prompts(PROMPT_FILE)
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada em {PROMPT_FILE.name}"
    return data[PROMPT_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data, "Campo 'system_prompt' não existe"
        assert isinstance(prompt_data["system_prompt"], str)
        assert prompt_data["system_prompt"].strip(), "Campo 'system_prompt' está vazio"

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt_data["system_prompt"]
        assert re.search(r"Você é (um|uma) \w+", system_prompt), \
            "O prompt não define uma persona no formato 'Você é um(a) ...'"
        assert "Product Manager" in system_prompt, \
            "A persona esperada (Product Manager) não foi encontrada"

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt_data["system_prompt"]
        assert "User Story" in system_prompt or "Markdown" in system_prompt, \
            "O prompt não menciona o formato User Story nem Markdown"
        for trecho in ("Como um", "eu quero", "para que"):
            assert trecho in system_prompt, \
                f"O modelo da User Story padrão não contém '{trecho}'"
        assert "Critérios de Aceitação" in system_prompt, \
            "O prompt não exige critérios de aceitação"

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt_data["system_prompt"]
        entradas = re.findall(r"<relato>(.*?)</relato>", system_prompt, re.DOTALL)
        saidas = re.findall(r"<resposta>(.*?)</resposta>", system_prompt, re.DOTALL)

        assert len(entradas) >= 2, f"Few-shot exige ao menos 2 exemplos; encontrados {len(entradas)}"
        assert len(entradas) == len(saidas), "Cada exemplo de entrada precisa de uma saída"
        for saida in saidas:
            assert saida.strip().startswith("Como "), \
                "A saída de um exemplo não começa com a User Story ('Como ...')"

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        for campo in ("description", "system_prompt", "user_prompt"):
            texto = prompt_data.get(campo, "")
            assert "[TODO]" not in texto, f"Campo '{campo}' contém [TODO]"
            assert "TODO" not in texto, f"Campo '{campo}' contém TODO"

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])
        assert isinstance(techniques, list), "'techniques_applied' deve ser uma lista"
        assert len(techniques) >= 2, f"Mínimo de 2 técnicas; encontradas {len(techniques)}"
        assert "few_shot" in techniques, "Few-shot é obrigatório e deve estar em 'techniques_applied'"

        is_valid, errors = validate_prompt_structure(prompt_data)
        assert is_valid, f"Estrutura do prompt inválida: {errors}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
