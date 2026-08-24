import re
import time
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Ranking de Aromas", layout="centered")

# Título e botão de atualização na mesma linha
col_titulo, col_botao = st.columns([0.7, 0.3])
with col_titulo:
  st.title("🌺 Ranking dos Aromas")
with col_botao:
  # Botão manual para forçar a busca de novas respostas
  if st.button("🔄 Atualizar"):
    st.cache_data.clear()
    st.rerun()

# Link da sua planilha do Google Sheets
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/16SOoKvVjdB3gWADHAH1zKLSrwqALz3MN66e10s-c_kA/edit?usp=sharing"

try:
  sheet_id = URL_PLANILHA.split("/d/")[1].split("/")[0]
  tsv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=tsv"
except Exception:
  st.error("Cole um link válido do Google Sheets na variável URL_PLANILHA.")
  st.stop()


# Cache de apenas 1 segundo para buscar os dados em tempo real
@st.cache_data(ttl=1)
def carregar_dados():
  # O parâmetro 'nocache' com timestamp impede o Google de entregar dados antigos do cache dele
  timestamp = int(time.time())
  url_sem_cache = f"{tsv_url}&nocache={timestamp}"
  return pd.read_csv(url_sem_cache, sep="\t", on_bad_lines="skip")


try:
  df = carregar_dados()

  # Dicionário de pesos para as posições
  pesos_por_posicao = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}
  pontuacao_total = {}

  # Procura as colunas de classificação (1 a 5 Lugar)
  for col in df.columns:
    match = re.search(r"([1-5])\s*Lugar", str(col), re.IGNORECASE)

    if match:
      posicao = int(match.group(1))
      peso = pesos_por_posicao.get(posicao, 0)

      # Conta quantas vezes cada aroma apareceu na coluna
      contagem = df[col].dropna().value_counts()

      for aroma, qtd in contagem.items():
        nome_aroma = str(aroma).strip()
        if nome_aroma and nome_aroma.lower() != "nan":
          pontuacao_total[nome_aroma] = pontuacao_total.get(
              nome_aroma, 0
          ) + (qtd * peso)

  # Cria o ranking ordenado
  df_ranking = pd.DataFrame(
      list(pontuacao_total.items()), columns=["Aroma", "Pontuação Total"]
  ).sort_values(by="Pontuação Total", ascending=False)

  # EXIBIÇÃO
  if not df_ranking.empty:
    vencedor = df_ranking.iloc[0]["Aroma"]
    pontos_vencedor = df_ranking.iloc[0]["Pontuação Total"]

    st.success(
        f"🥇 **{vencedor}** é o aroma favorito até agora com"
        f" **{pontos_vencedor}** pontos!"
    )

    st.subheader("📊 Classificação Geral")
    st.dataframe(df_ranking, hide_index=True, use_container_width=True)

    st.subheader("📈 Pontuação")
    st.bar_chart(df_ranking.set_index("Aroma"))
  else:
    st.warning(
        "Nenhum dado de ranking foi encontrado. Verifique se há respostas"
        " preenchidas na planilha."
    )

except Exception as e:
  st.error(f"Erro ao processar a planilha: {e}")