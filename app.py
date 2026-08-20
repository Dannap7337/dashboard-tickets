import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de Tickets", layout="wide")
st.title("📊 Panel de Control y Métricas de Tickets")

# --- 1. Carga y limpieza de datos ---
@st.cache_data(ttl=60)  # Recarga si actualizas el archivo en GitHub
def load_data(Book1.xlsx):
    df = pd.read_excel(Book1.xlsx)
    
    # Limpieza de nombres de columnas (elimina espacios en blanco)
    df.columns = df.columns.str.strip().str.upper()
    
    # Conversión de fechas
    df['INICIO'] = pd.to_datetime(df['INICIO'], errors='coerce')
    df['FIN'] = pd.to_datetime(df['FIN'], errors='coerce')
    
    # Normalización de strings para comparaciones seguras
    df['TECNICO'] = df['TECNICO'].astype(str).str.strip().str.capitalize()
    df['FALLA'] = df['FALLA'].astype(str).str.strip()
    df['USUARIO'] = df['USUARIO'].astype(str).str.strip()
    
    # Si agregaste la columna 'FUERA_DE_MES', la normalizamos
    if 'FUERA_DE_MES' in df.columns:
        df['FUERA_DE_MES'] = df['FUERA_DE_MES'].astype(str).str.strip().str.upper()
    else:
        df['FUERA_DE_MES'] = 'NO'
        
    return df

# Cargar el archivo directamente desde tu repositorio
EXCEL_PATH = "tickets.xlsx"  # Ajusta la ruta a tu archivo
df = load_data(EXCEL_PATH)

# --- 2. Lista de usuarios especiales SSC ---
USUARIOS_SSC = [
    "ANA SOFIA JARA HERNANDEZ",
    "MARIEL ARANZA ESPAÑA AGUILAR",
    "MONSERRAT MARTINEZ CORDERO",
    "TOMAS MAGNO PEREZ LORANCA",
    "PAMELA JAZMIN SANCHEZ DIAZ"
]

# --- 3. Métricas y Gráficas ---

col1, col2 = st.columns(2)

# GRÁFICA 1: Tickets no levantados en el mes
with col1:
    st.subheader("📌 Tickets No Levantados en el Mes")
    df_no_mes = df[df['FUERA_DE_MES'].isin(['SI', '1', 'TRUE'])]
    
    if not df_no_mes.empty:
        fig1 = px.bar(
            df_no_mes,
            x="N° TICKET",
            y="HRS",
            color="TECNICO",
            title=f"Tickets Extemporáneos Registrados ({len(df_no_mes)})",
            hover_data=["USUARIO", "FALLA"],
            text_auto=True
        )
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No se encontraron tickets marcados como fuera de mes.")

# GRÁFICA 2: Cumplimiento de Agenda Diaria (Día 1 a la fecha)
with col2:
    st.subheader("📅 Envío de Agenda / Actividad por Día")
    df_dias = df.dropna(subset=['FIN']).copy()
    df_dias['DIA'] = df_dias['FIN'].dt.date
    
    resumen_dias = df_dias.groupby('DIA').size().reset_index(name='TOTAL_TICKETS')
    
    fig2 = px.line(
        resumen_dias,
        x="DIA",
        y="TOTAL_TICKETS",
        markers=True,
        title="Tickets Cerrados por Día",
        labels={"DIA": "Fecha", "TOTAL_TICKETS": "Tickets Procesados"}
    )
    st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

# GRÁFICA 3: Tickets de Nivel 2 (Hector)
with col3:
    st.subheader("⚙️ Tickets Nivel 2 (Hector)")
    df_n2 = df[df['TECNICO'].str.upper() == 'HECTOR']
    
    if not df_n2.empty:
        fig3 = px.pie(
            df_n2,
            names="FALLA",
            values="HRS",
            title=f"Distribución de Horas N2 ({len(df_n2)} tickets)",
            hole=0.4
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No hay tickets asignados a Hector.")

# GRÁFICA 4: Tickets SSC (Filtro por Falla o Usuario)
with col4:
    st.subheader("🏢 Tickets SSC")
    condicion_falla = df['FALLA'].str.contains("SSC", case=False, na=False)
    condicion_usuario = df['USUARIO'].str.upper().isin([u.upper() for u in USUARIOS_SSC])
    
    df_ssc = df[condicion_falla | condicion_usuario]
    
    if not df_ssc.empty:
        fig4 = px.bar(
            df_ssc,
            x="USUARIO",
            y="HRS",
            color="FALLA",
            title=f"Total Horas SSC ({len(df_ssc)} tickets)",
            barmode="stack"
        )
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No se registraron tickets del área SSC.")
