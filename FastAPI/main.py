import secrets
import smtplib
import string
from email.mime.text import MIMEText
from typing import List


import uvicorn
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
import pyodbc
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
import bcrypt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
import os
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from starlette import status

app = FastAPI()


# Función para obtener conexión a SQL Server con autenticación integrada de Windows
def get_db_connection():
    server = "DESKTOP-I7CE289\\SQLEXPRESS"  # Tu servidor
    database = "ss"  # Tu base de datos
    connection_string = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};"
        f"DATABASE={database};Trusted_Connection=yes"  # Autenticación integrada
    )

    try:
        connection = pyodbc.connect(connection_string)
    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar con la base de datos: {str(e)}")

    return connection  # Devolver la conexión directamente


class UpdatePasswordRequest(BaseModel):
    email: str
    new_password: str
# Endpoint para actualizar la contraseña
@app.put("/update-password")
def update_password(request: UpdatePasswordRequest, db_connection: pyodbc.Connection = Depends(get_db_connection)):
    # Hash de la nueva contraseña
    hashed_password = bcrypt.hashpw(request.new_password.encode('utf-8'), bcrypt.gensalt())

    # Crea la consulta SQL para actualizar la contraseña
    query = "UPDATE USERS SET PASSWORD = ? WHERE EMAIL = ?"

    # Crear el cursor
    cursor = db_connection.cursor()

    # Ejecutar la consulta con parámetros para evitar SQL Injection
    cursor.execute(query, (hashed_password.decode('utf-8'), request.email))

    # Confirmar los cambios en la base de datos
    db_connection.commit()

    # Imprimir mensaje para confirmar
    print("Contraseña actualizada exitosamente")

    # Cerrar el cursor y la conexión
    cursor.close()

    return {"message": "Contraseña actualizada exitosamente"}

def get_db():
    db = get_db_connection()
    try:
        yield db
    finally:
        db.close()

# Modelos de datos
class ProductCreate(BaseModel):
    id_categorie: int
    id_measure_prod: int
    product_name: str
    unit_value: float
    quantity: float
    description: str
    location: str
    image: str

class ProductUpdate(BaseModel):
    id_categorie: int
    id_measure_prod: int
    product_name: str
    unit_value: float
    quantity: float
    description: str
    location: str
    image: str

class LoginRequest(BaseModel):
    email: str
    password: str



class CartItem(BaseModel):
    id_publish_prod: int
    quantity: int

class CartItems(BaseModel):
    cart_items: List[CartItem]

class User(BaseModel):
    id_user: int
    id_person: int
    password: str
    email: str
    credit_number: str
    is_admin: int


class Product(BaseModel):
    id_product: int
    id_categorie: int
    id_measure_prod: int
    product_name: str
    unit_value: float
    quantity: float
    description: str
    location: str
    image: str

class Category(BaseModel):
    id_categorie: int
    name_categorie: str



class Person(BaseModel):
    first_name: str
    last_name: str
    doc_type: str
    doc_number: str
    phone_number: str
    location: str
# Modelo para crear usuarios
class UserCreate(BaseModel):
    person: Person
    email: str
    credit_number: str
    password: str

@app.post("/register", response_model=UserCreate)
def register_user(user_data: UserCreate, db: pyodbc.Connection = Depends(get_db_connection)):
    cursor = db.cursor()
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), salt)

    # Insertar en PERSONS
    cursor.execute(
        """
        INSERT INTO PERSONS (FIRST_NAME, LAST_NAME, DOC_TYPE, DOC_NUMBER, PHONE_NUMBER, LOCATION)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_data.person.first_name,
            user_data.person.last_name,
            user_data.person.doc_type,
            user_data.person.doc_number,
            user_data.person.phone_number,
            user_data.person.location,
        ),
    )

    # Confirmar la inserción
    db.commit()

    # Obtener el ID del último registro
    cursor.execute("SELECT MAX(ID_PERSON) FROM PERSONS")
    row = cursor.fetchone()
    person_id = row[0]

    # Insertar en USERS
    cursor.execute(
        """
        INSERT INTO USERS (ID_PERSON, PASSWORD, EMAIL, IS_ADMIN, CREDIT_NUMBER)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            person_id,
            hashed_password,  # Usar el hash de la contraseña
            user_data.email,
            0,  # No administradores por defecto
            user_data.credit_number,  # Corregir nombre de campo
        ),
    )

    # Confirmar la inserción
    db.commit()

    return user_data


