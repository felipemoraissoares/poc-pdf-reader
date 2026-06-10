"""
Motor de regras de validação por país fornecedor.
Cada país tem um conjunto de validações que devem ser verificadas no texto extraído.
"""

import re
from typing import Optional

# Países parceiros da Embraer com nomes em português e inglês para busca
PAISES_PARCEIROS = {
    "Portugal": ["Portugal"],
    "Espanha": ["Espanha", "Spain", "España"],
    "Argentina": ["Argentina"],
    "EUA": ["EUA", "USA", "United States", "Estados Unidos", "U.S.A", "U.S."],
    "Reino Unido": ["Reino Unido", "United Kingdom", "UK", "Great Britain", "England"],
    "Rep. Tcheca": ["Rep. Tcheca", "República Tcheca", "Czech Republic", "Czechia"],
    "Alemanha": ["Alemanha", "Germany", "Deutschland"],
    "França": ["França", "France"],
    "Israel": ["Israel"],
    "Itália": ["Itália", "Italy", "Italia"],
    "Bélgica": ["Bélgica", "Belgium", "Belgique", "België"],
    "Holanda": ["Holanda", "Netherlands", "Nederland", "Holland"],
    "Uruguai": ["Uruguai", "Uruguay"],
    "Índia": ["Índia", "India"],
    "Coreia": ["Coreia", "Korea", "South Korea", "República da Coreia"],
    "Emirados Árabes": ["Emirados Árabes", "UAE", "United Arab Emirates", "الإمارات"],
    "Áustria": ["Áustria", "Austria", "Österreich"],
    "Suécia": ["Suécia", "Sweden", "Sverige"],
}

# Países permitidos para a regra V3 da Alemanha
PAISES_PERMITIDOS_ALEMANHA = [
    "Australia", "Latvia", "Austria", "Belgium", "Bulgaria", "Canada",
    "Croatia", "Cyprus", "Czech Republic", "Denmark", "Estonia", "Finland",
    "France", "Germany", "Great Britain", "Greece", "Hungary", "Ireland",
    "Italy", "Japan", "Lithuania", "Luxembourg", "Malta", "Netherlands",
    "New Zealand", "Norway", "Poland", "Portugal", "Romania",
    "Slovak Republic", "Slovenia", "Spain", "Sweden", "Switzerland", "USA"
]

# Definição das regras de validação por país fornecedor
REGRAS_POR_PAIS = {
    "Portugal": [
        {
            "id": "PT-V1",
            "descricao": "Licença no padrão anexo Portugal + nome do fornecedor presente no documento",
            "tipo": "automatico",
            "termos_busca": ["Licença", "License", "Licencia", "fornecedor"],
        },
        {
            "id": "PT-V2",
            "descricao": "Consta 'Licença Geral' no documento",
            "tipo": "automatico",
            "termos_busca": ["Licença Geral", "General License", "Licencia General"],
        },
    ],
    "Espanha": [
        {
            "id": "ES-V1",
            "descricao": "Licença no padrão anexo Espanha + nome do fornecedor presente no documento",
            "tipo": "automatico",
            "termos_busca": ["Licencia", "License", "DUA", "CCATS"],
        },
        {
            "id": "ES-V2",
            "descricao": "Destinatário é Embraer ou End User",
            "tipo": "automatico",
            "termos_busca": ["Embraer", "End User", "usuario final", "destinatario", "destinatário"],
        },
    ],
    "Argentina": [
        {
            "id": "AR-V1",
            "descricao": "Licença no padrão anexo Argentina + nome do fornecedor presente no documento",
            "tipo": "automatico",
            "termos_busca": ["Certificado", "Licencia", "DGCE", "fornecedor"],
        },
        {
            "id": "AR-V2",
            "descricao": "Não consta nome de cliente específico diferente do End User",
            "tipo": "automatico",
            "termos_busca": ["End User", "Usuario Final", "Embraer"],
        },
    ],
    "EUA": [
        {
            "id": "US-V1",
            "descricao": "Licença nos 2 padrões do anexo EUA (EAR/ITAR) + nome do fornecedor presente",
            "tipo": "automatico",
            "termos_busca": ["EAR", "ITAR", "Export License", "BIS", "DDTC", "EAR99"],
        },
        {
            "id": "US-V2",
            "descricao": "End User consta na lista Approved End User (EAR) ou Foreign End User (ITAR)",
            "tipo": "automatico",
            "termos_busca": ["Approved End User", "Foreign End User", "Embraer", "End User"],
        },
    ],
    "Reino Unido": [
        {
            "id": "UK-V1",
            "descricao": "Licença no padrão anexo Reino Unido + nome do fornecedor presente",
            "tipo": "automatico",
            "termos_busca": ["SIEL", "OIEL", "OGEL", "Export Licence", "ECJU"],
        },
        {
            "id": "UK-V2",
            "descricao": "Validação conforme tipo de licença UK:\n• SIEL: End User é Embraer/End User procurado\n• OIEL: país do End User listado como destination\n• OGEL: país do End User NÃO consta em destination concerned",
            "tipo": "automatico",
            "termos_busca": ["Embraer", "End User", "destination", "consignee"],
        },
    ],
    "Rep. Tcheca": [
        {
            "id": "CZ-V1",
            "descricao": "Licença no padrão anexo Rep. Tcheca + nome do fornecedor presente",
            "tipo": "automatico",
            "termos_busca": ["Licence", "Vývozní", "CEKIA", "Ministerstvo", "fornecedor"],
        },
    ],
    "Alemanha": [
        {
            "id": "DE-V1",
            "descricao": "Licença no padrão anexo Alemanha + nome do fornecedor presente",
            "tipo": "automatico",
            "termos_busca": ["Ausfuhrgenehmigung", "BAFA", "Bundesamt", "Genehmigung"],
        },
        {
            "id": "DE-V2",
            "descricao": "End User consta no campo Endverwender",
            "tipo": "automatico",
            "termos_busca": ["Endverwender", "Embraer"],
        },
        {
            "id": "DE-V3",
            "descricao": "Se não constar no Endverwender, verificar se o país está na lista de países permitidos da Alemanha",
            "tipo": "automatico",
            "termos_busca": PAISES_PERMITIDOS_ALEMANHA[:5],  # amostra para busca
        },
    ],
    "França": [
        {
            "id": "FR-V1",
            "descricao": "Licença no padrão anexo França + nome do fornecedor presente",
            "tipo": "automatico",
            "termos_busca": ["Licence d'exportation", "SBDU", "Douanes", "autorisation", "fournisseur"],
        },
    ],
    "Israel": [
        {
            "id": "IL-V1",
            "descricao": "Licença no padrão anexo Israel + nome do fornecedor presente",
            "tipo": "automatico",
            "termos_busca": ["Export License", "רישיון", "Ministry of Defense", "SIBAT"],
        },
        {
            "id": "IL-V2",
            "descricao": "Verificar no SAP se o item tem SN aprovado (confirmação manual necessária)",
            "tipo": "manual",
            "instrucao": "Acesse o SAP e verifique se o número de série do item consta como aprovado para exportação.",
        },
        {
            "id": "IL-V3",
            "descricao": "Se SN aprovado, verificar PEP no campo 'Class Cont.' (confirmação manual necessária)",
            "tipo": "manual",
            "instrucao": "Com o SN confirmado, verifique se o PEP consta no campo 'Class Cont.' no SAP.",
        },
    ],
    "Itália": [
        {
            "id": "IT-V1",
            "descricao": "Licença no padrão anexo Itália + nome do fornecedor presente",
            "tipo": "automatico",
            "termos_busca": ["Autorizzazione", "UAMA", "ICE", "licenza", "fornitore"],
        },
        {
            "id": "IT-V2",
            "descricao": "Cliente procurado consta no campo 'Utilizzatore Finale'",
            "tipo": "automatico",
            "termos_busca": ["Utilizzatore Finale", "Embraer", "utilizzatore"],
        },
    ],
    "Bélgica": [
        {
            "id": "BE-V1",
            "descricao": "Licença no padrão anexo Bélgica + nome do fornecedor presente",
            "tipo": "automatico",
            "termos_busca": ["Licence d'exportation", "Exportvergunning", "DGCD", "fournisseur", "leverancier"],
        },
    ],
    "Holanda": [
        {
            "id": "NL-V1",
            "descricao": "Licença no padrão anexo Holanda + nome do fornecedor presente",
            "tipo": "automatico",
            "termos_busca": ["Uitvoervergunning", "RVO", "exportvergunning", "leverancier"],
        },
    ],
}


