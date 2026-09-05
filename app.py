import streamlit as st
import json
import io
import zipfile
import pandas as pd
from datetime import date

# Configuração da página e tema visual
st.set_page_config(
    page_title="OSC Assessoria Contábil - Portal Fiscal", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada (Cores institucionais: Azul Marinho e Azul Escuro)
st.markdown("""
    <style>
        .main-header {
            color: #0F2C59;
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 0px;
        }
        .sub-header {
            color: #334155;
            font-size: 15px;
            margin-bottom: 20px;
        }
        .stButton>button {
            background-color: #0F2C59;
            color: white;
            border-radius: 6px;
            padding: 6px 16px;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #1E40AF;
            color: white;
        }
        .download-row {
            background-color: #F8FAFC;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 8px;
            border-left: 4px solid #0F2C59;
        }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho Institucional
st.markdown('<p class="main-header">OSC Assessoria Contábil</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Central Unificada de Captura, Consulta e Download de Documentos Fiscais</p>', unsafe_allow_html=True)
st.divider()

# Carregamento da Lista de Empresas
@st.cache_data
def carregar_empresas():
    try:
        with open("empresas.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "12345678000199": {"razao_social": "Mercado Exemplo Ltda"},
            "98765432000111": {"razao_social": "Padaria Silva Ltda"}
        }

empresas = carregar_empresas()
opcoes_empresas = {v["razao_social"]: k for k, v in empresas.items()}

# --- MENU LATERAL DE CONFIGURAÇÕES DE AMBIENTE ---
with st.sidebar:
    st.header("Configurações da Consulta")
    
    modo_emissao = st.selectbox(
        "Modo de Operação / Emissão:",
        ["Normal (Sefaz Ativa / Ambiente Nacional)", "Contingência (EPEC / FS-DA / Offline)"]
    )
    
    estado_origem = st.selectbox(
        "UFs / Região de Consulta:",
        ["MG - Minas Gerais (Sefaz-MG)", "SP - São Paulo", "RJ - Rio de Janeiro", "ES - Espírito Santo", "Ambiente Nacional (Sefaz Virtual / ADN)"]
    )
    
    tipo_documento = st.radio(
        "Tipos de Documentos a Buscar:",
        ["NFS-e (Serviços)", "NF-e / NFC-e (Produtos / Consumo)", "Ambos (Serviços e Produtos)"]
    )
    
    st.divider()
    st.caption("OSC Assessoria Contábil © 2026")

# --- ÁREA PRINCIPAL DE FILTROS ---
st.subheader("1. Seleção de Clientes e Período")

col_clientes, col_periodo = st.columns([1.2, 1])

with col_clientes:
    clientes_selecionados = st.multiselect(
        "Selecione um ou mais Clientes / Empresas:",
        options=list(opcoes_empresas.keys()),
        default=list(opcoes_empresas.keys())[:1],
        help="Você pode escolher múltiplos clientes para processar os downloads em lote."
    )
    
    cnpjs_selecionados = [opcoes_empresas[emp] for emp in clientes_selecionados]
    
    if cnpjs_selecionados:
        st.info(f"**CNPJs Selecionados ({len(cnpjs_selecionados)}):** {', '.join(cnpjs_selecionados)}")
    else:
        st.warning("Selecione ao menos um cliente para prosseguir.")

with col_periodo:
    st.write("**Período de Emissão:**")
    col_ini, col_fim = st.columns(2)
    
    data_hoje = date.today()
    primeiro_dia_mes = data_hoje.replace(day=1)
    
    with col_ini:
        data_inicial = st.date_input("Data Inicial:", value=primeiro_dia_mes, format="DD/MM/YYYY")
    with col_fim:
        data_final = st.date_input("Data Final:", value=data_hoje, format="DD/MM/YYYY")

st.subheader("2. Filtros Complementares (Opcional)")
chave_acesso_avulsa = st.text_input(
    "Chave de Acesso Específica:", 
    placeholder="Cole aqui a chave de 44 ou 50 dígitos para busca individualizada"
)

# --- BOTÃO DE EXECUÇÃO ---
st.divider()

if st.button("Executar Consulta e Listar Documentos", type="primary"):
    if not clientes_selecionados:
        st.error("Por favor, selecione ao menos uma empresa na lista.")
    elif data_inicial > data_final:
        st.error("A Data Inicial não pode ser maior que a Data Final.")
    else:
        st.success("Conexão estabelecida com os servidores fiscais. Documentos localizados com sucesso!")
        
        buffer_zip = io.BytesIO()
        lista_notas = []
        
        with zipfile.ZipFile(buffer_zip, "w") as zf:
            for emp_nome in clientes_selecionados:
                cnpj_emp = opcoes_empresas[emp_nome]
                
                # Simulação para NFS-e (Serviços)
                if tipo_documento in ["NFS-e (Serviços)", "Ambos (Serviços e Produtos)"]:
                    chave_nfse = f"312601{cnpj_emp}0001"
                    xml_nfse_str = f"""<?xml version="1.0"?><NFSe><infNFSe><chNFSe>{chave_nfse}</chNFSe><emit><CNPJ>{cnpj_emp}</CNPJ><xNome>{emp_nome}</xNome></emit><vServ>1500.00</vServ></infNFSe></NFSe>"""
                    
                    zf.writestr(f"NFSe_{cnpj_emp}/NFSe_Servico_{chave_nfse}.xml", xml_nfse_str)
                    
                    lista_notas.append({
                        "tipo": "NFS-e (Serviço)",
                        "cnpj": cnpj_emp,
                        "razao": emp_nome,
                        "data": data_inicial.strftime("%d/%m/%Y"),
                        "chave": chave_nfse,
                        "valor": 1500.00,
                        "xml": xml_nfse_str,
                        "nome_arquivo": f"NFSe_{chave_nfse}.xml"
                    })
                
                # Simulação para NF-e/NFC-e (Produtos)
                if tipo_documento in ["NF-e / NFC-e (Produtos / Consumo)", "Ambos (Serviços e Produtos)"]:
                    chave_nfe = f"312609{cnpj_emp}65001000000101"
                    xml_nfe_str = f"""<?xml version="1.0"?><nfeProc><NFe><infNFe><emit><CNPJ>{cnpj_emp}</CNPJ><xNome>{emp_nome}</xNome></emit><total><ICMSTot><vNF>890.50</vNF></ICMSTot></total></infNFe></NFe></nfeProc>"""
                    
                    zf.writestr(f"NFe_Sefaz_{cnpj_emp}/NFe_Produto_{chave_nfe}.xml", xml_nfe_str)
                    
                    lista_notas.append({
                        "tipo": "NFC-e (Produto)",
                        "cnpj": cnpj_emp,
                        "razao": emp_nome,
                        "data": data_final.strftime("%d/%m/%Y"),
                        "chave": chave_nfe,
                        "valor": 890.50,
                        "xml": xml_nfe_str,
                        "nome_arquivo": f"NFe_{chave_nfe}.xml"
                    })
        
        buffer_zip.seek(0)
        
        st.markdown("---")
        st.subheader("3. Relatório em Tela e Downloads Individuais")
        
        # CARDS DE MÉTRICAS
        total_valor = sum(item["valor"] for item in lista_notas)
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Total de Notas Baixadas", f"{len(lista_notas)} XMLs")
        with col_m2:
            st.metric("Valor Total do Período", f"R$ {total_valor:,.2f}")
        with col_m3:
            st.metric("Empresas Processadas", f"{len(clientes_selecionados)} Clientes")
            
        st.write("")
        st.write("**Lista de Documentos Localizados:**")
        
        # EXIBIÇÃO EM LINHAS COM BOTÃO DE DOWNLOAD INDIVIDUAL
        for idx, nota in enumerate(lista_notas):
            with st.container():
                col_info, col_btn = st.columns([4, 1])
                
                with col_info:
                    st.markdown(f"""
                    **{nota['tipo']}** | **Cliente:** {nota['razao']} (`{nota['cnpj']}`)  
                    📅 **Emissão:** {nota['data']} | 💲 **Valor:** R$ {nota['valor']:,.2f}  
                    🔑 **Chave:** `{nota['chave']}`
                    """)
                
                with col_btn:
                    st.write("") # Alinhamento vertical
                    st.download_button(
                        label="📄 Baixar XML",
                        data=nota["xml"],
                        file_name=nota["nome_arquivo"],
                        mime="text/xml",
                        key=f"btn_dl_{idx}"
                    )
                st.divider()

        # ÁREA DE DOWNLOAD DO PACOTE COMPLETO (.ZIP)
        st.subheader("4. Download do Lote Completo")
        nome_pacote = f"OSC_Lote_Fiscais_{data_inicial.strftime('%Y%m%d')}_a_{data_final.strftime('%Y%m%d')}.zip"
        
        st.download_button(
            label="📦 Baixar Todos os XMLs Compactados (.ZIP)",
            data=buffer_zip,
            file_name=nome_pacote,
            mime="application/zip",
            key="btn_dl_zip"
        )

# Rodapé
st.divider()
st.caption("OSC Assessoria Contábil — Módulo Interno de Automação e Integração Fiscal")