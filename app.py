#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicación web con Streamlit para análisis de adjetivos musicales
Soporta archivos .txt y .pdf
Descarga de resultados en PDF y CSV
Despliegue: Streamlit Cloud
"""

import streamlit as st
import re
import pandas as pd
from collections import defaultdict
import plotly.graph_objects as go
import PyPDF2
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Adjetivos musicales
ADJETIVOS_MUSICALES = {
    'talentoso', 'virtuoso', 'brillante', 'genial', 'excepcional',
    'legendario', 'icónico', 'revolucionario', 'innovador', 'maestro',
    'consumado', 'experto', 'extraordinario', 'magnífico', 'sensacional',
    'aclamado', 'premiado', 'galardonado', 'influyente', 'destacado',
    'prodigioso', 'formidable', 'versátil', 'experimentado', 'renombrado',
    'visionario', 'audaz', 'intrépido', 'creativo', 'artístico', 'expresivo',
    'emocional', 'apasionado', 'intenso', 'profundo', 'conmovedor',
    'melódico', 'armónico', 'rítmico', 'técnico', 'sofisticado', 'refinado',
    'pulido', 'preciso', 'impecable', 'fluido', 'dinámico', 'energético',
    'poderoso', 'vibrante', 'resonante', 'vocal', 'agudo', 'profundo',
    'suave', 'potente', 'melodioso', 'armonioso', 'ritmado', 'modulado',
    'experimentador', 'innovante', 'revolucionante', 'transformador',
    'influyente', 'icónico', 'legendario', 'mítico', 'épico', 'trascendente'
}

# Adjetivos físicos
ADJETIVOS_FISICOS = {
    'guapo', 'hermoso', 'bello', 'bonito', 'atractivo', 'rubio', 'moreno',
    'alto', 'bajo', 'delgado', 'musculoso', 'joven', 'viejo', 'pálido',
    'radiante', 'bronceado', 'elegante', 'seductor', 'esbelto', 'grácil',
    'lindo', 'precioso', 'pelirrojo', 'trigueño', 'castaño', 'fornido',
    'deslumbrante', 'resplandeciente', 'reluciente', 'luminoso', 'corpulento',
    'robusto', 'ágil', 'estilizado', 'andrógino', 'exótico', 'atlético',
    'flexible', 'torpe', 'tosco', 'puro', 'carnoso', 'esquelético',
    'maduro', 'aniñado', 'rejuvenecido', 'femenino', 'masculino', 'morena',
    'peliblanco', 'canoso', 'calvo', 'velludo', 'suave', 'áspero',
    'juvenil', 'envejecido', 'corporal', 'físico', 'sexi', 'sexy',
    'carismático', 'magnético', 'cautivador', 'hipnotizante'
}

# ==================== FUNCIONES AUXILIARES ====================

def limpiar(texto):
    """Elimina puntuación."""
    return re.sub(r'[.,;:\'"´`]', '', texto).strip().lower()

def clasificar_adjetivo(palabra):
    """Clasifica una palabra como adjetivo musical, físico o neutral."""
    palabra_limpia = limpiar(palabra)
    
    if palabra_limpia in ADJETIVOS_MUSICALES:
        return 'Musical'
    elif palabra_limpia in ADJETIVOS_FISICOS:
        return 'Físico'
    return None

def extraer_texto_pdf(file):
    """Extrae texto de un archivo PDF."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        texto = ""
        
        for num_pagina, pagina in enumerate(pdf_reader.pages, 1):
            texto += f"\n--- Página {num_pagina} ---\n"
            texto += pagina.extract_text()
        
        return texto
    except Exception as e:
        return None

def procesar_archivo(file):
    """Procesa un archivo (txt o pdf) y devuelve su contenido."""
    nombre_archivo = file.name
    
    try:
        if file.type == "text/plain":
            texto = file.read().decode('utf-8', errors='ignore')
        elif file.type == "application/pdf":
            texto = extraer_texto_pdf(file)
            if texto is None:
                return None, nombre_archivo, False
        else:
            return None, nombre_archivo, False
        
        return texto, nombre_archivo, True
    
    except Exception as e:
        return None, nombre_archivo, False

def buscar_nombre(textos, nombre_busca):
    """Busca un nombre en los textos y encuentra adjetivos cercanos."""
    nombre_busca = nombre_busca.lower()
    resultados = {
        'nombre': nombre_busca,
        'ocurrencias': 0,
        'adjetivos_musicales': defaultdict(int),
        'adjetivos_fisicos': defaultdict(int),
    }
    
    for texto in textos:
        oraciones = re.split(r'[.!?\n]+', texto)
        
        for oracion in oraciones:
            oracion_lower = oracion.lower()
            palabras = oracion_lower.split()
            
            for idx, palabra in enumerate(palabras):
                palabra_limpia = limpiar(palabra)
                
                if nombre_busca in palabra_limpia or palabra_limpia in nombre_busca:
                    resultados['ocurrencias'] += 1
                    
                    ventana_inicio = max(0, idx - 5)
                    ventana_fin = min(len(palabras), idx + 6)
                    
                    for i in range(ventana_inicio, ventana_fin):
                        if i != idx:
                            categoria = clasificar_adjetivo(palabras[i])
                            
                            if categoria:
                                adjetivo_limpio = limpiar(palabras[i])
                                
                                if categoria == 'Musical':
                                    resultados['adjetivos_musicales'][adjetivo_limpio] += 1
                                else:
                                    resultados['adjetivos_fisicos'][adjetivo_limpio] += 1
    
    return resultados

def generar_pdf_resultados(resultados, adj_musicales, adj_fisicos, ratio, porcentaje_musicales, porcentaje_fisicos):
    """Genera un PDF con los resultados del análisis."""
    
    # Crear buffer de PDF
    pdf_buffer = io.BytesIO()
    
    # Crear documento PDF
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    story = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # Título
    story.append(Paragraph("🎵 ANÁLISIS DE ADJETIVOS MUSICALES", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Información general
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    story.append(Paragraph(f"<b>Nombre analizado:</b> {resultados['nombre'].title()}", info_style))
    story.append(Paragraph(f"<b>Fecha de generación:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", info_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Estadísticas principales
    story.append(Paragraph("ESTADÍSTICAS PRINCIPALES", heading_style))
    
    stats_data = [
        ['Métrica', 'Valor'],
        ['Adjetivos Musicales', str(len(adj_musicales))],
        ['Adjetivos Físicos', str(len(adj_fisicos))],
        ['Total Adjetivos', str(len(adj_musicales) + len(adj_fisicos))],
        ['Ratio M/F', f'{ratio:.2f}x'],
        ['% Musicales', f'{porcentaje_musicales:.1f}%'],
        ['% Físicos', f'{porcentaje_fisicos:.1f}%'],
    ]
    
    stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Adjetivos Musicales
    story.append(Paragraph("ADJETIVOS MUSICALES", heading_style))
    
    if adj_musicales:
        musicales_data = [['#', 'Adjetivo', 'Frecuencia']]
        for idx, (adj, freq) in enumerate(adj_musicales[:20], 1):
            musicales_data.append([str(idx), adj.title(), str(freq)])
        
        musicales_table = Table(musicales_data, colWidths=[0.5*inch, 3*inch, 1.5*inch])
        musicales_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e67e22')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff5e6')]),
        ]))
        story.append(musicales_table)
    else:
        story.append(Paragraph("No se encontraron adjetivos musicales", info_style))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Adjetivos Físicos
    story.append(Paragraph("ADJETIVOS FÍSICOS", heading_style))
    
    if adj_fisicos:
        fisicos_data = [['#', 'Adjetivo', 'Frecuencia']]
        for idx, (adj, freq) in enumerate(adj_fisicos[:20], 1):
            fisicos_data.append([str(idx), adj.title(), str(freq)])
        
        fisicos_table = Table(fisicos_data, colWidths=[0.5*inch, 3*inch, 1.5*inch])
        fisicos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5e6f5')]),
        ]))
        story.append(fisicos_table)
    else:
        story.append(Paragraph("No se encontraron adjetivos físicos", info_style))
    
    # Construir PDF
    doc.build(story)
    
    # Devolver buffer
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

# ==================== CONFIGURACIÓN STREAMLIT ====================

