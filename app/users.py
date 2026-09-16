from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import bcrypt
from datetime import datetime, timedelta


router = APIRouter(prefix="/users", tags=["Users"])


# --------------------------------------------------
# Modelos de entrada
# --------------------------------------------------

class UserCreate(BaseModel):
    name: str = Field(..., min_length=3)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: str
    password: str


# --------------------------------------------------
# Almacenamiento temporal
# --------------------------------------------------

users = {}
next_user_id = 1


# --------------------------------------------------
# Representación pública del usuario
# --------------------------------------------------

def public_user(user):
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "active": user["active"]
    }


# --------------------------------------------------
# Registrar usuario
# --------------------------------------------------

@router.post("/", status_code=201)
def create_user(user: UserCreate):
    global next_user_id

    email = user.email.strip().lower()

    # Comprobar si el email ya existe
    for existing_user in users.values():
        if existing_user["email"] == email:
            raise HTTPException(
                status_code=409,
                detail="El email ya está registrado"
            )

    # Crear hash de la contraseña
    password_hash = bcrypt.hashpw(
        user.password.encode("utf-8"),
        bcrypt.gensalt()
    )

    new_user = {
        "id": next_user_id,
        "name": user.name.strip(),
        "email": email,
        "password_hash": password_hash,
        "active": True,
        "failed_attempts": 0,
        "locked_until": None
    }

    users[next_user_id] = new_user
    next_user_id += 1

    return public_user(new_user)


# --------------------------------------------------
# Iniciar sesión
# --------------------------------------------------

@router.post("/login")
def login(user: UserLogin):

    email = user.email.strip().lower()

    # Buscar usuario
    found_user = None

    for existing_user in users.values():
        if existing_user["email"] == email:
            found_user = existing_user
            break

    if found_user is None:
        raise HTTPException(
            status_code=401,
            detail="Usuario o contraseña incorrectos"
        )

    # Comprobar si el usuario está dado de baja
    if not found_user["active"]:
        raise HTTPException(
            status_code=403,
            detail="El usuario está dado de baja"
        )

    # Comprobar si la cuenta está temporalmente bloqueada
    if (
        found_user["locked_until"] is not None
        and found_user["locked_until"] > datetime.now()
    ):
        raise HTTPException(
            status_code=401,
            detail="La cuenta está temporalmente bloqueada"
        )

    # Comprobar contraseña
    password_ok = bcrypt.checkpw(
        user.password.encode("utf-8"),
        found_user["password_hash"]
    )

    if not password_ok:

        found_user["failed_attempts"] += 1

        # Bloquear después de 5 intentos
        if found_user["failed_attempts"] >= 5:
            found_user["locked_until"] = (
                datetime.now() + timedelta(minutes=15)
            )

        raise HTTPException(
            status_code=401,
            detail="Usuario o contraseña incorrectos"
        )

    # Login correcto: reiniciar contador
    found_user["failed_attempts"] = 0
    found_user["locked_until"] = None

    return {
        "message": "Inicio de sesión exitoso",
        "user": public_user(found_user)
    }


# --------------------------------------------------
# Dar de baja usuario
# --------------------------------------------------

@router.delete("/{user_id}")
def delete_user(user_id: int):

    if user_id not in users:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    users[user_id]["active"] = False

    return {
        "message": "Usuario dado de baja correctamente"
    }
