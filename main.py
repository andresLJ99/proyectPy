
"""
API REST con FastAPI para prueba tecnica 
"""
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from tinydb import TinyDB, Query
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

# --- Configuración básica ---
app = FastAPI(
        title="API Prueba Tecnica",
        version="1.0",
        description="API REST que permita la autenticación de un usuario mediante JWT, y que dicho usuario pueda guardar y consultar varios números asociados a su cuenta."
)

# --- Base de datos ---
db = TinyDB("db.json")

# --- Configuración JWT ---
SECRET_KEY = "claveProyectPy"
ALGORITHM = "HS256"
TOKEN_DURATION_MINUTES = 15

oauth2_scheme = HTTPBearer()

# --- Usuario predefinido ---
USER = {"username": "admin", "password": "1234"}

# --- Modelos ---
class LoginData(BaseModel):
    username: str
    password: str

class NumberData(BaseModel):
    value: int = Field(..., gt=0, description="El número debe ser mayor a 0")

# --- Funciones ---
def create_token(username: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_DURATION_MINUTES)
    data = {"sub": username, "exp": expire}
    token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username != USER["username"]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")

# --- Endpoints ---

@app.post("/login")
def login(data: LoginData):
    if data.username == USER["username"] and data.password == USER["password"]:
        token = create_token(data.username)
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

@app.post("/numbers")
def save_number(number: NumberData, username: str = Depends(verify_token)):
    record = {
        "username": username,
        "value": number.value,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    db.insert(record)
    return {"message": "Número guardado correctamente", "data": record}

@app.get("/numbers")
def get_numbers(username: str = Depends(verify_token)):
    UserQuery = Query()
    numbers = db.search(UserQuery.username == username)
    formatted = [
        {"value": n["value"], "created_at": n["created_at"]}
        for n in numbers
    ]
    return {"username": username, "numbers": formatted}

# --- Ejecución ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