@app.post("/logink")
def login(login_data: LoginRequest, db: pyodbc.Connection = Depends(get_db_connection)):
    cursor = db.cursor()

    # Verificar si el email existe en la base de datos
    cursor.execute("SELECT PASSWORD FROM USERS WHERE EMAIL = ?", login_data.email)
    result = cursor.fetchone()
    print(result)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    hashed_password = result[0]

    # Asegúrate de que el hash es del tipo correcto
    if not isinstance(hashed_password, bytes):
        hashed_password = hashed_password.encode("utf-8")

    # Verificar la contraseña
    if bcrypt.checkpw(login_data.password.encode("utf-8"), hashed_password):
        # Contraseña correcta, obtener información del usuario
        cursor.execute("SELECT ID_USER, ID_PERSON, EMAIL, CREDIT_NUMBER, IS_ADMIN FROM USERS WHERE EMAIL = ?", login_data.email)
        user_row = cursor.fetchone()
        cursor.close()

        if not user_row:
            raise HTTPException(status_code=500, detail="User data not found after successful login")

        # Devuelve los detalles del usuario
        return {
            "id_user": user_row[0],
            "id_person": user_row[1],
            "email": user_row[2],
            "credit_number": user_row[3],
            "is_admin": user_row[4],
        }
    else:
        cursor.close()
        raise HTTPException(status_code=401, detail="Invalid email or password")


@app.get("/users", response_model=List[User])
def get_users(db: pyodbc.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT ID_USER, ID_PERSON, PASSWORD, EMAIL, CREDIT_NUMBER, IS_ADMIN FROM USERS")
    users = []
    for row in cursor.fetchall():
        user = User(
            id_user=row[0],
            id_person=row[1],
            password=row[2],
            email=row[3],
            credit_number=row[4],
            is_admin=row[5]
        )
        print("dsfdsf",row[0])
        users.append(user)

    cursor.close()
    return users



#---------------------------------------------------------------------------------------



# Endpoint para publicar un producto
@app.post("/products/{user_id}", response_model=Product)
def publish_product(user_id: int, product: ProductCreate, db: pyodbc.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO PRODUCTS (ID_CATEGORIE, ID_MEASURE_PROD, PRODUCT_NAME, UNIT_VALUE, QUANTITY, DESCRIPTION, LOCATION, IMAGE)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product.id_categorie,
            product.id_measure_prod,
            product.product_name,
            product.unit_value,
            product.quantity,
            product.description,
            product.location,
            product.image,
        ),
    )

    # Obtener el ID del último registro insertado en PRODUCTS
    cursor.execute("SELECT MAX(ID_PRODUCT) FROM PRODUCTS")
    row = cursor.fetchone()
    product_id = row[0]

    cursor.execute(
        "INSERT INTO PUBLISH_PRODUCT (ID_PRODUCT, ID_USER) VALUES (?, ?)",
        (product_id, user_id),
    )
    db.commit()
    cursor.close()
    return Product(
        id_product=product_id,
        id_categorie=product.id_categorie,
        id_measure_prod=product.id_measure_prod,
        product_name=product.product_name,
        unit_value=product.unit_value,
        quantity=product.quantity,
        description=product.description,
        location=product.location,
        image=product.image,
    )


