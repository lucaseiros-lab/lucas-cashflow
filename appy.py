import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Lucas Financial Engine", layout="wide")

# --- SELECTOR DE TEMA ---
theme = st.sidebar.radio("Apariencia", ["Oscuro", "Claro"])
if theme == "Oscuro":
    bg, txt, chart_theme = "#0E1117", "white", "plotly_dark"
else:
    bg, txt, chart_theme = "#FFFFFF", "#31333F", "plotly_white"

st.markdown(f"<style>.stApp {{ background-color: {bg}; color: {txt}; }}</style>", unsafe_allow_html=True)

# --- CARGA DE DATOS A PRUEBA DE BALAS ---
def robust_load(file):
    try:
        # Detectar separador automáticamente
        content = file.read().decode('utf-8-sig')
        file.seek(0)
        sep = ';' if content.count(';') > content.count(',') else ','
        df = pd.read_csv(file, sep=sep, encoding='utf-8-sig')
        
        # 1. Limpiar nombres de columnas (quitar espacios y caracteres raros)
        df.columns = [str(c).strip().replace('\ufeff', '') for c in df.columns]
        
        # 2. Mapeo TOTAL de variantes de nombres
        mapping = {
            'Fecha': ['Fecha', 'FECHA', 'Date', 'fecha', 'Fec'],
            'Detalle': ['Detalle', 'Concepto', 'Descripcion', 'Movimiento', 'Description'],
            'Importe Pesos': ['Importe Pesos', 'Monto Pesos', 'Pesos', 'Importe', 'Monto'],
            'Tipo': ['Tipo', 'Categoria', 'Rubro', 'Category']
        }
        
        for oficial, variantes in mapping.items():
            if oficial not in df.columns:
                for v in variantes:
                    if v in df.columns:
                        df.rename(columns={v: oficial}, inplace=True)
                        break
        
        # 3. Crear columnas faltantes si el archivo viene muy pelado (evita KEYERROR)
        for col in ['Fecha', 'Detalle', 'Importe Pesos', 'Tipo']:
            if col not in df.columns:
                df[col] = "N/A" if col != 'Importe Pesos' else 0.0

        # 4. Limpiar Importes (Puntos por Comas)
        if 'Importe Pesos' in df.columns:
            df['Importe Pesos'] = df['Importe Pesos'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df['Importe Pesos'] = pd.to_numeric(df['Importe Pesos'], errors='coerce').fillna(0.0)
        
        return df
    except Exception as e:
        st.error(f"Error cargando el archivo: {e}")
        return None

# --- INTERFAZ ---
st.sidebar.header("📁 Carga de Resumen")
uploaded_file = st.sidebar.file_uploader("Arrastrá tu CSV aquí", type=["csv"])

df = robust_load(uploaded_file) if uploaded_file else None

if df is not None:
    st.title("💸 Lucas Financial Dashboard")
    
    # 5. Lógica de Negocio
    ingresos_fijos = 6000000.0
    df['det_low'] = df['Detalle'].astype(str).str.lower()
    
    # Identificar Pagos de Tarjeta vs Consumos
    es_pago = df['det_low'].str.contains('pago tarjeta', na=False)
    es_tarjeta = df['det_low'].str.contains('visa|amex|uber|rappi|cabify|netflix|spotify|apple|google', na=False)
    
    pago_tjt_total = df[es_pago]['Importe Pesos'].abs().sum()
    deuda_pendiente = df[es_tarjeta & ~es_pago]['Importe Pesos'].abs().sum()
    gastos_cash = df[(df['Importe Pesos'] < 0) & ~es_pago & ~es_tarjeta]['Importe Pesos'].abs().sum()
    
    disponible = ingresos_fijos - pago_tjt_total - gastos_cash

    # 6. KPIs (Vista iPhone)
    c1, c2 = st.columns(2)
    c1.metric("SALDO DISPONIBLE", f"$ {disponible:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    c2.metric("DEUDA TARJETAS", f"$ {deuda_pendiente:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta="Pasivo", delta_color="inverse")

    # 7. Gráficos (Vista Analítica)
    st.markdown("---")
    col_pie, col_stats = st.columns([2, 1])
    
    with col_pie:
        df_g = df[df['Importe Pesos'] < 0].copy()
        if not df_g.empty:
            fig = px.pie(df_g, values=df_g['Importe Pesos'].abs(), names='Tipo', 
                         title="Distribución de Gastos", template=chart_theme, hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
    with col_stats:
        st.write("### Regla 50-30-20")
        st.progress(0.5, text=f"Fijos (50%): $ {ingresos_fijos*0.5:,.0f}")
        st.progress(0.3, text=f"Deseos (30%): $ {ingresos_fijos*0.3:,.0f}")
        st.progress(0.2, text=f"Ahorro (20%): $ {ingresos_fijos*0.2:,.0f}")

    # 8. Auditoría Segura
    if st.checkbox("Ver Planilla de Movimientos"):
        # Solo mostramos lo que existe
        cols_ok = [c for c in ['Fecha', 'Detalle', 'Importe Pesos', 'Tipo'] if c in df.columns]
        st.dataframe(df[cols_ok], use_container_width=True)

else:
    st.title("👋 ¡Hola Lucas!")
    st.info("Arrastrá tu archivo CSV en el panel lateral para encender el Dashboard.")
