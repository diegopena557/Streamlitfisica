import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime

# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================

st.set_page_config(
    page_title="Monitoreo de Luminosidad Solar",
    page_icon="☀️",
    layout="wide"
)

# ============================================================
# CSS PERSONALIZADO
# ============================================================

st.markdown("""
    <style>

    .main {
        padding: 2rem;
    }

    .stMetric {
        background-color: #f7f7f7;
        padding: 15px;
        border-radius: 10px;
    }

    h1 {
        color: #F39C12;
    }

    h2, h3 {
        color: #2C3E50;
    }

    </style>
""", unsafe_allow_html=True)

# ============================================================
# TÍTULO
# ============================================================

st.title("☀️ Monitoreo Inteligente de Luminosidad Solar")

st.markdown("""
Esta aplicación permite analizar datos de luminosidad capturados
por un sensor LDR conectado a un ESP32.

### Variables monitoreadas:
- 🌞 Luminosidad (%)
- 💡 Valor analógico LDR
- ☀️ Detección de luz solar
- ⏳ Horas acumuladas de luz
""")

# ============================================================
# MAPA
# ============================================================

eafit_location = pd.DataFrame({
    'lat': [6.2006],
    'lon': [-75.5783]
})

st.subheader("📍 Ubicación del Sensor")

st.map(eafit_location, zoom=15)

# ============================================================
# CARGA DE ARCHIVO
# ============================================================

uploaded_file = st.file_uploader(
    'Seleccione archivo CSV',
    type=['csv']
)

# ============================================================
# PROCESAMIENTO
# ============================================================

