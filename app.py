import streamlit as st
import google.generativeai as genai
from PIL import Image
import re

# Configuração da página do App
st.set_page_config(page_title="IA Diet Contador - Foto", page_icon="📸", layout="centered")

st.title("📸 Detector de Calorias por Foto")
st.write("Foco: **Emagrecimento e Déficit Calórico**")

# Configuração da API do Gemini na barra lateral
st.sidebar.header("⚙️ Configuração")
api_key = st.sidebar.text_input("Insira sua Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.warning("⚠️ Por favor, insira sua API Key do Gemini na barra lateral para ativar o reconhecimento por foto.")

# Inicializar o histórico de calorias do dia
if 'total_calorias_dia' not in st.session_state:
    st.session_state.total_calorias_dia = 0.0
if 'historico_refeicoes' not in st.session_state:
    st.session_state.historico_refeicoes = []

# Meta padrão para emagrecimento
META_EMAGRECIMENTO = 1600 

# Interface de Upload / Câmera
st.header("🍽️ Analisar Prato / Alimento")
opcao_envio = st.radio("Como deseja enviar a foto?", ("Tirar Foto (Câmera)", "Carregar Imagem da Galeria"))

imagem = None
if opcao_envio == "Tirar Foto (Câmera)":
    foto_capturada = st.camera_input("Tire a foto do seu prato")
    if foto_capturada:
        imagem = Image.open(foto_capturada)
else:
    arquivo_upload = st.file_uploader("Escolha uma imagem do alimento...", type=["jpg", "jpeg", "png"])
    if arquivo_upload:
        imagem = Image.open(arquivo_upload)

# Processamento da Imagem pela IA
if imagem is not None:
    st.image(imagem, caption="Sua Refeição", use_container_width=True)
    
    botao_analisar = st.button("🔍 Identificar Alimentos e Calcular Calorias")
    
    if botao_analisar:
        if not api_key:
            st.error("Você precisa colar sua API Key na barra lateral primeiro!")
        else:
            with st.spinner("A IA está analisando seu prato..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = """
                    Analise esta imagem de comida com foco estrito em uma dieta de emagrecimento.
                    1. Identifique todos os alimentos presentes.
                    2. Estime a quantidade aproximada de cada um (em gramas ou unidades).
                    3. Calcule as calorias de cada item e forneça o TOTAL GERAL DO PRATO.
                    4. Dê um breve feedback se este prato é adequado para o objetivo de emagrecimento (ex: se tem boa quantidade de proteína, fibras, ou se tem excesso de gordura/carboidrato refinado).
                    
                    OBRIGATÓRIO: No final da sua resposta, escreva exatamente a tag [TOTAL_KCAL: X] onde X é apenas o número inteiro do total de calorias calculadas para o prato. Exemplo: [TOTAL_KCAL: 450]
                    """
                    
                    response = model.generate_content([prompt, imagem])
                    texto_resposta = response.text
                    
                    st.subheader("📊 Análise da IA:")
                    st.write(texto_resposta)
                    
                    match = re.search(r"\[TOTAL_KCAL:\s*(\d+)\]", texto_resposta)
                    if match:
                        calorias_refeicao = int(match.group(1))
                        st.session_state.total_calorias_dia += calorias_refeicao
                        st.session_state.historico_refeicoes.append(f"Refeição identificada por foto: +{calorias_refeicao} kcal")
                        st.success(f"✔️ {calorias_refeicao} kcal adicionadas ao seu dia!")
                    else:
                        st.warning("Não consegui extrair o valor exato para a soma automática, mas o detalhamento está no texto acima.")
                        
                except Exception as e:
                    st.error(f"Erro ao processar imagem: {e}")

st.markdown("---")

# Painel de Controle de Emagrecimento do Dia
st.header("📉 Seu Painel de Emagrecimento")

col1, col2 = st.columns(2)
with col1:
    st.metric(label="🔥 Consumido Hoje", value=f"{st.session_state.total_calorias_dia:.0f} kcal")
with col2:
    restante = META_EMAGRECIMENTO - st.session_state.total_calorias_dia
    st.metric(label="🎯 Saldo Restante para Emagrecer", value=f"{restante:.0f} kcal")

progresso = min(st.session_state.total_calorias_dia / META_EMAGRECIMENTO, 1.0)
st.progress(progresso)

if st.session_state.historico_refeicoes:
    st.subheader("📋 Registro de Hoje:")
    for item in st.session_state.historico_refeicoes:
        st.write(item)

if st.button("🔄 Reiniciar o Dia"):
    st.session_state.total_calorias_dia = 0.0
    st.session_state.historico_refeicoes = []
    st.rerun()
