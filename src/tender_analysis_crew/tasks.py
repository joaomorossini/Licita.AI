from crewai import Task
from textwrap import dedent
from datetime import datetime

from src.tender_analysis_crew.templates.tender_summary_task_template import TENDER_ANALYSIS_FINAL_REPORT_TEMPLATE, TENDER_ANALYSIS_REPORT_DRAFT_TEMPLATE

from .agents import (
    analista_de_licitacoes,
    compilador_de_relatorio,
    revisor_de_relatório,
)

from .tools import calculator_tool


current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")

montagem_de_cronograma = Task(
    description=dedent(
        """
        Selecionar e organizar as datas e prazos MAIS RELEVANTES do edital, sob o ponto de vista de uma empresa decidindo sobre participar ou não da licitação, construindo duas tabelas.
        - Tabela 1 - Processo Licitatório: Lançamento do edital até data da disputa
        - Tabela 2: Execução do contrato: Prazos e datas relevantes para a execução do objeto contratual. Nota: Como não se pode ter certeza de antemão quando a execução vai iniciar (isso pode ser afetado por recursos administrativos, judiciais, prazos de avaliação de propostas, etc.), costuma-se avaliar o cronograma de execução em termos da data zero, que normalmente é a data de assinatura do contrato e, a partir daí, existem prazos para execução e comprovação das etapas do objeto contratual.

        PRESTE MUITA ATENÇÃO
        1) Os prazos e datas são de extrema importância. Certifique-se de que as datas e prazos estão corretos, ou seja, que foram extraídos do edital cuidadosamente, sem erros de digitação ou interpretação e, em especial, sem alucionações ou suposições. Se houver dúvidas, adicione notas abaixo das tabelas para indicar as dúvidas e as possíveis interpretações.
        2) A soma dos valores na coluna "Medição" da Tabela 2 deve SEMPRE ser igual a 100%. Use a ferramenta "Calculator" para verificar se a soma está correta. Caso as informações disponíveis não totalizem 100%, elimine as colunas "Medição Evento (%)" e "Medição Acumulada (%)" e adicione uma nota explicativa (com um emoji de warning), contendo as informações disponíveis.

        Dados de entrada:
        {cronograma_sections}
        """
    ),
    expected_output=dedent(
        """
        IMPORTANTE: Abaixo encontram-se exemplos meramente ilustrativos.
        SUBSTITUA-OS PELOS DADOS REAIS DA LICITAÇÃO.

        <EXEMPLO TABELA 1>
        # 1) Processo Licitatório
        |Data      | Evento                                          |
        |----------|-------------------------------------------------|
        |DD/MM/AAAA| Publicação do edital                            |
        |DD/MM/AAAA| Data limite para pedidos de esclarecimento      |
        |DD/MM/AAAA| Abertura das propostas                          |
        |DD/MM/AAAA| Data limite para apresentação de recurso admin  |
        </EXEMPLO TABELA 1>

        <EXEMPLO TABELA 2>
        # 2) Execução do Contrato
        | Prazo (dias) | Marco Contratual                 | Tipo            | Medição Evento (%) | Medição Acumulada (%) |
        |--------------|----------------------------------|-----------------|--------------------|-----------------------|
        | 0            | Assinatura do contrato           | Início          | 0                  | 0                     |
        | 30           | Aprovação do Projeto Básico      | Projeto         | 10                 | 10                    |
        | 90           | Aprovação do Projeto Executivo   | Projeto         | 20                 | 30                    |
        | 180          | Término das obras de implantação | Obras           | 50                 | 80                    |
        | 210          | Término do comissionamento       | Comissionamento | 0                  | 80                    |
        | 300          | Fim da pré-operação              | Operação        | 10                 | 90                    |
        | 300          | Fim da operação assistida        | Operação        | 10                 | 100                   |
        | 360          | Fim da vigência contratual       | Encerramento    | 0                  | 100                   |
        Nota: Todos os prazos são contados em dias corridos a partir da data de assinatura do contrato.
        </EXEMPLO TABELA 2>
        """
    ),
    agent=analista_de_licitacoes,
    tools=[calculator_tool],
    async_execution=False,
    human_input=False,
)

esboco_do_relatorio = Task( 
    description=dedent(
        """
        Fundamentado nos DADOS DE ENTRADA e nos tabelas de cronograma fornecidas, compile um relatório de análise correto, preciso e útil para a empresa interessada em participar da licitação. Siga a estrutura fornecida.

        EVITE incluir informações óbvias ou irrelevantes, especialmente aquelas que são verdadeiras para todas as licitações. Por exemplo, não é necessário adicionar observações como "o não cumprimento do contrato pode resultar em penalidades" ou "condições climáticas podem afetar a execução das obras". Leve em consideração que esse relatório é destinado a uma equipe experiente no assunto.

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

# TODO: Adicionar ferramenta para obtenção de feedback humano
# TODO: IMPROVE revision task to add more value to the final report
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
