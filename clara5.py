import streamlit as st
import matplotlib.pyplot as plt
import re
from docx import Document
import PyPDF2
from datetime import datetime

# Configuração inicial da página
st.set_page_config(
    page_title="Clara - Análise Jurídica de Contratos",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .header-style {
        font-size: 20px;
        font-weight: bold;
        color: #2e86de;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .risk-high {
        background-color: #ff6b6b;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .risk-medium {
        background-color: #feca57;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .risk-low {
        background-color: #1dd1a1;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .contract-summary {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #2e86de;
        margin-bottom: 20px;
    }
    .clause-card {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .footer {
        font-size: 12px;
        text-align: center;
        margin-top: 30px;
        color: #7f8c8d;
    }
</style>
""", unsafe_allow_html=True)

def analisar_clausulas(texto):
    regras = {
        # Cláusulas educacionais
        r"(não poderá cancelar|proibido cancelar|vedado rescindir).*(qualquer hipótese|mesmo em caso)": {
            "mensagem": "Proibição Total de Cancelamento",
            "explicacao": "Cláusula que impede o cancelamento em qualquer circunstância é considerada abusiva pelo CDC (Art. 51, IV).",
            "pontuacao": 15,
            "tipo": "abusiva",
            "recomendacao": "Solicite a modificação para permitir cancelamento com aviso prévio de 30 dias."
        },
        r"(renovação automática|prorrogado automaticamente).*(sem aviso|não notifica)": {
            "mensagem": "Renovação Automática sem Aviso",
            "explicacao": "Contratos devem prever aviso prévio de pelo menos 30 dias para renovação automática (Art. 9º, Lei 8.245/91).",
            "pontuacao": 10,
            "tipo": "abusiva",
            "recomendacao": "Exija cláusula que obrigue notificação com antecedência mínima de 30 dias."
        },
        r"(multa|juros).*(superior a 2%|acima de 10%|20%)": {
            "mensagem": "Multa/Juros Abusivos",
            "explicacao": "Multas superiores a 2% ao mês ou juros acima da taxa média do mercado são considerados abusivos (Súmula 54 do STJ).",
            "pontuacao": 12,
            "tipo": "abusiva",
            "recomendacao": "Negocie redução para no máximo 2% de multa e juros de 1% ao mês."
        },
        r"(não se responsabiliza|isenção de responsabilidade).*(qualquer falha|indisponibilidade)": {
            "mensagem": "Isenção Total de Responsabilidade",
            "explicacao": "Empresas não podem se eximir totalmente de responsabilidade por falhas na prestação de serviços (Art. 14, CDC).",
            "pontuacao": 15,
            "tipo": "abusiva",
            "recomendacao": "Exija redação que limite responsabilidade apenas a casos de força maior."
        },
        r"(foro|jurisdição).*(Luxemburgo|exterior|estrangeiro)": {
            "mensagem": "Foro em País Estrangeiro",
            "explicacao": "Contratos com consumidores brasileiros devem prever foro no Brasil (Art. 78, CDC).",
            "pontuacao": 15,
            "tipo": "abusiva",
            "recomendacao": "Insista em foro no local de sua residência no Brasil."
        },
        
        # Boas práticas
        r"(direito ao arrependimento|desistência|7 dias)": {
            "mensagem": "Direito ao Arrependimento",
            "explicacao": "Cláusula que respeita o direito legal de arrependimento em 7 dias (Art. 49, CDC).",
            "pontuacao": -5,
            "tipo": "favoravel",
            "recomendacao": "Mantenha esta cláusula que protege seus direitos."
        }
    }

    resultados = []
    for padrao, detalhes in regras.items():
        matches = re.finditer(padrao, texto, re.IGNORECASE)
        for match in matches:
            contexto = texto[max(0, match.start()-50):match.end()+50].replace("\n", " ")
            resultados.append({
                "padrao": padrao,
                "contexto": f"...{contexto}..." if len(contexto) > 100 else contexto,
                **detalhes
            })

    return resultados

def gerar_resumo_contrato(texto):
    # Identifica tipo de contrato
    tipo_contrato = "Contrato Genérico"
    if "EDUCACIONAIS" in texto.upper():
        tipo_contrato = "Contrato Educacional"
    elif "LOCAÇÃO" in texto.upper():
        tipo_contrato = "Contrato de Locação"
    elif "PRESTAÇÃO DE SERVIÇOS" in texto.upper():
        tipo_contrato = "Contrato de Prestação de Serviços"
    
    # Extrai partes principais
    partes = re.search(r"CONTRATANTE:(.*?)CONTRATADA:(.*?)CLÁUSULAS:", texto, re.IGNORECASE|re.DOTALL)
    contratante = partes.group(1).strip() if partes else "Não identificado"
    contratada = partes.group(2).strip() if partes else "Não identificado"
    
    # Extrai valor se existir
    valor = re.search(r"(valor total|valor do curso).*?R\$\s*([\d.,]+)", texto, re.IGNORECASE)
    valor_formatado = f"R$ {valor.group(2)}" if valor else "Não especificado"
    
    # Extrai duração se existir
    duracao = re.search(r"(duração|prazo).*?(\d+)\s*(meses|anos|dias)", texto, re.IGNORECASE)
    duracao_formatada = f"{duracao.group(2)} {duracao.group(3)}" if duracao else "Não especificada"
    
    return {
        "tipo": tipo_contrato,
        "contratante": contratante,
        "contratada": contratada,
        "valor": valor_formatado,
        "duracao": duracao_formatada,
        "resumo": f"""
        **Tipo de Contrato:** {tipo_contrato}\n
        **Contratante:** {contratante}\n
        **Contratada:** {contratada}\n
        **Valor Total:** {valor_formatado}\n
        **Duração:** {duracao_formatada}\n
        """
    }

def main():
    # Inicializa resultados como lista vazia
    resultados = []
    
    # Sidebar com informações
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/contract.png", width=80)
        st.markdown("""
        ### Sobre a Clara
        A Clara é uma ferramenta de análise preliminar de contratos que identifica cláusulas potencialmente abusivas com base no Código de Defesa do Consumidor.
        
        **Limitações:**
        - Não substitui análise jurídica profissional
        - Baseada em padrões conhecidos
        - Pode não identificar todas as nuances
        
        **Dicas:**
        - Sempre leia todo o contrato
        - Destaque pontos que não entender
        - Consulte um advogado para análise completa
        """)
        st.markdown("---")
        st.markdown(f"<div class='footer'>Versão 2.1 | {datetime.now().year} © Clara Analytics</div>", unsafe_allow_html=True)

    # Cabeçalho principal
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("⚖️ Clara - Análise Jurídica de Contratos")
        st.markdown("""
        <div class='header-style'>
        Identifique cláusulas abusivas em contratos antes de assinar. Envie seu documento e receba uma análise preliminar em segundos.
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.image("https://img.icons8.com/fluency/96/000000/law.png", width=100)

    # Upload do documento
    st.markdown("### 📤 Envie seu contrato para análise")
    uploaded_file = st.file_uploader(
        "Arraste seu arquivo (PDF, DOCX ou TXT) ou clique para selecionar",
        type=["txt", "docx", "pdf"],
        help="Formatos aceitos: .txt, .docx e .pdf",
        label_visibility="collapsed"
    )

    if uploaded_file:
        # Processamento do arquivo
        conteudo = ""
        try:
            if uploaded_file.type == "text/plain":
                conteudo = uploaded_file.read().decode("utf-8")
            elif uploaded_file.type == "application/pdf":
                reader = PyPDF2.PdfReader(uploaded_file)
                conteudo = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = Document(uploaded_file)
                conteudo = "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {str(e)}")
            return

        if conteudo:
            # Resumo do contrato
            resumo = gerar_resumo_contrato(conteudo)
            
            st.markdown("---")
            st.markdown("## 📝 Resumo do Contrato")
            with st.container():
                st.markdown(f"""
                <div class='contract-summary'>
                {resumo['resumo']}
                </div>
                """, unsafe_allow_html=True)
                
                st.caption("""
                **Legenda do Resumo:**
                - Identificamos as partes, valor e duração para ajudar na compreensão do contrato.
                - Este é apenas um resumo automático - leia o documento completo atentamente.
                """)

            # Análise das cláusulas
            resultados = analisar_clausulas(conteudo) if conteudo else []
            
            st.markdown("---")
            st.markdown("## 🔍 Análise Detalhada das Cláusulas")
            
            if resultados:
                # Calcula pontuação total
                pontuacao_total = sum(item["pontuacao"] for item in resultados if item["pontuacao"] > 0)
                clausulas_favoraveis = sum(1 for item in resultados if item["tipo"] == "favoravel")
                
                # Determina nível de risco
                if pontuacao_total >= 30:
                    risco = "<span class='risk-high'>ALTO RISCO</span>"
                    recomendacao = "⚠️ Contrato com múltiplas cláusulas abusivas. Recomendamos NÃO ASSINAR e consultar um advogado para revisão completa."
                elif pontuacao_total >= 15:
                    risco = "<span class='risk-medium'>RISCO MODERADO</span>"
                    recomendacao = "🔍 Contrato com algumas cláusulas problemáticas. Recomendamos negociar alterações antes de assinar."
                else:
                    risco = "<span class='risk-low'>BAIXO RISCO</span>"
                    recomendacao = "✅ Contrato parece razoável, mas revise cuidadosamente as observações abaixo."
                
                # Mostra resumo de risco
                col1, col2, col3 = st.columns(3)
                col1.markdown(f"**Pontuação Total de Risco**\n# {pontuacao_total} pts")
                col2.markdown(f"**Nível de Risco**\n<div style='margin-top:10px'>{risco}</div>", unsafe_allow_html=True)
                col3.markdown(f"**Cláusulas Favoráveis**\n# {clausulas_favoraveis}")
                
                st.markdown(f"""
                <div style='background-color:#f8f9fa; padding:15px; border-radius:10px; margin-top:20px'>
                <strong>📌 Recomendação:</strong> {recomendacao}
                </div>
                """, unsafe_allow_html=True)

                # Exibe cada cláusula encontrada
                st.markdown("### ⚖️ Cláusulas Identificadas")
                
                tab1, tab2 = st.tabs(["Cláusulas Problemáticas", "Cláusulas Favoráveis"])
                
                with tab1:
                    clausulas_problematicas = [item for item in resultados if item["tipo"] != "favoravel"]
                    if clausulas_problematicas:
                        for item in clausulas_problematicas:
                            st.markdown(f"""
                            <div class='clause-card' style='border-left: 5px solid {'#ff6b6b' if item["tipo"] == "abusiva" else '#feca57'};'>
                                <h4>{'🚨 ' if item["tipo"] == "abusiva" else '⚠️ '}{item["mensagem"]}</h4>
                                <p><strong>Trecho do contrato:</strong> <em>{item["contexto"]}</em></p>
                                <p><strong>Problema:</strong> {item["explicacao"]}</p>
                                <p><strong>Pontuação de risco:</strong> {item["pontuacao"]} pontos</p>
                                <p><strong>✔️ Recomendação:</strong> {item["recomendacao"]}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.success("Nenhuma cláusula problemática encontrada!")
                
                with tab2:
                    clausulas_favoraveis = [item for item in resultados if item["tipo"] == "favoravel"]
                    if clausulas_favoraveis:
                        for item in clausulas_favoraveis:
                            st.markdown(f"""
                            <div class='clause-card' style='border-left: 5px solid #1dd1a1;'>
                                <h4>✅ {item["mensagem"]}</h4>
                                <p><strong>Trecho do contrato:</strong> <em>{item["contexto"]}</em></p>
                                <p><strong>Benefício:</strong> {item["explicacao"]}</p>
                                <p><strong>Pontuação positiva:</strong> {item["pontuacao"]} pontos</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("Nenhuma cláusula especialmente favorável foi identificada.")

                # Gráfico de análise
                st.markdown("---")
                st.markdown("## 📊 Visão Geral da Análise")
                
                # Contagem de cada tipo de cláusula
                counts = {
                    "abusiva": sum(1 for item in resultados if item["tipo"] == "abusiva"),
                    "potencial": sum(1 for item in resultados if item["tipo"] == "potencial"),
                    "favoravel": sum(1 for item in resultados if item["tipo"] == "favoravel")
                }
                
                # Preparando dados para o gráfico
                labels = []
                sizes = []
                colors = []
                
                for clause_type in counts:
                    if counts[clause_type] > 0:
                        labels.append({
                            "abusiva": "Abusivas",
                            "potencial": "Problemáticas",
                            "favoravel": "Favoráveis"
                        }[clause_type])
                        sizes.append(counts[clause_type])
                        colors.append({
                            "abusiva": "#ff6b6b",
                            "potencial": "#feca57",
                            "favoravel": "#1dd1a1"
                        }[clause_type])
                
                if sizes:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    
                    # Apenas destaque se houver mais de um segmento
                    explode = [0.1 if label == "Abusivas" and counts["abusiva"] > 0 else 0 for label in labels] if len(labels) > 1 else None
                    
                    ax.pie(
                        sizes,
                        labels=labels,
                        colors=colors,
                        autopct='%1.1f%%',
                        startangle=90,
                        explode=explode,
                        shadow=True
                    )
                    ax.set_title("Distribuição de Cláusulas Identificadas", pad=20)
                    st.pyplot(fig)
                else:
                    st.warning("Não há dados suficientes para gerar o gráfico.")
                
                # Botão de download do relatório
                st.markdown("---")
                relatorio = f"""
                RELATÓRIO DE ANÁLISE DE CONTRATO - CLARA
                ========================================
                
                Data da Análise: {datetime.now().strftime("%d/%m/%Y %H:%M")}
                
                RESUMO DO CONTRATO:
                -------------------
                {resumo['resumo']}
                
                PONTUAÇÃO TOTAL: {pontuacao_total} pontos
                NÍVEL DE RISCO: {risco.replace('<span class="risk-high">', '').replace('</span>', '')}
                
                CLÁUSULAS IDENTIFICADAS:
                ------------------------
                {chr(10).join(f"- {item['mensagem']} ({item['pontuacao']} pts): {item['explicacao']}" for item in resultados)}
                
                RECOMENDAÇÃO FINAL:
                -------------------
                {recomendacao}
                
                Observação: Este relatório é gerado automaticamente e não substitui consulta jurídica profissional.
                """
                
                st.download_button(
                    label="📥 Baixar Relatório Completo (TXT)",
                    data=relatorio,
                    file_name=f"analise_contrato_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.success("""
                🎉 Nenhuma cláusula problemática foi identificada com as regras atuais!
                
                **Recomendamos ainda:**
                - Ler todo o contrato atentamente
                - Verificar se todas as promessas verbais estão no documento
                - Confirmar prazos e valores
                """)
                st.balloons()

if __name__ == "__main__":
    main()