import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Lucas Cash Flow", layout="wide")

# --- ESTILOS ---
theme = st.sidebar.radio("Apariencia", ["Oscuro", "Claro"])
if theme == "Oscuro":
    bg, txt, chart_theme = "#0E1117", "white", "plotly_dark"
else:
    bg, txt, chart_theme = "#FFFFFF", "#31333F", "plotly_white"

st.markdown(f"<style>.stApp {{ background-color: {bg}; color: {txt}; }}</style>", unsafe_allow_html=True)

# --- CARGA DE DATOS ROBUSTA ---
st.sidebar.header("📁 Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Subí tu CSV", type=["csv"])

def load_data(file):
    try:
        # Probamos leer con ; y si falla con ,
        try:
            df = pd.read_csv(file, sep=';', encoding='utf-8')
            if len(df.columns) < 2: raise Exception()
        except:
            file.seek(0)
            df = pd.read_csv(file, sep=',', encoding='utf-8')
        
        # Limpiar nombres de columnas (quitar espacios)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Limpiar importes
        for col in ['Importe Pesos', 'Importe Dólares']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        # Asegurar que 'Tipo' exista para que no tire KeyError
        if 'Tipo' not in df.columns:
            df['Tipo'] = 'Sin Categoría'
        
        return df
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return None

df = None
if uploaded_file:
    df = load_data(uploaded_file)

# --- DASHBOARD ---
if df is not None:
    st.title("💸 Lucas Financial Dashboard")
    
    # Cálculos
    ingresos = 6000000.0
    
    # Identificar pagos y consumos
    def check_str(val, search):
        return search.lower() in str(val).lower()

    pagos_mask = df['Detalle'].apply(lambda x: check_str(x, 'Pago tarjeta'))
    pagos_tjt = df[pagos_mask]['Importe Pesos'].abs().sum()
    
    consumos_mask = df['Detalle'].apply(lambda x: any(k in str(x).lower() for k in ['visa', 'amex', 'uber', 'rappi', 'cabify', 'netflix', 'spotify']))
    consumos_tjt = df[consumos_mask & ~pagos_mask]['Importe Pesos'].abs().sum()
    
    gastos_directos = df[(df['Importe Pesos'] < 0) & ~pagos_mask & ~consumos_mask]['Importe Pesos'].abs().sum()
    
    disponible = ingresos - pagos_tjt - gastos_directos

    # KPIs
    c1, c2 = st.columns(2)
    c1.metric("SALDO DISPONIBLE", f"$ {disponible:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    c2.metric("DEUDA TARJETAS", f"$ {consumos_tjt:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta="Pendiente", delta_color="inverse")

    # Gráfico
    st.markdown("---")
    df_gastos = df[df['Importe Pesos'] < 0]
    if not df_gastos.empty:
        fig = px.pie(df_gastos, values=df_gastos['Importe Pesos'].abs(), names='Tipo', 
                     title="Distribución de Gastos", template=chart_theme)
        st.plotly_chart(fig, use_container_width=True)
    
    # Vista de tabla para auditar
    if st.checkbox("Ver movimientos detectados"):
        st.dataframe(df)

else:
    st.title("👋 ¡Hola Lucas!")
    st.info("Arrastrá el archivo CSV en el panel de la izquierda para empezar.")
