from crewai import Task
from textwrap import dedent
from datetime import datetime

from .agents import (
    analista_de_licitacoes,
    compilador_de_relatorio,
    revisor_de_relatório,
)

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")

# TODO: Adicionar ferramenta para cálculo de prazos e datas
montagem_de_cronograma = Task(
    description=dedent(
        """
        Organizar todos os prazos e datas relevantes do edital, construindo um cronograma em formato de tabela ou bullet points (desde abertura da licitação até encerramento do contrato).

        Dados de entrada:
        {cronograma_sections}
        """
    ),
    expected_output=dedent(
        """
        # Exemplo de Cronograma
        | Evento / Data  | Descrição                          |
        |--------------- |------------------------------------|
        | 10/01/2025     | Publicação do edital               |
        | 25/01/2025     | Limite para esclarecimentos        |
        | 01/02/2025     | Abertura das propostas             |
        | 15/03/2025     | Início de execução do contrato     |
        | 15/04/2025     | Aprovação do Projeto Básico        |
        | 15/06/2025     | Aprovação do Projeto Executivo     |
        | 15/12/2025     | Término das obras de implantação   |
        | 15/01/2026     | Término do comissionamento         |
        | 15/04/2026     | Fim da operação assistida          |
        | 15/08/2026     | Fim da vigência contratual         |
        """
    ),
    agent=analista_de_licitacoes,
    tools=[],
    async_execution=False,
    human_input=False,
)

compilacao_de_relatorio = Task(
    description=dedent(
        """
        Com base nos resultados validados pela revisão, compile um relatório final contendo:
        1) Visão Geral do Edital
        2) Cronograma
        3) Riscos
        4) Oportunidades
        5) Lista de Requisitos por categoria
        6) Checklist para participação na licitação

        Dados de entrada:
        {technical_sections}
        {overview}
        """
    ),
    expected_output=dedent(
        """
        # Relatório Final
        
        ## Visão Geral
        Referência: [Cliente] - [ID da Licitação]
        Data para submissão de propostas: [Data limite]
        Objeto da licitação: [Transcrição do objeto da licitação]

        ## Cronograma
        (Tabela com datas, marcos e prazos)

        ## Riscos
        [Principais Riscos, Penalidades, Fontes de Incerteza]

        ## Oportunidades
        [Oportunidades, Bônus, Remuneração Variável]

        ## Requisitos
        ### Prazos e cronograma
        - [...]

        ### Requisitos técnicos
        - [...]

        ### Econômico financeiro
        - [...]

        ### Riscos
        - [...]

        ### Oportunidades
        - [...]

        ### Outros requisitos
        - [...]

        ### Outras informações relevantes
        - [...]

        ## Checklist de Participação
        - [Lista de documentos necessários]
        - [Requisitos para proposta]
        - [Critérios de avaliação]
        """
    ),
    agent=compilador_de_relatorio,
    tools=[],
    async_execution=False,
    human_input=False,
    context=[montagem_de_cronograma],
)

revisao_de_relatorio = Task(
    description=dedent(
        """
        Com base nos resultados validados pela revisão, compile um relatório final contendo:
        1) Visão Geral do Edital
        2) Cronograma
        3) Riscos
        4) Oportunidades
        5) Lista de Requisitos por categoria
        6) Checklist para participação na licitação
        7) Glossário

        Dados de entrada:
        {overview}
        {all_sections}
        """
    ),
    expected_output=dedent(
        """
        # Relatório Final
        
        ## Visão Geral
        Referência: [Cliente] - [Número da Licitação]
        Data para submissão de propostas: [Data limite]
        Objeto da licitação: [Transcrição do objeto da licitação]

        ## Cronograma
        (Tabela com datas, marcos e prazos)

        ## Riscos
        [Principais Riscos, Penalidades, Fontes de Incerteza]

        ## Oportunidades
        [Oportunidades, Bônus, Remuneração Variável]

        ## Requisitos
        ### Prazos e cronograma
        - [...]

        ### Requisitos técnicos
        - [...]

        ### Econômico financeiro
        - [...]

        ### Riscos
        - [...]

        ### Oportunidades
        - [...]

        ### Outros requisitos
        - [...]

        ### Outras informações relevantes
        - [...]

        ## Checklist de Participação
        - [Lista de documentos necessários]
        - [Requisitos para proposta]
        - [Critérios de avaliação]

        ## Glossário
        - [Termo 1: Definição]
        - [Termo 2: Definição]
        - [Termo 3: Definição]
        """
    ),
    agent=revisor_de_relatório,
    tools=[],
    async_execution=False,
    human_input=False,
    context=[montagem_de_cronograma, compilacao_de_relatorio],
)
