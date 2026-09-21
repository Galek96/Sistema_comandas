import sys
import os
import sqlite3
import csv
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, 
                             QHeaderView, QSpinBox, QDoubleSpinBox, QTabWidget, QGroupBox, QFormLayout,
                             QAbstractItemView, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QTextDocument

# Temas Claro / Oscuro
LIGHT_THEME = """
QMainWindow { background-color: #F8FAFC; }
QLabel { font-size: 13px; color: #1E293B; font-weight: 500; }
QGroupBox { font-weight: bold; border: 1px solid #CBD5E1; border-radius: 8px; margin-top: 10px; background-color: #FFFFFF; padding: 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #0F172A; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { padding: 6px; border: 1px solid #CBD5E1; border-radius: 5px; background-color: #F1F5F9; font-size: 13px; color: #0F172A; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #2563EB; background-color: #FFFFFF; }
QPushButton { padding: 8px 12px; border-radius: 6px; font-weight: bold; font-size: 12px; color: white; background-color: #2563EB; border: none; }
QPushButton:hover { background-color: #1D4ED8; }
QPushButton#btn_danger { background-color: #EF4444; }
QPushButton#btn_danger:hover { background-color: #DC2626; }
QPushButton#btn_success { background-color: #10B981; }
QPushButton#btn_success:hover { background-color: #059669; }
QPushButton#btn_warning { background-color: #F59E0B; }
QPushButton#btn_warning:hover { background-color: #D97706; }
QPushButton#btn_toggle_theme { background-color: #64748B; padding: 4px 8px; font-size: 11px; }
QTableWidget { background-color: #FFFFFF; border: 1px solid #E2E8F0; gridline-color: #E2E8F0; color: #0F172A; }
QHeaderView::section { background-color: #1E293B; color: white; font-weight: bold; padding: 6px; border: none; }
"""

DARK_THEME = """
QMainWindow { background-color: #0F172A; }
QLabel { font-size: 13px; color: #F8FAFC; font-weight: 500; }
QGroupBox { font-weight: bold; border: 1px solid #334155; border-radius: 8px; margin-top: 10px; background-color: #1E293B; padding: 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #F8FAFC; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { padding: 6px; border: 1px solid #475569; border-radius: 5px; background-color: #334155; font-size: 13px; color: #F8FAFC; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid #3B82F6; background-color: #1E293B; }
QPushButton { padding: 8px 12px; border-radius: 6px; font-weight: bold; font-size: 12px; color: white; background-color: #3B82F6; border: none; }
QPushButton:hover { background-color: #2563EB; }
QPushButton#btn_danger { background-color: #EF4444; }
QPushButton#btn_danger:hover { background-color: #DC2626; }
QPushButton#btn_success { background-color: #10B981; }
QPushButton#btn_success:hover { background-color: #059669; }
QPushButton#btn_warning { background-color: #F59E0B; }
QPushButton#btn_warning:hover { background-color: #D97706; }
QPushButton#btn_toggle_theme { background-color: #475569; padding: 4px 8px; font-size: 11px; }
QTableWidget { background-color: #1E293B; border: 1px solid #334155; gridline-color: #334155; color: #F8FAFC; }
QHeaderView::section { background-color: #020617; color: white; font-weight: bold; padding: 6px; border: none; }
"""

CATEGORIAS_MODULOS = [
    "Bebestibles",
    "Bebidas Calientes",
    "Menús",
    "Platos Preparados",
    "Postres",
    "Tragos",
    "Otros"
]

