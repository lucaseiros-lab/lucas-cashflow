import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Lucas Financial Engine", layout="wide")

# --- TEMA ---
theme = st.sidebar.radio("Apariencia", ["Oscuro", "Claro"])
if theme == "Oscuro":
    bg, txt, chart_theme = "#0E1117", "white", "plotly_dark"
else:
    bg, txt, chart_theme = "#FFFFFF", "#31333F", "plotly_white"

st.markdown(f"<style>.stApp {{ background-color: {bg}; color: {txt}; }}</style>", unsafe_allow_html=True)

# --- CARGA ULTRA-DEFENSIVA ---
def load_data_final(file):
    try:
        # Detectar separador
        raw_data = file.read()
        file.seek(0)
        decoded = raw_data.decode('utf-8-sig', errors='ignore')
        sep = ';' if decoded.count(';') > decoded.count(',') else ','
        
        df = pd.read_csv(file, sep=sep, encoding='utf-8-sig', engine='python')
        
        # 1. Limpiar columnas
        df.columns = [str(c).strip().replace('\ufeff', '') for c in df.columns]
        
        # 2. Mapeo de Nombres
        mapa = {
            'Fecha': ['Fecha', 'date', 'fec'],
            'Detalle': ['Detalle', 'concepto', 'descripcion', 'movimiento'],
            'Importe Pesos': ['Importe Pesos', 'monto pesos', 'pesos', 'importe'],
            'Tipo': ['Tipo', 'categoria', 'rubro']
        }
        for oficial, variantes in mapa.items():
            if oficial not in df.columns:
                for v in variantes:
                    columnas_actuales = [c.lower() for c in df.columns]
                    if v.lower() in columnas_actuales:
                        idx = columnas_actuales.index(v.lower())
                        df.rename(columns={df.columns[idx]: oficial}, inplace=True)
                        break

        # 3. Asegurar columnas mínimas para que NO falle el dashboard
        for c in ['Fecha', 'Detalle', 'Importe Pesos', 'Tipo']:
            if c not in df.columns: df[c] = ""
            
        # 4. Limpiar Números (Fallo crítico anterior corregido)
        def clean_currency(x):
            s = str(x).replace('.', '').replace(',', '.')
            try: return float(s)
            except: return 0.0

        df['Importe Pesos'] = df['Importe Pesos'].apply(clean_currency)
        if 'Importe Dólares' in df.columns:
            df['Importe Dólares'] = df['Importe Dólares'].apply(clean_currency)
        else:
            df['Importe Dólares'] = 0.0

        # 5. Asegurar que Detalle sea STRING siempre (Evita el error de la foto)
        df['Detalle'] = df['Detalle'].astype(str).fillna('')
        
        return df
    except Exception as e:
        st.error(f"Error al leer: {e}")
        return None

# --- INTERFAZ ---
st.sidebar.header("📁 Resumen Bancario")
uploaded_file = st.sidebar.file_uploader("Subí tu CSV", type=["csv"])

df = load_data_final(uploaded_file) if uploaded_file else None

if df is not None:
    st.title("💸 Lucas Financial Dashboard")
    
    # Lógica de flujo
    ingresos_fijos = 6000000.0
    df['det_low'] = df['Detalle'].str.lower()
    
    # REGLA DE DETECCIÓN (Nativa de Pandas, no falla con floats/NaNs)
    es_pago = df['det_low'].str.contains('pago tarjeta', na=False)
    # Filtro de palabras clave para tarjetas
    kw = 'visa|amex|uber|rappi|cabify|netflix|spotify|apple|google|youtube'
    es_tarjeta = df['det_low'].str.contains(kw, na=False)
    
    pago_tjt_total = df[es_pago]['Importe Pesos'].abs().sum()
    deuda_pendiente = df[es_tarjeta & ~es_pago]['Importe Pesos'].abs().sum()
    gastos_directos = df[(df['Importe Pesos'] < 0) & ~es_pago & ~es_tarjeta]['Importe Pesos'].abs().sum()
    
    disponible = ingresos_fijos - pago_tjt_total - gastos_directos

    # KPIs
    c1, c2 = st.columns(2)
    c1.metric("SALDO DISPONIBLE", f"$ {disponible:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    c2.metric("DEUDA TARJETAS", f"$ {deuda_pendiente:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta="Pasivo", delta_color="inverse")

    st.markdown("---")
    
    # Gráfico y Presupuesto
    col_a, col_b = st.columns([2, 1])
    with col_a:
        df_g = df[df['Importe Pesos'] < 0].copy()
        if not df_g.empty:
            fig = px.pie(df_g, values=df_g['Importe Pesos'].abs(), names='Tipo', 
                         title="Gastos por Rubro", template=chart_theme, hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
    
    with col_b:
        st.write("### Presupuesto 50-30-20")
        st.progress(0.5, text=f"Fijos (50%): $ {ingresos_fijos*0.5:,.0f}")
        st.progress(0.3, text=f"Deseos (30%): $ {ingresos_fijos*0.3:,.0f}")
        st.progress(0.2, text=f"Ahorro (20%): $ {ingresos_fijos*0.2:,.0f}")

    if st.checkbox("Ver Auditoría de Movimientos"):
        st.dataframe(df[['Fecha', 'Detalle', 'Importe Pesos', 'Tipo']], use_container_width=True)

else:
    st.title("👋 Bienvenido Lucas")
    st.info("Subí el archivo CSV en el panel de la izquierda para ver tu estado financiero.")
