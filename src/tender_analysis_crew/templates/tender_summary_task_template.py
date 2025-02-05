from textwrap import dedent


TENDER_ANALYSIS_REPORT_DRAFT_TEMPLATE = dedent(
        """
        # Relatório de Análise de Licitação
        
        ## Visão Geral
        Referência: [Cliente] - [ID da Licitação]
        Data para submissão de propostas: [Data limite]
        Objeto da licitação: [Transcrição do objeto da licitação]

        ## Cronograma
        [Tabelas 1 e 2 com datas, marcos e prazos]

        ## Medição
        [Descrição dos eventos de medição e percentuais de pagamento. Medição é um jargão do segmento de obras de engenharia/formecimento de equipamentos, que se refere à mensuração do avanço físico do contrato, para fins de pagamento. Alguns contratos preveem medições mensais de acordo com quantitativos detalhados, porém o mais comum é estabelecer eventos de medição que, ao serem executados e comprovados, dão direito ao fornecedor de receber um percentual do valor total do contrato.]

        ## Riscos
        [Penalidades, Garantias, Licenças e alvarás, Fontes de Incerteza...]

        ## Oportunidades
        [Bônus, Remuneração Variável]

        ## Requisitos
        ### Prazos e cronograma
        - [...]

        ### Requisitos técnicos
        - [...]

        ### Econômico financeiro
        - [...]

        ### Outros requisitos
        - [...]

        ### Outras informações relevantes
        - [...]

        ## Checklist de Participação da Disputa
        - [Lista de documentos necessários]
        - [Requisitos para elaboração e entrega da proposta]
        - [Critérios para escolha da proposta vencedora]
        """)

# TODO: IMPROVE THIS WITH FOOTNOTES AND CROSS REFERENCES TO CHUNK_IDS
TENDER_ANALYSIS_FINAL_REPORT_TEMPLATE = dedent(f"""
    {TENDER_ANALYSIS_REPORT_DRAFT_TEMPLATE}
    """)
