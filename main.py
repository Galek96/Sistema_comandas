import sys
import os
import sqlite3
import csv
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, 
                             QHeaderView, QSpinBox, QTabWidget, QGroupBox, QFormLayout,
                             QAbstractItemView, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
from PyQt5.QtGui import QTextDocument

claro/oscuro
LIGHT_THEME = """
QMainWindow { background-color: #F8FAFC; }
QLabel { font-size: 13px; color: #1E293B; font-weight: 500; }
QGroupBox { font-weight: bold; border: 1px solid #CBD5E1; border-radius: 8px; margin-top: 10px; background-color: #FFFFFF; padding: 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #0F172A; }
QLineEdit, QComboBox, QSpinBox { padding: 6px; border: 1px solid #CBD5E1; border-radius: 5px; background-color: #F1F5F9; font-size: 13px; color: #0F172A; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid #2563EB; background-color: #FFFFFF; }
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
QLineEdit, QComboBox, QSpinBox { padding: 6px; border: 1px solid #475569; border-radius: 5px; background-color: #334155; font-size: 13px; color: #F8FAFC; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid #3B82F6; background-color: #1E293B; }
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

class SistemaComandasPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema POS y Comandas - Restaurante Pro")
        self.resize(1100, 720)
        
        self.es_modo_noche = False
        self.setStyleSheet(LIGHT_THEME)
        
        self.carrito = [] 
        
        self.init_db()
        self.init_ui()

    def init_db(self):
        self.conn = sqlite3.connect("restaurante.db")
        self.cursor = self.conn.cursor()
        
     
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL,
            categoria TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'Disponible'
        )''')
        
   
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_mesa TEXT,
            total REAL,
            medio_pago TEXT,
            fecha TEXT
        )''')

      
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS detalle_ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER,
            producto TEXT,
            cantidad INTEGER,
            subtotal REAL,
            FOREIGN KEY (venta_id) REFERENCES ventas(id)
        )''')
        
        self.conn.commit()

        self.cursor.execute("SELECT COUNT(*) FROM productos")
        if self.cursor.fetchone()[0] == 0:
            productos_iniciales = [
                ('Lomo a lo Pobre', 8500, 15, 'Platos', 'Disponible'),
                ('Hamburguesa Italiana', 6500, 20, 'Platos', 'Disponible'),
                ('Papas Fritas Familiares', 4500, 10, 'Acompañamientos', 'Disponible'),
                ('Bebida 350ml', 1500, 30, 'Bebidas', 'Disponible'),
                ('Cerveza Artesanal', 3500, 25, 'Bebidas', 'Disponible'),
                ('Pie de Limón', 2500, 0, 'Postres', 'Agotado')
            ]
            self.cursor.executemany("INSERT INTO productos (nombre, precio, stock, categoria, estado) VALUES (?, ?, ?, ?, ?)", productos_iniciales)
            self.conn.commit()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        
        lbl_titulo = QLabel("🍽️ SISTEMA DE COMANDAS Y CONTROL DE STOCK")
        lbl_titulo.setFont(QFont("Arial", 14, QFont.Bold))
        
        self.btn_theme = QPushButton("🌙 Modo Noche")
        self.btn_theme.setObjectName("btn_toggle_theme")
        self.btn_theme.clicked.connect(self.toggle_theme)

        header_layout.addWidget(lbl_titulo)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_theme)
        
        main_layout.addLayout(header_layout)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.crear_pestaña_ventas(), "📝 Nueva Comanda")
        self.tabs.addTab(self.crear_pestaña_stock(), "📦 Control de Inventario")
        self.tabs.addTab(self.crear_pestaña_caja(), "📊 Cierre de Caja / Historial")
        
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

    def crear_pestaña_ventas(self):
        widget = QWidget()
        layout = QHBoxLayout()

      
        left_box = QGroupBox("Selección de Productos")
        left_layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.combo_productos = QComboBox()
        self.combo_productos.currentIndexChanged.connect(self.al_seleccionar_producto)
        
        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setMinimum(1)
        self.spin_cantidad.setMaximum(100)

        self.lbl_precio_unitario = QLabel("$0")
        self.lbl_precio_unitario.setFont(QFont("Arial", 11, QFont.Bold))

        form_layout.addRow("Producto:", self.combo_productos)
        form_layout.addRow("Precio Unitario:", self.lbl_precio_unitario)
        form_layout.addRow("Cantidad:", self.spin_cantidad)

        btn_agregar = QPushButton("➕ Agregar al Carrito")
        btn_agregar.setObjectName("btn_success")
        btn_agregar.clicked.connect(self.agregar_al_carrito)

        left_layout.addLayout(form_layout)
        left_layout.addWidget(btn_agregar)
        left_layout.addStretch()
        left_box.setLayout(left_layout)

        # Derecha: Carrito y Confirmación
        right_box = QGroupBox("Comanda Actual")
        right_layout = QVBoxLayout()

        info_layout = QHBoxLayout()
        self.input_cliente = QLineEdit()
        self.input_cliente.setPlaceholderText("Ej: Mesa 4 / Juan Pérez")
        
        self.combo_pago = QComboBox()
        self.combo_pago.addItems(["Efectivo", "Tarjeta Débito/Crédito", "Transferencia"])

        info_layout.addWidget(QLabel("Mesa/Cliente:"))
        info_layout.addWidget(self.input_cliente)
        info_layout.addWidget(QLabel("Pago:"))
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

        layout.addWidget(left_box, 1)
        layout.addWidget(right_box, 2)
        widget.setLayout(layout)
        return widget

    def crear_pestaña_stock(self):
        widget = QWidget()
        layout = QHBoxLayout()

        box_form = QGroupBox("Agregar / Editar Producto")
        form_layout = QFormLayout()

        self.input_prod_nombre = QLineEdit()
        self.input_prod_precio = QLineEdit()
        self.input_prod_stock = QSpinBox()
        self.input_prod_stock.setMaximum(9999)
        self.combo_prod_cat = QComboBox()
        self.combo_prod_cat.addItems(["Platos", "Bebidas", "Acompañamientos", "Postres", "Otros"])

        form_layout.addRow("Nombre:", self.input_prod_nombre)
        form_layout.addRow("Precio ($):", self.input_prod_precio)
        form_layout.addRow("Stock Inicial:", self.input_prod_stock)
        form_layout.addRow("Categoría:", self.combo_prod_cat)

        btn_guardar_prod = QPushButton("💾 Guardar Producto")
        btn_guardar_prod.setObjectName("btn_success")
        btn_guardar_prod.clicked.connect(self.guardar_producto)

        v_layout = QVBoxLayout()
        v_layout.addLayout(form_layout)
        v_layout.addWidget(btn_guardar_prod)
        v_layout.addStretch()
        box_form.setLayout(v_layout)

        box_tabla = QGroupBox("Inventario Actual")
        t_layout = QVBoxLayout()

        self.tabla_stock = QTableWidget()
        self.tabla_stock.setColumnCount(6)
        self.tabla_stock.setHorizontalHeaderLabels(["ID", "Producto", "Precio", "Stock", "Categoría", "Estado"])
        self.tabla_stock.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_stock.setSelectionBehavior(QAbstractItemView.SelectRows)

        btn_layout = QHBoxLayout()
        btn_toggle_estado = QPushButton("🔄 Cambiar Estado (Disponible/Agotado)")
        btn_toggle_estado.setObjectName("btn_warning")
        btn_toggle_estado.clicked.connect(self.cambiar_estado_stock)

        btn_eliminar = QPushButton("🗑️ Eliminar Producto")
        btn_eliminar.setObjectName("btn_danger")
        btn_eliminar.clicked.connect(self.eliminar_producto)

        btn_layout.addWidget(btn_toggle_estado)
        btn_layout.addWidget(btn_eliminar)

        t_layout.addWidget(self.tabla_stock)
        t_layout.addLayout(btn_layout)
        box_tabla.setLayout(t_layout)

        layout.addWidget(box_form, 1)
        layout.addWidget(box_tabla, 2)
        widget.setLayout(layout)
        return widget

    def crear_pestaña_caja(self):
        widget = QWidget()
        layout = QVBoxLayout()

        box_resumen = QGroupBox("Arqueo de Caja del Día")
        resumen_layout = QHBoxLayout()

        self.lbl_caja_total = QLabel("Total Día: $0")
        self.lbl_caja_total.setFont(QFont("Arial", 11, QFont.Bold))
        
        self.lbl_caja_efectivo = QLabel("Efectivo: $0")
        self.lbl_caja_tarjeta = QLabel("Tarjeta: $0")
        self.lbl_caja_transf = QLabel("Transferencia: $0")

        resumen_layout.addWidget(self.lbl_caja_total)
        resumen_layout.addWidget(self.lbl_caja_efectivo)
        resumen_layout.addWidget(self.lbl_caja_tarjeta)
        resumen_layout.addWidget(self.lbl_caja_transf)
        box_resumen.setLayout(resumen_layout)

        box_historial = QGroupBox("Historial de Ventas")
        h_layout = QVBoxLayout()

        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(5)
        self.tabla_historial.setHorizontalHeaderLabels(["N° Folio", "Mesa / Cliente", "Total", "Medio Pago", "Fecha / Hora"])
        self.tabla_historial.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        btn_exportar = QPushButton("📥 Exportar Reporte a Excel / CSV")
        btn_exportar.setObjectName("btn_success")
        btn_exportar.clicked.connect(self.exportar_a_csv)

        h_layout.addWidget(self.tabla_historial)
        h_layout.addWidget(btn_exportar)
        box_historial.setLayout(h_layout)

        layout.addWidget(box_resumen)
        layout.addWidget(box_historial)
        widget.setLayout(layout)
        return widget


    def actualizar_todo(self):
        self.cargar_combo_productos()
        self.cargar_tabla_stock()
        self.cargar_historial_y_caja()

    def cargar_combo_productos(self):
        self.combo_productos.clear()
        self.cursor.execute("SELECT id, nombre, precio, stock FROM productos WHERE estado = 'Disponible' AND stock > 0")
        productos = self.cursor.fetchall()
        for p in productos:
            self.combo_productos.addItem(f"{p[1]} (Stock: {p[3]})", p)

    def al_seleccionar_producto(self):
        data = self.combo_productos.currentData()
        if data:
            self.lbl_precio_unitario.setText(f"${data[2]:,.0f}")
            self.spin_cantidad.setMaximum(data[3])

    def agregar_al_carrito(self):
        data = self.combo_productos.currentData()
        if not data:
            QMessageBox.warning(self, "Atención", "Selecciona un producto disponible.")
            return

        cant = self.spin_cantidad.value()
        subtotal = data[2] * cant

        self.carrito.append({
            'id': data[0],
            'nombre': data[1],
            'precio': data[2],
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

        cliente = self.input_cliente.text().strip() or "Mesa General"
        pago = self.combo_pago.currentText()
        total = sum(item['subtotal'] for item in self.carrito)
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute("INSERT INTO ventas (cliente_mesa, total, medio_pago, fecha) VALUES (?, ?, ?, ?)",
                            (cliente, total, pago, fecha))
        venta_id = self.cursor.lastrowid

        ticket_html = f"<h2>COMANDA #{venta_id}</h2><p><b>Mesa/Cliente:</b> {cliente}<br><b>Fecha:</b> {fecha}</p><hr><ul>"

        for item in self.carrito:
            self.cursor.execute("INSERT INTO detalle_ventas (venta_id, producto, cantidad, subtotal) VALUES (?, ?, ?, ?)",
                                (venta_id, item['nombre'], item['cantidad'], item['subtotal']))
            
            self.cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (item['cantidad'], item['id']))
            self.cursor.execute("UPDATE productos SET estado = 'Agotado' WHERE id = ? AND stock <= 0", (item['id'],))
            
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
            QMessageBox.information(self, f"Comanda #{venta_id} Procesada", "La comanda se registró correctamente en la base de datos.")

        
        self.carrito.clear()
        self.input_cliente.clear()
        self.actualizar_tabla_carrito()
        self.actualizar_todo()

    def guardar_producto(self):
        nombre = self.input_prod_nombre.text().strip()
        precio_str = self.input_prod_precio.text().strip()
        stock = self.input_prod_stock.value()
        cat = self.combo_prod_cat.currentText()

        if not nombre or not precio_str:
            QMessageBox.warning(self, "Error", "Completa nombre y precio.")
            return

        try:
            precio = float(precio_str)
        except ValueError:
            QMessageBox.warning(self, "Error", "El precio debe ser un número válido.")
            return

        estado = "Disponible" if stock > 0 else "Agotado"

        self.cursor.execute("INSERT INTO productos (nombre, precio, stock, categoria, estado) VALUES (?, ?, ?, ?, ?)",
                            (nombre, precio, stock, cat, estado))
        self.conn.commit()

        self.input_prod_nombre.clear()
        self.input_prod_precio.clear()
        self.input_prod_stock.setValue(0)
        self.actualizar_todo()

    def cargar_tabla_stock(self):
        self.cursor.execute("SELECT id, nombre, precio, stock, categoria, estado FROM productos")
        filas = self.cursor.fetchall()
        self.tabla_stock.setRowCount(len(filas))
        for f_idx, fila in enumerate(filas):
            for c_idx, val in enumerate(fila):
                item = QTableWidgetItem(f"${val:,.0f}" if c_idx == 2 else str(val))
                self.tabla_stock.setItem(f_idx, c_idx, item)

    def cambiar_estado_stock(self):
        fila = self.tabla_stock.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Selecciona un producto de la tabla.")
            return

        prod_id = self.tabla_stock.item(fila, 0).text()
        estado_actual = self.tabla_stock.item(fila, 5).text()
        nuevo_estado = "Agotado" if estado_actual == "Disponible" else "Disponible"

        self.cursor.execute("UPDATE productos SET estado = ? WHERE id = ?", (nuevo_estado, prod_id))
        self.conn.commit()
        self.actualizar_todo()

    def eliminar_producto(self):
        fila = self.tabla_stock.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Atención", "Selecciona un producto para eliminar.")
            return

        prod_id = self.tabla_stock.item(fila, 0).text()
        confirmacion = QMessageBox.question(self, "Confirmar", "¿Eliminar este producto permanentemente?",
                                            QMessageBox.Yes | QMessageBox.No)
        
        if confirmacion == QMessageBox.Yes:
            self.cursor.execute("DELETE FROM productos WHERE id = ?", (prod_id,))
            self.conn.commit()
            self.actualizar_todo()

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
            elif "Tarjeta" in v[3]:
                tarjeta += monto
            elif v[3] == "Transferencia":
                transf += monto

        self.lbl_caja_total.setText(f"Total Día: ${total_dia:,.0f}")
        self.lbl_caja_efectivo.setText(f"Efectivo: ${efectivo:,.0f}")
        self.lbl_caja_tarjeta.setText(f"Tarjeta: ${tarjeta:,.0f}")
        self.lbl_caja_transf.setText(f"Transferencia: ${transf:,.0f}")

    def exportar_a_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar Reporte", "Cierre_Caja.csv", "Archivos CSV (*.csv)")
        if path:
            self.cursor.execute("SELECT * FROM ventas")
            ventas = self.cursor.fetchall()
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["ID Folio", "Mesa / Cliente", "Total ($)", "Medio de Pago", "Fecha / Hora"])
                writer.writerows(ventas)
            QMessageBox.information(self, "Exportación Éxito", "El reporte CSV/Excel se ha guardado correctamente.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SistemaComandasPro()
    window.show()
    sys.exit(app.exec_())