st.set_page_config(
    page_title="Análisis de Adjetivos Musicales",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    h1 {
        color: #667eea;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 18px;
        margin-bottom: 20px;
    }
    
    .metric-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin: 20px 0;
    }
    
    .stMetric {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .section-header {
        color: #667eea;
        font-size: 24px;
        font-weight: bold;
        margin-top: 30px;
        margin-bottom: 20px;
        border-bottom: 3px solid #667eea;
        padding-bottom: 10px;
    }
    
    .file-upload-info {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 12px;
        border-radius: 5px;
        margin-top: 10px;
    }
    
    .download-buttons {
        display: flex;
        gap: 10px;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== HEADER ====================

st.markdown("# 🎵 Análisis de Adjetivos Musicales")
st.markdown('<div class="subtitle">Descubre qué adjetivos se usan para describir a una persona en textos musicales</div>', unsafe_allow_html=True)
st.markdown("---")

# ==================== SIDEBAR ====================

st.sidebar.markdown("# 📁 Configuración")
st.sidebar.markdown("### Carga tus archivos")

uploaded_files = st.sidebar.file_uploader(
    "Selecciona archivos (.txt o .pdf)",
    type=["txt", "pdf"],
    accept_multiple_files=True,
    help="Puedes cargar varios archivos simultáneamente. Máximo 50MB por archivo."
)

# Información sobre formatos soportados
st.sidebar.markdown("""
    <div class='file-upload-info'>
    <strong>📄 Formatos soportados:</strong>
    <ul>
    <li>📝 Archivos .txt</li>
    <li>📕 Archivos .pdf</li>
    </ul>
    <p><small>Los PDFs se convierten automáticamente a texto.</small></p>
    </div>
    """, unsafe_allow_html=True)

# Variables de sesión
if 'textos' not in st.session_state:
    st.session_state.textos = []

if 'nombres_archivos' not in st.session_state:
    st.session_state.nombres_archivos = []

if 'ultima_busqueda' not in st.session_state:
    st.session_state.ultima_busqueda = None

if 'archivos_procesados' not in st.session_state:
    st.session_state.archivos_procesados = []

if uploaded_files:
    st.session_state.textos = []
    st.session_state.nombres_archivos = []
    st.session_state.archivos_procesados = []
    
    procesados_exitosos = 0
    procesados_fallidos = 0
    
    for file in uploaded_files:
        texto, nombre, exito = procesar_archivo(file)
        
        if exito:
            st.session_state.textos.append(texto)
            st.session_state.nombres_archivos.append(nombre)
            st.session_state.archivos_procesados.append({
                'nombre': nombre,
                'tipo': 'PDF' if file.type == 'application/pdf' else 'TXT',
                'estado': '✅ Procesado'
            })
            procesados_exitosos += 1
        else:
            st.session_state.archivos_procesados.append({
                'nombre': nombre,
                'tipo': 'PDF' if file.type == 'application/pdf' else 'TXT',
                'estado': '❌ Error'
            })
            procesados_fallidos += 1
    
    if procesados_exitosos > 0:
        st.sidebar.success(f"✅ {procesados_exitosos} archivo(s) procesado(s) correctamente")
    
    if procesados_fallidos > 0:
        st.sidebar.error(f"❌ {procesados_fallidos} archivo(s) con error")
    
    # Mostrar tabla de archivos procesados
    with st.sidebar.expander("📊 Archivos cargados"):
        df_archivos = pd.DataFrame(st.session_state.archivos_procesados)
        st.dataframe(df_archivos, use_container_width=True, hide_index=True)
    
    # Estadísticas de archivos
    if st.session_state.textos:
        with st.sidebar.expander("📈 Estadísticas"):
            total_caracteres = sum(len(t) for t in st.session_state.textos)
            total_palabras = sum(len(t.split()) for t in st.session_state.textos)
            total_lineas = sum(len(t.split('\n')) for t in st.session_state.textos)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📄 Archivos", len(st.session_state.textos))
                st.metric("📝 Caracteres", f"{total_caracteres:,}")
            with col2:
                st.metric("📚 Palabras", f"{total_palabras:,}")
                st.metric("📋 Líneas", f"{total_lineas:,}")

# ==================== MAIN CONTENT ====================

if st.session_state.textos:
    # Input de búsqueda
    st.markdown("### 🔍 Buscar Nombre")
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        nombre_buscar = st.text_input(
            "Nombre a analizar",
            placeholder="Ej: John, Lennon, David Bowie",
            help="Puedes buscar nombre, apellido o nombre completo",
            label_visibility="collapsed"
        )
    
    with col2:
        buscar_btn = st.button("🔍 Buscar", use_container_width=True, type="primary")
    
    with col3:
        limpiar_btn = st.button("🗑️ Limpiar", use_container_width=True)
    
    if limpiar_btn:
        st.session_state.ultima_busqueda = None
        nombre_buscar = ""
        st.rerun()
    
    if nombre_buscar and buscar_btn:
        with st.spinner("🔄 Analizando textos..."):
            resultados = buscar_nombre(st.session_state.textos, nombre_buscar)
        
        st.session_state.ultima_busqueda = resultados
    
    if st.session_state.ultima_busqueda:
        resultados = st.session_state.ultima_busqueda
        
        # Ordenar adjetivos
        adj_musicales = sorted(resultados['adjetivos_musicales'].items(), 
                              key=lambda x: (-x[1], x[0]))
        adj_fisicos = sorted(resultados['adjetivos_fisicos'].items(), 
                            key=lambda x: (-x[1], x[0]))
        
        # Calcular ratio
        total_musicales = len(adj_musicales)
        total_fisicos = len(adj_fisicos)
        total_adjetivos = total_musicales + total_fisicos
        
        if total_adjetivos > 0:
            ratio = total_musicales / total_fisicos if total_fisicos > 0 else total_musicales
            porcentaje_musicales = (total_musicales / total_adjetivos) * 100
            porcentaje_fisicos = (total_fisicos / total_adjetivos) * 100
        else:
            ratio = 0
            porcentaje_musicales = 0
            porcentaje_fisicos = 0
        
        # Resultados
        if resultados['ocurrencias'] == 0:
            st.error(f"❌ No se encontraron ocurrencias de '{resultados['nombre']}'")
        else:
            # Info bar con estadísticas
            st.markdown('<div class="section-header">📊 Estadísticas</div>', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🎵 Musicales", total_musicales)
            with col2:
                st.metric("👤 Físicos", total_fisicos)
            with col3:
                st.metric("📊 Total", total_adjetivos)
            with col4:
                st.metric("📈 Ratio M/F", f"{ratio:.2f}x")
            
            # Porcentajes
            st.markdown('<div class="section-header">📈 Distribución</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"🎵 **Adjetivos Musicales:** {porcentaje_musicales:.1f}%")
            with col2:
                st.info(f"👤 **Adjetivos Físicos:** {porcentaje_fisicos:.1f}%")
            
            # Botones de descarga
            st.markdown('<div class="section-header">📥 Descargar Resultados</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Descargar PDF
                pdf_bytes = generar_pdf_resultados(
                    resultados, 
                    adj_musicales, 
                    adj_fisicos, 
                    ratio, 
                    porcentaje_musicales, 
                    porcentaje_fisicos
                )
                st.download_button(
                    "📕 Descargar PDF",
                    pdf_bytes,
                    f"analisis_{resultados['nombre'].replace(' ', '_')}.pdf",
                    "application/pdf",
                    use_container_width=True
                )
            
            with col2:
                # Descargar CSV Musicales
                df_musicales = pd.DataFrame(adj_musicales, columns=['Adjetivo', 'Frecuencia'])
                csv_m = df_musicales.to_csv(index=False)
                st.download_button(
                    "🎵 Descargar CSV Musicales",
                    csv_m,
                    f"musicales_{resultados['nombre'].replace(' ', '_')}.csv",
                    "text/csv",
                    use_container_width=True
                )
            
            with col3:
                # Descargar CSV Físicos
                df_fisicos = pd.DataFrame(adj_fisicos, columns=['Adjetivo', 'Frecuencia'])
                csv_f = df_fisicos.to_csv(index=False)
                st.download_button(
                    "👤 Descargar CSV Físicos",
                    csv_f,
                    f"fisicos_{resultados['nombre'].replace(' ', '_')}.csv",
                    "text/csv",
                    use_container_width=True
                )
            
            st.markdown("---")
            
            # Gráficos circulares
            st.markdown('<div class="section-header">📊 Gráficos</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            
            with col1:
                if adj_musicales:
                    st.subheader("🎵 Adjetivos Musicales")
                    
                    # Top 8 para gráfico
                    top_musicales = adj_musicales[:8]
                    labels_m = [adj[0].title() for adj in top_musicales]
                    values_m = [adj[1] for adj in top_musicales]
                    
                    fig_m = go.Figure(data=[go.Pie(
                        labels=labels_m,
                        values=values_m,
                        marker=dict(colors=['#e67e22', '#d35400', '#f39c12', '#f1c40f',
                                           '#f8b739', '#e8a73f', '#da8e0d', '#c86300']),
                        hole=0.3,
                        textposition='inside',
                        textinfo='label+percent'
                    )])
                    fig_m.update_layout(
                        height=400,
                        showlegend=True,
                        font=dict(size=12)
                    )
                    st.plotly_chart(fig_m, use_container_width=True)
                else:
                    st.info("No se encontraron adjetivos musicales")
            
            with col2:
                if adj_fisicos:
                    st.subheader("👤 Adjetivos Físicos")
                    
                    # Top 8 para gráfico
                    top_fisicos = adj_fisicos[:8]
                    labels_f = [adj[0].title() for adj in top_fisicos]
                    values_f = [adj[1] for adj in top_fisicos]
                    
                    fig_f = go.Figure(data=[go.Pie(
                        labels=labels_f,
                        values=values_f,
                        marker=dict(colors=['#9b59b6', '#8e44ad', '#af7ac5', '#bb8fce',
                                           '#d2b4de', '#d7bde2', '#c39bd3', '#af7ac5']),
                        hole=0.3,
                        textposition='inside',
                        textinfo='label+percent'
                    )])
                    fig_f.update_layout(
                        height=400,
                        showlegend=True,
                        font=dict(size=12)
                    )
                    st.plotly_chart(fig_f, use_container_width=True)
                else:
                    st.info("No se encontraron adjetivos físicos")
            
            # Listado completo
            st.markdown('<div class="section-header">📋 Listado Completo</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🎵 Adjetivos Musicales")
                if adj_musicales:
                    df_musicales_display = pd.DataFrame(
                        [[adj[0].title(), adj[1]] for adj in adj_musicales],
                        columns=['Adjetivo', 'Frecuencia']
                    )
                    st.dataframe(df_musicales_display, use_container_width=True, hide_index=True)
                else:
                    st.info("No se encontraron adjetivos musicales")
            
            with col2:
                st.subheader("👤 Adjetivos Físicos")
                if adj_fisicos:
                    df_fisicos_display = pd.DataFrame(
                        [[adj[0].title(), adj[1]] for adj in adj_fisicos],
                        columns=['Adjetivo', 'Frecuencia']
                    )
                    st.dataframe(df_fisicos_display, use_container_width=True, hide_index=True)
                else:
                    st.info("No se encontraron adjetivos físicos")

else:
    st.markdown("---")
    st.info("👈 **Comienza cargando archivos .txt o .pdf en la barra lateral**")
    st.markdown("""
    ### 📝 Cómo usar esta aplicación:
    
    1. **📁 Carga tus archivos** de texto musicales en la barra lateral (pueden ser .txt o .pdf)
    2. **👤 Escribe el nombre** que quieres analizar (nombre, apellido o nombre completo)
    3. **🔍 Haz clic en Buscar** para ver los resultados
    
    ### 📊 Verás:
    - ✅ Cantidad de adjetivos musicales y físicos encontrados
    - ✅ Ratio de musicales vs físicos (ej: 2.5x)
    - ✅ Porcentajes de distribución
    - ✅ Gráficos circulares interactivos con los más comunes
    - ✅ Listados completos ordenados por frecuencia
    
    ### 📥 Descargas disponibles:
    - 📕 **PDF** con reporte completo
    - 📊 **CSV** con adjetivos musicales
    - 📊 **CSV** con adjetivos físicos
    
    ### 🎵 Ejemplos de búsqueda:
    - Busca un solo nombre: "John"
    - Busca un apellido: "Lennon"
    - Busca nombre completo: "John Lennon"
    - Prueba con diferentes artistas musicales
    """)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #999; font-size: 12px; margin-top: 30px;'>
    <p>🎵 Análisis de Adjetivos Musicales | Versión 2.0</p>
    <p>Con soporte para PDF y descarga de resultados</p>
    </div>
    """, unsafe_allow_html=True)
