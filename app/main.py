from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import socket

app = FastAPI()
security = HTTPBearer()

# Táctica: Validar la Entrada (Esquema estricto)
class PayloadModel(BaseModel):
    item_id: int = Field(..., gt=0, description="Debe ser un entero positivo")
    name: str = Field(..., min_length=3, description="Nombre con al menos 3 caracteres")

# Táctica: Autenticar Actores (Verificación de Identidad)
async def auth_handler(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "TFU-UT2-SECRET-KEY":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identidad no verificada"
        )
    return credentials.credentials

@app.post("/process")
async def process_data(data: PayloadModel, token: str = Depends(auth_handler)):
    # Reportamos el hostname para evidenciar qué réplica específica responde
    return {
        "status": "success",
        "processed_by": socket.gethostname(),
        "received": data.model_dump() if hasattr(data, "model_dump") else data.dict()
    }
