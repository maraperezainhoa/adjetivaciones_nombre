#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicación web con Streamlit para análisis de adjetivos musicales
Diseño elegante académico similar a musicologia.usal.es
"""

import streamlit as st
import re
import pandas as pd
from collections import defaultdict
import plotly.graph_objects as go
import PyPDF2
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
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
    
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a3a3a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2d5a5a'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    story.append(Paragraph("ANÁLISIS DE ADJETIVOS MUSICALES", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    story.append(Paragraph(f"<b>Nombre analizado:</b> {resultados['nombre'].title()}", info_style))
    story.append(Paragraph(f"<b>Fecha de generación:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", info_style))
    story.append(Spacer(1, 0.3*inch))
    
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
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d5a5a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("ADJETIVOS MUSICALES", heading_style))
    
    if adj_musicales:
        musicales_data = [['#', 'Adjetivo', 'Frecuencia']]
        for idx, (adj, freq) in enumerate(adj_musicales[:20], 1):
            musicales_data.append([str(idx), adj.title(), str(freq)])
        
        musicales_table = Table(musicales_data, colWidths=[0.5*inch, 3*inch, 1.5*inch])
        musicales_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b6f47')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(musicales_table)
    else:
        story.append(Paragraph("No se encontraron adjetivos musicales", info_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("ADJETIVOS FÍSICOS", heading_style))
    
    if adj_fisicos:
        fisicos_data = [['#', 'Adjetivo', 'Frecuencia']]
        for idx, (adj, freq) in enumerate(adj_fisicos[:20], 1):
            fisicos_data.append([str(idx), adj.title(), str(freq)])
        
        fisicos_table = Table(fisicos_data, colWidths=[0.5*inch, 3*inch, 1.5*inch])
        fisicos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6b5b4a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(fisicos_table)
    else:
        story.append(Paragraph("No se encontraron adjetivos físicos", info_style))
    
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

# ==================== CONFIGURACIÓN STREAMLIT ====================

st.set_page_config(
    page_title="Análisis de Adjetivos Musicales | USAL",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado - Diseño académico elegante
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital@0;1&family=Lora:wght@400;600;700&family=Playfair+Display:wght@700&display=swap');
    
    * {
        font-family: 'Lora', serif;
    }
    
    html, body, .main {
        background: linear-gradient(180deg, #fafaf8 0%, #f5f3f0 100%);
        color: #2c2c2c;
    }
    
    .stApp {
        background: transparent;
    }
    
    /* Header Principal */
    .header-container {
        background: linear-gradient(135deg, #1a3a3a 0%, #2d5a5a 100%);
        padding: 60px 40px;
        text-align: center;
        border-bottom: 4px solid #8b6f47;
        margin-bottom: 40px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .header-title {
        font-family: 'Playfair Display', serif;
        font-size: 48px;
        color: #f5f3f0;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        letter-spacing: 2px;
    }
    
    .header-subtitle {
        font-family: 'Crimson Text', serif;
        font-size: 22px;
        color: #d4c5b9;
        margin-top: 15px;
        font-style: italic;
        letter-spacing: 1px;
    }
    
    .header-divider {
        width: 100px;
        height: 3px;
        background: #8b6f47;
        margin: 20px auto;
    }
    
    /* Sidebar */
    .css-1d58n96 {
        background: linear-gradient(180deg, #f5f3f0 0%, #ede9e4 100%);
    }
    
    .sidebar-title {
        font-family: 'Playfair Display', serif;
        font-size: 24px;
        color: #1a3a3a;
        border-bottom: 2px solid #8b6f47;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    /* Secciones */
    .section-title {
        font-family: 'Playfair Display', serif;
        font-size: 32px;
        color: #1a3a3a;
        margin-top: 40px;
        margin-bottom: 25px;
        padding-bottom: 15px;
        border-bottom: 3px solid #8b6f47;
        letter-spacing: 1px;
    }
    
    .section-subtitle {
        font-family: 'Lora', serif;
        font-size: 18px;
        color: #2d5a5a;
        margin-bottom: 20px;
        font-weight: 600;
    }
    
    /* Métricas */
    .metric-card {
        background: white;
        border: 2px solid #e0d5cc;
        padding: 25px;
        border-radius: 3px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        border-color: #8b6f47;
    }
    
    .metric-label {
        font-family: 'Crimson Text', serif;
        font-size: 14px;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }
    
    .metric-value {
        font-family: 'Playfair Display', serif;
        font-size: 36px;
        color: #1a3a3a;
        font-weight: bold;
    }
    
    /* Info boxes */
    .info-box {
        background: #f0ebe4;
        border-left: 4px solid #8b6f47;
        padding: 20px;
        border-radius: 3px;
        margin: 15px 0;
        font-size: 16px;
    }
    
    .info-box-musical {
        border-left-color: #8b6f47;
        background: #fffbf5;
    }
    
    .info-box-fisico {
        border-left-color: #6b5b4a;
        background: #faf8f5;
    }
    
    /* Botones */
    .stButton > button {
        font-family: 'Lora', serif;
        font-size: 14px;
        background: #1a3a3a;
        color: #f5f3f0;
        border: none;
        padding: 12px 24px;
        border-radius: 3px;
        font-weight: 600;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        text-transform: uppercase;
    }
    
    .stButton > button:hover {
        background: #8b6f47;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .stButton > button[type="primary"] {
        background: #8b6f47;
    }
    
    .stButton > button[type="primary"]:hover {
        background: #6b5537;
    }
    
    /* Input */
    .stTextInput > div > div > input {
        font-family: 'Lora', serif;
        border: 2px solid #e0d5cc;
        border-radius: 3px;
        font-size: 16px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #8b6f47;
        box-shadow: 0 0 0 2px rgba(139, 111, 71, 0.1);
    }
    
    /* File uploader */
    .stFileUploader {
        background: #fffbf5;
        border: 2px dashed #d4c5b9;
        border-radius: 3px;
        padding: 20px;
    }
    
    /* DataFrames */
    .stDataFrame {
        font-family: 'Lora', serif;
    }
    
    /* Tables */
    table {
        background: white;
        border-collapse: collapse;
    }
    
    th {
        background: #2d5a5a;
        color: #f5f3f0;
        padding: 12px;
        font-weight: 600;
        text-align: center;
    }
    
    td {
        padding: 10px;
        border-bottom: 1px solid #e0d5cc;
    }
    
    tr:hover {
        background: #f5f3f0;
    }
    
    /* Expandable sections */
    .streamlit-expanderHeader {
        background: #f0ebe4;
        border: 1px solid #d4c5b9;
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: #2d5a5a;
        color: white;
    }
    
    .stDownloadButton > button:hover {
        background: #1a3a3a;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #999;
        font-size: 12px;
        margin-top: 60px;
        padding-top: 20px;
        border-top: 1px solid #e0d5cc;
        font-family: 'Crimson Text', serif;
    }
    
    /* Info y advertencias */
    .stAlert {
        background: #f0ebe4;
        border: 2px solid #d4c5b9;
        border-radius: 3px;
    }
    
    .stSuccess {
        background: #e8f5e9;
        border: 2px solid #8b6f47;
    }
    
    .stError {
        background: #ffebee;
        border: 2px solid #c62828;
    }
    
    /* Gráficos */
    .plotly-graph-div {
        background: white;
        border-radius: 3px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Search bar */
    .search-container {
        background: white;
        padding: 20px;
        border: 2px solid #e0d5cc;
        border-radius: 3px;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== HEADER ====================

st.markdown("""
    <div class="header-container">
        <h1 class="header-title">ANÁLISIS DE ADJETIVOS</h1>
        <p class="header-subtitle">Estudio semántico de descripciones en textos musicales</p>
        <div class="header-divider"></div>
    </div>
    """, unsafe_allow_html=True)

# ==================== SIDEBAR ====================

with st.sidebar:
    st.markdown("""
        <h2 class="sidebar-title">📁 Cargar Documentos</h2>
        """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Selecciona archivos (.txt o .pdf)",
        type=["txt", "pdf"],
        accept_multiple_files=True,
        help="Formatos soportados: TXT y PDF"
    )
    
    st.markdown("""
        <div style='background: #fffbf5; border-left: 4px solid #8b6f47; padding: 12px; margin-top: 15px; border-radius: 3px;'>
        <p style='margin: 0; font-size: 14px;'><strong>ℹ️ Formatos soportados:</strong></p>
        <p style='margin: 5px 0 0 0; font-size: 13px;'>• Archivos de texto (.txt)<br>• Documentos PDF</p>
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
                'Archivo': nombre,
                'Tipo': 'PDF' if file.type == 'application/pdf' else 'TXT',
                'Estado': '✅ Procesado'
            })
            procesados_exitosos += 1
        else:
            st.session_state.archivos_procesados.append({
                'Archivo': nombre,
                'Tipo': 'PDF' if file.type == 'application/pdf' else 'TXT',
                'Estado': '❌ Error'
            })
            procesados_fallidos += 1
    
    with st.sidebar:
        if procesados_exitosos > 0:
            st.success(f"✅ {procesados_exitosos} archivo(s) procesado(s)")
        
        if procesados_fallidos > 0:
            st.error(f"❌ {procesados_fallidos} archivo(s) con error")
        
        with st.expander("📊 Archivos cargados"):
            df_archivos = pd.DataFrame(st.session_state.archivos_procesados)
            st.dataframe(df_archivos, use_container_width=True, hide_index=True)
        
        if st.session_state.textos:
            with st.expander("📈 Estadísticas"):
                total_caracteres = sum(len(t) for t in st.session_state.textos)
                total_palabras = sum(len(t.split()) for t in st.session_state.textos)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Archivos", len(st.session_state.textos))
                    st.metric("Caracteres", f"{total_caracteres:,}")
                with col2:
                    st.metric("Palabras", f"{total_palabras:,}")

