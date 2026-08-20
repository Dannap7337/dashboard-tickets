from pathlib import Path
from datetime import date
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard de Tickets", layout="wide")
st.title("📊 Panel de Control y Métricas de Tickets")

# --- 1. Carga y limpieza de datos ---
@st.cache_data(ttl=60)
def load_data(file_path):
    df = pd.read_excel(file_path)
    
    # Estandarizar nombres de columnas eliminando espacios accidentales
    df.columns = df.columns.str.strip().str.upper()
    
    # Conversión de tipos
    df['TECNICO'] = df['TECNICO'].astype(str).str.strip().str.capitalize()
    df['FALLA'] = df['FALLA'].astype(str).str.strip()
    df['USUARIO'] = df['USUARIO'].astype(str).str.strip()
    
    # Estandarización de ESTADO (Abierto / Cerrado)
    if 'ESTADO' in df.columns:
        df['ESTADO_LIMPIO'] = df['ESTADO'].astype(str).apply(
            lambda x: 'Abierto' if 'ABIERTO' in x.upper() else 'Cerrado'
        )
    else:
        df['ESTADO_LIMPIO'] = df['FIN'].apply(lambda x: 'Cerrado' if pd.notnull(x) else 'Abierto')

    # Limpieza de la columna FUERA DE MES
    col_fuera_mes = [c for c in df.columns if 'FUERA' in c and 'MES' in c]
    if col_fuera_mes:
        col = col_fuera_mes[0]
        df['ES_FUERA_MES'] = df[col].astype(str).str.strip().isin(['1', '1.0', 'SI', 'TRUE', 'S'])
    else:
        df['ES_FUERA_MES'] = False
        
    return df

BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = "Book1.xlsx"  # Tu archivo Excel
df = load_data(EXCEL_PATH)

# --- Lista editable de usuarios SSC ---
USUARIOS_SSC = [
    "ANA SOFIA JARA HERNANDEZ",
    "MARIEL ARANZA ESPAÑA AGUILAR",
    "MONSERRAT MARTINEZ CORDERO",
    "TOMAS MAGNO PEREZ LORANCA",
    "PAMELA JAZMIN SANCHEZ DIAZ"
]

# Grid 2x2 para las 4 gráficas
row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

# ==========================================
# 1. SSC vs Soporte (Pie Chart)
# ==========================================
with row1_col1:
    st.subheader("🏢 1. Clasificación: SSC vs Soporte General")
    cond_falla = df['FALLA'].str.contains("SSC", case=False, na=False)
    cond_user = df['USUARIO'].str.upper().isin([u.upper() for u in USUARIOS_SSC])
    
    df_tipo = df.copy()
    df_tipo['CATEGORIA'] = df_tipo.apply(
        lambda r: 'Tickets SSC' if (('SSC' in str(r['FALLA']).upper()) or (str(r['USUARIO']).upper() in [u.upper() for u in USUARIOS_SSC])) else 'Soporte General',
        axis=1
    )
    
    resumen_ssc = df_tipo['CATEGORIA'].value_counts().reset_index()
    resumen_ssc.columns = ['Categoría', 'Cantidad']
    
    fig1 = px.pie(
        resumen_ssc,
        names='Categoría',
        values='Cantidad',
        hole=0.4,
        color='Categoría',
        color_discrete_map={'Tickets SSC': '#3498db', 'Soporte General': '#95a5a6'}
    )
    fig1.update_traces(textinfo='percent+value+label')
    st.plotly_chart(fig1, use_container_width=True)

# ==========================================
# 2. Tickets Fuera de Mes (Pie Chart)
# ==========================================
with row1_col2:
    st.subheader("📌 2. Tickets Fuera de Mes")
    df_mes = df.copy()
    df_mes['TIPO_MES'] = df_mes['ES_FUERA_MES'].apply(
        lambda x: 'Fuera de Mes (No Levantado)' if x else 'Mes Regular'
    )
    
    resumen_mes = df_mes['TIPO_MES'].value_counts().reset_index()
    resumen_mes.columns = ['Tipo', 'Cantidad']
    
    fig2 = px.pie(
        resumen_mes,
        names='Tipo',
        values='Cantidad',
        hole=0.4,
        color='Tipo',
        color_discrete_map={'Fuera de Mes (No Levantado)': '#e74c3c', 'Mes Regular': '#2ecc71'}
    )
    fig2.update_traces(textinfo='percent+value+label')
    st.plotly_chart(fig2, use_container_width=True)

# ==========================================
# 3. Segundo Nivel - Abiertos / Cerrados (Sunburst / Anillos)
# ==========================================
with row2_col1:
    st.subheader("⚙️ 3. Tickets Segundo Nivel vs Equipo")
    df_n2 = df.copy()
    
    # Nivel 1: 'Segundo Nivel' (Hector) vs 'Equipo' (resto)
    # Nivel 2: Para Segundo Nivel se abre en Abierto / Cerrado
    def asignar_jerarquia(row):
        if str(row['TECNICO']).upper() == 'HECTOR':
            return 'Segundo Nivel', f"N2 - {row['ESTADO_LIMPIO']}"
        else:
            return 'Equipo General', 'Equipo General'
            
    df_n2[['NIVEL_1', 'NIVEL_2']] = df_n2.apply(asignar_jerarquia, axis=1, result_type='expand')
    resumen_n2 = df_n2.groupby(['NIVEL_1', 'NIVEL_2']).size().reset_index(name='CANTIDAD')
    
    fig3 = px.sunburst(
        resumen_n2,
        path=['NIVEL_1', 'NIVEL_2'],
        values='CANTIDAD',
        color='NIVEL_1',
        color_discrete_map={'Segundo Nivel': '#f39c12', 'Equipo General': '#bdc3c7'}
    )
    fig3.update_traces(textinfo="label+value+percent parent")
    st.plotly_chart(fig3, use_container_width=True)

# ==========================================
# 4. Cumplimiento Agenda (1 de Agosto a la fecha)
# ==========================================
with row2_col2:
    st.subheader("📅 4. Cumplimiento de Agenda")
    
    # Cálculo de días desde el 1 de agosto hasta hoy
    fecha_inicio = date(2026, 8, 1)
    hoy = date.today()
    total_dias_transcurridos = max(1, (hoy - fecha_inicio).days + 1)
    
    # Selector rápido para los días que no se mandó a tiempo
    dias_no_enviados = st.number_input("Días que NO se mandó a tiempo:", min_value=0, max_value=total_dias_transcurridos, value=0, step=1)
    dias_a_tiempo = max(0, total_dias_transcurridos - dias_no_enviados)
    
    df_agenda = pd.DataFrame({
        'Estado Agenda': ['Enviada a Tiempo', 'No Enviada / Con Retraso'],
        'Días': [dias_a_tiempo, dias_no_enviados]
    })
    
    fig4 = px.pie(
        df_agenda,
        names='Estado Agenda',
        values='Días',
        hole=0.4,
        color='Estado Agenda',
        color_discrete_map={'Enviada a Tiempo': '#27ae60', 'No Enviada / Con Retraso': '#c0392b'},
        title=f"Total: {total_dias_transcurridos} días (1 Ago - Hoy)"
    )
    fig4.update_traces(textinfo='percent+value+label')
    st.plotly_chart(fig4, use_container_width=True)
