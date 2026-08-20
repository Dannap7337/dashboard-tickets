from pathlib import Path
from datetime import date
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard de Tickets", layout="wide")
st.title("📊 Panel de Control y Métricas de Tickets")

# --- 1. Carga y limpieza de datos ---

# --- 1. Carga y limpieza de datos ---
@st.cache_data(ttl=60)
def load_data(file_path):
    df = pd.read_excel(file_path)
    
    # Estandarizar nombres de columnas
    df.columns = df.columns.astype(str).str.strip().str.upper()
    
    # Conversión segura de strings
    df['TECNICO'] = df['TECNICO'].fillna('').astype(str).str.strip().str.capitalize()
    df['FALLA'] = df['FALLA'].fillna('').astype(str).str.strip()
    df['USUARIO'] = df['USUARIO'].fillna('').astype(str).str.strip()
    
    # Estandarización 100% segura de ESTADO
    if 'ESTADO' in df.columns:
        df['ESTADO_LIMPIO'] = df['ESTADO'].fillna('').astype(str).apply(
            lambda x: 'Abierto' if 'ABIERTO' in str(x).upper() else 'Cerrado'
        )
    else:
        df['ESTADO_LIMPIO'] = df['FIN'].apply(lambda x: 'Cerrado' if pd.notnull(x) else 'Abierto')

    # Limpieza segura de la columna FUERA DE MES
    col_fuera_mes = [c for c in df.columns if 'FUERA' in c and 'MES' in c]
    if col_fuera_mes:
        col = col_fuera_mes[0]
        df['ES_FUERA_MES'] = df[col].fillna('').astype(str).str.strip().str.upper().isin(['1', '1.0', 'SI', 'TRUE', 'S'])
    else:
        df['ES_FUERA_MES'] = False
        
    return df

BASE_DIR = Path(__file__).resolve().parent
EXCEL_PATH = 'Book1.xlsx'
df = load_data(EXCEL_PATH)

# --- Lista de usuarios SSC ---
USUARIOS_SSC = [
    "CASTILLO CONTRERAS, LAURA",
    "HUERTA NIETO, OSVALDO",
    "ALEJANDRO PÉREZ SALAZAR",
    "Flores Rosas, Israel",
    "SADIE VIVEROS"
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
    st.subheader("📌 2. Tickets Fuera de Tiempo")
    df_mes = df.copy()
    df_mes['TIPO_MES'] = df_mes['ES_FUERA_MES'].apply(
        lambda x: 'Fuera de Tiempo (No Levantado)' if x else 'Mes Regular'
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
# 3. Tickets Segundo Nivel vs Equipo (Sunburst 2 aros)
# ==========================================
with row2_col1:
    st.subheader("⚙️ 3. Tickets Segundo Nivel vs Equipo")
    
    # 1. Total del equipo general (no Hector)
    total_equipo = len(df[df['TECNICO'].str.upper() != 'HECTOR'])
    
    # 2. Tickets de Hector (Segundo Nivel)
    df_hector = df[df['TECNICO'].str.upper() == 'HECTOR'].copy()
    
    # Regla: Si FIN es nulo/vacío -> Abierto, si tiene fecha -> Cerrado
    df_hector['ESTADO_HECTOR'] = df_hector['FIN'].apply(
        lambda x: 'Cerrado' if pd.notnull(x) and str(x).strip() != '' and str(x).strip() != 'NaT' else 'Abierto'
    )
    
    total_n2_cerrados = len(df_hector[df_hector['ESTADO_HECTOR'] == 'Cerrado'])
    total_n2_abiertos = len(df_hector[df_hector['ESTADO_HECTOR'] == 'Abierto'])
    total_segundo_nivel = total_n2_cerrados + total_n2_abiertos

    # Construcción directa de la jerarquía de nodos
    # Anillo 1 (Centro): 'Equipo General' y 'Segundo Nivel'
    # Anillo 2 (Exterior): Solo hijos de 'Segundo Nivel' ('Cerrados' y 'Abiertos')
    labels = ["Equipo General", "Segundo Nivel", "Cerrados (N2)", "Abiertos (N2)"]
    parents = ["", "", "Segundo Nivel", "Segundo Nivel"]
    values = [total_equipo, total_segundo_nivel, total_n2_cerrados, total_n2_abiertos]
    
    # Paleta de colores personalizada
    colors = ["#bdc3c7", "#f39c12", "#27ae60", "#e74c3c"]

    fig3 = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(colors=colors),
        textinfo="label+value+percent parent"
    ))
    
    fig3.update_layout(margin=dict(t=10, l=10, r=10, b=10))
    st.plotly_chart(fig3, use_container_width=True)
    
# ==========================================
# 4. Cumplimiento Agenda (1 de Agosto a la fecha)
# ==========================================
# ==========================================
# 4. Cumplimiento Agenda (1 de Agosto a la fecha)
# ==========================================
with row2_col2:
    st.subheader("📅 4. Cumplimiento de Agenda")
    
    # Cálculo automático de días transcurridos desde el 1 de agosto hasta hoy
    fecha_inicio = date(2026, 8, 1)
    hoy = date.today()
    total_dias_transcurridos = max(1, (hoy - fecha_inicio).days + 1)
    
    # Variable interna (cámbiala directamente aquí en el código cuando lo requieras)
    dias_no_enviados = 0  
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

# ==========================================
# 5. Vista General de Datos
# ==========================================
st.markdown("---")
st.subheader("📋 Detalle de Tickets")

# 1. Crear una copia y calcular la clasificación SSC
df_tabla = df.copy()

df_tabla['CLASIFICACIÓN SSC'] = df_tabla.apply(
    lambda r: 'Tickets SSC' if (
        ('SSC' in str(r.get('FALLA', '')).upper()) or 
        (str(r.get('USUARIO', '')).upper() in [u.upper() for u in USUARIOS_SSC])
    ) else 'Soporte General',
    axis=1
)

# 2. Identificar y descartar columnas relacionadas a 'FUERA DE MES'
cols_a_ocultar = [c for c in df_tabla.columns if ('FUERA' in c and 'MES' in c) or c == 'ES_FUERA_MES']
df_tabla = df_tabla.drop(columns=cols_a_ocultar, errors='ignore')

# 3. Mostrar la tabla con la clasificación incluida
st.dataframe(df_tabla, use_container_width=True, hide_index=True)
