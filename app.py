import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings('ignore')

st.set_page_config(page_title="The One Ring: Bot 3 Eärendil DCA", layout="wide", page_icon="⚖️")

st.title("⚖️ Bot 3 — Eärendil DCA (Martingala Controlada)")
st.caption("Ecosistema Cuantitativo 'The One Ring' | Matriz de Promediación Asimétrica de Costo para Gestión Dinámica")
st.markdown("---")

# CONFIGURACIÓN TÁCTICA DE CAPITAL EN LA BARRA LATERAL
st.sidebar.header("⚙️ Configuración de Capas (Martingala)")
capital_base = st.sidebar.number_input("Monto Tramo 1 (Base USD)", value=100.0, step=10.0)
multiplicador_t2 = st.sidebar.slider("Multiplicador Tramo 2 (x)", 1.2, 2.0, 1.5, step=0.1)
multiplicador_t3 = st.sidebar.slider("Multiplicador Tramo 3 (x)", 2.0, 3.5, 2.5, step=0.1)

st.sidebar.markdown("---")
st.sidebar.header("🛡️ Umbrales de Caída")
caida_t2 = st.sidebar.slider("Caída para Activar Tramo 2 (%)", 0.5, 3.0, 1.0, step=0.1) / 100
caida_t3 = st.sidebar.slider("Caída para Activar Tramo 3 (%)", 1.5, 5.0, 2.0, step=0.1) / 100

# Cálculo dinámico del peor escenario para la tesorería
cap_t2 = capital_base * multiplicador_t2
cap_t3 = capital_base * multiplicador_t3
capital_total_requerido = capital_base + cap_t2 + cap_t3

st.sidebar.info(f"💰 Exposición Máxima por Activo: ${capital_total_requerido:.2f} USD")

# Universo de tickers institucionales estables ideales para promediar
UNIVERSO_ESTABLE = ["AAPL", "MSFT", "GOOGL", "NVDA", "JPM", "V", "MA", "XOM", "CVX", "COST", "WMT", "AMD", "AVGO", "TSM"]

def calcular_matriz_martingala(ticker, p_base, m_t2, m_t3, c_t2, c_t3):
    try:
        # Descarga del último precio spot (barra de 1 minuto)
        df = yf.download(ticker, period="1d", interval="1m", progress=False, auto_adjust=True)
        if df.empty: return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        precio_entrada = float(df['Close'].iloc[-1])
        
        # --- MODELACIÓN DE LOS TRAMOS MATEMÁTICOS ---
        # Tramo 1: Entrada
        precio_t1 = precio_entrada
        monto_t1 = p_base
        acciones_t1 = monto_t1 / precio_t1
        
        # Tramo 2: Primera Caída (Duplica/Aumenta posición)
        precio_t2 = precio_t1 * (1 - c_t2)
        monto_t2 = p_base * m_t2
        acciones_t2 = monto_t2 / precio_t2
        
        # Tramo 3: Segunda Caída (Capa Defensiva Final)
        precio_t3 = precio_t1 * (1 - c_t3)
        monto_t3 = p_base * m_t3
        acciones_t3 = monto_t3 / precio_t3
        
        # --- CÁLCULO DE PRECIOS PROMEDIO PONDERADOS ---
        # Si se activa el Tramo 2:
        total_acciones_f2 = acciones_t1 + acciones_t2
        total_capital_f2 = monto_t1 + monto_t2
        precio_promedio_f2 = total_capital_f2 / total_acciones_f2
        rebote_necesario_f2 = (precio_promedio_f2 / precio_t2) - 1
        
        # Si se activa el Tramo 3:
        total_acciones_f3 = acciones_t1 + acciones_t2 + acciones_t3
        total_capital_f3 = monto_t1 + monto_t2 + monto_t3
        precio_promedio_f3 = total_capital_f3 / total_acciones_f3
        rebote_necesario_f3 = (precio_promedio_f3 / precio_t3) - 1
        
        return {
            "Ticker": ticker,
            "Precio Entrada": precio_t1,
            "Monto T1": monto_t1,
            "Gatillo T2 (-%)": precio_t2,
            "Monto T2": monto_t2,
            "Costo Promedio (T1+T2)": precio_promedio_f2,
            "Rebote Req. T2": rebote_necesario_f2,
            "Gatillo T3 (-%)": precio_t3,
            "Monto T3": monto_t3,
            "Costo Promedio Total": precio_promedio_f3,
            "Rebote Req. T3": rebote_necesario_f3
        }
    except:
        return None

st.subheader("📋 Planificador de Órdenes y Promedios")
st.markdown("Este panel simula instantáneamente los niveles exactos donde IBKR sembrará las órdenes de compra hijas y calcula el precio promedio ponderado para salir sin rasguños.")

if st.button("⚖️ Calcular Matrices de Reducción de Costo"):
    with st.spinner("Procesando estructuras asimétricas de capital..."):
        resultados = []
        for t in UNIVERSO_ESTABLE:
            res = calcular_matriz_martingala(t, capital_base, multiplicador_t2, multiplicador_t3, caida_t2, caida_t3)
            if res: resultados.append(res)
            
        if resultados:
            df_visual = pd.DataFrame(resultados)
            
            st.dataframe(df_visual.style.format({
                "Precio Entrada": "${:.2f}", "Monto T1": "${:.2f}",
                "Gatillo T2 (-%)": "${:.2f}", "Monto T2": "${:.2f}", "Costo Promedio (T1+T2)": "${:.2f}", "Rebote Req. T2": "{:.2%}",
                "Gatillo T3 (-%)": "${:.2f}", "Monto T3": "${:.2f}", "Costo Promedio Total": "${:.2f}", "Rebote Req. T3": "{:.2%}"
            }), use_container_width=True, hide_index=True)
            
            st.success("💡 Nota de Gestión: Observa cómo en el peor escenario (Tramo 3), gracias al peso del capital asimétrico, el bot solo necesita un micro-rebote para salir en verde general.")
        else:
            st.error("Error al descargar la estructura de precios del mercado actual.")
