from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime


router = APIRouter(prefix="/cards", tags=["Cards"])


# --------------------------------------------------
# Modelos de entrada
# --------------------------------------------------

class CardCreate(BaseModel):
    user_id: int = Field(..., gt=0)


class CardRecharge(BaseModel):
    amount: float = Field(..., gt=0)


# --------------------------------------------------
# Almacenamiento temporal
# --------------------------------------------------

cards = {}
next_card_id = 1


# --------------------------------------------------
# Crear tarjeta
# --------------------------------------------------

@router.post("/", status_code=201)
def create_card(card: CardCreate):
    global next_card_id

    new_card = {
        "id": next_card_id,
        "user_id": card.user_id,
        "balance": 0.0,
        "active": True,
        "history": []
    }

    cards[next_card_id] = new_card
    next_card_id += 1

    return new_card


# --------------------------------------------------
# Dar de baja una tarjeta
# --------------------------------------------------

@router.delete("/{card_id}")
def delete_card(card_id: int):

    if card_id not in cards:
        raise HTTPException(
            status_code=404,
            detail="Tarjeta no encontrada"
        )

    cards[card_id]["active"] = False

    return {
        "message": "Tarjeta dada de baja correctamente"
    }


# --------------------------------------------------
# Recargar tarjeta
# --------------------------------------------------

@router.patch("/{card_id}/recharge")
def recharge_card(card_id: int, recharge: CardRecharge):

    if card_id not in cards:
        raise HTTPException(
            status_code=404,
            detail="Tarjeta no encontrada"
        )

    card = cards[card_id]

    if not card["active"]:
        raise HTTPException(
            status_code=403,
            detail="La tarjeta está dada de baja"
        )

    # Actualizar saldo
    card["balance"] += recharge.amount

    # Registrar la operación
    transaction = {
        "type": "recharge",
        "amount": recharge.amount,
        "date": datetime.now().isoformat()
    }

    card["history"].append(transaction)

    return card


# --------------------------------------------------
# Consultar tarjeta
# --------------------------------------------------

@router.get("/{card_id}")
def get_card(card_id: int):

    if card_id not in cards:
        raise HTTPException(
            status_code=404,
            detail="Tarjeta no encontrada"
        )

    card = cards[card_id]

    return {
        "id": card["id"],
        "user_id": card["user_id"],
        "balance": card["balance"],
        "active": card["active"]
    }


# --------------------------------------------------
# Consultar historial
# --------------------------------------------------

@router.get("/{card_id}/history")
def get_card_history(card_id: int):

    if card_id not in cards:
        raise HTTPException(
            status_code=404,
            detail="Tarjeta no encontrada"
        )

    return {
        "card_id": card_id,
        "history": cards[card_id]["history"]
    }
