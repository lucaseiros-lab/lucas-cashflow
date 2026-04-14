import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Lucas Cash Flow", layout="wide")

# --- SELECTOR DE TEMA ---
theme = st.sidebar.radio("Elegir Fondo", ["Oscuro", "Claro"])
if theme == "Oscuro":
    st.markdown("""<style> .main { background-color: #0E1117; color: white; } </style>""", unsafe_allow_html=True)
else:
    st.markdown("""<style> .main { background-color: #F0F2F6; color: black; } </style>""", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
# Usamos el archivo que auditamos en el Capítulo 1
@st.cache_data
def load_data():
    df = pd.read_csv('MVP_CashFlow_Lucas_Completo.csv', sep=';')
    # Limpieza de importes (puntos y comas)
    for col in ['Importe Pesos', 'Importe Dólares']:
        df[col] = df[col].astype(str).str.replace('.', '').str.replace(',', '.').replace('-', '0').astype(float)
    return df

df = load_data()

# --- LÓGICA DE NEGOCIO (Capítulo 2) ---
ingresos_honorarios = 6000000.0
pagos_tarjeta = df[df['Detalle'].str.contains('Pago tarjeta', case=False)]['Importe Pesos'].abs().sum()
gastos_efectivo = df[df['Tipo'] == 'Gasto']['Importe Pesos'].abs().sum() - pagos_tarjeta

# Deuda es todo lo que NO es pago de tarjeta ni movimiento entre cuentas
deuda_visa = df[df['Detalle'].str.contains('Visa', case=False) & ~df['Detalle'].str.contains('Pago', case=False)]['Importe Pesos'].abs().sum()
deuda_amex = df[df['Detalle'].str.contains('Amex|dlorappi|cabify', case=False) & ~df['Detalle'].str.contains('Pago', case=False)]['Importe Pesos'].abs().sum()

disponible = ingresos_honorarios - pagos_tarjeta - gastos_efectivo

# --- DASHBOARD IPHONE (KPIs) ---
st.title("💸 Lucas Financial Dashboard")
col1, col2 = st.columns(2)

with col1:
    st.metric("DISPONIBLE HOY", f"$ {disponible:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta_color="normal")
with col2:
    st.metric("DEUDA TARJETAS", f"$ {(deuda_visa + deuda_amex):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), delta="- Pendiente")

# --- SECCIÓN ANALÍTICA (Interactivo) ---
st.markdown("---")
st.subheader("📊 Módulo Analítico")
show_503020 = st.checkbox("Ver Regla 50-30-20", value=True)
show_rubros = st.checkbox("Ver Gastos por Rubro", value=True)

if show_503020:
    st.write("### Presupuesto 50-30-20")
    # Lógica de cálculo basada en tus rubros
    fijos = ingresos_honorarios * 0.5
    variables = ingresos_honorarios * 0.3
    ahorro = ingresos_honorarios * 0.2
    st.progress(0.5, text=f"Necesidades: $ {fijos:,.0f}")
    st.progress(0.3, text=f"Deseos: $ {variables:,.0f}")
    st.progress(0.2, text=f"Ahorro: $ {ahorro:,.0f}")

if show_rubros:
    # Gráfico de barras interactivo
    fig = px.bar(df[df['Importe Pesos'] < 0], x='Fecha', y='Importe Pesos', color='Tipo', title="Detalle de Egresos")
    st.plotly_chart(fig, use_container_width=True)

st.sidebar.markdown("### Configuración de Auditoría")
st.sidebar.write("Carga tu nuevo PDF aquí (Drag & Drop)")
uploaded_file = st.sidebar.file_uploader("", type=["pdf", "csv", "xlsx"])