class SistemaCasinoProfesional(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema POS Casino Pro - Gestión de Stock y Rentabilidad")
        self.resize(1300, 820)
        
        self.es_modo_noche = False
        self.setStyleSheet(LIGHT_THEME)
        
        self.carrito = [] 
        self.producto_seleccionado = None
        self.producto_id_edicion = None  # Para controlar la edición de producto
        self.tablas_categoria = {}
        
        self.init_db()
        self.init_ui()

    def init_db(self):
        self.conn = sqlite3.connect("casino_profesional.db")
        self.cursor = self.conn.cursor()
        
        # 1. Menú de Productos a la venta
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            categoria TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'Disponible'
        )''')

        # 2. Insumos / Materia Prima en Bodega
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS insumos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            unidad_medida TEXT NOT NULL,
            stock_actual REAL NOT NULL,
            stock_minimo REAL DEFAULT 5.0,
            costo_unidad_proveedor REAL DEFAULT 0.0,
            proveedor TEXT DEFAULT 'General'
        )''')

        # 3. Recetas (Relación Producto <-> Insumos con Gramaje Requerido)
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS recetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            insumo_id INTEGER NOT NULL,
            cantidad_requerida REAL NOT NULL,
            FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
            FOREIGN KEY (insumo_id) REFERENCES insumos(id) ON DELETE CASCADE
        )''')

        # 4. Ventas Generales
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_mesa TEXT,
            total REAL,
            medio_pago TEXT,
            fecha TEXT
        )''')

        # 5. Detalle de Ventas
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS detalle_ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER,
            producto TEXT,
            cantidad INTEGER,
            subtotal REAL,
            FOREIGN KEY (venta_id) REFERENCES ventas(id)
        )''')
        
        self.conn.commit()
        self.poblar_datos_iniciales()

    def poblar_datos_iniciales(self):
        self.cursor.execute("SELECT COUNT(*) FROM insumos")
        if self.cursor.fetchone()[0] == 0:
            insumos_demo = [
                ('Carne Molida', 'Kg', 15.0, 3.0, 6500.0, 'Distribuidora Carnes SA'),
                ('Papas Prefritas', 'Kg', 20.0, 5.0, 2200.0, 'Congelados del Sur'),
                ('Pan de Hamburguesa', 'Unidades', 50.0, 10.0, 350.0, 'Panadería Central'),
                ('Huevos', 'Unidades', 60.0, 12.0, 180.0, 'Avícola Santa Rosa'),
                ('Café en Grano', 'Kg', 8.0, 2.0, 14000.0, 'Tostaduría Gourmet'),
                ('Leche Entera', 'Lt', 25.0, 5.0, 1050.0, 'Lácteos del Valle'),
                ('Bebida Cordon 350ml', 'Unidades', 40.0, 10.0, 650.0, 'Embotelladora Andina'),
                ('Cerveza Lata 350ml', 'Unidades', 30.0, 6.0, 900.0, 'CCU')
            ]
            self.cursor.executemany("""
                INSERT INTO insumos (nombre, unidad_medida, stock_actual, stock_minimo, costo_unidad_proveedor, proveedor) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, insumos_demo)
            self.conn.commit()

        self.cursor.execute("SELECT COUNT(*) FROM productos")
        if self.cursor.fetchone()[0] == 0:
            prods_demo = [
                ('Lomo a lo Pobre', 8500, 'Platos Preparados', 'Disponible'),
                ('Hamburguesa Italiana', 6500, 'Platos Preparados', 'Disponible'),
                ('Cappuccino Grande', 2500, 'Bebidas Calientes', 'Disponible'),
                ('Bebida 350ml', 1500, 'Bebestibles', 'Disponible'),
                ('Cerveza Artesanal', 3500, 'Tragos', 'Disponible'),
                ('Pie de Limón', 2500, 'Postres', 'Disponible')
            ]
            self.cursor.executemany("INSERT INTO productos (nombre, precio, categoria, estado) VALUES (?, ?, ?, ?)", prods_demo)
            self.conn.commit()

        self.cursor.execute("SELECT COUNT(*) FROM recetas")
        if self.cursor.fetchone()[0] == 0:
            recetas_demo = [
                (1, 1, 0.250), # Lomo a lo Pobre -> 0.250 kg carne
                (1, 2, 0.300), # Lomo a lo Pobre -> 0.300 kg papas
                (1, 4, 2.0),   # Lomo a lo Pobre -> 2 huevos
                (2, 1, 0.150), # Hamburguesa -> 0.150 kg carne
                (2, 3, 1.0),   # Hamburguesa -> 1 pan
                (3, 5, 0.018), # Cappuccino -> 0.018 kg café
                (3, 6, 0.200), # Cappuccino -> 0.200 lt leche
                (4, 7, 1.0),   # Bebida -> 1 unid bebida
                (5, 8, 1.0)    # Cerveza -> 1 unid cerveza
            ]
            self.cursor.executemany("INSERT INTO recetas (producto_id, insumo_id, cantidad_requerida) VALUES (?, ?, ?)", recetas_demo)
            self.conn.commit()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        lbl_titulo = QLabel("🍽️ CASINO POS - PANEL DE CONTROL Y GESTIÓN DE STOCK")
        lbl_titulo.setFont(QFont("Arial", 14, QFont.Bold))
        
        self.btn_theme = QPushButton("🌙 Modo Noche")
        self.btn_theme.setObjectName("btn_toggle_theme")
        self.btn_theme.clicked.connect(self.toggle_theme)

        header_layout.addWidget(lbl_titulo)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_theme)
        
        main_layout.addLayout(header_layout)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.crear_pestaña_ventas(), "📝 Punto de Venta (POS)")
        self.tabs.addTab(self.crear_pestaña_caja(), "📊 Ventas del Día / Caja")
        self.tabs.addTab(self.crear_pestaña_bodega(), "📦 Planilla de Bodega e Insumos")
        self.tabs.addTab(self.crear_pestaña_ganancias(), "📈 Análisis de Ganancias y Margen")
        self.tabs.addTab(self.crear_pestaña_productos(), "🍔 Menú y Productos")
        self.tabs.addTab(self.crear_pestaña_recetas(), "🍳 Gestión de Recetas")
        
        main_layout.addWidget(self.tabs)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.actualizar_todo()

    def toggle_theme(self):
        self.es_modo_noche = not self.es_modo_noche
        if self.es_modo_noche:
            self.setStyleSheet(DARK_THEME)
            self.btn_theme.setText("☀️ Modo Día")
        else:
            self.setStyleSheet(LIGHT_THEME)
            self.btn_theme.setText("🌙 Modo Noche")

    # --- PESTAÑA 1: POS MÓDULOS ---
    def crear_pestaña_ventas(self):
        widget = QWidget()
        layout = QHBoxLayout()

        left_box = QGroupBox("Catálogo por Módulos")
        left_layout = QVBoxLayout()

        self.tabs_modulos = QTabWidget()
        for cat in CATEGORIAS_MODULOS:
            tabla = QTableWidget()
            tabla.setColumnCount(3)
            tabla.setHorizontalHeaderLabels(["ID", "Producto", "Precio"])
            tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
            tabla.itemClicked.connect(self.al_seleccionar_producto_tabla)
            
            self.tablas_categoria[cat] = tabla
            self.tabs_modulos.addTab(tabla, cat)

        form_agregar = QFormLayout()
        self.lbl_prod_seleccionado = QLabel("Ninguno seleccionado")
        self.lbl_prod_seleccionado.setFont(QFont("Arial", 11, QFont.Bold))
        
        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setMinimum(1)
        self.spin_cantidad.setMaximum(100)

        form_agregar.addRow("Producto Seleccionado:", self.lbl_prod_seleccionado)
        form_agregar.addRow("Cantidad:", self.spin_cantidad)

        btn_agregar = QPushButton("➕ Agregar al Carrito")
        btn_agregar.setObjectName("btn_success")
        btn_agregar.clicked.connect(self.agregar_al_carrito)

        left_layout.addWidget(self.tabs_modulos)
        left_layout.addLayout(form_agregar)
        left_layout.addWidget(btn_agregar)
        left_box.setLayout(left_layout)

        right_box = QGroupBox("Comanda Actual")
        right_layout = QVBoxLayout()

        info_layout = QHBoxLayout()
        self.input_cliente = QLineEdit()
        self.input_cliente.setPlaceholderText("Mesa / Cliente / Alumno")
        
        self.combo_pago = QComboBox()
        self.combo_pago.addItems(["Efectivo", "Débito/Crédito", "Transferencia", "Cuenta Corriente"])

        info_layout.addWidget(QLabel("Cliente/Mesa:"))
        info_layout.addWidget(self.input_cliente)
        info_layout.addWidget(QLabel("Medio de Pago:"))
        info_layout.addWidget(self.combo_pago)

        self.tabla_carrito = QTableWidget()
        self.tabla_carrito.setColumnCount(4)
        self.tabla_carrito.setHorizontalHeaderLabels(["Producto", "Cant.", "P. Unit", "Subtotal"])
        self.tabla_carrito.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_carrito.setSelectionBehavior(QAbstractItemView.SelectRows)

        total_layout = QHBoxLayout()
        self.lbl_total = QLabel("TOTAL: $0")
        self.lbl_total.setFont(QFont("Arial", 15, QFont.Bold))
        
        btn_quitar = QPushButton("❌ Quitar Seleccionado")
        btn_quitar.setObjectName("btn_danger")
        btn_quitar.clicked.connect(self.quitar_del_carrito)

        total_layout.addWidget(self.lbl_total)
        total_layout.addStretch()
        total_layout.addWidget(btn_quitar)

        btn_procesar = QPushButton("🖨️ IMPRIMIR Y PROCESAR COMANDA")
        btn_procesar.setFont(QFont("Arial", 11, QFont.Bold))
        btn_procesar.setMinimumHeight(40)
        btn_procesar.setObjectName("btn_success")
        btn_procesar.clicked.connect(self.procesar_comanda)

        right_layout.addLayout(info_layout)
        right_layout.addWidget(self.tabla_carrito)
        right_layout.addLayout(total_layout)
        right_layout.addWidget(btn_procesar)
        right_box.setLayout(right_layout)

        layout.addWidget(left_box, 3)
        layout.addWidget(right_box, 2)
        widget.setLayout(layout)
        return widget

    def cargar_tablas_modulos_pos(self):
        for cat in CATEGORIAS_MODULOS:
            tabla = self.tablas_categoria[cat]
            self.cursor.execute("SELECT id, nombre, precio FROM productos WHERE categoria = ? AND estado = 'Disponible'", (cat,))
            prods = self.cursor.fetchall()
            
            tabla.setRowCount(len(prods))
            for f_idx, (p_id, nombre, precio) in enumerate(prods):
                tabla.setItem(f_idx, 0, QTableWidgetItem(str(p_id)))
                tabla.setItem(f_idx, 1, QTableWidgetItem(nombre))
                tabla.setItem(f_idx, 2, QTableWidgetItem(f"${precio:,.0f}"))

    def al_seleccionar_producto_tabla(self, item):
        tabla = item.tableWidget()
        fila = item.row()
        p_id = int(tabla.item(fila, 0).text())
        p_nombre = tabla.item(fila, 1).text()
        p_precio_str = tabla.item(fila, 2).text().replace("$", "").replace(".", "").replace(",", "")
        p_precio = float(p_precio_str)

        self.producto_seleccionado = (p_id, p_nombre, p_precio)
        self.lbl_prod_seleccionado.setText(f"{p_nombre} (${p_precio:,.0f})")

    # --- PESTAÑA 2: CAJA ---
    def crear_pestaña_caja(self):
        widget = QWidget()
        layout = QVBoxLayout()

        box_resumen = QGroupBox("Arqueo de Caja del Día")
        resumen_layout = QHBoxLayout()

        self.lbl_caja_total = QLabel("Total Día: $0")
        self.lbl_caja_total.setFont(QFont("Arial", 11, QFont.Bold))
        
        self.lbl_caja_efectivo = QLabel("Efectivo: $0")
        self.lbl_caja_tarjeta = QLabel("Débito/Crédito: $0")
        self.lbl_caja_transf = QLabel("Transferencia: $0")

        resumen_layout.addWidget(self.lbl_caja_total)
        resumen_layout.addWidget(self.lbl_caja_efectivo)
        resumen_layout.addWidget(self.lbl_caja_tarjeta)
        resumen_layout.addWidget(self.lbl_caja_transf)
        box_resumen.setLayout(resumen_layout)

        box_historial = QGroupBox("Historial de Comandas")
        h_layout = QVBoxLayout()

        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(5)
        self.tabla_historial.setHorizontalHeaderLabels(["N° Folio", "Cliente / Mesa", "Total", "Medio Pago", "Fecha / Hora"])
        self.tabla_historial.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        btn_exportar = QPushButton("📥 Exportar Ventas a CSV")
        btn_exportar.setObjectName("btn_success")
        btn_exportar.clicked.connect(self.exportar_a_csv)

        h_layout.addWidget(self.tabla_historial)
        h_layout.addWidget(btn_exportar)
        box_historial.setLayout(h_layout)

        layout.addWidget(box_resumen)
        layout.addWidget(box_historial)
        widget.setLayout(layout)
        return widget

    # --- PESTAÑA 3: BODEGA ---
    def crear_pestaña_bodega(self):
        widget = QWidget()
        layout = QHBoxLayout()

        box_form = QGroupBox("Registro de Insumo / Entrada Proveedor")
        form_layout = QFormLayout()

        self.input_insumo_nombre = QLineEdit()
        self.combo_insumo_unidad = QComboBox()
        self.combo_insumo_unidad.addItems(["Kg", "Gramos", "Lt", "Cc", "Unidades", "Cajas", "Paquetes"])
        
        self.input_insumo_stock = QDoubleSpinBox()
        self.input_insumo_stock.setMaximum(99999.0)
        
        self.input_insumo_costo = QDoubleSpinBox()
        self.input_insumo_costo.setMaximum(9999999.0)
        
        self.input_insumo_min = QDoubleSpinBox()
        self.input_insumo_min.setValue(5.0)

        self.input_insumo_prov = QLineEdit()
        self.input_insumo_prov.setPlaceholderText("Ej: Distribuidora Carnes SA")

        form_layout.addRow("Insumo / Materia Prima:", self.input_insumo_nombre)
        form_layout.addRow("Unidad de Medida/Gramaje:", self.combo_insumo_unidad)
        form_layout.addRow("Stock en Bodega:", self.input_insumo_stock)
        form_layout.addRow("Costo Unit. Proveedor ($):", self.input_insumo_costo)
        form_layout.addRow("Stock Mínimo (Alerta):", self.input_insumo_min)
        form_layout.addRow("Proveedor / Distribuidor:", self.input_insumo_prov)

        btn_guardar_insumo = QPushButton("💾 Registrar / Actualizar Insumo")
        btn_guardar_insumo.setObjectName("btn_success")
        btn_guardar_insumo.clicked.connect(self.guardar_insumo)

        v_layout = QVBoxLayout()
        v_layout.addLayout(form_layout)
        v_layout.addWidget(btn_guardar_insumo)
        v_layout.addStretch()
        box_form.setLayout(v_layout)

        box_tabla = QGroupBox("Planilla de Control de Bodega (Rojo = Stock Crítico)")
        t_layout = QVBoxLayout()

        self.tabla_insumos = QTableWidget()
        self.tabla_insumos.setColumnCount(7)
        self.tabla_insumos.setHorizontalHeaderLabels(["ID", "Insumo", "Unidad", "Stock Actual", "Costo Prov.", "Stock Mín.", "Proveedor"])
        self.tabla_insumos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_insumos.setSelectionBehavior(QAbstractItemView.SelectRows)

        btn_eliminar_ins = QPushButton("🗑️ Eliminar Insumo")
        btn_eliminar_ins.setObjectName("btn_danger")
        btn_eliminar_ins.clicked.connect(self.eliminar_insumo)

        t_layout.addWidget(self.tabla_insumos)
        t_layout.addWidget(btn_eliminar_ins)
        box_tabla.setLayout(t_layout)

        layout.addWidget(box_form, 1)
        layout.addWidget(box_tabla, 2)
        widget.setLayout(layout)
        return widget

    # --- PESTAÑA 4: GANANCIAS ---
    def crear_pestaña_ganancias(self):
        widget = QWidget()
        layout = QVBoxLayout()

        box_info = QGroupBox("Rentabilidad y Márgenes por Producto (Calculado según Costo de Receta / Insumos)")
        v_layout = QVBoxLayout()

        self.tabla_ganancias = QTableWidget()
        self.tabla_ganancias.setColumnCount(6)
        self.tabla_ganancias.setHorizontalHeaderLabels(["ID", "Producto / Plato", "Costo Receta ($)", "Precio Venta ($)", "Ganancia Neta ($)", "Margen (%)"])
        self.tabla_ganancias.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        btn_recargar_ganancias = QPushButton("🔄 Recalcular Márgenes y Costos")
        btn_recargar_ganancias.setObjectName("btn_warning")
        btn_recargar_ganancias.clicked.connect(self.cargar_tabla_ganancias)

        v_layout.addWidget(self.tabla_ganancias)
        v_layout.addWidget(btn_recargar_ganancias)
        box_info.setLayout(v_layout)

        layout.addWidget(box_info)
        widget.setLayout(layout)
        return widget

    # --- PESTAÑA 5: PRODUCTOS Y MENÚ (EDITABLE DIRECTO Y CON FORMULARIO) ---
    def crear_pestaña_productos(self):
        widget = QWidget()
        layout = QHBoxLayout()

        box_form = QGroupBox("Formulario de Producto")
        form_layout = QFormLayout()

        self.input_prod_nombre = QLineEdit()
        self.input_prod_precio = QLineEdit()
        self.combo_prod_cat = QComboBox()
        self.combo_prod_cat.addItems(CATEGORIAS_MODULOS)

        form_layout.addRow("Nombre Producto:", self.input_prod_nombre)
        form_layout.addRow("Precio Venta ($):", self.input_prod_precio)
        form_layout.addRow("Módulo / Categoría:", self.combo_prod_cat)

        self.btn_guardar_prod = QPushButton("💾 Guardar / Actualizar Producto")
        self.btn_guardar_prod.setObjectName("btn_success")
        self.btn_guardar_prod.clicked.connect(self.guardar_producto)

        btn_limpiar_prod = QPushButton("➕ Limpiar para Nuevo Producto")
        btn_limpiar_prod.setObjectName("btn_warning")
        btn_limpiar_prod.clicked.connect(self.limpiar_form_producto)

        v_layout = QVBoxLayout()
        v_layout.addLayout(form_layout)
        v_layout.addWidget(self.btn_guardar_prod)
        v_layout.addWidget(btn_limpiar_prod)
        v_layout.addStretch()
        box_form.setLayout(v_layout)

        box_tabla = QGroupBox("Productos en Menú (Doble Clic en Celda para Editar)")
        t_layout = QVBoxLayout()

        self.tabla_productos = QTableWidget()
        self.tabla_productos.setColumnCount(5)
        self.tabla_productos.setHorizontalHeaderLabels(["ID", "Producto", "Precio", "Categoría", "Estado"])
        self.tabla_productos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_productos.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Conectar selección y cambios directos en celdas
        self.tabla_productos.itemClicked.connect(self.al_seleccionar_producto_edicion)
        self.tabla_productos.itemChanged.connect(self.al_editar_celda_producto)

        btn_layout = QHBoxLayout()
        btn_toggle_estado = QPushButton("🔄 Cambiar Estado (Disponible/Agotado)")
        btn_toggle_estado.setObjectName("btn_warning")
        btn_toggle_estado.clicked.connect(self.cambiar_estado_producto)

        btn_eliminar = QPushButton("🗑️ Eliminar Producto")
        btn_eliminar.setObjectName("btn_danger")
        btn_eliminar.clicked.connect(self.eliminar_producto)

        btn_layout.addWidget(btn_toggle_estado)
        btn_layout.addWidget(btn_eliminar)

        t_layout.addWidget(self.tabla_productos)
        t_layout.addLayout(btn_layout)
        box_tabla.setLayout(t_layout)

        layout.addWidget(box_form, 1)
        layout.addWidget(box_tabla, 2)
        widget.setLayout(layout)
        return widget

    def al_seleccionar_producto_edicion(self, item):
        fila = item.row()
        self.producto_id_edicion = self.tabla_productos.item(fila, 0).text()
        
        nombre = self.tabla_productos.item(fila, 1).text()
        precio_str = self.tabla_productos.item(fila, 2).text().replace("$", "").replace(".", "").replace(",", "")
        cat = self.tabla_productos.item(fila, 3).text()

        self.input_prod_nombre.setText(nombre)
        self.input_prod_precio.setText(precio_str)
        index = self.combo_prod_cat.findText(cat)
        if index >= 0:
            self.combo_prod_cat.setCurrentIndex(index)

    def limpiar_form_producto(self):
        self.producto_id_edicion = None
        self.input_prod_nombre.clear()
        self.input_prod_precio.clear()
        self.combo_prod_cat.setCurrentIndex(0)

    def guardar_producto(self):
        nombre = self.input_prod_nombre.text().strip()
        precio_str = self.input_prod_precio.text().strip()
        cat = self.combo_prod_cat.currentText()

        if not nombre or not precio_str:
            QMessageBox.warning(self, "Error", "Completa nombre y precio.")
            return

        try:
            precio = float(precio_str)
        except ValueError:
            QMessageBox.warning(self, "Error", "El precio debe ser un número válido.")
            return

        if self.producto_id_edicion:
            # Edición de producto existente
            self.cursor.execute("UPDATE productos SET nombre = ?, precio = ?, categoria = ? WHERE id = ?",
                                (nombre, precio, cat, self.producto_id_edicion))
            QMessageBox.information(self, "Éxito", "Producto actualizado correctamente.")
        else:
            # Inserción de un nuevo producto
            self.cursor.execute("INSERT INTO productos (nombre, precio, categoria, estado) VALUES (?, ?, ?, 'Disponible')",
                                (nombre, precio, cat))
            QMessageBox.information(self, "Éxito", "Producto creado correctamente.")

        self.conn.commit()
        self.limpiar_form_producto()
        self.actualizar_todo()

    def al_editar_celda_producto(self, item):
        fila = item.row()
        col = item.column()
        
        # Evitar ciclos infinitos si la tabla se está recargando
        if col not in [1, 2, 3] or self.tabla_productos.signalsBlocked():
            return

        p_id = self.tabla_productos.item(fila, 0).text()
        nuevo_valor = item.text().strip()

        if col == 1: # Editar Nombre
            self.cursor.execute("UPDATE productos SET nombre = ? WHERE id = ?", (nuevo_valor, p_id))
        elif col == 2: # Editar Precio
            try:
                precio_clean = float(nuevo_valor.replace("$", "").replace(".", "").replace(",", ""))
                self.cursor.execute("UPDATE productos SET precio = ? WHERE id = ?", (precio_clean, p_id))
            except ValueError:
                QMessageBox.warning(self, "Error", "El precio ingresado no es válido.")
                self.actualizar_todo()
                return
        elif col == 3: # Editar Categoría
            if nuevo_valor in CATEGORIAS_MODULOS:
                self.cursor.execute("UPDATE productos SET categoria = ? WHERE id = ?", (nuevo_valor, p_id))
            else:
                QMessageBox.warning(self, "Error", f"La categoría debe ser una de las siguientes: {', '.join(CATEGORIAS_MODULOS)}")
                self.actualizar_todo()
                return

        self.conn.commit()
        self.actualizar_todo()

    def cargar_tabla_productos(self):
        self.tabla_productos.blockSignals(True) # Bloquear señales durante la carga para evitar disparar el evento de edición
        self.cursor.execute("SELECT id, nombre, precio, categoria, estado FROM productos")
        filas = self.cursor.fetchall()
        self.tabla_productos.setRowCount(len(filas))
        
        for f_idx, fila in enumerate(filas):
            for c_idx, val in enumerate(fila):
                if c_idx == 2:
                    item = QTableWidgetItem(f"${val:,.0f}")
                else:
                    item = QTableWidgetItem(str(val))
                
                # Deshabilitar edición directa de ID y Estado (Se cambian por botón)
                if c_idx in [0, 4]:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                self.tabla_productos.setItem(f_idx, c_idx, item)

        self.tabla_productos.blockSignals(False)

    def cambiar_estado_producto(self):
        fila = self.tabla_productos.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Selecciona un producto de la tabla.")
            return

        prod_id = self.tabla_productos.item(fila, 0).text()
        estado_actual = self.tabla_productos.item(fila, 4).text()
        nuevo_estado = "Agotado" if estado_actual == "Disponible" else "Disponible"

        self.cursor.execute("UPDATE productos SET estado = ? WHERE id = ?", (nuevo_estado, prod_id))
        self.conn.commit()
        self.actualizar_todo()

    def eliminar_producto(self):
        fila = self.tabla_productos.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Selecciona un producto para eliminar.")
            return

        prod_id = self.tabla_productos.item(fila, 0).text()
        if QMessageBox.question(self, "Confirmar", "¿Eliminar producto permanentemente?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.cursor.execute("DELETE FROM productos WHERE id = ?", (prod_id,))
            self.conn.commit()
            self.limpiar_form_producto()
            self.actualizar_todo()

    # --- PESTAÑA 6: RECETAS ---
    def crear_pestaña_recetas(self):
        widget = QWidget()
        layout = QHBoxLayout()

        box_form = QGroupBox("Asignar Insumo a Producto")
        form_layout = QFormLayout()

        self.combo_receta_prod = QComboBox()
        self.combo_receta_ins = QComboBox()
        self.input_receta_cant = QDoubleSpinBox()
        self.input_receta_cant.setDecimals(3)
        self.input_receta_cant.setMaximum(999.0)

        form_layout.addRow("Seleccionar Producto:", self.combo_receta_prod)
        form_layout.addRow("Insumo Requerido:", self.combo_receta_ins)
        form_layout.addRow("Gramaje / Cantidad por Porción:", self.input_receta_cant)

        btn_asociar = QPushButton("➕ Agregar a la Receta")
        btn_asociar.setObjectName("btn_success")
        btn_asociar.clicked.connect(self.asociar_receta)

        v_layout = QVBoxLayout()
        v_layout.addLayout(form_layout)
        v_layout.addWidget(btn_asociar)
        v_layout.addStretch()
        box_form.setLayout(v_layout)

        box_tabla = QGroupBox("Receta del Producto Seleccionado")
        t_layout = QVBoxLayout()

        self.combo_receta_filtro = QComboBox()
        self.combo_receta_filtro.currentIndexChanged.connect(self.cargar_tabla_recetas)

        self.tabla_recetas = QTableWidget()
        self.tabla_recetas.setColumnCount(4)
        self.tabla_recetas.setHorizontalHeaderLabels(["ID Receta", "Insumo", "Cantidad Usada", "Unidad"])
        self.tabla_recetas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_recetas.setSelectionBehavior(QAbstractItemView.SelectRows)

        btn_quitar_receta = QPushButton("🗑️ Eliminar Insumo de la Receta")
        btn_quitar_receta.setObjectName("btn_danger")
        btn_quitar_receta.clicked.connect(self.eliminar_receta_item)

        t_layout.addWidget(QLabel("Filtrar receta por producto:"))
        t_layout.addWidget(self.combo_receta_filtro)
        t_layout.addWidget(self.tabla_recetas)
        t_layout.addWidget(btn_quitar_receta)
        box_tabla.setLayout(t_layout)

        layout.addWidget(box_form, 1)
        layout.addWidget(box_tabla, 2)
        widget.setLayout(layout)
        return widget

    # --- LÓGICA DE ACTUALIZACIÓN ---
    def actualizar_todo(self):
        self.cargar_tablas_modulos_pos()
        self.cargar_tabla_bodega()
        self.cargar_tabla_ganancias()
        self.cargar_tabla_productos()
        self.cargar_combos_recetas()
        self.cargar_historial_y_caja()

    def agregar_al_carrito(self):
        if not self.producto_seleccionado:
            QMessageBox.warning(self, "Atención", "Haz clic en algún producto de los módulos para seleccionarlo.")
            return

        p_id, p_nombre, p_precio = self.producto_seleccionado
        cant = self.spin_cantidad.value()
        subtotal = p_precio * cant

        self.carrito.append({
            'id': p_id,
            'nombre': p_nombre,
            'precio': p_precio,
            'cantidad': cant,
            'subtotal': subtotal
        })

        self.actualizar_tabla_carrito()

    def actualizar_tabla_carrito(self):
        self.tabla_carrito.setRowCount(len(self.carrito))
        total = 0
        for i, item in enumerate(self.carrito):
            self.tabla_carrito.setItem(i, 0, QTableWidgetItem(item['nombre']))
            self.tabla_carrito.setItem(i, 1, QTableWidgetItem(str(item['cantidad'])))
            self.tabla_carrito.setItem(i, 2, QTableWidgetItem(f"${item['precio']:,.0f}"))
            self.tabla_carrito.setItem(i, 3, QTableWidgetItem(f"${item['subtotal']:,.0f}"))
            total += item['subtotal']

        self.lbl_total.setText(f"TOTAL: ${total:,.0f}")

    def quitar_del_carrito(self):
        fila = self.tabla_carrito.currentRow()
        if fila >= 0:
            self.carrito.pop(fila)
            self.actualizar_tabla_carrito()

    def procesar_comanda(self):
        if not self.carrito:
            QMessageBox.warning(self, "Error", "La comanda está vacía.")
            return

        for item in self.carrito:
            self.cursor.execute("""
                SELECT i.nombre, i.stock_actual, (r.cantidad_requerida * ?) as total_nec, i.unidad_medida
                FROM recetas r
                JOIN insumos i ON r.insumo_id = i.id
                WHERE r.producto_id = ?
            """, (item['cantidad'], item['id']))
            ingredientes = self.cursor.fetchall()

            for nombre_ins, stock_act, nec, unidad in ingredientes:
                if stock_act < nec:
                    QMessageBox.critical(self, "Stock Insuficiente", 
                                         f"No se puede vender '{item['nombre']}'.\nInsumo faltante: {nombre_ins} (Stock actual: {stock_act} {unidad}, Requiere: {nec} {unidad})")
                    return

        cliente = self.input_cliente.text().strip() or "General"
        pago = self.combo_pago.currentText()
        total = sum(item['subtotal'] for item in self.carrito)
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute("INSERT INTO ventas (cliente_mesa, total, medio_pago, fecha) VALUES (?, ?, ?, ?)",
                            (cliente, total, pago, fecha))
        venta_id = self.cursor.lastrowid

        ticket_html = f"<h2>COMANDA CASINO #{venta_id}</h2><p><b>Cliente/Mesa:</b> {cliente}<br><b>Fecha:</b> {fecha}</p><hr><ul>"

        for item in self.carrito:
            self.cursor.execute("INSERT INTO detalle_ventas (venta_id, producto, cantidad, subtotal) VALUES (?, ?, ?, ?)",
                                (venta_id, item['nombre'], item['cantidad'], item['subtotal']))
            
            self.cursor.execute("SELECT insumo_id, cantidad_requerida FROM recetas WHERE producto_id = ?", (item['id'],))
            receta_items = self.cursor.fetchall()
            for ins_id, cant_req in receta_items:
                descuento = cant_req * item['cantidad']
                self.cursor.execute("UPDATE insumos SET stock_actual = stock_actual - ? WHERE id = ?", (descuento, ins_id))
            
            ticket_html += f"<li><b>{item['cantidad']}x</b> {item['nombre']} - ${item['subtotal']:,.0f}</li>"

        ticket_html += f"</ul><hr><h3>TOTAL: ${total:,.0f}</h3><p><b>Pago:</b> {pago}</p>"

        self.conn.commit()

        documento = QTextDocument()
        documento.setHtml(ticket_html)

        printer = QPrinter()
        dialogo = QPrintDialog(printer, self)
        if dialogo.exec_() == QPrintDialog.Accepted:
            documento.print_(printer)
        else:
            QMessageBox.information(self, f"Comanda #{venta_id} Procesada", "Venta registrada con éxito y descontada del stock.")

        self.carrito.clear()
        self.input_cliente.clear()
        self.producto_seleccionado = None
        self.lbl_prod_seleccionado.setText("Ninguno seleccionado")
        self.actualizar_tabla_carrito()
        self.actualizar_todo()

    # --- LÓGICA DE BODEGA ---
    def guardar_insumo(self):
        nombre = self.input_insumo_nombre.text().strip()
        unidad = self.combo_insumo_unidad.currentText()
        stock = self.input_insumo_stock.value()
        costo = self.input_insumo_costo.value()
        stock_min = self.input_insumo_min.value()
        prov = self.input_insumo_prov.text().strip() or "General"

        if not nombre:
            QMessageBox.warning(self, "Error", "Ingresa el nombre del insumo.")
            return

        self.cursor.execute("""
            INSERT INTO insumos (nombre, unidad_medida, stock_actual, stock_minimo, costo_unidad_proveedor, proveedor) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nombre, unidad, stock, stock_min, costo, prov))
        self.conn.commit()

        self.input_insumo_nombre.clear()
        self.input_insumo_stock.setValue(0)
        self.input_insumo_costo.setValue(0)
        self.input_insumo_prov.clear()
        self.actualizar_todo()

    def cargar_tabla_bodega(self):
        self.cursor.execute("SELECT id, nombre, unidad_medida, stock_actual, costo_unidad_proveedor, stock_minimo, proveedor FROM insumos")
        filas = self.cursor.fetchall()
        self.tabla_insumos.setRowCount(len(filas))

        for f_idx, fila in enumerate(filas):
            for c_idx, val in enumerate(fila):
                if c_idx == 4:
                    texto = f"${val:,.0f}"
                else:
                    texto = str(val)

                item = QTableWidgetItem(texto)
                
                if fila[3] <= fila[5]:
                    item.setBackground(QColor(254, 226, 226))
                    item.setForeground(QColor(185, 28, 28))

                self.tabla_insumos.setItem(f_idx, c_idx, item)

    def eliminar_insumo(self):
        fila = self.tabla_insumos.currentRow()
        if fila < 0:
            return

        ins_id = self.tabla_insumos.item(fila, 0).text()
        if QMessageBox.question(self, "Confirmar", "¿Eliminar este insumo?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.cursor.execute("DELETE FROM insumos WHERE id = ?", (ins_id,))
            self.conn.commit()
            self.actualizar_todo()

    # --- LÓGICA DE GANANCIAS ---
    def cargar_tabla_ganancias(self):
        self.cursor.execute("SELECT id, nombre, precio FROM productos")
        prods = self.cursor.fetchall()

        self.tabla_ganancias.setRowCount(len(prods))

        for idx, (p_id, p_nombre, p_precio) in enumerate(prods):
            self.cursor.execute("""
                SELECT SUM(r.cantidad_requerida * i.costo_unidad_proveedor)
                FROM recetas r
                JOIN insumos i ON r.insumo_id = i.id
                WHERE r.producto_id = ?
            """, (p_id,))
            costo_total_receta = self.cursor.fetchone()[0] or 0.0

            ganancia = p_precio - costo_total_receta
            margen_pct = (ganancia / p_precio * 100) if p_precio > 0 else 0.0

            self.tabla_ganancias.setItem(idx, 0, QTableWidgetItem(str(p_id)))
            self.tabla_ganancias.setItem(idx, 1, QTableWidgetItem(p_nombre))
            self.tabla_ganancias.setItem(idx, 2, QTableWidgetItem(f"${costo_total_receta:,.0f}"))
            self.tabla_ganancias.setItem(idx, 3, QTableWidgetItem(f"${p_precio:,.0f}"))
            
            item_ganancia = QTableWidgetItem(f"${ganancia:,.0f}")
            if ganancia > 0:
                item_ganancia.setForeground(QColor(16, 185, 129))
            else:
                item_ganancia.setForeground(QColor(239, 68, 68))
            self.tabla_ganancias.setItem(idx, 4, item_ganancia)

            self.tabla_ganancias.setItem(idx, 5, QTableWidgetItem(f"{margen_pct:.1f}%"))

    # --- LÓGICA DE RECETAS ---
    def cargar_combos_recetas(self):
        self.combo_receta_prod.clear()
        self.combo_receta_ins.clear()
        self.combo_receta_filtro.clear()

        self.cursor.execute("SELECT id, nombre FROM productos")
        prods = self.cursor.fetchall()
        for p in prods:
            self.combo_receta_prod.addItem(p[1], p[0])
            self.combo_receta_filtro.addItem(p[1], p[0])

        self.cursor.execute("SELECT id, nombre, unidad_medida FROM insumos")
        ins = self.cursor.fetchall()
        for i in ins:
            self.combo_receta_ins.addItem(f"{i[1]} ({i[2]})", i)

        self.cargar_tabla_recetas()

    def asociar_receta(self):
        prod_id = self.combo_receta_prod.currentData()
        ins_data = self.combo_receta_ins.currentData()
        cant = self.input_receta_cant.value()

        if not prod_id or not ins_data or cant <= 0:
            QMessageBox.warning(self, "Atención", "Selecciona producto e insumo válido.")
            return

        self.cursor.execute("INSERT INTO recetas (producto_id, insumo_id, cantidad_requerida) VALUES (?, ?, ?)",
                            (prod_id, ins_data[0], cant))
        self.conn.commit()
        self.cargar_tabla_recetas()
        self.cargar_tabla_ganancias()

    def cargar_tabla_recetas(self):
        prod_id = self.combo_receta_filtro.currentData()
        if not prod_id:
            self.tabla_recetas.setRowCount(0)
            return

        self.cursor.execute("""
            SELECT r.id, i.nombre, r.cantidad_requerida, i.unidad_medida
            FROM recetas r
            JOIN insumos i ON r.insumo_id = i.id
            WHERE r.producto_id = ?
        """, (prod_id,))
        filas = self.cursor.fetchall()
        self.tabla_recetas.setRowCount(len(filas))

        for f_idx, fila in enumerate(filas):
            for c_idx, val in enumerate(fila):
                self.tabla_recetas.setItem(f_idx, c_idx, QTableWidgetItem(str(val)))

    def eliminar_receta_item(self):
        fila = self.tabla_recetas.currentRow()
        if fila < 0:
            return

        receta_id = self.tabla_recetas.item(fila, 0).text()
        self.cursor.execute("DELETE FROM recetas WHERE id = ?", (receta_id,))
        self.conn.commit()
        self.cargar_tabla_recetas()
        self.cargar_tabla_ganancias()

    # --- LÓGICA DE CAJA Y REPORTES ---
    def cargar_historial_y_caja(self):
        hoy = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute("SELECT id, cliente_mesa, total, medio_pago, fecha FROM ventas WHERE fecha LIKE ? ORDER BY id DESC", (f"{hoy}%",))
        ventas = self.cursor.fetchall()

        self.tabla_historial.setRowCount(len(ventas))
        total_dia = 0
        efectivo = 0
        tarjeta = 0
        transf = 0

        for f_idx, v in enumerate(ventas):
            self.tabla_historial.setItem(f_idx, 0, QTableWidgetItem(f"#{v[0]}"))
            self.tabla_historial.setItem(f_idx, 1, QTableWidgetItem(v[1]))
            self.tabla_historial.setItem(f_idx, 2, QTableWidgetItem(f"${v[2]:,.0f}"))
            self.tabla_historial.setItem(f_idx, 3, QTableWidgetItem(v[3]))
            self.tabla_historial.setItem(f_idx, 4, QTableWidgetItem(v[4]))

            monto = v[2]
            total_dia += monto
            if v[3] == "Efectivo":
                efectivo += monto
            elif "Débito" in v[3] or "Crédito" in v[3]:
                tarjeta += monto
            elif v[3] == "Transferencia":
                transf += monto

        self.lbl_caja_total.setText(f"Total Día: ${total_dia:,.0f}")
        self.lbl_caja_efectivo.setText(f"Efectivo: ${efectivo:,.0f}")
        self.lbl_caja_tarjeta.setText(f"Débito/Crédito: ${tarjeta:,.0f}")
        self.lbl_caja_transf.setText(f"Transferencia: ${transf:,.0f}")

    def exportar_a_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar Reporte", "Ventas_Casino.csv", "Archivos CSV (*.csv)")
        if path:
            self.cursor.execute("SELECT * FROM ventas")
            ventas = self.cursor.fetchall()
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID Folio", "Cliente / Mesa", "Total ($)", "Medio de Pago", "Fecha / Hora"])
                writer.writerows(ventas)
            QMessageBox.information(self, "Exportación Éxito", "Reporte guardado correctamente.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SistemaCasinoProfesional()
    window.show()
    sys.exit(app.exec_())