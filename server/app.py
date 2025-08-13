# FastAPI - Víctima: verificación con hash truncado + modo DEMO + modo CTF

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import hashlib, hmac, os, secrets

app = FastAPI(title="PoC03 - Victim (Truncated Hash Verify)")

# =========================
# CONFIG
# =========================
SECRET   = os.environ.get("LAB_SECRET", "super_secret_demo_key").encode()
LAB_DEBUG = os.environ.get("LAB_DEBUG", "0") == "1"   # permite /challenge_debug
CTF_MODE  = os.environ.get("LAB_CTF",  "0") == "1"   # agrega flag en /verify si acierta

# =========================
# HELPERS
# =========================
def h_truncated(msg: bytes, bits: int) -> str:
    """SHA-256(SECRET || msg) y trunca a 'bits' bits en binario."""
    h = hashlib.sha256(SECRET + msg).digest()
    return "".join(f"{b:08b}" for b in h)[:bits]

# =========================
# MODELOS
# =========================
class VerifyReq(BaseModel):
    msg: str
    proof_bits: str
    nbits: int

class DebugReq(BaseModel):
    msg: str
    nbits: int

# =========================
# ENDPOINTS
# =========================
@app.get("/challenge")
def challenge(nbits: int = 8):
    """Devuelve un mensaje aleatorio y el tamaño de hash truncado esperado."""
    if not (1 <= nbits <= 64):
        raise HTTPException(400, "nbits inválido (1..64)")
    msg = secrets.token_hex(4)  # mensaje corto aleatorio
    return {"msg": msg, "nbits": nbits}

@app.post("/challenge_debug")
def challenge_debug(req: DebugReq):
    """Solo demo: revela el objetivo para construir el oráculo."""
    if not LAB_DEBUG:
        raise HTTPException(403, "debug deshabilitado")
    if not (1 <= req.nbits <= 64):
        raise HTTPException(400, "nbits inválido (1..64)")
    return {"target": h_truncated(req.msg.encode(), req.nbits), "nbits": req.nbits}

@app.post("/verify")
def verify(req: VerifyReq):
    """Verifica el bitstring propuesto contra el hash truncado."""
    if not (1 <= req.nbits <= 64):
        raise HTTPException(400, "nbits inválido (1..64)")
    if any(c not in "01" for c in req.proof_bits):
        raise HTTPException(400, "proof_bits debe ser binario")
    if len(req.proof_bits) != req.nbits:
        raise HTTPException(400, "proof_bits debe tener longitud nbits")

    target = h_truncated(req.msg.encode(), req.nbits)
    ok = hmac.compare_digest(target, req.proof_bits)

    if CTF_MODE and ok:
        # Flag no revela el bitstring; ata el éxito a este msg concreto.
        flag = f"flag{{grover_ok::{req.msg}}}"
        return {"ok": True, "nbits": req.nbits, "flag": flag}

    return {"ok": ok, "nbits": req.nbits}
