import streamlit as st
import requests
from datetime import datetime

# --- Configurações da Página ---
st.set_page_config(
    page_title="Gerador de ETP/TR",
    page_icon="📝",
    layout="wide"
)

# --- Dicionário de Modalidades ---
# Mapeia os nomes das modalidades para seus códigos na API do PNCP.
MODALIDADES = {
    "Pregão": 5,
    "Dispensa de Licitação": 6,
    "Inexigibilidade": 7,
    "Concorrência": 1,
    "Credenciamento": 8,
}

# --- Funções ---

def buscar_contratos_pncp(termo: str, codigos_modalidades: list[int]):
    """
    Função para buscar contratos na API do PNCP, agora com filtro de modalidade.
    """
    # Define as datas inicial e final para a busca.
    data_inicial_str = "2020-01-03"
    data_final_str = datetime.now().strftime('%Y-%m-%d')

    # Adiciona os termos específicos para ETP e TR na busca para filtrar os resultados.
    termo_filtrado = f'{termo} "Estudo Técnico Preliminar" "Termo de Referência"'

    # Constrói a URL base da API.
    api_url = (
        f"https://pncp.gov.br/api/consulta/v1/contratacoes"
        f"?termo={requests.utils.quote(termo_filtrado)}"
        f"&dataInicial={data_inicial_str}"
        f"&dataFinal={data_final_str}"
        f"&pagina=1&tamanhoPagina=50"
    )

    # Adiciona os códigos de modalidade à URL, se algum for selecionado.
    if codigos_modalidades:
        for codigo in codigos_modalidades:
            api_url += f"&codigoModalidadeContratacao={codigo}"

    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        return response.json().get('data', [])
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao conectar com a API do PNCP: {e}")
        return None

# --- Interface do Usuário (UI) ---

st.title("🔎 Gerador Inteligente de ETP/TR")
st.markdown("Busque em licitações e contratos reais do **Portal Nacional de Contratações Públicas (PNCP)** para criar seus documentos.")

with st.form(key="search_form"):
    termo_busca = st.text_area(
        "**Qual o objeto da contratação ou credenciamento?**",
        placeholder="Ex: Credenciamento de laboratórios para exames de análises clínicas...",
        height=100
    )
    
    # Novo campo de seleção para filtrar por modalidade.
    modalidades_selecionadas = st.multiselect(
        "**Filtrar por modalidade (opcional):**",
        options=list(MODALIDADES.keys()),
        help="Selecione uma ou mais modalidades para refinar a busca."
    )
    
    submit_button = st.form_submit_button(label="Pesquisar no PNCP", type="primary")

# --- Lógica Principal ---

if submit_button and termo_busca:
    # Converte os nomes das modalidades selecionadas para seus códigos correspondentes.
    codigos_selecionados = [MODALIDADES[nome] for nome in modalidades_selecionadas]
    
    with st.spinner("Buscando no PNCP... Por favor, aguarde."):
        resultados = buscar_contratos_pncp(termo_busca, codigos_selecionados)

    st.divider()

    if resultados:
        st.success(f"**{len(resultados)} resultados encontrados para '{termo_busca}'**")
        
        for resultado in resultados:
            data_publicacao = datetime.fromisoformat(resultado['dataPublicacao']).strftime('%d/%m/%Y')
            valor_formatado = "Não informado"
            if resultado.get('valorTotalEstimado'):
                valor_formatado = f"R$ {resultado['valorTotalEstimado']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            with st.expander(f"**{resultado['orgaoNome']}** - {data_publicacao}"):
                st.markdown(f"**Objeto:** {resultado['objetoContratacao']}")
                st.markdown(f"**Modalidade:** {resultado.get('modalidadeNome', 'Não especificada')}")
                st.markdown(f"**Município/UF:** {resultado['municipioNome']}/{resultado['ufSigla']}")
                st.markdown(f"**Valor Estimado:** {valor_formatado}")

                link_pncp = f"https://pncp.gov.br/app/contratos/{resultado['id']}"
                st.link_button("Ver Contrato e Anexos no PNCP ↗️", link_pncp)

    elif resultados is not None:
        st.warning("Nenhum resultado encontrado para os critérios pesquisados. Tente usar outras palavras-chave ou alterar o filtro de modalidade.")
