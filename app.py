from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard de Tickets - Agosto", layout="wide")
st.title("📊 Panel de Métricas Operativas")

# --- Carga y limpieza de datos (Agosto) ---
@st.cache_data(ttl=60)
def load_data(file_path):
    df = pd.read_excel(file_path)
    df.columns = df.columns.astype(str).str.strip().str.upper()

    for col in ['TECNICO', 'FALLA', 'USUARIO']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()

    if 'TECNICO' in df.columns:
        df['TECNICO'] = df['TECNICO'].str.capitalize()

    return df

EXCEL_PATH = 'Book1.xlsx'  # Ajusta al nombre de tu archivo de agosto
try:
    df = load_data(EXCEL_PATH)
except Exception:
    df = pd.DataFrame(columns=['TECNICO', 'FIN'])

# Grid 2x2 para las 4 visualizaciones
col_row1_1, col_row1_2 = st.columns(2)
col_row2_1, col_row2_2 = st.columns(2)

# =========================================================
# 1. Levantamiento de tickets (Sunburst jerárquico de 3 fases)
# =========================================================
with col_row1_1:
    st.subheader("📋 1. Levantamiento de Tickets (Semanal)")

    data_levantamiento = {
        "Día": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
        "Técnico": ["Juan Carlos"] * 5,
        "1. Revisión Correo": [1, 1, 1, 1, 1],
        "2. Evidencia Inicial": [1, 1, 1, 1, 1],
        "3. Evidencia Final": [1, 1, 1, 1, None]
    }
    df_act = pd.DataFrame(data_levantamiento)
    procesos = ["1. Revisión Correo", "2. Evidencia Inicial", "3. Evidencia Final"]

    # Estructura base: Raíz (Centro)
    ids = ["RAIZ"]
    labels = ["Levantamiento"]
    parents = [""]
    values = [len(df_act) * len(procesos)]
    colors = ["#2c3e50"]

    color_estado_map = {
        "Completado": "#27ae60",
        "Pendiente": "#f39c12",
        "No Cumplido": "#e74c3c"
    }

    # Nivel 1: Procesos | Nivel 2: Estatus por cada proceso
    for proc in procesos:
        proc_id = f"PROC_{proc}"
        serie = df_act[proc]
        
        # Conteo por estado en cada proceso
        n_comp = int(serie.eq(1).sum())
        n_pend = int(serie.isna().sum())
        n_fall = int(serie.eq(0).sum())

        # Nodo de proceso intermedio
        ids.append(proc_id)
        labels.append(proc)
        parents.append("RAIZ")
        values.append(len(serie))
        colors.append("#34495e")

        # Hojas exteriores de estados
        if n_comp > 0:
            ids.append(f"{proc_id}_COMP")
            labels.append("Completado")
            parents.append(proc_id)
            values.append(n_comp)
            colors.append(color_estado_map["Completado"])

        if n_pend > 0:
            ids.append(f"{proc_id}_PEND")
            labels.append("Pendiente")
            parents.append(proc_id)
            values.append(n_pend)
            colors.append(color_estado_map["Pendiente"])

        if n_fall > 0:
            ids.append(f"{proc_id}_FALL")
            labels.append("No Cumplido")
            parents.append(proc_id)
            values.append(n_fall)
            colors.append(color_estado_map["No Cumplido"])

    fig1 = go.Figure(go.Sunburst(
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(colors=colors),
        textinfo="label+value+percent parent"
    ))
    fig1.update_layout(margin=dict(t=10, l=10, r=10, b=10))
    st.plotly_chart(fig1, use_container_width=True)
# =========================================================
# 2. Envío de agenda (Semanal simulado: 3 estados)
# =========================================================
with col_row1_2:
    st.subheader("📅 2. Envío de Agenda (Semanal)")

    # Simulación de estados para los 5 días hábiles
    data_agenda_sem = {
        "Día": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
        "Estado": ["Se envió", "Se envió", "Se envió", "Se envió", "Se envió"]
    #"Sin agenda física" , "Falló" Agregar en caso de fallos
    }
    df_agenda_sem = pd.DataFrame(data_agenda_sem)
    resumen_agenda = df_agenda_sem["Estado"].value_counts().reset_index()
    resumen_agenda.columns = ["Estado", "Días"]

    fig2 = px.pie(
        resumen_agenda,
        names="Estado",
        values="Días",
        hole=0.45,
        color="Estado",
        color_discrete_map={
            "Se envió": "#27ae60",
            "Sin agenda física": "#f39c12",
            "Falló": "#e74c3c"
        }
    )
    fig2.update_traces(textinfo="label+value+percent")
    fig2.update_layout(margin=dict(t=10, l=10, r=10, b=10))
    st.plotly_chart(fig2, use_container_width=True)

