from crewai import Task
from textwrap import dedent
from datetime import datetime

from src.tender_analysis_crew.templates.tender_summary_task_template import TENDER_ANALYSIS_FINAL_REPORT_TEMPLATE, TENDER_ANALYSIS_REPORT_DRAFT_TEMPLATE

from .agents import (
    analista_de_licitacoes,
    compilador_de_relatorio,
    revisor_de_relatório,
)

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")

montagem_de_cronograma = Task(
    description=dedent(
        """
        Selecionar e organizar as datas e prazos MAIS RELEVANTES do edital, sob o ponto de vista de uma empresa decidindo sobre participar ou não da licitação, construindo duas tabelas.
        - Tabela 1 - Processo Licitatório: Lançamento do edital até data da disputa
        - Tabela 2: Execução do contrato: Prazos e datas relevantes para a execução do objeto contratual. Nota: Como não se pode ter certeza de antemão quando a execução vai iniciar (isso pode ser afetado por recursos administrativos, judiciais, prazos de avaliação de propostas, etc.), costuma-se avaliar o cronograma de execução em termos da data zero, que normalmente é a data de assinatura do contrato e, a partir daí, existem prazos para execução e comprovação das etapas do objeto contratual.

        Dados de entrada:
        {cronograma_sections}
        """
    ),
    expected_output=dedent(
        """
        # 1) Processo Licitatório
        |Data      | Evento                                          |
        |----------|-------------------------------------------------|
        |10/01/2025| Publicação do edital                            |
        |25/01/2025| Data limite para pedidos de esclarecimento      |
        |01/02/2025| Abertura das propostas                          |
        |10/02/2025| Data limite para apresentação de recurso admin  |

        # 2) Execução do Contrato
        | Prazo | Marco Contratual                 | Tipo            | Medição |
        |-------|----------------------------------|-----------------|---------|
        | 0     | Assinatura do contrato           | Início          | 0%      |
        | 30    | Aprovação do Projeto Básico      | Projeto         | 10%     |
        | 90    | Aprovação do Projeto Executivo   | Projeto         | 20%     |
        | 180   | Término das obras de implantação | Obras           | 50%     |
        | 210   | Término do comissionamento       | Comissionamento | 0%      |
        | 300   | Fim da pré-operação              | Operação        | 10%     |
        | 300   | Fim da operação assistida        | Operação        | 10%     |
        | 360   | Fim da vigência contratual       | Encerramento    | 0%      |
        Nota: Todos os prazos são contados em dias corridos a partir da data de assinatura do contrato.
        """
    ),
    agent=analista_de_licitacoes,
    tools=[],
    async_execution=False,
    human_input=False,
)

esboco_do_relatorio = Task(
    description=dedent(
        """
        Fundamentado nos DADOS DE ENTRADA e nos tabelas de cronograma fornecidas, compile um relatório de análise correto, preciso e útil para a empresa interessada em participar da licitação. Siga a estrutura fornecida.

        <DADOS DE ENTRADA>
            <VISÃO GERAL>
            {overview}
            </VISÃO GERAL>

            <TRECHOS RELEVANTES>
            {all_sections}
            </TRECHOS RELEVANTES>
        </DADOS DE ENTRADA>
        """
    ),
    expected_output=TENDER_ANALYSIS_REPORT_DRAFT_TEMPLATE,
    agent=compilador_de_relatorio,
    tools=[],
    async_execution=False,
    human_input=False,
    context=[montagem_de_cronograma],
)

# TODO: Corrigir etapa de revisão. A tarefa estava exatamente igual à tarea anterior.
revisao_final_do_relatorio = Task(
    description=dedent(
        """
        - Com base nos dados de entrada e no relatório compilado a partir destes dados, revise e complemento o esboço do relatório para produzir a versão final, que será entrega ao seu Diretor.
        - Garante que todas as informações estejam CORRETAS, claras e bem estruturadas.
        - Caso encontre algum erro ou inconsistência, corrija imediatamente.
        - Adicione comentários e observações relevantes, se necessário.
        - Reescreva ou reformule trechos ambíguos ou confusos.

        <DADOS DE ENTRADA>
            <VISÃO GERAL>
            {overview}
            </VISÃO GERAL>

            <TRECHOS RELEVANTES>
            {all_sections}
            </TRECHOS RELEVANTES>
        </DADOS DE ENTRADA>
        """
    ),
    expected_output=TENDER_ANALYSIS_FINAL_REPORT_TEMPLATE,
    agent=revisor_de_relatório,
    tools=[],
    async_execution=False,
    human_input=False,
    context=[esboco_do_relatorio],
)
