import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la App
st.set_page_config(page_title="Lucas Cashflow", layout="wide")

# Estilos de Fondo
theme = st.sidebar.radio("Apariencia", ["Oscuro", "Claro"])
if theme == "Oscuro":
    bg, txt, chart_theme = "#0E1117", "white", "plotly_dark"
else:
    bg, txt, chart_theme = "#FFFFFF", "#31333F", "plotly_white"

st.markdown(f"<style>.stApp {{ background-color: {bg}; color: {txt}; }}</style>", unsafe_allow_html=True)

# 2. Función de Carga Blindada
def cargar_datos(archivo):
    try:
        # Detectar separador automáticamente
        raw = archivo.read()
        archivo.seek(0)
        encoding = 'utf-8-sig'
        decoded = raw.decode(encoding, errors='ignore')
        sep = ';' if decoded.count(';') > decoded.count(',') else ','
        
        # Leer el CSV
        df = pd.read_csv(archivo, sep=sep, engine='python', encoding=encoding)
        
        # Limpiar nombres de columnas
        df.columns = [str(c).strip().replace('\ufeff', '') for c in df.columns]
        
        return df
    except Exception as e:
        st.error(f"No se pudo leer el archivo: {e}")
        return pd.DataFrame() # Devuelve tabla vacía, no None, para evitar el error de la foto

# 3. Interfaz Principal
st.sidebar.header("📁 Carga de Resumen")
subido = st.sidebar.file_uploader("Subí tu CSV aquí", type=["csv"])

if subido:
    df = cargar_datos(subido)
    
    if not df.empty:
        st.title("💸 Lucas Cashflow")
        
        # Mapeo de columnas por si cambian los nombres
        columnas = list(df.columns)
        def buscar_col(keys):
            for k in keys:
                for c in columnas:
                    if k.lower() in c.lower(): return c
            return None

        col_detalle = buscar_col(['detalle', 'concepto', 'movimiento'])
        col_monto = buscar_col(['pesos', 'importe', 'monto'])
        col_tipo = buscar_col(['tipo', 'rubro', 'categ'])

        # Si faltan columnas, pedimos que las elija
        if not col_detalle or not col_monto:
            st.warning("⚠️ No pude detectar las columnas automáticamente. Por favor, seleccionalas:")
            col_detalle = st.selectbox("Columna de Detalle", columnas)
            col_monto = st.selectbox("Columna de Importe", columnas)
            col_tipo = st.selectbox("Columna de Rubro", columnas)

        # Limpieza de Números
        def limpiar_guita(x):
            s = str(x).replace('.', '').replace(',', '.')
            try: return float(''.join(c for c in s if c in '0123456789.-'))
            except: return 0.0

        df['Monto_Limpio'] = df[col_monto].apply(limpiar_guita)
        df['Detalle_Limpio'] = df[col_detalle].astype(str).fillna('')
        
        # 4. Lógica de Flujo (Tus Reglas)
        ingresos_mes = 6000000.0
        df_low = df['Detalle_Limpio'].str.lower()
        
        es_pago = df_low.str.contains('pago tarjeta', na=False)
        es_tarjeta = df_low.str.contains('visa|amex|uber|rappi|cabify|netflix|spotify|apple|google', na=False)
        
        pago_tjt_total = df[es_pago]['Monto_Limpio'].abs().sum()
        deuda_tarjetas = df[es_tarjeta & ~es_pago]['Monto_Limpio'].abs().sum()
        gastos_cash = df[(df['Monto_Limpio'] < 0) & ~es_pago & ~es_tarjeta]['Monto_Limpio'].abs().sum()
        
        disponible = ingresos_mes - pago_tjt_total - gastos_cash

        # 5. Visualización (KPIs)
        c1, c2 = st.columns(2)
        c1.metric("SALDO DISPONIBLE", f"$ {disponible:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        c2.metric("DEUDA TARJETAS (ROJO)", f"$ {deuda_tarjetas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta_color="inverse")

        st.markdown("---")

        # 6. Gráfico de Rubros (Protegido contra errores)
        df_egresos = df[df['Monto_Limpio'] < 0]
        if not df_egresos.empty:
            nombre_rubro = col_tipo if col_tipo else col_detalle
            fig = px.pie(df_egresos, values=df_egresos['Monto_Limpio'].abs(), names=nombre_rubro, 
                         title="Distribución por Rubro", hole=0.4, template=chart_theme)
            st.plotly_chart(fig, use_container_width=True)

        # Auditoría
        if st.checkbox("Ver todos los movimientos"):
            st.dataframe(df)
    else:
        st.error("El archivo está vacío o no tiene el formato correcto.")
else:
    st.title("👋 Bienvenido Lucas")
    st.info("Subí el archivo CSV para ver tu Lucas Cashflow.")
