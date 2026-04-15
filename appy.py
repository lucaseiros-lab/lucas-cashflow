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

# --- CARGA DE DATOS ULTRA-ROBUSTA ---
st.sidebar.header("📁 Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Subí tu CSV", type=["csv"])

def load_data(file):
    try:
        # Probamos diferentes encodings y separadores
        try:
            df = pd.read_csv(file, sep=';', encoding='utf-8-sig')
        except:
            file.seek(0)
            df = pd.read_csv(file, sep=',', encoding='utf-8-sig')
        
        # 1. Limpiar nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        # 2. Mapeo inteligente de columnas (por si cambió el nombre)
        mapeo = {
            'Detalle': ['Detalle', 'Concepto', 'Descripcion', 'Movimiento'],
            'Importe Pesos': ['Importe Pesos', 'Monto Pesos', 'Pesos'],
            'Tipo': ['Tipo', 'Categoria', 'Rubro']
        }
        
        for oficial, variantes in mapeo.items():
            if oficial not in df.columns:
                for v in variantes:
                    if v in df.columns:
                        df.rename(columns={v: oficial}, inplace=True)
                        break
        
        # 3. Validar columnas críticas
        if 'Detalle' not in df.columns:
            st.error(f"⚠️ No encuentro la columna 'Detalle'. Columnas detectadas: {list(df.columns)}")
            return None

        # 4. Limpiar importes
        for col in ['Importe Pesos', 'Importe Dólares']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        if 'Tipo' not in df.columns: df['Tipo'] = 'Sin Categoría'
        
        return df
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return None

df = None
if uploaded_file:
    df = load_data(uploaded_file)

# --- RENDERIZADO ---
if df is not None:
    st.title("💸 Lucas Financial Dashboard")
    
    # Cálculos con protección contra valores nulos
    ingresos = 6000000.0
    
    # Filtros inteligentes
    df['Detalle_Lower'] = df['Detalle'].astype(str).str.lower()
    
    pagos_mask = df['Detalle_Lower'].str.contains('pago tarjeta', na=False)
    pagos_tjt = df[pagos_mask]['Importe Pesos'].abs().sum()
    
    keywords_tjt = ['visa', 'amex', 'uber', 'rappi', 'cabify', 'netflix', 'spotify', 'apple', 'google']
    consumos_mask = df['Detalle_Lower'].apply(lambda x: any(k in x for k in keywords_tjt))
    consumos_tjt = df[consumos_mask & ~pagos_mask]['Importe Pesos'].abs().sum()
    
    gastos_directos = df[(df['Importe Pesos'] < 0) & ~pagos_mask & ~consumos_mask]['Importe Pesos'].abs().sum()
    disponible = ingresos - pagos_tjt - gastos_directos

    # KPIs
    c1, c2 = st.columns(2)
    with c1:
        st.metric("SALDO DISPONIBLE", f"$ {disponible:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    with c2:
        st.metric("DEUDA TARJETAS", f"$ {consumos_tjt:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta="Pasivo Pendiente", delta_color="inverse")

    # Gráfico
    st.markdown("---")
    df_gastos = df[df['Importe Pesos'] < 0].copy()
    if not df_gastos.empty:
        fig = px.pie(df_gastos, values=df_gastos['Importe Pesos'].abs(), names='Tipo', 
                     title="Gastos por Rubro", template=chart_theme, hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    
    if st.checkbox("Ver Planilla de Movimientos"):
        st.dataframe(df[['Fecha', 'Detalle', 'Importe Pesos', 'Tipo']])

else:
    st.title("👋 ¡Hola Lucas!")
    st.info("Para activar el sistema, subí tu archivo CSV desde el panel lateral.")
