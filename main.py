from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random
import logging
import os
from typing import Type, List, Dict, TypeVar, Generic

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a type variable for generics
T = TypeVar('T', bound=BaseModel)

# Define example data models
class Shirt(BaseModel):
    size: str
    color: str

class Pants(BaseModel):
    size: str
    color: str

class Sock(BaseModel):
    size: str
    color: str

# Register types
registered_types: Dict[str, Type[BaseModel]] = {
    "shirt": Shirt,
    "pants": Pants,
    "sock": Sock
}

# Define custom error for handling large input lists
class InputTooLargeError(HTTPException):
    def __init__(self, detail: str = "Input list is too large."):
        super().__init__(status_code=400, detail=detail)

# Define the class to manage the pool of objects
class RandomObjectPool(Generic[T]):
    def __init__(self, expected_type: Type[T], max_size: int):
        self.pool: List[T] = []
        self.expected_type = expected_type
        self.max_size = max_size

    def add_object_to_pool(self, obj: T) -> None:
        if not isinstance(obj, self.expected_type):
            raise ValueError("Object type does not match expected type")
        if len(self.pool) >= self.max_size:
            raise InputTooLargeError()
        self.pool.append(obj)

    def remove_object_from_pool(self, obj: T) -> None:
        if obj not in self.pool:
            raise ValueError("Object not found in pool")
        self.pool.remove(obj)

    def get_random_object_from_pool(self) -> T:
        if not self.pool:
            raise IndexError("No objects in the pool")
        return random.choice(self.pool)

# Dictionary to store pools for different types
pools: Dict[str, RandomObjectPool] = {}

# Retrieve max_size from environment variable or use default
max_size = int(os.getenv("MAX_POOL_SIZE", 536870912))  # Default max size of list in Python is 536870912

@app.post("/create_object_pool/")
async def create_object_pool(type_name: str):
    if type_name in pools:
        raise HTTPException(status_code=400, detail="Pool for this type already exists")
    if type_name not in registered_types:
        raise HTTPException(status_code=400, detail="Type not registered")
    pool_type = registered_types[type_name]
    pools[type_name] = RandomObjectPool(expected_type=pool_type, max_size=max_size)
    return {"message": f"Pool created for type {type_name}"}

@app.post("/add_object_to_pool/")
async def add_object_to_pool(type_name: str, item: BaseModel):
    if type_name not in pools:
        raise HTTPException(status_code=404, detail="Pool not found")
    pool = pools[type_name]
    if not isinstance(item, pool.expected_type):
        raise HTTPException(status_code=400, detail="Object type does not match pool type")
    try:
        pool.add_object_to_pool(item)
        return {"message": "Object added successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InputTooLargeError as e:
        raise e

@app.delete("/remove/")
async def remove_object_from_pool(type_name: str, item: BaseModel):
    if type_name not in pools:
        raise HTTPException(status_code=404, detail="Pool not found")
    pool = pools[type_name]
    if not isinstance(item, pool.expected_type):
        raise HTTPException(status_code=400, detail="Object type does not match pool type")
    try:
        pool.remove_object_from_pool(item)
        return {"message": "Object removed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/random/")
async def get_random_object_from_pool(type_name: str):
    if type_name not in pools:
        raise HTTPException(status_code=404, detail="Pool not found")
    pool = pools[type_name]
    try:
        obj = pool.get_random_object_from_pool()
        return obj.dict()  # Use `dict()` to return the object's data
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))
