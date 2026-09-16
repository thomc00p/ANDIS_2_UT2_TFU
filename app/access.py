from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

from cards import cards
from rides import rides


router = APIRouter(prefix="/access", tags=["Access"])


# --------------------------------------------------
# Modelo de entrada
# --------------------------------------------------

class AccessRequest(BaseModel):
    card_id: int = Field(..., gt=0)
    ride_id: int = Field(..., gt=0)


# --------------------------------------------------
# Validar acceso a una atracción
# --------------------------------------------------

@router.post("/validate")
def validate_access(request: AccessRequest):

    if request.card_id not in cards:
        raise HTTPException(
            status_code=404,
            detail="Tarjeta no encontrada"
        )

    card = cards[request.card_id]

    if not card["active"]:
        raise HTTPException(
            status_code=403,
            detail="La tarjeta está dada de baja"
        )

    if request.ride_id not in rides:
        raise HTTPException(
            status_code=404,
            detail="Atracción no encontrada"
        )

    ride = rides[request.ride_id]

    if ride["status"] != "active":
        raise HTTPException(
            status_code=403,
            detail="La atracción está fuera de servicio"
        )

    if ride["current_occupancy"] >= ride["capacity"]:
        raise HTTPException(
            status_code=403,
            detail="La atracción alcanzó su capacidad máxima"
        )

    price = ride["price"]

    if card["balance"] < price:
        raise HTTPException(
            status_code=403,
            detail="Saldo insuficiente"
        )

    card["balance"] -= price

    transaction = {
        "type": "ride_access",
        "ride_id": request.ride_id,
        "amount": price,
        "date": datetime.now().isoformat()
    }

    card["history"].append(transaction)

    ride["current_occupancy"] += 1

    return {
        "message": "Acceso permitido",
        "card_id": request.card_id,
        "ride_id": request.ride_id,
        "charged": price,
        "remaining_balance": card["balance"],
        "current_occupancy": ride["current_occupancy"]
    }
