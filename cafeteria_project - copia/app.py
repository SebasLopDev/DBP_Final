from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_admin import Admin, expose, BaseView
from flask_admin.contrib.sqla import ModelView
import random
import string

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/store1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'una_clave_secreta_aleatoria'

# Genera un sufijo aleatorio para la URL de administración
def generate_admin_url_suffix(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

admin_url_suffix = generate_admin_url_suffix()
app.config['ADMIN_URL_SUFFIX'] = admin_url_suffix

db = SQLAlchemy(app)

# Modelos de la base de datos
class Usuario(db.Model):    
    id = db.Column(db.Integer, primary_key=True)  
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    numero_de_personas = db.Column(db.Integer, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    
class Administrador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  
    is_admin = db.Column(db.Boolean, default=True)  
    
class Ventas1(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto = db.Column(db.String(100))
    cantidad = db.Column(db.Integer)
    nombre = db.Column(db.String(100))  # Nuevo campo
    correo = db.Column(db.String(100))  # Nuevo campo

# Crear todas las tablas
with app.app_context():
    db.create_all()

# Vista de administración solo accesible para administradores autenticados
class AdminView(ModelView):
    def is_accessible(self):
        return 'admin_id' in session
    
# Clase personalizada para el enlace "Cerrar sesión"
class LogoutMenuLink(BaseView):
    @expose('/')
    def index(self):
        return redirect(url_for('logout'))  # Redirige a la ruta de logout    

# Configuración de Flask-Admin con URL dinámica
admin = Admin(app, name='admin', template_mode='bootstrap3', url=f"/admin/{app.config['ADMIN_URL_SUFFIX']}")
admin.add_view(AdminView(Usuario, db.session))
admin.add_view(AdminView(Administrador, db.session))
admin.add_view(AdminView(Ventas1, db.session))
admin.add_view(LogoutMenuLink(name='Cerrar sesión', category='', endpoint='logout'))

# Crear un administrador inicial si no existe
with app.app_context():
    admin_password = 'mi_contraseña_segura'
    if not Administrador.query.filter_by(email='admin@correo.com').first():
        new_admin = Administrador(nombre='Admin', email='admin@correo.com', password=admin_password)
        db.session.add(new_admin)
        db.session.commit()

# Ruta de inicio de sesión para administradores
@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        admin = Administrador.query.filter_by(email=email).first()

        if admin and admin.password == password:
            session['admin_id'] = admin.id  # Guarda el id del admin en la sesión
            return redirect(f"/admin/{app.config['ADMIN_URL_SUFFIX']}")  # Redirige al panel de administración dinámico
        else:
            flash('Correo o contraseña incorrectos', 'danger')

    return render_template('loginAdmin.html')

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.pop('admin_id', None)   
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('login_admin'))

# Rutas del sitio principal
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/galeria')
def galeria():
    return render_template('galeria.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/administrador')
def loginAdmin():
    return render_template('loginAdmin.html')

# Ruta para el formulario de usuario
@app.route('/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        numero_de_personas = int(request.form['numero_de_personas'])
        hora = request.form['hora']
        fecha = request.form['fecha']

        nuevo_usuario = Usuario(
            nombre=nombre, 
            email=email, 
            numero_de_personas=numero_de_personas, 
            hora=hora, 
            fecha=fecha
        )

        try:
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('Usuario registrado con éxito.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Este correo electrónico ya está registrado. Por favor, elige otro.', 'warning')

    return render_template('login.html')

@app.route('/productos', methods=['GET'])
def product0s():
    return render_template('productos.html')

@app.route('/confirmacionProducto', methods=['POST'])
def confirmacion_producto():
    # Obtener los datos de los contadores
    contadores = {
        'cafeEmbolsado1': int(request.form.get('cafeEmbolsado1', 0)),
        'chirinos': int(request.form.get('chirinos', 0)),
        'conjunto': int(request.form.get('conjunto', 0)),
        'cusco': int(request.form.get('cusco', 0)),
        'perene': int(request.form.get('perene', 0)),
        'taza': int(request.form.get('taza', 0)),
        'tazasvarias': int(request.form.get('tazasvarias', 0))
    }
    
    # Obtener nombre y correo
    nombre = request.form.get('nombre', '')
    correo = request.form.get('correo', '')

    # Guardar los contadores y datos del usuario en la sesión
    session['contadores'] = contadores
    session['nombre'] = nombre
    session['correo'] = correo
    
    # Pasar los datos al template
    return render_template('Pago.html', contadores=contadores, nombre=nombre, correo=correo)



@app.route('/pago', methods=['GET'])
def pago():
    contadores = session.get('contadores', {})  # Recuperar contadores desde la sesión
    nombre = session.get('nombre', '')  # Recuperar nombre desde la sesión
    correo = session.get('correo', '')  # Recuperar correo desde la sesión
    print(f"Nombre: {nombre}, Correo: {correo}")  # Verifica en la consola
    return render_template('Pago.html', contadores=contadores, nombre=nombre, correo=correo)



@app.route('/Adquirido', methods=['POST'])
def Adquirido():
    # Obtener los valores de los botones
    accion = request.form.get('accion')  # Este campo se debe agregar al formulario

    if accion == 'confirmar':
        # Recuperar los contadores, nombre y correo desde la sesión
        contadores = session.get('contadores', {})
        nombre = session.get('nombre', '')
        correo = session.get('correo', '')

        if not contadores:
            flash("No hay productos seleccionados para guardar.", "warning")
            return redirect(url_for('productos'))  # Redirige al menú si no hay productos

        # Guardar los productos en la base de datos
        for producto, cantidad in contadores.items():
            if cantidad > 0:  # Guardar solo los productos con cantidad mayor a 0
                nueva_venta = Ventas1(producto=producto, cantidad=cantidad, nombre=nombre, correo=correo)
                db.session.add(nueva_venta)

        try:
            db.session.commit()
            flash("Productos guardados exitosamente en la base de datos.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error al guardar en la base de datos: {e}", "danger")

        return redirect(url_for('product0s'))  # Redirige al menú después de confirmar

    elif accion == 'retornar':
        # Redirigir a la página de productos sin hacer nada más
        return redirect(url_for('product0s'))  # Redirige a la página de productos



if __name__ == '__main__':
    print(f"Admin URL: http://localhost:5000/admin/{app.config['ADMIN_URL_SUFFIX']}")  # Imprime la URL de administración
    app.run(debug=True)
