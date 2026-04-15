import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración
st.set_page_config(page_title="Lucas Cashflow", layout="wide")
st.markdown("<style>.stApp { background-color: #0E1117; color: white; }</style>", unsafe_allow_html=True)
st.title("💸 Lucas Cashflow")

# 2. Carga de Archivo
archivo = st.sidebar.file_uploader("Subí tu CSV", type=["csv"])

if archivo:
    try:
        # Lectura ultra-flexible (ignora errores de formato inicial)
        df = pd.read_csv(archivo, sep=None, engine='python', encoding='utf-8-sig')
        
        # Limpieza total de nombres de columnas (quita espacios y comillas locas)
        df.columns = [str(c).strip().replace('"', '').replace("'", "") for c in df.columns]
        
        st.sidebar.subheader("⚙️ Configuración de Columnas")
        st.sidebar.write("Columnas encontradas:", list(df.columns))

        # Buscamos las mejores coincidencias para que no tengas que elegir siempre
        def encontrar_columna(opciones, actual_cols):
            for opt in opciones:
                for col in actual_cols:
                    if opt.lower() in col.lower(): return col
            return actual_cols[0]

        # Selectores manuales en el lateral para que NUNCA más falle
        c_det = st.sidebar.selectbox("Elegí la columna de DETALLE", df.columns, 
                                     index=list(df.columns).index(encontrar_columna(['detalle', 'concepto', 'movimiento'], df.columns)))
        
        c_mon = st.sidebar.selectbox("Elegí la columna de IMPORTE", df.columns, 
                                     index=list(df.columns).index(encontrar_columna(['pesos', 'monto', 'importe'], df.columns)))
        
        c_rub = st.sidebar.selectbox("Elegí la columna de RUBRO/TIPO", df.columns, 
                                     index=list(df.columns).index(encontrar_columna(['tipo', 'rubro', 'categor'], df.columns)))

        # PROCESAMIENTO DE DATOS
        # Aseguramos que Detalle sea texto y no explote
        df['Detalle_Final'] = df[c_det].astype(str).fillna('')
        
        # Limpieza de montos (quita puntos de miles y maneja comas)
        def limpiar_plata(val):
            try:
                s = str(val).strip().replace('$', '').replace(' ', '')
                if ',' in s and '.' in s: s = s.replace('.', '') # 1.234,56 -> 1234,56
                s = s.replace(',', '.') # 1234,56 -> 1234.56
                return float(s)
            except: return 0.0

        df['Monto_Final'] = df[c_mon].apply(limpiar_plata)
        
        # LÓGICA DE NEGOCIO (Tus reglas)
        ingresos = 6000000.0
        det_low = df['Detalle_Final'].str.lower()
        
        es_pago = det_low.str.contains('pago tarjeta', na=False)
        kw_tarjetas = 'visa|amex|uber|rappi|cabify|netflix|spotify|apple|google'
        es_tjt = det_low.str.contains(kw_tarjetas, na=False)
        
        pago_tjt_total = df[es_pago]['Monto_Final'].abs().sum()
        deuda_tarjetas = df[es_tjt & ~es_pago]['Monto_Final'].abs().sum()
        gastos_directos = df[(df['Monto_Final'] < 0) & ~es_pago & ~es_tjt]['Monto_Final'].abs().sum()
        
        disponible = ingresos - pago_tjt_total - gastos_directos

        # DASHBOARD (Vista iPhone)
        col1, col2 = st.columns(2)
        col1.metric("DISPONIBLE HOY", f"$ {disponible:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col2.metric("DEUDA ACUMULADA", f"$ {deuda_tarjetas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta="Pasivo", delta_color="inverse")

        st.markdown("---")
        
        # Gráfico de Rubros
        df_gastos = df[df['Monto_Final'] < 0].copy()
        if not df_gastos.empty:
            fig = px.pie(df_gastos, values=df_gastos['Monto_Final'].abs(), names=c_rub, 
                         hole=0.4, title="Distribución de Gastos", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

        if st.checkbox("Ver Planilla de Auditoría"):
            st.dataframe(df[[c_det, 'Monto_Final', c_rub]])

    except Exception as e:
        st.error(f"Error técnico detectado: {e}")
        st.write("Por favor, revisá que las columnas seleccionadas en la izquierda sean las correctas.")
else:
    st.info("Subí el archivo CSV para activar el Dashboard.")
