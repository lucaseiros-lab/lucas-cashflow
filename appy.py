import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la App
st.set_page_config(page_title="Lucas Financial Engine", layout="wide")

# 2. Selector de Apariencia (Claro / Oscuro)
theme = st.sidebar.radio("Apariencia", ["Oscuro", "Claro"])
if theme == "Oscuro":
    bg, txt, chart_theme = "#0E1117", "white", "plotly_dark"
else:
    bg, txt, chart_theme = "#FFFFFF", "#31333F", "plotly_white"

st.markdown(f"<style>.stApp {{ background-color: {bg}; color: {txt}; }}</style>", unsafe_allow_html=True)

# 3. Función de Carga "Terminator" (No falla)
def load_data_v4(file):
    try:
        # Detectar si es coma o punto y coma
        raw = file.read()
        file.seek(0)
        decoded = raw.decode('utf-8-sig', errors='ignore')
        sep = ';' if decoded.count(';') > decoded.count(',') else ','
        
        df = pd.read_csv(file, sep=sep, engine='python')
        
        # Limpieza agresiva de nombres de columnas
        df.columns = [str(c).strip().replace('\ufeff', '') for c in df.columns]

        # Mapeo por palabras clave (si la columna contiene la palabra, la usamos)
        def find_best_col(keywords, columns):
            for k in keywords:
                for c in columns:
                    if k.lower() in c.lower(): return c
            return None

        c_fecha = find_best_col(['fecha', 'date'], df.columns)
        c_detalle = find_best_col(['detalle', 'concepto', 'movimiento', 'descrip'], df.columns)
        c_monto = find_best_col(['pesos', 'importe', 'monto'], df.columns)
        c_tipo = find_best_col(['tipo', 'rubro', 'categ'], df.columns)

        # Renombramos para uniformar
        renames = {}
        if c_fecha: renames[c_fecha] = 'Fecha'
        if c_detalle: renames[c_detalle] = 'Detalle'
        if c_monto: renames[c_monto] = 'Importe Pesos'
        if c_tipo: renames[c_tipo] = 'Tipo'
        df = df.rename(columns=renames)

        # Asegurar que existan para que el Dashboard no explote
        for col in ['Fecha', 'Detalle', 'Importe Pesos', 'Tipo']:
            if col not in df.columns: df[col] = 0.0 if col == 'Importe Pesos' else "N/A"

        # Limpiar números de forma segura
        def safe_float(x):
            if pd.isna(x): return 0.0
            s = str(x).strip().replace('$', '').replace(' ', '')
            if ',' in s and '.' in s: s = s.replace('.', '').replace(',', '.') # 1.234,56 -> 1234.56
            elif ',' in s: s = s.replace(',', '.') # 1234,56 -> 1234.56
            try: return float(s)
            except: return 0.0

        df['Importe Pesos'] = df['Importe Pesos'].apply(safe_float)
        df['Detalle'] = df['Detalle'].astype(str).fillna('')
        
        return df
    except Exception as e:
        st.error(f"Error cargando el archivo: {e}")
        return None

# 4. Interfaz Principal
st.sidebar.header("📁 Subir Resumen")
uploaded = st.sidebar.file_uploader("Arrastrá tu CSV", type=["csv"])

df = load_data_v4(uploaded) if uploaded else None

if df is not None:
    st.title("💸 Lucas Financial Dashboard")
    
    # KPIs y Lógica
    ingresos_honorarios = 6000000.0
    df_low = df['Detalle'].str.lower()
    
    # Identificar pagos y consumos
    es_pago = df_low.str.contains('pago tarjeta', na=False)
    kw_tjt = 'visa|amex|uber|rappi|cabify|netflix|spotify|apple|google|youtube'
    es_tjt = df_low.str.contains(kw_tjt, na=False)
    
    pago_total = df[es_pago]['Importe Pesos'].abs().sum()
    deuda_pendiente = df[es_tjt & ~es_pago]['Importe Pesos'].abs().sum()
    gastos_efectivo = df[(df['Importe Pesos'] < 0) & ~es_pago & ~es_tjt]['Importe Pesos'].abs().sum()
    
    disponible = ingresos_honorarios - pago_total - gastos_efectivo

    # FILA 1: KPIs (iPhone Style)
    c1, c2 = st.columns(2)
    c1.metric("SALDO DISPONIBLE", f"$ {disponible:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    c2.metric("DEUDA TARJETAS", f"$ {deuda_pendiente:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta="Pasivo Acumulado", delta_color="inverse")

    # FILA 2: Analítica Profesional
    st.markdown("---")
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        df_gastos = df[df['Importe Pesos'] < 0]
        if not df_gastos.empty:
            fig = px.pie(df_gastos, values=df_gastos['Importe Pesos'].abs(), names='Tipo', 
                         title="Gastos por Rubro", hole=0.4, template=chart_theme)
            st.plotly_chart(fig, use_container_width=True)
    
    with col_b:
        st.write("### Plan 50-30-20")
        st.progress(0.5, text=f"Fijos (50%): $ {ingresos_honorarios*0.5:,.0f}")
        st.progress(0.3, text=f"Variables (30%): $ {ingresos_honorarios*0.3:,.0f}")
        st.progress(0.2, text=f"Ahorro (20%): $ {ingresos_honorarios*0.2:,.0f}")

    # FILA 3: Comparativa (Opcional)
    if st.checkbox("Ver Auditoría Total"):
        st.dataframe(df[['Fecha', 'Detalle', 'Importe Pesos', 'Tipo']], use_container_width=True)

else:
    st.title("👋 ¡Hola Lucas!")
    st.info("Para activar el Dashboard, arrastrá el archivo CSV en el panel lateral.")