if uploaded_file is not None:

    try:

        # ====================================================
        # CARGAR CSV
        # ====================================================

        df = pd.read_csv(uploaded_file)

        # ====================================================
        # LIMPIAR COLUMNAS
        # ====================================================

        df.columns = [c.strip() for c in df.columns]

        # ====================================================
        # CONVERTIR TIME
        # ====================================================

        if 'Time' in df.columns:
            df['Time'] = pd.to_datetime(df['Time'])
            df = df.set_index('Time')

        # ====================================================
        # DETECTAR VARIABLES DISPONIBLES
        # ====================================================

        variables_disponibles = []

        posibles = [
            'ldr_raw',
            'luminosidad_pct',
            'es_luz_solar',
            'horas_luz_acum'
        ]

        for var in posibles:
            if var in df.columns:
                variables_disponibles.append(var)

        if len(variables_disponibles) == 0:
            st.error("No se encontraron variables compatibles.")
            st.stop()

        # ====================================================
        # SELECTOR DE VARIABLE
        # ====================================================

        st.sidebar.header("⚙️ Configuración")

        variable = st.sidebar.selectbox(
            "Seleccione variable",
            variables_disponibles
        )

        # ====================================================
        # INFORMACIÓN VARIABLE
        # ====================================================

        nombres = {
            'ldr_raw': '💡 LDR Raw',
            'luminosidad_pct': '☀️ Luminosidad (%)',
            'es_luz_solar': '🌞 Luz Solar Detectada',
            'horas_luz_acum': '⏳ Horas de Luz Acumuladas'
        }

        unidades = {
            'ldr_raw': 'ADC',
            'luminosidad_pct': '%',
            'es_luz_solar': '',
            'horas_luz_acum': 'h'
        }

        # ====================================================
        # TABS
        # ====================================================

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Visualización",
            "📊 Estadísticas",
            "🔍 Filtros",
            "⚠️ Anomalías",
            "🗺️ Información"
        ])

        # ====================================================
        # TAB 1 — VISUALIZACIÓN
        # ====================================================

        with tab1:

            st.subheader(f"Visualización — {nombres[variable]}")

            chart_type = st.selectbox(
                "Seleccione tipo de gráfico",
                ["Línea", "Área", "Barra"]
            )

            if chart_type == "Línea":
                st.line_chart(df[variable])

            elif chart_type == "Área":
                st.area_chart(df[variable])

            else:
                st.bar_chart(df[variable])

            # Mostrar promedio

            promedio = df[variable].mean()

            st.metric(
                "Promedio",
                f"{promedio:.2f} {unidades[variable]}"
            )

            # Mostrar datos crudos

            if st.checkbox("Mostrar datos crudos"):
                st.dataframe(df)

        # ====================================================
        # TAB 2 — ESTADÍSTICAS
        # ====================================================

        with tab2:

            st.subheader("📊 Estadísticas Descriptivas")

            stats_df = df[variable].describe()

            col1, col2 = st.columns(2)

            with col1:

                st.dataframe(stats_df)

            with col2:

                st.metric(
                    "Promedio",
                    f"{stats_df['mean']:.2f} {unidades[variable]}"
                )

                st.metric(
                    "Máximo",
                    f"{stats_df['max']:.2f} {unidades[variable]}"
                )

                st.metric(
                    "Mínimo",
                    f"{stats_df['min']:.2f} {unidades[variable]}"
                )

                st.metric(
                    "Desviación",
                    f"{stats_df['std']:.2f}"
                )

            # Histograma

            st.subheader("Distribución de Datos")

            hist_values = np.histogram(
                df[variable],
                bins=20
            )[0]

            st.bar_chart(hist_values)

        # ====================================================
        # TAB 3 — FILTROS
        # ====================================================

        with tab3:

            st.subheader("🔍 Filtrado de Datos")

            min_value = float(df[variable].min())
            max_value = float(df[variable].max())

            rango = st.slider(
                "Seleccione rango",
                min_value,
                max_value,
                (
                    min_value,
                    max_value
                )
            )

            filtrado = df[
                (df[variable] >= rango[0]) &
                (df[variable] <= rango[1])
            ]

            st.write(
                f"Registros encontrados: {len(filtrado)}"
            )

            st.dataframe(filtrado)

            # Descargar CSV

            csv = filtrado.to_csv().encode('utf-8')

            st.download_button(
                label="⬇️ Descargar CSV filtrado",
                data=csv,
                file_name='datos_filtrados.csv',
                mime='text/csv'
            )

        # ====================================================
        # TAB 4 — ANOMALÍAS
        # ====================================================

        with tab4:

            st.subheader("⚠️ Detección de Anomalías")

            serie = df[variable]

            z_scores = (
                (serie - serie.mean()) /
                serie.std()
            )

            umbral = st.slider(
                "Umbral Z-score",
                1.0,
                5.0,
                2.5
            )

            anomalias = df[
                z_scores.abs() > umbral
            ]

            st.metric(
                "Anomalías detectadas",
                len(anomalias)
            )

            st.line_chart(df[variable])

            if len(anomalias) > 0:

                st.warning(
                    f"Se detectaron {len(anomalias)} anomalías."
                )

                st.dataframe(anomalias)

            else:

                st.success(
                    "No se detectaron anomalías."
                )

        # ====================================================
        # TAB 5 — INFORMACIÓN
        # ====================================================

        with tab5:

            st.subheader("🗺️ Información del Sitio")

            col1, col2 = st.columns(2)

            with col1:

                st.write("### 📍 Ubicación")

                st.write("**Universidad EAFIT**")
                st.write("- Medellín, Colombia")
                st.write("- Latitud: 6.2006")
                st.write("- Longitud: -75.5783")
                st.write("- Altitud: ~1495 msnm")

            with col2:

                st.write("### ⚙️ Sensor")

                st.write("- Microcontrolador: ESP32")
                st.write("- Sensor: LDR")
                st.write("- Variable principal: Luminosidad")
                st.write("- Plataforma: InfluxDB Cloud")
                st.write("- Visualización: Streamlit")

        # ====================================================
        # PANEL RESUMEN
        # ====================================================

        st.sidebar.markdown("---")

        st.sidebar.subheader("📌 Resumen")

        st.sidebar.metric(
            "Variable actual",
            nombres[variable]
        )

        st.sidebar.metric(
            "Registros",
            len(df)
        )

        st.sidebar.metric(
            "Promedio",
            f"{df[variable].mean():.2f}"
        )

    except Exception as e:

        st.error(
            f'Error al procesar archivo: {str(e)}'
        )

        st.info(
            'Verifique que el CSV contenga columnas válidas.'
        )

# ============================================================
# SI NO HAY ARCHIVO
# ============================================================

else:

    st.warning(
        '⚠️ Cargue un archivo CSV para comenzar.'
    )

# ============================================================
# FOOTER
# ============================================================

st.markdown("""
---
☀️ Sistema de monitoreo de luminosidad solar con ESP32 + LDR + InfluxDB + Streamlit  
📍 Universidad EAFIT — Medellín, Colombia
""")
