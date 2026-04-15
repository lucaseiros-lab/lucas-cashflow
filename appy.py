import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Lucas Cash Flow", layout="wide")

# --- ESTILOS DINÁMICOS (DARK/LIGHT) ---
theme = st.sidebar.radio("Apariencia", ["Oscuro", "Claro"])
if theme == "Oscuro":
    bg, txt, chart_theme = "#0E1117", "white", "plotly_dark"
else:
    bg, txt, chart_theme = "#FFFFFF", "#31333F", "plotly_white"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg}; color: {txt}; }}
    [data-testid="stMetricValue"] {{ color: {txt} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
st.sidebar.header("📁 Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Arrastrá tu resumen aquí (CSV)", type=["csv"])

def load_data(file_source):
    try:
        df = pd.read_csv(file_source, sep=';')
        df.columns = [c.strip() for c in df.columns]
        # Limpieza de importes
        for col in ['Importe Pesos', 'Importe Dólares']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        return df
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return None

# Intentar cargar archivo subido o el default
df = None
if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    try:
        df = load_data('MVP_CashFlow_Lucas_Completo.csv')
    except:
        df = None

# --- RENDERIZADO DEL DASHBOARD ---
if df is not None:
    st.title("💸 Lucas Financial Dashboard")
    
    # Lógica de Ingresos (Honorarios)
    ingresos = 6000000.0 # Valor fijo por ahora
    
    # Lógica de Deuda vs Gasto Real
    pagos_tjt = df[df['Detalle'].str.contains('Pago tarjeta', case=False, na=False)]['Importe Pesos'].abs().sum()
    consumos_tjt = df[df['Detalle'].str.contains('Visa|Amex|Uber|Rappi|Cabify|Netflix|Spotify', case=False, na=False) & 
                      ~df['Detalle'].str.contains('Pago', case=False, na=False)]['Importe Pesos'].abs().sum()
    
    gastos_directos = df[(df['Importe Pesos'] < 0) & 
                         ~df['Detalle'].str.contains('Visa|Amex|Lucas|Pago', case=False, na=False)]['Importe Pesos'].abs().sum()
    
    disponible = ingresos - pagos_tjt - gastos_directos

    # KPIs Principales (Vista iPhone)
    c1, c2 = st.columns(2)
    c1.metric("SALDO DISPONIBLE", f"$ {disponible:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta_color="normal")
    c2.metric("DEUDA TARJETAS", f"$ {consumos_tjt:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta="- Pendiente", delta_color="inverse")

    # Módulo Analítico
    st.markdown("---")
    show_analisis = st.sidebar.checkbox("Mostrar Análisis Profesional", value=True)
    
    if show_analisis:
        st.subheader("📊 Análisis de Gastos y Presupuesto")
        
        # Regla 50-30-20
        st.write("#### Cumplimiento Presupuesto 50-30-20")
        col_p1, col_p2, col_p3 = st.columns(3)
        col_p1.progress(0.4, text="Fijos (50%)")
        col_p2.progress(0.6, text="Deseos (30%)")
        col_p3.progress(0.2, text="Ahorro (20%)")

        # Gráfico de Rubros
        if not df.empty:
            df_gastos = df[df['Importe Pesos'] < 0]
            fig = px.pie(df_gastos, values='Importe Pesos', names='Tipo', title="Distribución de Gastos", template=chart_theme)
            st.plotly_chart(fig, use_container_width=True)

else:
    st.title("👋 ¡Hola Lucas!")
    st.info("Para activar el Dashboard, arrastrá el archivo CSV en el panel de la izquierda.")
    st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=100)