def obter_regras(pais_fornecedor: str) -> list:
    """Retorna a lista de regras de validação para o país fornecedor."""
    return REGRAS_POR_PAIS.get(pais_fornecedor, [])


def verificar_regra_automatica(regra: dict, texto_completo: str,
                                nome_fornecedor: str = "") -> dict:
    """
    Executa verificação automática de uma regra no texto extraído.
    Retorna dict com status e trechos encontrados.
    """
    termos = regra.get("termos_busca", [])
    trechos_encontrados = []
    encontrou_algum = False

    for termo in termos:
        if not termo:
            continue
        flags = re.IGNORECASE
        matches = list(re.finditer(re.escape(str(termo)), texto_completo, flags))
        if matches:
            encontrou_algum = True
            for m in matches[:2]:
                inicio = max(0, m.start() - 50)
                fim = min(len(texto_completo), m.end() + 50)
                trechos_encontrados.append({
                    "termo": termo,
                    "trecho": texto_completo[inicio:fim].strip()
                })

    # Verifica nome do fornecedor se fornecido
    fornecedor_encontrado = False
    if nome_fornecedor and len(nome_fornecedor) > 2:
        if re.search(re.escape(nome_fornecedor), texto_completo, re.IGNORECASE):
            fornecedor_encontrado = True

    # Determina status baseado nos achados
    if encontrou_algum:
        status = "Aprovado"
    elif trechos_encontrados:
        status = "Aprovado"
    else:
        status = "Inconclusivo"

    return {
        "status": status,
        "trechos": trechos_encontrados,
        "fornecedor_encontrado": fornecedor_encontrado,
        "automatico": True
    }


def verificar_paises_cobertos(texto_completo: str) -> dict:
    """
    Verifica quais países parceiros estão mencionados no texto do PDF.
    Retorna dict {país: "Coberto" | "Não coberto"}.
    """
    resultado = {}
    for pais, variantes in PAISES_PARCEIROS.items():
        coberto = False
        for variante in variantes:
            if re.search(re.escape(variante), texto_completo, re.IGNORECASE):
                coberto = True
                break
        resultado[pais] = "Coberto" if coberto else "Não coberto"
    return resultado


def calcular_resultado_geral(validacoes: list) -> str:
    """
    Calcula o resultado geral baseado nas validações.
    Aprovado = todas aprovadas; Reprovado = alguma reprovada; Revisar = alguma inconclusiva.
    """
    statuses = [v.get("status_analista", v.get("status", "Inconclusivo")) for v in validacoes]

    if all(s == "Aprovado" for s in statuses):
        return "Aprovado"
    elif any(s == "Reprovado" for s in statuses):
        return "Reprovado"
    else:
        return "Revisar"