# =========================================================
# 3. Gráfico de Respuesta y Folios Involucrados
# =========================================================
with col_row2_1:
    st.subheader("⏱️ 3. Tiempo de Respuesta a Correos")

    # Datos de respuesta (Recibido, Contestado, Días Laborales)
    data_respuesta = [
        {"dias": 2}, {"dias": 2}, {"dias": 1}, {"dias": 1}, {"dias": 2},
        {"dias": 1}, {"dias": 1}, {"dias": 1}, {"dias": 2}, {"dias": 1},
        {"dias": 2}, {"dias": 1}, {"dias": 3}, {"dias": 1}, {"dias": 1},
        {"dias": 1}, {"dias": 1}, {"dias": 1}, {"dias": 1}, {"dias": 1},
        {"dias": 1}, {"dias": 1}, {"dias": 1}, {"dias": 1}, {"dias": 1},
        {"dias": 1}, {"dias": 1}, {"dias": 1}, {"dias": 1}
    ]
    df_resp = pd.DataFrame(data_respuesta)

    # Mapeo descriptivo de los días
    def categorizar_tiempo(d):
        if d == 1:
            return "Mismo día / 24 hrs (1 día)"
        elif d == 2:
            return "Atención en 2 días"
        else:
            return f"Atención en {d} días"

    df_resp["Tiempo de Atención"] = df_resp["dias"].apply(categorizar_tiempo)
    conteo_tiempos = df_resp["Tiempo de Atención"].value_counts().reset_index()
    conteo_tiempos.columns = ["Tiempo de Atención", "Correos"]

    # Folios involucrados con formato SMART.XXXXXX
    raw_tickets = [225944, 226114, 226162, 226219, 226274, 226358, 225807]
    df_tickets_inv = pd.DataFrame({
        "N° Ticket": [f"SMART.{t}" for t in raw_tickets]
    })

    # Sub-columnas internas: Gráfica (65%) | Tabla (35%)
    subcol_grafico, subcol_tabla = st.columns([0.65, 0.35])

    with subcol_grafico:
        fig_resp = px.pie(
            conteo_tiempos,
            names="Tiempo de Atención",
            values="Correos",
            hole=0.45,
            color="Tiempo de Atención",
            color_discrete_map={
                "Mismo día / 24 hrs (1 día)": "#27ae60",
                "Atención en 2 días": "#f39c12",
                "Atención en 3 días": "#e74c3c"
            }
        )
        fig_resp.update_traces(textinfo="percent+value")
        fig_resp.update_layout(
            margin=dict(t=10, l=10, r=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_resp, use_container_width=True)

    with subcol_tabla:
        st.caption("**Tickets Involucrados**")
        st.dataframe(df_tickets_inv, use_container_width=True, hide_index=True)

        
# =========================================================
# 4. Tickets Segundo Nivel vs Equipo
# =========================================================
with col_row2_2:
    st.subheader("⚙️ 4. Tickets Segundo Nivel vs Equipo")

    if not df.empty and 'TECNICO' in df.columns:
        total_equipo = len(df[df['TECNICO'].str.upper() != 'HECTOR'])
        df_hector = df[df['TECNICO'].str.upper() == 'HECTOR'].copy()

        df_hector['ESTADO_HECTOR'] = df_hector['FIN'].apply(
            lambda x: 'Cerrado' if pd.notnull(x) and str(x).strip() not in ['', 'NaT'] else 'Abierto'
        )

        total_n2_cerrados = len(df_hector[df_hector['ESTADO_HECTOR'] == 'Cerrado'])
        total_n2_abiertos = len(df_hector[df_hector['ESTADO_HECTOR'] == 'Abierto'])
        total_segundo_nivel = total_n2_cerrados + total_n2_abiertos

        fig4 = go.Figure(go.Sunburst(
            labels=["Equipo General", "Segundo Nivel", "Cerrados (N2)", "Abiertos (N2)"],
            parents=["", "", "Segundo Nivel", "Segundo Nivel"],
            values=[total_equipo, total_segundo_nivel, total_n2_cerrados, total_n2_abiertos],
            branchvalues="total",
            marker=dict(colors=["#bdc3c7", "#f39c12", "#27ae60", "#e74c3c"]),
            textinfo="label+value+percent parent"
        ))
        fig4.update_layout(margin=dict(t=10, l=10, r=10, b=10))
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.warning("Sin datos disponibles para calcular Segundo Nivel.")