@app.get("/products", response_model=list[Product])
def get_products(db: pyodbc.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT ID_PRODUCT, ID_CATEGORIE, ID_MEASURE_PROD, PRODUCT_NAME, UNIT_VALUE, QUANTITY, DESCRIPTION, LOCATION, IMAGE
        FROM PRODUCTS
        """
    )
    rows = cursor.fetchall()
    products = []
    for row in rows:
        product = Product(
            id_product=row[0],
            id_categorie=row[1],
            id_measure_prod=row[2],
            product_name=row[3],
            unit_value=row[4],
            quantity=row[5],
            description=row[6],
            location=row[7],
            image=row[8]
        )
        products.append(product)
    cursor.close()
    return products
@app.get("/products/name/{product_name}", response_model=list[Product])
def get_products_by_name(product_name: str, db: pyodbc.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT ID_PRODUCT, ID_CATEGORIE, ID_MEASURE_PROD, PRODUCT_NAME, UNIT_VALUE, QUANTITY, DESCRIPTION, LOCATION, IMAGE
        FROM PRODUCTS
        WHERE PRODUCT_NAME LIKE ?
        """,
        ('%' + product_name + '%',)
    )
    rows = cursor.fetchall()
    products = []
    for row in rows:
        product = Product(
            id_product=row[0],
            id_categorie=row[1],
            id_measure_prod=row[2],
            product_name=row[3],
            unit_value=row[4],
            quantity=row[5],
            description=row[6],
            location=row[7],
            image=row[8]
        )
        products.append(product)
    cursor.close()
    return products

# Endpoint para editar producto
@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, product: ProductUpdate, db: pyodbc.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        """
        UPDATE PRODUCTS
        SET ID_CATEGORIE = ?, ID_MEASURE_PROD = ?, PRODUCT_NAME = ?, UNIT_VALUE = ?, QUANTITY = ?, DESCRIPTION = ?, LOCATION = ?, IMAGE = ?
        WHERE ID_PRODUCT = ?
        """,
        (
            product.id_categorie,
            product.id_measure_prod,
            product.product_name,
            product.unit_value,
            product.quantity,
            product.description,
            product.location,
            product.image,
            product_id,
        ),
    )
    db.commit()
    cursor.close()
    return Product(
        id_product=product_id,
        id_categorie=product.id_categorie,
        id_measure_prod=product.id_measure_prod,
        product_name=product.product_name,
        unit_value=product.unit_value,
        quantity=product.quantity,
        description=product.description,
        location=product.location,
        image=product.image,
    )



@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: pyodbc.Connection = Depends(get_db)):
    cursor = db.cursor()

    # Eliminar registros relacionados en PUBLISH_PRODUCT
    cursor.execute(
        """
        DELETE FROM PUBLISH_PRODUCT
        WHERE ID_PRODUCT = ?
        """,
        (product_id,)
    )

    # Eliminar el producto de PRODUCTS
    cursor.execute(
        """
        DELETE FROM PRODUCTS
        WHERE ID_PRODUCT = ?
        """,
        (product_id,)
    )

    db.commit()
    cursor.close()
    return None

#----------------------------------------------------------------

# Modelo de datos para los productos
class Product(BaseModel):
    id_product: int
    id_categorie: int
    id_measure_prod: int
    product_name: str
    unit_value: float
    quantity: float
    description: str
    location: str
    image: str


#----------------------------------------------------------------


# Endpoint para eliminar usuario
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: pyodbc.Connection = Depends(get_db)):
    cursor = db.cursor()
    # Eliminar las referencias en PUBLISH_PRODUCT
    cursor.execute("DELETE FROM PUBLISH_PRODUCT WHERE ID_USER = ?", user_id)

    # Ahora puedes eliminar el usuario
    cursor.execute("DELETE FROM USERS WHERE ID_USER = ?", user_id)

    db.commit()
    cursor.close()
    return {"message": "User deleted successfully"}

# Endpoint para obtener todos los usuarios

# Endpoint para obtener todos los usuarios
@app.get("/users", response_model=List[User])
def get_users(db=Depends(get_db_connection)):
    cursor = db.cursor()
    cursor.execute("SELECT ID_USER, ID_PERSON, PASSWORD, EMAIL, CREDIT_NUMBER, IS_ADMIN FROM USERS")
    users = []
    for row in cursor.fetchall():
        # Crear instancias de User usando argumentos nombrados
        user = User(
            id_user=row[0],
            id_person=row[1],
            password=row[2],
            email=row[3],
            credit_number=row[4],
            is_admin=row[5]
        )
        users.append(user)

    cursor.close()
    return users

