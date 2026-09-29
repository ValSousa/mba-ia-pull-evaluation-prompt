"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPT_KEY = "bug_to_user_story_v2"
PROMPT_PATH = f"prompts/{PROMPT_KEY}.yml"


def build_readme(prompt_data: dict) -> str:
    """
    Monta o README exibido na página do prompt no Hub.

    Args:
        prompt_data: Dados do prompt

    Returns:
        Texto em Markdown com descrição, versão e técnicas
    """
    techniques = "\n".join(f"- {t}" for t in prompt_data.get("techniques_applied", []))
    return (
        f"# {PROMPT_KEY}\n\n"
        f"{prompt_data.get('description', '')}\n\n"
        f"- Versão: {prompt_data.get('version', '')}\n"
        f"- Criado em: {prompt_data.get('created_at', '')}\n\n"
        f"## Técnicas aplicadas\n\n{techniques}\n"
    )


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("human", prompt_data.get("user_prompt", "{bug_report}")),
    ])

    tags = list(prompt_data.get("tags", []))
    for technique in prompt_data.get("techniques_applied", []):
        if technique not in tags:
            tags.append(technique)

    print(f"Fazendo push de: {prompt_name}...")
    print(f"   Variáveis: {prompt.input_variables}")
    print(f"   Tags: {tags}")

    try:
        url = hub.push(
            prompt_name,
            prompt,
            new_repo_is_public=True,
            new_repo_description=prompt_data.get("description", ""),
            readme=build_readme(prompt_data),
            tags=tags,
        )
    except Exception as e:
        if "nothing to commit" in str(e).lower():
            print("   ✓ O Hub já tem esta versão do prompt (nothing to commit)")
            return True
        print(f"❌ Erro ao fazer push do prompt: {e}")
        return False

    print(f"   ✓ Publicado (público): {url}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    is_valid, errors = validate_prompt_structure(prompt_data)

    if "{bug_report}" not in prompt_data.get("user_prompt", ""):
        errors.append("user_prompt deve conter a variável {bug_report}")

    if "{bug_report}" in prompt_data.get("system_prompt", ""):
        errors.append("system_prompt não deve conter {bug_report} (a entrada vai no user_prompt)")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS PARA O LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(PROMPT_PATH)
    if not data or PROMPT_KEY not in data:
        print(f"❌ Prompt '{PROMPT_KEY}' não encontrado em {PROMPT_PATH}")
        return 1

    prompt_data = data[PROMPT_KEY]

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1
    print("   ✓ Prompt validado")

    prompt_name = f"{os.getenv('USERNAME_LANGSMITH_HUB')}/{PROMPT_KEY}"
    if not push_prompt_to_langsmith(prompt_name, prompt_data):
        return 1

    print("\n✅ Push concluído com sucesso!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
