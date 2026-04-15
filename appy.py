import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Lucas Cashflow", layout="wide")

# Fondo y Estilo
st.markdown("<style>.stApp { background-color: #0E1117; color: white; }</style>", unsafe_allow_html=True)
st.sidebar.radio("Apariencia", ["Oscuro", "Claro"]) # Volvió la opción

st.title("💸 Lucas Cashflow")

archivo = st.sidebar.file_uploader("Subí tu CSV", type=["csv"])

if archivo:
    try:
        # LEER COMO SEA (Sin importar nombres de columnas)
        df = pd.read_csv(archivo, sep=None, engine='python', encoding='utf-8-sig')
        
        # Forzamos nombres por POSICIÓN (no por nombre)
        # 0=Fecha, 1=Detalle, 2=Importe Pesos, 3=Importe Dolares, 4=Tipo
        nuevos_nombres = ['Fecha', 'Detalle', 'Monto', 'Dolares', 'Tipo']
        # Si el archivo tiene más o menos columnas, lo ajustamos
        df.columns = nuevos_nombres[:len(df.columns)] + [f'Extra_{i}' for i in range(len(df.columns) - len(nuevos_nombres))]

        # Limpieza de Números
        def limpia(x):
            try:
                s = str(x).replace('.', '').replace(',', '.')
                return float(''.join(c for c in s if c in '0123456789.-'))
            except: return 0.0

        df['Monto_Limpio'] = df['Monto'].apply(limpia)
        df['Detalle_Limpio'] = df['Detalle'].astype(str).str.lower()
        
        # Cálculos
        ingresos = 6000000.0
        pago_tjt = df[df['Detalle_Limpio'].str.contains('pago tarjeta', na=False)]['Monto_Limpio'].abs().sum()
        
        kw = 'visa|amex|uber|rappi|cabify|netflix|spotify|apple|google'
        es_tjt = df['Detalle_Limpio'].str.contains(kw, na=False)
        es_pago = df['Detalle_Limpio'].str.contains('pago tarjeta', na=False)
        
        deuda = df[es_tjt & ~es_pago]['Monto_Limpio'].abs().sum()
        disponible = ingresos - pago_tjt - df[(df['Monto_Limpio'] < 0) & ~es_tjt & ~es_pago]['Monto_Limpio'].abs().sum()

        # KPIs
        c1, c2 = st.columns(2)
        c1.metric("DISPONIBLE", f"$ {disponible:,.2f}")
        c2.metric("DEUDA", f"$ {deuda:,.2f}", delta="Pasivo")

        # Gráfico
        fig = px.pie(df[df['Monto_Limpio'] < 0], values='Monto_Limpio', names='Tipo', hole=0.4, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}. Probá el Plan B de Google Sheets.")
else:
    st.info("Subí el archivo para activar.")