# ==================== MAIN CONTENT ====================

if st.session_state.textos:
    
    # Barra de búsqueda
    st.markdown('<h2 class="section-title">🔍 Búsqueda y Análisis</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        nombre_buscar = st.text_input(
            "Ingrese el nombre a analizar",
            placeholder="Ej: John, Lennon, David Bowie",
            label_visibility="collapsed"
        )
    
    with col2:
        buscar_btn = st.button("🔍 Buscar", use_container_width=True, type="primary")
    
    with col3:
        limpiar_btn = st.button("🗑️ Limpiar", use_container_width=True)
    
    if limpiar_btn:
        st.session_state.ultima_busqueda = None
        st.rerun()
    
    if nombre_buscar and buscar_btn:
        with st.spinner("Analizando documentos..."):
            resultados = buscar_nombre(st.session_state.textos, nombre_buscar)
        
        st.session_state.ultima_busqueda = resultados
    
    if st.session_state.ultima_busqueda:
        resultados = st.session_state.ultima_busqueda
        
        adj_musicales = sorted(resultados['adjetivos_musicales'].items(), 
                              key=lambda x: (-x[1], x[0]))
        adj_fisicos = sorted(resultados['adjetivos_fisicos'].items(), 
                            key=lambda x: (-x[1], x[0]))
        
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
        
        if resultados['ocurrencias'] == 0:
            st.error(f"No se encontraron resultados para '{resultados['nombre']}'")
        else:
            # Estadísticas
            st.markdown('<h2 class="section-title">📊 Resultados</h2>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("""
                    <div class="metric-card">
                        <div class="metric-label">Adjetivos Musicales</div>
                        <div class="metric-value">""" + str(total_musicales) + """</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                    <div class="metric-card">
                        <div class="metric-label">Adjetivos Físicos</div>
                        <div class="metric-value">""" + str(total_fisicos) + """</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col3:
                st.markdown("""
                    <div class="metric-card">
                        <div class="metric-label">Total</div>
                        <div class="metric-value">""" + str(total_adjetivos) + """</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col4:
                st.markdown("""
                    <div class="metric-card">
                        <div class="metric-label">Ratio M/F</div>
                        <div class="metric-value">""" + f"{ratio:.2f}x" + """</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Distribución
            st.markdown('<h2 class="section-title">📈 Distribución</h2>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                    <div class="info-box info-box-musical">
                        <strong>Adjetivos Musicales:</strong> {porcentaje_musicales:.1f}%
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class="info-box info-box-fisico">
                        <strong>Adjetivos Físicos:</strong> {porcentaje_fisicos:.1f}%
                    </div>
                    """, unsafe_allow_html=True)
            
            # Descargas
            st.markdown('<h2 class="section-title">📥 Descargar Resultados</h2>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                pdf_bytes = generar_pdf_resultados(
                    resultados, 
                    adj_musicales, 
                    adj_fisicos, 
                    ratio, 
                    porcentaje_musicales, 
                    porcentaje_fisicos
                )
                st.download_button(
                    "📄 Descargar PDF",
                    pdf_bytes,
                    f"analisis_{resultados['nombre'].replace(' ', '_')}.pdf",
                    "application/pdf",
                    use_container_width=True
                )
            
            with col2:
                df_musicales = pd.DataFrame(adj_musicales, columns=['Adjetivo', 'Frecuencia'])
                csv_m = df_musicales.to_csv(index=False)
                st.download_button(
                    "🎵 CSV Musicales",
                    csv_m,
                    f"musicales_{resultados['nombre'].replace(' ', '_')}.csv",
                    "text/csv",
                    use_container_width=True
                )
            
            with col3:
                df_fisicos = pd.DataFrame(adj_fisicos, columns=['Adjetivo', 'Frecuencia'])
                csv_f = df_fisicos.to_csv(index=False)
                st.download_button(
                    "👤 CSV Físicos",
                    csv_f,
                    f"fisicos_{resultados['nombre'].replace(' ', '_')}.csv",
                    "text/csv",
                    use_container_width=True
                )
            
            # Gráficos
            st.markdown('<h2 class="section-title">📊 Visualización</h2>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if adj_musicales:
                    st.markdown('<p class="section-subtitle">Adjetivos Musicales</p>', unsafe_allow_html=True)
                    
                    top_musicales = adj_musicales[:8]
                    labels_m = [adj[0].title() for adj in top_musicales]
                    values_m = [adj[1] for adj in top_musicales]
                    
                    fig_m = go.Figure(data=[go.Pie(
                        labels=labels_m,
                        values=values_m,
                        marker=dict(colors=['#8b6f47', '#a08060', '#b39579', '#c5a892', '#d4c5b9', '#ddd1c9', '#e5ddd7', '#ece6e1']),
                        hole=0.3,
                        textposition='inside',
                        textinfo='label+percent'
                    )])
                    fig_m.update_layout(
                        height=400,
                        showlegend=True,
                        font=dict(size=11, family='Lora, serif'),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(250,248,245,0)',
                        margin=dict(l=0, r=0, t=0, b=0)
                    )
                    st.plotly_chart(fig_m, use_container_width=True)
            
            with col2:
                if adj_fisicos:
                    st.markdown('<p class="section-subtitle">Adjetivos Físicos</p>', unsafe_allow_html=True)
                    
                    top_fisicos = adj_fisicos[:8]
                    labels_f = [adj[0].title() for adj in top_fisicos]
                    values_f = [adj[1] for adj in top_fisicos]
                    
                    fig_f = go.Figure(data=[go.Pie(
                        labels=labels_f,
                        values=values_f,
                        marker=dict(colors=['#6b5b4a', '#7d6d5c', '#8f7f6e', '#a09180', '#b1a392', '#c2b4a4', '#d3c5b6', '#e4d6c8']),
                        hole=0.3,
                        textposition='inside',
                        textinfo='label+percent'
                    )])
                    fig_f.update_layout(
                        height=400,
                        showlegend=True,
                        font=dict(size=11, family='Lora, serif'),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(250,248,245,0)',
                        margin=dict(l=0, r=0, t=0, b=0)
                    )
                    st.plotly_chart(fig_f, use_container_width=True)
            
            # Listados
            st.markdown('<h2 class="section-title">📋 Detalle de Resultados</h2>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<p class="section-subtitle">Adjetivos Musicales</p>', unsafe_allow_html=True)
                if adj_musicales:
                    df_musicales_display = pd.DataFrame(
                        [[adj[0].title(), adj[1]] for adj in adj_musicales],
                        columns=['Adjetivo', 'Frecuencia']
                    )
                    st.dataframe(df_musicales_display, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown('<p class="section-subtitle">Adjetivos Físicos</p>', unsafe_allow_html=True)
                if adj_fisicos:
                    df_fisicos_display = pd.DataFrame(
                        [[adj[0].title(), adj[1]] for adj in adj_fisicos],
                        columns=['Adjetivo', 'Frecuencia']
                    )
                    st.dataframe(df_fisicos_display, use_container_width=True, hide_index=True)

else:
    st.markdown("""
        <div style='text-align: center; padding: 60px 40px;'>
            <p style='font-family: Crimson Text, serif; font-size: 20px; color: #666; margin: 0;'>
                Comienza cargando documentos en la barra lateral
            </p>
            <p style='font-family: Lora, serif; font-size: 16px; color: #999; margin-top: 20px;'>
                Soporta archivos de texto (.txt) y PDF
            </p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("""
    <div class="footer">
        <p>Análisis de Adjetivos Musicales | Universidad de Salamanca</p>
        <p style='margin-top: 10px;'>© 2024 Departamento de Musicología</p>
    </div>
    """, unsafe_allow_html=True)
