from textwrap import dedent


TENDER_ANALYSIS_REPORT_DRAFT_TEMPLATE = dedent(
        """
        # Relatório de Análise de Licitação
        
        ## Visão Geral
        Referência: [Cliente] - [ID da Licitação]
        Data da disputa: [Data limite]
        Objeto da licitação: [Transcrição COMPLETA do objeto da licitação]

        ---

        ## Cronograma
        
        ### Tabela 1) Processo Licitatório
        [Datas e prazos do processo licitatório] 
        
        ###  Tabela 2) Execução do Contrato
        [Prazos, marcos contratuais, tipos de eventos de medição, percentuais de medição por evento e acumulados]

        #### Medição
        [Descrição dos eventos de medição e percentuais de pagamento. Medição é um jargão do segmento de obras de engenharia/formecimento de equipamentos, que se refere à mensuração do avanço físico do contrato, para fins de faturamento e pagamento. Alguns contratos preveem medições mensais de acordo com quantitativos detalhados, porém o mais comum é estabelecer eventos de medição que, ao serem executados e comprovados, dão direito ao contratado de receber um percentual do valor total do contrato.]

        #### Pagamento
        [Prazo de pagamento (Exemplos: a) 30 dias após a aprovação da fatura, b) 60 dias após a entrega do equipamento), garantias e retenções (Ex.: retenção de 5% do valor total do contrato até a entrega final), fonte dos recursos, outros detalhes relevantes]

        ---

        ## Riscos
        
        ### Penalidades
        [Descrição das penalidades potencialmente aplicáveis AO CONTRATADO por atraso, não conformidade, etc. incluindo valores por dia, valores máximos, suspensões e outras sanções relevantes]
        
        ### Garantias
        [Tipo, valor e condições de garantias exigidas, como caução, seguro-garantia, fiança bancária, etc.]
        
        ### Licenças e Alvarás
        [Responsabilidade pela obtenção de licenças e alvarás, custos e prazos envolvidos. Situação atual das licenças necessárias para a execução do contrato, especialmente relacionadas a meio ambiente] 
        
        ### Outros Riscos
        [Outros riscos relevantes ESPECÍFICOS desta licitação]

        ## Oportunidades
        [Bônus por antecipação de cronograma, Remuneração Variável por atingimento de metas, aproveitamento de estruturas pré-existentes, abertura para inovação tecnológica, frações do escopo com liberdade para inovação ou alteração, etc.]

        ## Características Técnicas

        ### Tecnologia e Processo de Tratamento
        [Descrição das tecnologias esperadas e/ou exigidas, tipo de tratamento, processos, características técnicas específicas, materiais aceitos, vendor list, etc.]

        ### Características [da Água ou do Efluente, conforme o caso]
        
        #### Entrada
        [Descrição das características físico-químicas e biológicas da água ou efluente a ser tratado]

        #### Saída
        [Descrição das características físico-químicas e biológicas da água ou efluente após o tratamento]

        ## Outras informações relevantes
        [Outras informações relevantes que não se enquadram nas categorias anteriores]

        ## Checklist de Participação da Disputa
        [Descrição qualitativa e quantitativa da atestação de capacidade técnica, lista de documentos de habilitação, tópicos e itens que devem constar da proposta, requisitos para elaboração e entrega da proposta, etc.]
        """)

# TODO: IMPROVE THIS WITH FOOTNOTES AND CROSS REFERENCES TO CHUNK_IDS
TENDER_ANALYSIS_FINAL_REPORT_TEMPLATE = dedent(f"""
<TEMPLATE>
{TENDER_ANALYSIS_REPORT_DRAFT_TEMPLATE}
</TEMPLATE>

Importante: O resultado final da tarefa é APENAS o relatório final revisado, sem nenhum comentário ou preambulo.
    """)
