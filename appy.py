import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la App
st.set_page_config(page_title="Lucas Financial Engine", layout="wide")

# Selector de Apariencia
theme = st.sidebar.radio("Apariencia", ["Oscuro", "Claro"])
if theme == "Oscuro":
    bg, txt, chart_theme = "#0E1117", "white", "plotly_dark"
else:
    bg, txt, chart_theme = "#FFFFFF", "#31333F", "plotly_white"

st.markdown(f"<style>.stApp {{ background-color: {bg}; color: {txt}; }}</style>", unsafe_allow_html=True)

# 2. Carga y Procesamiento
st.sidebar.header("📁 Datos")
uploaded = st.sidebar.file_uploader("Subí tu CSV", type=["csv"])

if uploaded:
    try:
        # Lectura con auto-detección de separador
        df_raw = pd.read_csv(uploaded, sep=None, engine='python', encoding='utf-8-sig')
        df_raw.columns = [str(c).strip().replace('\ufeff', '') for c in df_raw.columns]
        
        # --- MAPEO MANUAL (Si el auto-detect falla, vos mandás) ---
        st.sidebar.subheader("Validar Columnas")
        cols = list(df_raw.columns)
        
        def find_idx(keys, options):
            for i, opt in enumerate(options):
                if any(k in opt.lower() for k in keys): return i
            return 0

        sel_detalle = st.sidebar.selectbox("¿Cuál es la columna de Detalle?", cols, index=find_idx(['detalle', 'concepto', 'mov'], cols))
        sel_monto = st.sidebar.selectbox("¿Cuál es la columna de Importe?", cols, index=find_idx(['importe', 'pesos', 'monto'], cols))
        sel_tipo = st.sidebar.selectbox("¿Cuál es la columna de Rubro/Tipo?", cols, index=find_idx(['tipo', 'rubro', 'categ'], cols))
        
        # Crear DataFrame estandarizado
        df = df_raw.copy()
        df['Detalle'] = df[sel_detalle].astype(str).fillna('')
        
        def clean_num(x):
            try:
                s = str(x).replace('.', '').replace(',', '.')
                return float(''.join(c for c in s if c in '0123456789.-'))
            except: return 0.0
            
        df['Importe Pesos'] = df[sel_monto].apply(clean_num)
        df['Tipo'] = df[sel_tipo] if sel_tipo in df.columns else "Varios"
        
        # --- DASHBOARD ---
        st.title("💸 Lucas Financial Dashboard")
        
        ingresos = 6000000.0
        df_low = df['Detalle'].str.lower()
        
        # Lógica de detección
        es_pago = df_low.str.contains('pago tarjeta', na=False)
        kw_tjt = 'visa|amex|uber|rappi|cabify|netflix|spotify|apple|google|youtube'
        es_tjt = df_low.str.contains(kw_tjt, na=False)
        
        pago_tjt_total = df[es_pago]['Importe Pesos'].abs().sum()
        deuda_pendiente = df[es_tjt & ~es_pago]['Importe Pesos'].abs().sum()
        gastos_cash = df[(df['Importe Pesos'] < 0) & ~es_pago & ~es_tjt]['Importe Pesos'].abs().sum()
        disponible = ingresos - pago_tjt_total - gastos_cash

        # KPIs (Vista iPhone)
        c1, c2 = st.columns(2)
        c1.metric("SALDO DISPONIBLE", f"$ {disponible:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        c2.metric("DEUDA TARJETAS", f"$ {deuda_pendiente:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta="Pasivo", delta_color="inverse")

        st.markdown("---")
        
        # Gráfico y Plan 50-30-20
        col_a, col_b = st.columns([2, 1])
        with col_a:
            df_g = df[df['Importe Pesos'] < 0]
            if not df_g.empty:
                fig = px.pie(df_g, values=df_g['Importe Pesos'].abs(), names='Tipo', 
                             title="Gastos por Rubro", hole=0.4, template=chart_theme)
                st.plotly_chart(fig, use_container_width=True)
        
        with col_b:
            st.write("### Plan 50-30-20")
            st.progress(0.5, text=f"Fijos (50%): $ {ingresos*0.5:,.0f}")
            st.progress(0.3, text=f"Deseos (30%): $ {ingresos*0.3:,.0f}")
            st.progress(0.2, text=f"Ahorro (20%): $ {ingresos*0.2:,.0f}")
            
    except Exception as e:
        st.error(f"Error en el procesamiento: {e}")
else:
    st.title("👋 ¡Hola Lucas!")
    st.info("Subí el archivo CSV en el panel de la izquierda para activar el Dashboard.")
