import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

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
    
    # Manejo y limpieza del ESTADO
    if 'ESTADO' in df.columns:
        df['ESTADO'] = df['ESTADO'].astype(str).str.strip().str.capitalize()
    else:
        # Si la fecha FIN existe se considera Cerrado, si no, Abierto
        df['ESTADO'] = df['FIN'].apply(lambda x: 'Cerrado' if pd.notnull(x) else 'Abierto')

    # Manejo de la columna opcional FUERA_DE_MES
    if 'FUERA_DE_MES' in df.columns:
        df['FUERA_DE_MES'] = df['FUERA_DE_MES'].astype(str).str.strip().str.upper()
    else:
        df['FUERA_DE_MES'] = 'NO'
        
    return df

# Cargar el archivo directamente desde tu repositorio
EXCEL_PATH = "tickets.xlsx"  # Ajusta al nombre exacto de tu archivo Excel
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

# GRÁFICA 3: Tickets Nivel 2 - Hector (SUNBURST CHART)
with col3:
    st.subheader("⚙️ Nivel 2 - Hector (Sunburst)")
    df_n2 = df[df['TECNICO'].str.upper() == 'HECTOR'].copy()
    
    if not df_n2.empty:
        # Creamos una etiqueta clara para el nivel raíz
        df_n2['SOPORTE'] = 'Soporte Nivel 2'
        
        # Gráfica Sunburst: Soporte N2 -> Estado (Abierto/Cerrado) -> Falla
        fig3 = px.sunburst(
            df_n2,
            path=['SOPORTE', 'ESTADO', 'FALLA'],
            values='HRS',
            title=f"Distribución de Horas N2 ({len(df_n2)} tickets)",
            color='ESTADO',
            color_discrete_map={
                'Cerrado': '#2ecc71',
                'Abierto': '#e74c3c'
            }
        )
        fig3.update_traces(textinfo="label+value+percent parent")
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