# Endpoint para obtener usuario por ID

# Get un usuario por ID
@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, db=Depends(get_db_connection)):
    cursor = db.cursor()
    # Asegúrate de seleccionar las columnas correctas
    cursor.execute("SELECT ID_USER, ID_PERSON, PASSWORD, EMAIL, CREDIT_NUMBER, IS_ADMIN FROM USERS WHERE ID_USER = ?",
                   user_id)
    row = cursor.fetchone()

    if row:
        # Crear la instancia de User con argumentos nombrados
        user = User(
            id_user=row[0],
            id_person=row[1],
            password=row[2],
            email=row[3],
            credit_number=row[4],
            is_admin=row[5]
        )
        cursor.close()
        return user

    cursor.close()
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

# Endpoint para eliminar producto (solo para administradores)




from dotenv import load_dotenv

load_dotenv()  # Cargar las variables de entorno desde el archivo .env

SECRET_KEY='tu_clave_secreta'
ALGORITHM='HS256'
ACCESS_TOKEN_EXPIRE_MINUTES=30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except jwt.JWTError:
        raise credentials_exception
    return token_data





class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/login")
def login(login_data: LoginRequest, db: pyodbc.Connection = Depends(get_db_connection)):
    # Verificar las credenciales del usuario en la base de datos
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT password
        FROM users
        WHERE email = ?
        """,
        (login_data.email,)
    )
    result = cursor.fetchone()
    cursor.close()

    if result is None:
        raise HTTPException(status_code=400, detail="Correo electrónico o contraseña incorrectos")

    password_hash = result[0]

    # Verificar si la contraseña proporcionada coincide con el hash almacenado
    if not bcrypt.checkpw(login_data.password.encode('utf-8'), password_hash.encode('utf-8')):
        raise HTTPException(status_code=400, detail="Correo electrónico o contraseña incorrectos")

    # Si la autenticación es exitosa, crear un token JWT
    access_token = create_access_token(data={"sub": login_data.email})
    return {"access_token": access_token, "token_type": "bearer"}


# Modelo para la solicitud de recuperación
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

# Función para enviar el correo con el código de recuperación
def send_recovery_email(to_email, recovery_code):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    msg = MIMEText(f"Tu código de recuperación es: {recovery_code}")
    msg["Subject"] = "Recuperación de contraseña"
    msg["From"] = smtp_username
    msg["To"] = to_email

    with smtplib.SMTP(smtp_server, smtp_port) as smtp:
        smtp.starttls()  # Para conexiones seguras
        smtp.login(smtp_username, smtp_password)
        smtp.send_message(msg)

# Generar un código de recuperación único
def generate_recovery_code():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
@app.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest):
    email = request.email
    recovery_code = generate_recovery_code()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Verifica si el correo está en la tabla de usuarios
        cursor.execute("SELECT id_user FROM Users WHERE email = ?", (email,))
        result = cursor.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Correo electrónico no registrado")

    id_user = result[0]
    expiration_time = datetime.now() + timedelta(minutes=15)  # Código válido por 15 minutos

    # Almacena el código de recuperación en la base de datos
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO RecoveryCodes (id_user, code, expiration_time) VALUES (?, ?, ?)",
            (id_user, recovery_code, expiration_time)
        )
        conn.commit()

    # Envía el código al usuario por correo electrónico
    send_recovery_email(email, recovery_code)

    return {"message": "Código de recuperación enviado a tu correo electrónico"}


# Modelo para restablecer la contraseña
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

@app.post("/reset-password")
def reset_password(request: ResetPasswordRequest):
    email = request.email
    code = request.code
    new_password = request.new_password

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Verifica si el código es válido y no ha expirado
        cursor.execute(
            "SELECT id_user FROM RecoveryCodes WHERE code = ? AND expiration_time > ?",
            (code, datetime.now())
        )
        result = cursor.fetchone()

    if not result:
        raise HTTPException(status_code=400, detail="Código no válido o expirado")

    id_user = result[0]

    # Restablecer la contraseña
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Users SET password = ? WHERE id_user = ?",
            (new_password, id_user)
        )
        conn.commit()

    return {"message": "Contraseña restablecida con éxito"}


# Función para obtener al usuario actual (ejemplo básico)
async def get_current_user(token: str = Depends(oauth2_scheme), db: pyodbc.Connection = Depends(get_db_connection)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except jwt.JWTError:
        raise credentials_exception

    # Obtener la información del usuario de la base de datos usando el correo electrónico
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT id_user
        FROM users
        WHERE email = ?
        """,
        (token_data.email,)
    )
    result = cursor.fetchone()
    cursor.close()

    if result is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user_id = result[0]
    current_user = {"id_user": user_id}
    return current_user



