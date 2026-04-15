import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="Lucas Financial Engine", layout="wide")

# --- ESTILOS ---
st.markdown("""<style> .stApp { background-color: #0E1117; color: white; } </style>""", unsafe_allow_html=True)

st.title("💸 Lucas Financial Dashboard")

# --- CARGA ATÓMICA ---
st.sidebar.header("📁 Carga de Resumen")
uploaded_file = st.sidebar.file_uploader("Subí tu CSV", type=["csv"])

if uploaded_file is not None:
    # Intentar leer el archivo de todas las formas posibles
    df = None
    try:
        # Intento 1: Separador ;
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8-sig', on_bad_lines='skip')
        if len(df.columns) < 2: raise Exception()
    except:
        try:
            # Intento 2: Separador ,
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep=',', encoding='utf-8-sig', on_bad_lines='skip')
        except Exception as e:
            st.error(f"Error crítico de lectura: {e}")

    if df is not None:
        # Limpiar nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        # --- SELECTORES MANUALES (PARA QUE NO FALLE NUNCA) ---
        st.sidebar.subheader("Verificar Columnas")
        col_detalle = st.sidebar.selectbox("Columna de Detalle/Concepto", df.columns)
        col_importe = st.sidebar.selectbox("Columna de Importe/Pesos", df.columns)
        col_tipo = st.sidebar.selectbox("Columna de Tipo/Rubro", df.columns)

        try:
            # Limpiar importes
            def clean_val(x):
                s = str(x).replace('.', '').replace(',', '.')
                return pd.to_numeric(''.join(c for c in s if c in '0123456789.-'), errors='coerce')

            df['Monto'] = df[col_importe].apply(clean_val).fillna(0.0)
            df['Concepto'] = df[col_detalle].astype(str).fillna('')
            
            # --- LÓGICA DE DASHBOARD ---
            ingresos = 6000000.0
            
            # Detección
            pago_tjt = df[df['Concepto'].str.contains('pago tarjeta', case=False, na=False)]['Monto'].abs().sum()
            
            kw = 'visa|amex|uber|rappi|cabify|netflix|spotify|apple|google'
            es_tjt = df['Concepto'].str.contains(kw, case=False, na=False)
            es_pago = df['Concepto'].str.contains('pago tarjeta', case=False, na=False)
            
            deuda_tjt = df[es_tjt & ~es_pago]['Monto'].abs().sum()
            gastos_cash = df[(df['Monto'] < 0) & ~es_tjt & ~es_pago]['Monto'].abs().sum()
            
            disponible = ingresos - pago_tjt - gastos_cash

            # KPIs
            c1, c2 = st.columns(2)
            c1.metric("SALDO DISPONIBLE", f"$ {disponible:,.2f}")
            c2.metric("DEUDA TARJETAS", f"$ {deuda_tjt:,.2f}", delta="Pasivo")

            # Gráfico
            st.markdown("---")
            df_g = df[df['Monto'] < 0]
            if not df_g.empty:
                fig = px.pie(df_g, values=df_g['Monto'].abs(), names=col_tipo, hole=0.4, template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error al procesar los datos: {e}")
            st.write("Columnas detectadas:", list(df.columns))
            st.dataframe(df.head())
else:
    st.info("Subí el CSV para empezar.")
