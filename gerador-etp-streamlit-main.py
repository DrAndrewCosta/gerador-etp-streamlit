import streamlit as st
import requests
from datetime import datetime, timedelta

# --- Configurações da Página ---
# Define o título da página, ícone e layout. Isso deve ser o primeiro comando do Streamlit.
st.set_page_config(
    page_title="Gerador de ETP/TR",
    page_icon="📝",
    layout="wide"
)

# --- Funções ---

def buscar_contratos_pncp(termo: str):
    """
    Função para buscar contratos na API do PNCP.
    Ela constrói a URL, faz a requisição e retorna os dados em formato JSON.
    """
    # Calcula a data de 3 anos atrás para filtrar os resultados.
    data_limite = datetime.now() - timedelta(days=3*365)
    data_inicial_str = data_limite.strftime('%Y-%m-%d')

    # Monta a URL da API com os parâmetros de busca.
    # Usamos f-string para inserir as variáveis diretamente na URL.
    # O termo de busca é codificado para ser seguro para URLs.
    api_url = (
        f"https://pncp.gov.br/api/pncp/v1/contratacoes"
        f"?termo={requests.utils.quote(termo)}"
        f"&dataInicial={data_inicial_str}"
        f"&pagina=1&tamanhoPagina=50" # Buscamos até 50 resultados
    )

    try:
        # Faz a requisição GET para a API.
        response = requests.get(api_url, timeout=30)
        # Verifica se a resposta foi bem-sucedida (código 200).
        response.raise_for_status()
        # Converte a resposta para JSON e retorna os dados.
        return response.json().get('data', [])
    except requests.exceptions.RequestException as e:
        # Em caso de erro na requisição, exibe uma mensagem de erro e retorna None.
        st.error(f"Erro ao conectar com a API do PNCP: {e}")
        return None

# --- Interface do Usuário (UI) ---

# Título principal da aplicação.
st.title("🔎 Gerador Inteligente de ETP/TR")
st.markdown("Busque em licitações e contratos reais do **Portal Nacional de Contratações Públicas (PNCP)** para criar seus documentos.")

# Cria um formulário para agrupar o campo de texto e o botão.
# Isso evita que a página recarregue de formas inesperadas.
with st.form(key="search_form"):
    # Campo de área de texto para o usuário inserir o objeto da contratação.
    termo_busca = st.text_area(
        "**Qual o objeto da contratação ou credenciamento?**",
        placeholder="Ex: Credenciamento de laboratórios para exames de análises clínicas...",
        height=100
    )
    # Botão para submeter o formulário de busca.
    submit_button = st.form_submit_button(label="Pesquisar no PNCP", type="primary")

# --- Lógica Principal ---

# Verifica se o botão de busca foi pressionado e se o campo de busca não está vazio.
if submit_button and termo_busca:
    # Mostra um "spinner" de carregamento enquanto a busca é realizada.
    with st.spinner("Buscando no PNCP... Por favor, aguarde."):
        resultados = buscar_contratos_pncp(termo_busca)

    st.divider() # Adiciona uma linha divisória para separar a busca dos resultados.

    # Verifica se a busca retornou resultados.
    if resultados:
        st.success(f"**{len(resultados)} resultados encontrados para '{termo_busca}'**")
        
        # Itera sobre cada resultado encontrado para exibi-lo.
        for resultado in resultados:
            # Formata a data para o padrão brasileiro.
            data_publicacao = datetime.fromisoformat(resultado['dataPublicacao']).strftime('%d/%m/%Y')
            # Formata o valor para a moeda brasileira.
            valor_formatado = "Não informado"
            if resultado.get('valorTotalEstimado'):
                valor_formatado = f"R$ {resultado['valorTotalEstimado']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            # Usa um "expander" para mostrar os detalhes de cada contrato de forma organizada.
            with st.expander(f"**{resultado['orgaoSubRogado']['nome']}** - {data_publicacao}"):
                st.markdown(f"**Objeto:** {resultado['objetoContratacao']}")
                st.markdown(f"**Modalidade:** {resultado.get('modalidadeNome', 'Não especificada')}")
                st.markdown(f"**Município/UF:** {resultado['municipioNome']}/{resultado['ufSigla']}")
                st.markdown(f"**Valor Estimado:** {valor_formatado}")

                # Cria o link direto para a página do contrato no PNCP.
                link_pncp = f"https://pncp.gov.br/app/contratos/{resultado['id']}"
                st.link_button("Ver Contrato e Anexos no PNCP ↗️", link_pncp)

    # Se a busca não retornou resultados.
    elif resultados is not None:
        st.warning("Nenhum resultado encontrado para o termo pesquisado. Tente usar outras palavras-chave.")

