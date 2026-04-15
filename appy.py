import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración Básica
st.set_page_config(page_title="Lucas Cashflow", layout="wide")

# Fondo Oscuro por defecto (Híbrido)
st.markdown("""<style> .stApp { background-color: #0E1117; color: white; } </style>""", unsafe_allow_html=True)

st.title("💸 Lucas Cashflow")

# 2. Carga de Archivo
st.sidebar.header("📁 Subir Datos")
archivo = st.sidebar.file_uploader("Arrastrá el CSV", type=["csv"])

if archivo:
    try:
        # Leer el archivo ignorando errores de filas
        df = pd.read_csv(archivo, sep=None, engine='python', on_bad_lines='skip')
        
        # Limpiar nombres de columnas (quitar espacios)
        df.columns = [str(c).strip() for c in df.columns]

        # 3. Selección de Columnas (Si el auto-detect falla, las elegís vos)
        st.sidebar.subheader("Configurar Columnas")
        col_det = st.sidebar.selectbox("Columna de Detalle", df.columns, index=0)
        col_mon = st.sidebar.selectbox("Columna de Monto/Pesos", df.columns, index=1)
        col_rub = st.sidebar.selectbox("Columna de Rubro/Tipo", df.columns, index=len(df.columns)-1)

        # 4. Limpieza de Datos (A PRUEBA DE TODO)
        # Forzamos texto en el detalle para que no tire el error de la foto
        df['Detalle_Safe'] = df[col_det].astype(str).fillna('').str.lower()
        
        # Limpieza de números (maneja puntos y comas)
        def a_numero(val):
            s = str(val).replace('.', '').replace(',', '.')
            try:
                return float(''.join(c for c in s if c in '0123456789.-'))
            except:
                return 0.0

        df['Monto_Safe'] = df[col_mon].apply(a_numero)

        # 5. Cálculos (Tus reglas de negocio)
        ingresos_total = 6000000.0
        
        # Buscamos pagos y consumos de forma ultra segura
        es_pago = df['Detalle_Safe'].apply(lambda x: 'pago tarjeta' in x)
        
        tarjetas_keywords = ['visa', 'amex', 'uber', 'rappi', 'cabify', 'netflix', 'spotify', 'apple', 'google']
        es_tjt = df['Detalle_Safe'].apply(lambda x: any(k in x for k in tarjetas_keywords))
        
        pago_tjt_valor = df[es_pago]['Monto_Safe'].abs().sum()
        deuda_pendiente = df[es_tjt & ~es_pago]['Monto_Safe'].abs().sum()
        gastos_directos = df[(df['Monto_Safe'] < 0) & ~es_pago & ~es_tjt]['Monto_Safe'].abs().sum()
        
        disponible = ingresos_total - pago_tjt_valor - gastos_directos

        # 6. Mostrar KPIs (Vista iPhone)
        c1, c2 = st.columns(2)
        c1.metric("SALDO DISPONIBLE (VERDE)", f"$ {disponible:,.2f}")
        c2.metric("DEUDA TARJETAS (ROJO)", f"$ {deuda_pendiente:,.2f}", delta="Pasivo")

        st.markdown("---")

        # 7. Gráfico Analítico
        df_gastos = df[df['Monto_Safe'] < 0].copy()
        if not df_gastos.empty:
            fig = px.pie(df_gastos, values=df_gastos['Monto_Safe'].abs(), names=col_rub, 
                         hole=0.4, template="plotly_dark", title="Gastos por Rubro")
            st.plotly_chart(fig, use_container_width=True)
            
        # 8. Tabla de Auditoría
        if st.checkbox("Ver todos los movimientos"):
            st.dataframe(df[[col_det, col_mon, col_rub]])

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
else:
    st.info("Subí el CSV para ver el Dashboard.")