# Función para crear un carrito de compras
@app.post("/crear_carrito")
def crear_carrito(current_user=Depends(get_current_user), db=Depends(get_db)):
    cursor = db.cursor()

    # Verificar si ya existe un carrito para el usuario actual
    cursor.execute("""
        SELECT ID_SHOP_CAR
        FROM SHOPPING_CARS
        WHERE ID_USER = ?
    """, (current_user["id_user"],))
    existing_cart = cursor.fetchone()

    if existing_cart:
        cursor.close()
        return {"mensaje": "Ya existe un carrito para el usuario actual"}

    # Si no existe un carrito, crear uno nuevo
    cursor.execute("""
        INSERT INTO SHOPPING_CARS (ID_USER)
        VALUES (?)
    """, (current_user["id_user"],))
    db.commit()

    cursor.execute("""
        SELECT ID_SHOP_CAR
        FROM SHOPPING_CARS
        WHERE ID_USER = ?
    """, (current_user["id_user"],))
    cart_id = cursor.fetchone()[0]

    cursor.close()
    return {"mensaje": "Carrito creado exitosamente", "id_carrito": cart_id}


from typing import List
from pydantic import BaseModel

class CartItem(BaseModel):
    id_publish_prod: int
    quantity: int

class CartItems(BaseModel):
    cart_items: List[CartItem]

# Función para agregar productos al carrito
@app.post("/agregar_al_carrito")
def agregar_al_carrito(items: CartItems, current_user=Depends(get_current_user), db=Depends(get_db)):
    cursor = db.cursor()

    # Verificar si el usuario tiene un carrito de compras
    cursor.execute("""
        SELECT ID_SHOP_CAR
        FROM SHOPPING_CARS
        WHERE ID_USER = ?
    """, (current_user["id_user"],))
    shopping_cart = cursor.fetchone()

    if not shopping_cart:
        # Si el usuario no tiene un carrito de compras, crear uno nuevo
        cursor.execute("""
            INSERT INTO SHOPPING_CARS (ID_USER)
            VALUES (?)
        """, (current_user["id_user"],))
        db.commit()
        shopping_cart_id = cursor.lastrowid
    else:
        shopping_cart_id = shopping_cart[0]

    for item in items.cart_items:
        # Verificar si el producto ya está en el carrito
        cursor.execute("""
            SELECT *
            FROM PRODUCTS_ADDED
            WHERE ID_SHOP_CAR = ?
              AND ID_PUBLISH_PROD = ?
        """, (shopping_cart_id, item.id_publish_prod))
        existing_item = cursor.fetchone()

        if existing_item:
            # Si el producto ya está en el carrito, actualizar la cantidad
            cursor.execute("""
                UPDATE PRODUCTS_ADDED
                SET QUANTITY = QUANTITY + ?
                WHERE ID_SHOP_CAR = ?
                  AND ID_PUBLISH_PROD = ?
            """, (item.quantity, shopping_cart_id, item.id_publish_prod))
        else:
            # Si el producto no está en el carrito, crear un nuevo registro
            cursor.execute("""
                INSERT INTO PRODUCTS_ADDED (ID_SHOP_CAR, ID_PUBLISH_PROD, QUANTITY)
                VALUES (?, ?, ?)
            """, (shopping_cart_id, item.id_publish_prod, item.quantity))

    db.commit()
    cursor.close()
    return {"mensaje": "Productos agregados al carrito"}
if _name_ == "_main_":
    uvicorn.run(app, host="0.0.0.0", port=8000)
