from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel
import logging
from model import RandomObjectPool, registered_types, InputTooLargeError
from typing import Dict
import os

app = FastAPI(
    title="Random Object Selector API",
    description="An API for managing pools of objects and selecting one at random."
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

'''
Dictionary to store pools for different types
'''
pools: Dict[str, RandomObjectPool] = {}

'''
Retrieve max_size from environment variable or use default. Default max size of list in Python is 536870912.
'''
max_size = int(os.getenv("MAX_POOL_SIZE", 536870912)) 

@app.post("/create_object_pool/", 
          summary="Create an Object Pool", 
          description="""
            This endpoint allows for users to create an object pool for a specified object type. 
            The specified type should match one of the registered object types.
            """, 
          tags=["Object Pool Management"],
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
        })
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
          tags=["Object Management"],
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
        example={ 'Shirt': {
            "size": "M",
            "color": "blue"
        }}
    )
):
    """
    This endpoint allows for users to add an object to a pool of that specified type. The pool should exist.

    Args:
        type_name (str): The object type name of the pool to add the object to.
        item (BaseModel): The object to be added to the pool. Must be of the expected type.

    Raises:
        HTTPException: If the pool of the specified type is not found or the object type doesn't match.
        InputTooLargeError: If the size of the pool is exceeded.
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
            tags=["Object Management"],
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
        example= {'Shirt': {
            "size": "L",
            "color": "red"
        }}
)):
    """
    This endpoint allows users to remove an object from the specified object pool.

    Args:
        type_name (str): The object type name of the pool to remove the object from.
        item (BaseModel): The object to be removed from the pool.

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
    tags=["Object Retrieval"],
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
        return obj.dict()
    except IndexError as e:
        raise HTTPException(status_code=404, detail=str(e))

