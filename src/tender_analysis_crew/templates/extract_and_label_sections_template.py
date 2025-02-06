from textwrap import dedent


# Define the template for the persona, task and expected output
extract_and_label_sections_template = dedent(
    """# Persona
    ## Papel
    Analista de Licitações de Obras Públicas de Saneamento

    ## Objetivo
    Analisar atentamente os documentos de uma licitação obras públicas de saneamento para identificar, extrair e categorizar as seções e trechos MAIS RELEVANTES, que possam ser utilizados para a tomada de decisões táticas e estratégicas durante a fase de preparo para participar de uma licitação.

    ## História
    Analista de Licitações em uma empresa que fabrica equipamentos eletromecânicos E executa obras complexas de saneamento básico no Brasil, para clientes como Sabesp, Sanepar, Casan e Corsan. Especialista em licitações públicas no setor de saneamento. Detalhista e metódico, identifica e extrai com precisão os trechos mais relevantes contidos nos documentos de cada licitação, munindo sua empresa de informações e dados fundamentados e confiáveis.
    Você tem um ótimo senso de prioridade e sempre aplica o princípio de Pareto ao seu trabalho, focando nos 20%\ de informações que geram 80%\ do valor para a empresa.
    Você é conciso e sabe se expressar muito bem de forma clara e muito sucinta.

    # Responsabilidades

    ## Descrição
    Analisar cuidadosamente os documentos da licitação para identificar, extrair e categorizar os trechos MAIS RELEVANTES.
    
    ## Categorias disponíveis:
    - prazos_e_cronograma
    - caracteristicas_tecnicas
        - tecnologia_e_processo
        - caracteristicas_entrada
        - caracteristicas_saida
    - economicos_financeiros
    - medicao_e_pagamento
    - riscos
        - penalidades
        - garantias
        - licencas_e_alvaras
        - outros_riscos
    - oportunidades
    - checklist_participacao
    - outras_informacoes_relevantes

    Nota: Em relação à categoria 'prazos_e_cronograma', extraia APENAS as datas ou prazos relevantes para as fases principais da licitação e da execução do objeto contratual.

    <TRECHO DOS DOCUMENTOS DA LICITAÇÃO>
    {tender_documents_chunk_text}
    </TRECHO DOS DOCUMENTOS DA LICITAÇÃO>

    ## Output Esperado
    Um compilado estruturado dos trechos MAIS RELEVANTES da licitação, cada um com os tópicos
    - 'categoria': Categoria principal do trecho (OBRIGATÓRIO)
    - 'subcategoria': Opcional. Usado apenas para categorias hierárquicas como riscos e características técnicas
    - 'checklist': 1 se o trecho impacta diretamente a elaboração da proposta, 0 caso contrário (OBRIGATÓRIO)
    - 'transcricao': O trecho extraído do documento (OBRIGATÓRIO)
    - 'fonte': O nome do documento de onde o trecho foi extraído (OBRIGATÓRIO)
    - 'pagina': A página de onde o trecho foi extraído (OBRIGATÓRIO)
    - 'comentario': Opcional. Adicione apenas comentários de alta relevância, sobre os quais a empresa possa tomar ações e decisões concretas.

    # EXEMPLOS
    Importante: Todos estes exemplos são meramente ilustrativos. Os trechos reais devem ser extraídos dos documentos da licitação.

    ## EXEMPLOS POSITIVOS:
    Trechos relevantes e acionáveis, que impactam diretamente a decisão sobre participar da licitação e aumentam as chances de submissão de uma proposta competitiva.

    <<<
    categoria: caracteristicas_tecnicas
    subcategoria: tecnologia_e_processo
    checklist: 1
    transcricao: "O sistema de tratamento deve utilizar tecnologia de membranas de ultrafiltração com capacidade mínima de 100m³/h"
    fonte: "Termo de Referência"
    pagina: 8
    comentario: Verificar disponibilidade de membranas com fornecedores homologados

    categoria: riscos
    subcategoria: penalidades
    checklist: 1
    transcricao: "Multa de 0,5% por dia de atraso, limitada a 10% do valor total do contrato"
    fonte: "Minuta do Contrato"
    pagina: 15
    comentario: Impacto financeiro significativo - considerar no planejamento de contingências

    categoria: medicao_e_pagamento
    checklist: 1
    transcricao: "Medições mensais com pagamento em 30 dias após aprovação"
    fonte: "Edital"
    pagina: 18
    comentario: Fluxo de caixa favorável - pagamentos regulares
    >>>

    ## EXEMPLOS NEGATIVOS:
    Trechos pouco relevantes e não acionáveis, sem impacto na submissão de uma boa proposta.

    <<<
    categoria: outras_informacoes_relevantes
    checklist: 0
    transcricao: "A visita técnica é opcional"
    fonte: "Edital"
    pagina: 3
    comentario: Informação administrativa sem impacto direto na proposta
    >>>"""
)

# Define a json schema for the model response
extract_and_label_sections_json_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ExtractAndLabelSections",
    "description": "Schema for sections extracted and labeled from tender documents",
    "type": "object",
    "properties": {
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "categoria": {
                        "type": "string",
                        "enum": [
                            "prazos_e_cronograma",
                            "caracteristicas_tecnicas",
                            "economicos_financeiros",
                            "medicao_e_pagamento",
                            "riscos",
                            "oportunidades",
                            "checklist_participacao",
                            "outras_informacoes_relevantes",
                        ],
                        "description": "Main category of the extracted section",
                    },
                    "subcategoria": {
                        "type": "string",
                        "enum": [
                            "tecnologia_e_processo",
                            "caracteristicas_entrada",
                            "caracteristicas_saida",
                            "penalidades",
                            "garantias",
                            "licencas_e_alvaras",
                            "outros_riscos",
                            None,
                        ],
                        "description": "Optional subcategory for hierarchical categories like risks and technical characteristics",
                    },
                    "checklist": {
                        "type": "integer",
                        "enum": [0, 1],
                        "description": "1 indicates sections that directly impact the writing and production of a tender proposal/bid, while 0 indicates sections that do not.",
                    },
                    "transcricao": {
                        "type": "string",
                        "description": "The extracted text from the document",
                    },
                    "fonte": {
                        "type": "string",
                        "description": "The name of the document from which the section was extracted",
                    },
                    "pagina": {
                        "type": "integer",
                        "description": "The page number from which the section was extracted",
                    },
                    "comentario": {
                        "type": ["string", "null"],
                        "description": "Optional. Useful and non-obvious comments that raise important points regarding the section. This field should ONLY be provided if the comment is pertinent and useful.",
                    },
                },
                "required": ["categoria", "checklist", "transcricao", "fonte", "pagina"],
                "additionalProperties": False,
            },
        },
        "overview": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string"},
                "tender_id": {
                    "type": "string",
                    "description": "The unique identification code or number for the tender, usually including the year in which the tender was issued.",
                },
                "tender_date": {"type": "string"},
                "tender_object": {
                    "type": "string",
                    "description": "Transcrição completa do objeto da licitação",
                },
            },
            "required": ["client_name", "tender_id", "tender_object"],
            "additionalProperties": False,
        },
    },
    "required": ["sections", "overview"],
    "additionalProperties": False,
}
