from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel
from pysondb import db
import hashlib

prior_hash = "0"

a=db.getDb("db.json")

app = FastAPI()

class Message(BaseModel):
    message: str
    user: str
    university: str

@app.post("/")
def read_root(
    msg: Message
):
    global prior_hash
    message = f'{msg.message}, {msg.user}, {msg.university}'
    hash_object = hashlib.sha256(message.encode('utf-8'))
    hex_dig = str(hash_object.hexdigest())
    obj = {"message": message, "prev_hash": prior_hash, "signature": hex_dig}
    a.add(obj)
    prior_hash = hex_dig
    return
