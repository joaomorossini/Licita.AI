from crewai import Task
from textwrap import dedent
from datetime import datetime

from .agents import (
    analista_de_licitacoes,
    compilador_de_relatorio,
    revisor_de_relatório,
)

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")

analise_de_licitacao = Task(
    description=dedent(
        """
        Analisar cuidadosamente os documentos da licitação para identificar, extrair e categorizar as seções relevantes. Categorias disponíveis: 'objeto_da_licitação', 'prazos_e_cronograma', 'requisitos_tecnicos', 'economicos_financeiros', 'riscos', 'oportunidades', 'outros_requisitos' e 'outras_informacoes_relevantes'.

        <documentos_do_edital>
        {tender_documents_text}
        </documentos_do_edital>
        """
    ),
    expected_output=dedent(
        """
        Um markdown contendo uma visão geral e um compilado estruturado de trechos relevantes do edital, cada um com os tópicos 'categoria', 'checklist_de_proposta' (usar 'sim' para informações que impactam diretamente a elaboração e apresentação da proposta e 'não' para as demais), 'transcricao' e 'comentario'. Siga o modelo abaixo, delimitado por <<<>>>. Colchetes foram usados para representar placeholders.
        
        
        MODELO:
        <<<
        # Visão Geral

        Referência: [Cliente] - [Número da Licitação]
        Data para submissão de propostas: [Data limite]
        Objeto da licitação: [Transcrição do objeto da licitação]

        ---

        # Trechos Relevantes

        ## Trecho 1
        - categoria: prazos_e_cronograma
        - checklist_de_proposta: não
        - transcricao: "Aprovação do projeto executivo em até 30 dias após a assinatura do contrato."
        - comentario: Necessário verificar prazo de avaliação pelo cliente e confirmar se os 30 dias incluem essa etapa.

        ## Trecho 2
        - categoria: economicos_financeiros
        - checklist_de_proposta: sim
        - transcricao: "Valor máximo aceito pelo contrante: R$ 2.500.000,00."
        - comentario: Propostas acima deste valor serão desclassificadas.

        ## Trecho 3
        - categoria: requisitos_tecnicos
        - checklist_de_proposta: sim
        - transcricao: "Todos os equipamentos devem ser fabricados em aço inox 304 ou superior"
        - comentario: Importante que o orçamento e a proposta técnica levem em consideração a qualidade do aço e o custo do material exigido.

        ## Trecho 4
        - categoria: riscos
        - checklist_de_proposta: nao
        - transcricao: "Nenhum valor será devido referente à Etapa 2 em caso de não atendimento dos parâmetros de qualidade do efluente tratado"
        - comentario: equipe técnica deve avaliar a qualidade do efluente bruto e confirmar a viabilidade de atender aos parâmetros de qualidade exigidos.
        >>>
        """
    ),
    agent=analista_de_licitacoes,
    tools=[],
    async_execution=False,
    human_input=False,
)

# TODO: Adicionar ferramenta para cálculo de prazos e datas
montagem_de_cronograma = Task(
    description=dedent(
        """
        Organizar todos os prazos e datas relevantes do edital, construindo um cronograma em formato de tabela ou bullet points (desde abertura da licitação até encerramento do contrato).
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
    context=[analise_de_licitacao],
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
        7) Glossário
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
    agent=compilador_de_relatorio,
    tools=[],
    async_execution=False,
    human_input=False,
    # The final compilation depends on the review step, which in turn references the prior tasks
    context=[analise_de_licitacao, montagem_de_cronograma],
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
    context=[analise_de_licitacao, montagem_de_cronograma, compilacao_de_relatorio],
)
