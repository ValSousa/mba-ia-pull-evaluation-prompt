"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
import yaml
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPT_NAME = "leonanluppi/bug_to_user_story_v1"
OUTPUT_PATH = "prompts/bug_to_user_story_v1.yml"

# O prompt no Hub não tem descrição nem tags próprias; estes valores
# mantêm o formato do YAML original do repositório.
DEFAULT_DESCRIPTION = "Prompt para converter relatos de bugs em User Stories"
DEFAULT_TAGS = ["bug-analysis", "user-story", "product-management"]


def _str_presenter(dumper, data):
    """Grava strings de várias linhas no estilo de bloco (|), mais legível."""
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


yaml.add_representer(str, _str_presenter)


def extract_prompt_data(prompt: ChatPromptTemplate) -> dict:
    """
    Extrai system_prompt e user_prompt de um ChatPromptTemplate.

    Args:
        prompt: Prompt retornado pelo hub.pull

    Returns:
        Dicionário com o conteúdo e os metadados do prompt
    """
    system_prompt = ""
    user_prompt = ""

    for message in prompt.messages:
        if isinstance(message, SystemMessagePromptTemplate):
            system_prompt = message.prompt.template
        elif isinstance(message, HumanMessagePromptTemplate):
            user_prompt = message.prompt.template

    hub_metadata = prompt.metadata or {}

    return {
        "description": DEFAULT_DESCRIPTION,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "version": "v1",
        "created_at": date.today().isoformat(),
        "tags": DEFAULT_TAGS,
        "source": {
            "hub": PROMPT_NAME,
            "commit_hash": hub_metadata.get("lc_hub_commit_hash", ""),
        },
    }


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt v1 do LangSmith Hub e salva em YAML.

    Returns:
        True se sucesso, False caso contrário
    """
    print(f"Fazendo pull de: {PROMPT_NAME}...")

    try:
        prompt = hub.pull(PROMPT_NAME)
    except Exception as e:
        print(f"❌ Erro ao fazer pull do prompt: {e}")
        return False

    if not isinstance(prompt, ChatPromptTemplate):
        print(f"❌ Tipo de prompt inesperado: {type(prompt).__name__}")
        return False

    prompt_data = extract_prompt_data(prompt)

    if not prompt_data["system_prompt"].strip():
        print("❌ O prompt não tem mensagem de sistema")
        return False

    prompt_key = PROMPT_NAME.split("/")[-1]
    if not save_yaml({prompt_key: prompt_data}, OUTPUT_PATH):
        return False

    print(f"   ✓ Variáveis: {prompt.input_variables}")
    print(f"   ✓ Commit no Hub: {prompt_data['source']['commit_hash'][:8]}")
    print(f"   ✓ Salvo em: {Path(OUTPUT_PATH)}")
    return True


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    if not pull_prompts_from_langsmith():
        return 1

    print("\n✅ Pull concluído com sucesso!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
