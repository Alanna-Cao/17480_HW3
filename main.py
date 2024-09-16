from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel
import random
import logging
import os
from typing import Type, List, Dict, TypeVar, Generic

app = FastAPI(
    title="Random Object Selector API",
    description="An API for managing pools of objects and selecting one at random."
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a type variable for generics
T = TypeVar('T', bound=BaseModel)

# Define example data models
class Shirt(BaseModel):
    """
    Model representing a Shirt.
    """
    size: str
    color: str

class Pants(BaseModel):
    """
    Model representing a Pants.
    """
    size: str
    color: str

class Sock(BaseModel):
    """
    Model representing a Sock.
    """
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
    """
    Exception which is raised when an input list is too large for the pool.
    """
    def __init__(self, detail: str = "Input list is too large."):
        super().__init__(status_code=400, detail=detail)

# Define the class to manage the pool of objects
class RandomObjectPool(Generic[T]):
    """
    Class that manages a pool of objects.
    """
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

@app.post("/create_object_pool/", 
          summary="Create an Object Pool", 
          description="""
            This endpoint allows for users to create an object pool for a specified object type. 
            The specified type should match one of the registered object types.
            """, 
            responses={
            200: {
                "description": "Pool created successfully",
                "content": {
                    "application/json": {
                        "example": {"message": "Pool created for type shirt"}
                    }
                }
            },
            400: {
                "description": "Pool already exists or the type is not registered",
                "content": {
                    "application/json": {
                        "example": {"detail": "Pool for this type already exists"}
                    }
                }
            }
        }
            )
async def create_object_pool(type_name: str = Query(..., description="The object type name for which the pool is to be initialized.")):
    """
    This endpoint allows for users to initialize an object pool for a specified type. 
    The specified type should match one of the registered object types.

    Args:
        type_name (str): The object type name for which the pool is to be initialized.  

    Raises:
        HTTPException: If a pool for the specified object type already exists or if the object type is not registered.
    """
    if type_name in pools:
        raise HTTPException(status_code=400, detail="Pool for this type already exists")
    if type_name not in registered_types:
        raise HTTPException(status_code=400, detail="Type not registered")
    pool_type = registered_types[type_name]
    pools[type_name] = RandomObjectPool(expected_type=pool_type, max_size=max_size)
    return {"message": f"Pool created for type {type_name}"}


@app.post("/add_object_to_pool/", 
          summary="Add an Object to Pool", 
    description="This endpoint allows for users to add an object to a pool of that specified type. The pool should exist.",
    responses={
        200: {
            "description": "Object added successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Object added successfully"}
                }
            }
        },
        400: {
            "description": "Object type mismatch or pool size exceeded",
            "content": {
                "application/json": {
                    "example": {"detail": "Object type does not match pool type"}
                }
            }
        },
        404: {
            "description": "Pool not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Pool not found"}
                }
            }
        }
    })
async def add_object_to_pool(type_name: str = Query(..., description="The object type name of the pool."),
    item: BaseModel = Body(
        ..., 
        description="The object to be added to the pool, specified by the pool type.", 
        example={
            "size": "M",
            "color": "blue"
        }
    )
):
    """
    This endpoint allows for users to add an object to a pool of that specified type. The pool should exist.

    Args:
        type_name (str): The object type name of the pool to add the object to.
        item (BaseModel): The object to be added to the pool. Must be of the expected type.

    Raises:
        HTTPException: If the pool of the specified type is not found or the object type doesn't match.
    """
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

@app.delete("/remove/",
            summary="Remove an Object from Pool",
    description="This endpoint allows users to remove an object from the specified object pool.",
    responses={
        200: {
            "description": "Object removed successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Object removed successfully"}
                }
            }
        },
        400: {
            "description": "Object type mismatch",
            "content": {
                "application/json": {
                    "example": {"detail": "Object type does not match pool type"}
                }
            }
        },
        404: {
            "description": "Pool or Object not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Pool not found or object not found in pool"}
                }
            }
        }
    })
async def remove_object_from_pool(type_name: str = Query(..., description="The object type name of the pool."),
    item: BaseModel = Body(
        ..., 
        description="The object to be removed from the pool, specified by the pool type.", 
        example={
            "size": "L",
            "color": "red"
        }
)):
    """
    This endpoint allows users to remove an object from the specified object pool.

    Args:
        type_name (str): The object type name of the pool to remove the object from.
        item (Shirt): The object to be removed from the pool.

    Raises:
        HTTPException: If the pool is not found or the object type doesn't match the pool type.
    """
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

@app.get("/random/", 
    summary="Get a Random Object from Pool",
    description="This endpoint allows users to retrieve a random object from the specified object pool.",
    responses={
        200: {
            "description": "Random object retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "size": "M",
                        "color": "blue"
                    }
                }
            }
        },
        404: {
            "description": "Pool not found or pool is empty",
            "content": {
                "application/json": {
                    "example": {"detail": "No objects in the pool"}
                }
            }
        }
    }
)
async def get_random_object_from_pool(
    type_name: str = Query(..., description="The object type name of the pool.")
):
    """
    This endpoint allows users to retrieve a random object from the specified object pool.

    Args:
        type_name (str): The object type name of the pool from which to retrieve a random object.

    Raises:
        HTTPException: If the pool is not found or is empty.
    """
    if type_name not in pools:
        raise HTTPException(status_code=404, detail="Pool not found")
    pool = pools[type_name]
    try:
        obj = pool.get_random_object_from_pool()
        return obj.dict()  # Use `dict()` to return the object's data
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))

