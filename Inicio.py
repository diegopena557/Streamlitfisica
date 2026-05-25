import pandas as pd
import streamlit as st
import numpy as np

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
por un sensor LDR conectado a un ESP32 y almacenados en InfluxDB.

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
# SUBIR ARCHIVO
# ============================================================

uploaded_file = st.file_uploader(
    "Seleccione archivo CSV exportado desde InfluxDB",
    type=['csv']
)

# ============================================================
# PROCESAMIENTO
# ============================================================

if uploaded_file is not None:

    try:

        # ====================================================
        # LEER CSV COMPLETO
        # ====================================================

        raw_df = pd.read_csv(
            uploaded_file,
            header=None
        )

        # ====================================================
        # BUSCAR FILA DEL HEADER
        # ====================================================

        header_row = None

        for i in range(len(raw_df)):

            fila = raw_df.iloc[i].astype(str).tolist()

            if '_field' in fila or '_value' in fila:

                header_row = i
                break

        # ====================================================
        # VALIDAR HEADER
        # ====================================================

        if header_row is None:

            st.error(
                "❌ No se pudo detectar el encabezado del CSV."
            )

            st.stop()

        # ====================================================
        # LEER CSV CORRECTAMENTE
        # ====================================================

        uploaded_file.seek(0)

        df = pd.read_csv(
            uploaded_file,
            skiprows=header_row
        )

        # ====================================================
        # LIMPIAR COLUMNAS
        # ====================================================

        df.columns = [
            str(c).strip()
            for c in df.columns
        ]

        # ====================================================
        # DEBUG
        # ====================================================

        st.sidebar.subheader("🔍 Debug")

        st.sidebar.write(
            f"Header detectado en fila: {header_row}"
        )

        st.sidebar.write("Columnas originales:")

        st.sidebar.write(
            df.columns.tolist()
        )

        # ====================================================
        # RENOMBRAR TIME
        # ====================================================

        if '_time' in df.columns:

            df = df.rename(columns={
                '_time': 'Time'
            })

        elif 'time' in df.columns:

            df = df.rename(columns={
                'time': 'Time'
            })

        # ====================================================
        # ELIMINAR METADATA
        # ====================================================

        columnas_eliminar = [
            'result',
            'table',
            '_start',
            '_stop',
            '_measurement'
        ]

        for col in columnas_eliminar:

            if col in df.columns:

                df = df.drop(columns=col)

        # ====================================================
        # CONVERTIR TIEMPO
        # ====================================================

        if 'Time' in df.columns:

            df['Time'] = pd.to_datetime(
                df['Time']
            )

            df = df.set_index('Time')

        # ====================================================
        # TRANSFORMAR FORMATO FLUX
        # ====================================================

        if '_field' in df.columns and '_value' in df.columns:

            df = df.pivot_table(
                index=df.index,
                columns='_field',
                values='_value',
                aggfunc='first'
            )

            df.columns.name = None

        # ====================================================
        # LIMPIAR COLUMNAS NUEVAMENTE
        # ====================================================

        df.columns = [
            str(c).strip()
            for c in df.columns
        ]

        # ====================================================
        # DEBUG FINAL
        # ====================================================

        st.sidebar.write("Columnas transformadas:")

        st.sidebar.write(
            df.columns.tolist()
        )

        # ====================================================
        # VARIABLES ESPERADAS
        # ====================================================

        posibles = [
            'ldr_raw',
            'luminosidad_pct',
            'es_luz_solar',
            'horas_luz_acum'
        ]

        variables_disponibles = []

        for col in df.columns:

            if col in posibles:

                variables_disponibles.append(col)

        # ====================================================
        # VALIDAR VARIABLES
        # ====================================================

        if len(variables_disponibles) == 0:

            st.error(
                "❌ No se encontraron variables compatibles."
            )

            st.write(
                "Columnas encontradas:"
            )

            st.write(df.columns.tolist())

            st.stop()

        # ====================================================
        # CONVERTIR NUMÉRICOS
        # ====================================================

        for var in variables_disponibles:

            df[var] = pd.to_numeric(
                df[var],
                errors='coerce'
            )

        # ====================================================
        # SIDEBAR
        # ====================================================

        st.sidebar.header("⚙️ Configuración")

        variable = st.sidebar.selectbox(
            "Seleccione variable",
            variables_disponibles
        )

        # ====================================================
        # NOMBRES
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
        # LIMPIAR NaN
        # ====================================================

        df = df.dropna(
            subset=[variable]
        )

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

            st.subheader(
                f"Visualización — {nombres[variable]}"
            )

            chart_type = st.selectbox(
                "Seleccione tipo de gráfico",
                [
                    "Línea",
                    "Área",
                    "Barra"
                ]
            )

            if chart_type == "Línea":

                st.line_chart(
                    df[variable]
                )

            elif chart_type == "Área":

                st.area_chart(
                    df[variable]
                )

            else:

                st.bar_chart(
                    df[variable]
                )

            # ================================================
            # MÉTRICAS
            # ================================================

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Promedio",
                    f"{df[variable].mean():.2f} {unidades[variable]}"
                )

            with col2:

                st.metric(
                    "Máximo",
                    f"{df[variable].max():.2f} {unidades[variable]}"
                )

            with col3:

                st.metric(
                    "Mínimo",
                    f"{df[variable].min():.2f} {unidades[variable]}"
                )

            # ================================================
            # DATOS CRUDOS
            # ================================================

            if st.checkbox(
                "Mostrar datos crudos"
            ):

                st.dataframe(df)

        # ====================================================
        # TAB 2 — ESTADÍSTICAS
        # ====================================================

        with tab2:

            st.subheader(
                "📊 Estadísticas Descriptivas"
            )

            stats = df[variable].describe()

            st.dataframe(stats)

            st.subheader(
                "Distribución"
            )

            hist_values = np.histogram(
                df[variable],
                bins=20
            )[0]

            st.bar_chart(hist_values)

        # ====================================================
        # TAB 3 — FILTROS
        # ====================================================

        with tab3:

            st.subheader(
                "🔍 Filtrado de Datos"
            )

            min_value = float(
                df[variable].min()
            )

            max_value = float(
                df[variable].max()
            )

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

            st.dataframe(
                filtrado
            )

            csv = filtrado.to_csv().encode(
                'utf-8'
            )

            st.download_button(
                label="⬇️ Descargar CSV",
                data=csv,
                file_name='datos_filtrados.csv',
                mime='text/csv'
            )

        # ====================================================
        # TAB 4 — ANOMALÍAS
        # ====================================================

        with tab4:

            st.subheader(
                "⚠️ Detección de Anomalías"
            )

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

            st.line_chart(
                df[variable]
            )

            if len(anomalias) > 0:

                st.warning(
                    f"Se detectaron {len(anomalias)} anomalías."
                )

                st.dataframe(
                    anomalias
                )

            else:

                st.success(
                    "No se detectaron anomalías."
                )

        # ====================================================
        # TAB 5 — INFORMACIÓN
        # ====================================================

        with tab5:

            st.subheader(
                "🗺️ Información del Sitio"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.write(
                    "### 📍 Ubicación"
                )

                st.write(
                    "**Universidad EAFIT**"
                )

                st.write(
                    "- Medellín, Colombia"
                )

                st.write(
                    "- Latitud: 6.2006"
                )

                st.write(
                    "- Longitud: -75.5783"
                )

                st.write(
                    "- Altitud: 1495 msnm"
                )

            with col2:

                st.write(
                    "### ⚙️ Sensor"
                )

                st.write(
                    "- ESP32"
                )

                st.write(
                    "- Sensor LDR"
                )

                st.write(
                    "- InfluxDB Cloud"
                )

                st.write(
                    "- Streamlit"
                )

                st.write(
                    "- Monitoreo solar"
                )

        # ====================================================
        # RESUMEN SIDEBAR
        # ====================================================

        st.sidebar.markdown("---")

        st.sidebar.subheader(
            "📌 Resumen"
        )

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
            f"❌ Error al procesar archivo: {str(e)}"
        )

        st.info(
            "Verifique el formato del CSV exportado desde InfluxDB."
        )

# ============================================================
# SIN ARCHIVO
# ============================================================

else:

    st.warning(
        "⚠️ Cargue un archivo CSV para comenzar."
    )

# ============================================================
# FOOTER
# ============================================================

st.markdown("""
---
☀️ Sistema de monitoreo de luminosidad solar con ESP32 + LDR + InfluxDB + Streamlit  
📍 Universidad EAFIT — Medellín, Colombia
""")
