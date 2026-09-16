from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/rides", tags=["Rides"])


# ============================================================
# MODELOS
# ============================================================

class RideCreate(BaseModel):
    name: str = Field(..., min_length=3)
    price: float = Field(..., gt=0)
    capacity: int = Field(..., gt=0)


class RideUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3)
    price: float | None = Field(default=None, gt=0)
    capacity: int | None = Field(default=None, gt=0)


class RideStatusUpdate(BaseModel):
    status: str


# ============================================================
# BASE DE DATOS TEMPORAL
# ============================================================

rides = {}

next_ride_id = 1


# ============================================================
# CREAR ATRACCIÓN
# ============================================================

@router.post("/", status_code=201)
def create_ride(ride: RideCreate):
    global next_ride_id

    new_ride = {
        "id": next_ride_id,
        "name": ride.name,
        "price": ride.price,
        "capacity": ride.capacity,
        "current_occupancy": 0,
        "status": "active"
    }

    rides[next_ride_id] = new_ride

    next_ride_id += 1

    return new_ride


# ============================================================
# ELIMINAR ATRACCIÓN
# ============================================================

@router.delete("/{ride_id}")
def delete_ride(ride_id: int):

    if ride_id not in rides:
        raise HTTPException(
            status_code=404,
            detail="Atracción no encontrada"
        )

    del rides[ride_id]

    return {
        "message": "Atracción eliminada correctamente"
    }


# ============================================================
# MODIFICAR ATRACCIÓN
# ============================================================

@router.patch("/{ride_id}")
def update_ride(ride_id: int, ride: RideUpdate):

    if ride_id not in rides:
        raise HTTPException(
            status_code=404,
            detail="Atracción no encontrada"
        )

    current_ride = rides[ride_id]

    if ride.name is not None:
        current_ride["name"] = ride.name

    if ride.price is not None:
        current_ride["price"] = ride.price

    if ride.capacity is not None:

        if ride.capacity < current_ride["current_occupancy"]:
            raise HTTPException(
                status_code=400,
                detail="La capacidad no puede ser menor a la ocupación actual"
            )

        current_ride["capacity"] = ride.capacity

    return current_ride


# ============================================================
# CAMBIAR ESTADO
# ============================================================

@router.patch("/{ride_id}/status")
def change_ride_status(
    ride_id: int,
    status_update: RideStatusUpdate
):

    if ride_id not in rides:
        raise HTTPException(
            status_code=404,
            detail="Atracción no encontrada"
        )

    if status_update.status not in ["active", "out_of_service"]:
        raise HTTPException(
            status_code=400,
            detail="Estado inválido. Usar 'active' o 'out_of_service'"
        )

    rides[ride_id]["status"] = status_update.status

    return rides[ride_id]


# ============================================================
# OBTENER ATRACCIÓN
# ============================================================

@router.get("/{ride_id}")
def get_ride(ride_id: int):

    if ride_id not in rides:
        raise HTTPException(
            status_code=404,
            detail="Atracción no encontrada"
        )

    return rides[ride_id]
