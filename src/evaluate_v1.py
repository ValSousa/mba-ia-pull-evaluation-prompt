"""
Script para avaliar o prompt original (v1) com as mesmas métricas do evaluate.py.

Usado para preencher a coluna "v1" da tabela comparativa do README.

Este script:
1. Reutiliza as funções do evaluate.py (que não deve ser alterado)
2. Usa o mesmo dataset de avaliação do v2
3. Avalia o prompt leonanluppi/bug_to_user_story_v1 do LangSmith Hub
4. Envia os traces para um projeto separado, para não misturar com os do v2
5. Exibe o resultado no mesmo formato do evaluate.py
"""

import os
import sys
from pathlib import Path
from langsmith import Client
from langsmith import utils as ls_utils
from utils import check_env_vars, print_section_header
from evaluate import create_evaluation_dataset, evaluate_prompt, display_results

PROMPT_V1 = "leonanluppi/bug_to_user_story_v1"
JSONL_PATH = "datasets/bug_to_user_story.jsonl"


def main():
    """Função principal"""
    print_section_header("AVALIAÇÃO DO PROMPT ORIGINAL (v1)")

    provider = os.getenv("LLM_PROVIDER", "openai")
    print(f"Provider: {provider}")
    print(f"Modelo Principal: {os.getenv('LLM_MODEL', 'gpt-4o-mini')}")
    print(f"Modelo de Avaliação: {os.getenv('EVAL_MODEL', 'gpt-4o')}\n")

    required_vars = ["LANGSMITH_API_KEY", "LLM_PROVIDER"]
    if provider == "openai":
        required_vars.append("OPENAI_API_KEY")
    elif provider in ["google", "gemini"]:
        required_vars.append("GOOGLE_API_KEY")

    if not check_env_vars(required_vars):
        return 1

    if not Path(JSONL_PATH).exists():
        print(f"❌ Arquivo de dataset não encontrado: {JSONL_PATH}")
        return 1

    # Mesmo dataset do evaluate.py
    project_name = os.getenv("LANGSMITH_PROJECT", "prompt-optimization-challenge-resolved")
    dataset_name = f"{project_name}-eval"

    client = Client()
    create_evaluation_dataset(client, dataset_name, JSONL_PATH)

    # Traces do v1 em projeto separado (o dataset continua o mesmo).
    # O langsmith guarda o nome do projeto em cache (lru_cache): limpar para valer o novo nome.
    os.environ["LANGSMITH_PROJECT"] = f"{project_name}-v1"
    ls_utils.get_env_var.cache_clear()
    ls_utils.get_tracer_project.cache_clear()
    print(f"   Traces do v1 no projeto: {ls_utils.get_tracer_project()}")

    scores = evaluate_prompt(PROMPT_V1, dataset_name, client)

    # evaluate_prompt devolve tudo 0.0 quando falha (ex.: sem conexão com o LangSmith)
    if not any(scores.values()):
        print("\n❌ A avaliação do v1 não foi executada (todas as notas 0.0).")
        print("   Veja o erro acima; as notas NÃO devem ir para a tabela comparativa.")
        return 1

    display_results(PROMPT_V1, scores)

    print("\nUse estas notas na coluna v1 da tabela comparativa do README.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
