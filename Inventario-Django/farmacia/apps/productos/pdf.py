# apps/productos/pdf.py
"""
Generación de reportes PDF con ReportLab.
Sistema de Gestión de Farmacia - TDEA 2025
"""

from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from django.utils import timezone
from django.db.models import F


def build_producto_pdf(producto):
    """Genera PDF individual de un producto (ficha técnica)"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Título
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "FICHA DE PRODUCTO")

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, height - 80, f"Código: {producto.codigo}")

    # Tabla de datos
    data = [
        ["Nombre", producto.nombre],
        ["Código", producto.codigo],
        ["Categoría", producto.categoria.nombre if producto.categoria else "Sin categoría"],
        ["Principio Activo", producto.principio_activo.nombre if producto.principio_activo else "N/A"],
        ["Laboratorio", producto.laboratorio.nombre if producto.laboratorio else "N/A"],
        ["Precio Compra", f"${producto.precio_compra:,.2f}"],
        ["Precio Venta", f"${producto.precio_venta:,.2f}"],
        ["Stock Actual", str(producto.stock_actual)],
        ["Stock Mínimo", str(producto.stock_minimo)],
        # ✅ CORRECCIÓN: bajo_stock SIN paréntesis (es @property)
        ["Estado Stock", "⚠️ BAJO STOCK" if producto.bajo_stock else "✅ Normal"],
        ["Fecha Registro", timezone.localtime(producto.fecha_creacion).strftime("%d/%m/%Y %H:%M")],
    ]

    table = Table(data, colWidths=[5*cm, 10*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        # ✅ CORRECCIÓN: bajo_stock SIN paréntesis
        ('BACKGROUND', (0, 9), (1, 9), colors.red if producto.bajo_stock else colors.lightgreen),
        ('TEXTCOLOR', (0, 9), (1, 9), colors.white),
    ]))

    table.wrapOn(p, width, height)
    table.drawOn(p, 50, height - 400)

    # Pie de página
    p.setFont("Helvetica", 9)
    p.drawString(50, 50, f"Generado el {timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer


def build_todos_productos_pdf(productos):
    """Genera catálogo completo de productos en PDF"""
    buffer = BytesIO()
    
    # Configuración del documento con márgenes
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    elements = []
    styles = getSampleStyleSheet()

    # Título
    title = Paragraph("CATÁLOGO COMPLETO DE PRODUCTOS - FARMACIA", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.5*cm))

    # Fecha
    fecha_str = timezone.localtime(timezone.now()).strftime('%d de %B de %Y - %H:%M')
    elements.append(Paragraph(f"Fecha de generación: {fecha_str}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    # Encabezados de tabla
    data = [[
        "Código", "Nombre", "Categoría", "Lab.", "P. Compra", "P. Venta", "Stock", "Mínimo", "Estado"
    ]]

    # Estilos base de la tabla
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    bajos_stock_count = 0

    for i, prod in enumerate(productos):
        row_idx = i + 1
        # ✅ CORRECCIÓN: bajo_stock SIN paréntesis (es @property)
        estado = "⚠️ BAJO" if prod.bajo_stock else "✅ OK"
        
        if prod.bajo_stock:
            bajos_stock_count += 1
            # Resaltar fila completa si hay bajo stock
            style_cmds.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor("#ffcccc")))
        elif row_idx % 2 == 0:
            # Efecto cebra para filas normales
            style_cmds.append(('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor("#f8f9fa")))

        data.append([
            prod.codigo,
            prod.nombre[:25] + "..." if len(prod.nombre) > 25 else prod.nombre,
            prod.categoria.nombre[:15] if prod.categoria else "-",
            prod.laboratorio.nombre[:10] if prod.laboratorio else "-",
            f"${prod.precio_compra:,.0f}",
            f"${prod.precio_venta:,.0f}",
            str(prod.stock_actual),
            str(prod.stock_minimo),
            estado
        ])

    # Definición de anchos de columna optimizados para A4
    col_widths = [1.8*cm, 4.0*cm, 2.2*cm, 1.8*cm, 1.8*cm, 1.8*cm, 1.2*cm, 1.2*cm, 1.5*cm]

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle(style_cmds))

    elements.append(table)
    elements.append(Spacer(1, 1*cm))

    # Totales
    elements.append(Paragraph(f"<b>Total de productos:</b> {productos.count()}", styles['Normal']))
    elements.append(Paragraph(f"<b>Productos con bajo stock:</b> <font color='red'>{bajos_stock_count}</font>", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def build_movimiento_pdf(movimiento):
    """PDF individual de un movimiento"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, height - 60, f"MOVIMIENTO DE INVENTARIO #{movimiento.id}")

    usuario_nombre = movimiento.usuario.get_full_name() if movimiento.usuario else "Sistema"
    if not usuario_nombre or usuario_nombre.strip() == "":
        usuario_nombre = movimiento.usuario.username if movimiento.usuario else "Sistema"

    data = [
        ["Tipo", movimiento.get_tipo_display()],
        ["Fecha y Hora", timezone.localtime(movimiento.fecha).strftime("%d/%m/%Y %H:%M")],
        ["Producto", movimiento.producto.nombre],
        ["Código", movimiento.producto.codigo],
        ["Cantidad", str(movimiento.cantidad)],
        ["Motivo", movimiento.motivo or "Sin especificar"],
        ["Realizado por", usuario_nombre],
    ]

    table = Table(data, colWidths=[6*cm, 10*cm])
    
    # Color según tipo de movimiento
    color_fondo = colors.lightgreen if movimiento.tipo == 'entrada' else colors.HexColor("#ffebee")
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#34495e")),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (1, 0), (1, -1), color_fondo),
    ]))

    table.wrapOn(p, width, height)
    table.drawOn(p, 60, height - 300)

    # Pie de página
    p.setFont("Helvetica", 9)
    p.drawString(50, 50, f"Generado el {timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer


def build_todos_movimientos_pdf(movimientos):
    """PDF con todos los movimientos del día o filtrados"""
    buffer = BytesIO()
    
    # Usamos SimpleDocTemplate para un diseño flexible y profesional que maneja paginación
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Título y Encabezado
    title = Paragraph("REPORTE COMPLETO DE MOVIMIENTOS", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.5*cm))
    
    fecha_str = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
    elements.append(Paragraph(f"Generado: {fecha_str}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    data = [["ID", "Fecha", "Tipo", "Producto", "Cód.", "Cant.", "Usuario", "Motivo"]]
    
    for m in movimientos:
        usuario = m.usuario.username if m.usuario else "Sistema"
        # Truncar textos largos para mantener la tabla ordenada
        prod_nombre = m.producto.nombre[:20] + "..." if len(m.producto.nombre) > 20 else m.producto.nombre
        motivo = (m.motivo or "")[:25] + "..." if m.motivo and len(m.motivo) > 25 else (m.motivo or "-")
        
        data.append([
            str(m.id),
            timezone.localtime(m.fecha).strftime("%d/%m %H:%M"),
            m.get_tipo_display(),
            prod_nombre,
            m.producto.codigo,
            str(m.cantidad),
            usuario,
            motivo,
        ])

    # Anchos optimizados para A4 (Total ~19cm)
    col_widths = [1.2*cm, 2.5*cm, 2.0*cm, 4.5*cm, 2.0*cm, 1.5*cm, 2.5*cm, 3.0*cm]
    
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]), # Efecto cebra
    ]))

    elements.append(table)
    elements.append(Spacer(1, 1*cm))
    
    # Totales al final
    elements.append(Paragraph(f"<b>Total movimientos:</b> {movimientos.count()}", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer