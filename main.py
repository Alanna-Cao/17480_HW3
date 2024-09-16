from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel
import logging
from model import ObjectPoolManagement, registered_types, InputTooLargeError
from typing import Dict
import os

app = FastAPI(
    title="Object Pool Management API",
    description=(
        "**The Object Pool Management API** provides functionalities for managing pools of objects by type. Users can create pools for different object types (e.g., shirts, books), add or remove objects from these pools, and retrieve a random object from a specific pool. Each pool is identified by the type name of objects it contains.\n"
        "\nThe API checks the object type before adding to or removing from pools.\n\n"
        "**Key Features:**\n"
        "- **Create pools** for different object types (e.g., shirts, books).\n"
        "- **Add object** to the pool.\n"
        "- **Remove object** from the pool.\n"
        "- **Retrieve a random object** from a specified pool.\n\n"
        "**Example Usage:**\n"
        "To retrieve a random shirt from the 'Shirt' pool:\n\n"
        "```bash\n"
        "curl -X GET \"http://localhost:8000/get-random/?type_name=Shirt\"\n"
        "```\n"
        "**Response:**\n"
        "```json\n"
        "{\n"
        "    \"size\": \"M\",\n"
        "    \"color\": \"blue\"\n"
        "}\n"
        "```\n\n"
        "**Note:** Replace 'Shirt' with other object types as needed."
    )
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to store pools for different types
pools: Dict[str, ObjectPoolManagement] = {}

# Retrieve max_size from environment variable or use default. Default max size of list in Python is 536870912.
max_size = int(os.getenv("MAX_POOL_SIZE", 536870912))

class Shirt(BaseModel):
    size: str
    color: str

class Book(BaseModel):
    title: str
    author: str

@app.post("/create-pool/",
          summary="Create an Object Pool",
          description=(
              "**This endpoint initializes a pool for a specified object type.**\n\n"
              "**Parameters:**\n"
              "- **type_name** (str): The name of the object type for which the pool is to be created. The name must match a registered object type.\n\n"
              "**Responses:**\n"
              "- **200:** Pool created successfully.\n"
              "- **400:** Pool already exists or the object type is not registered.\n"
               "\n**Example Usage:**\n"
                "```bash\n"
                "curl -X GET \"http://localhost:8000/create-pool/?type_name=Shirt\"\n"
                "```\n"
                "**Response:**\n"
                "```json\n"
                "{ Pool created successfully } \n"
                "```\n\n"
          ),
          tags=["Object Pool Management"],
          responses={
            200: {
                "description": "Pool created successfully",
                "content": {
                    "application/json": {
                        "example": {"message": "Pool created for type Shirt"}
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
    pools[type_name] = ObjectPoolManagement(expected_type=pool_type, max_size=max_size)
    return {"message": f"Pool created for type {type_name}"}

@app.get("/get-random/", 
    summary="Retrieve a Random Object from Pool",
    description=(
        "**This endpoint retrieves a random object from a pool of the specified type.**\n\n"
        "**Parameters:**\n"
        "- **type_name** (str): The name of the object type pool from which a random object will be retrieved.\n\n"
        "**Responses:**\n"
        "- **200:** Successfully retrieved a random object.\n"
        "- **404:** Pool not found or pool is empty.\n"
        "\n **Example Usage:**\n"
        "```bash\n"
        "curl -X GET \"http://localhost:8000/get-random/?type_name=Shirt\"\n"
        "```\n"
        "**Response:**\n"
        "```json\n"
        "{\n"
        "    \"size\": \"M\",\n"
        "    \"color\": \"blue\"\n"
        "}\n"
        "```\n\n"
    ),
    tags=["Object Management"],
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

@app.post("/add-object/",
          summary="Add an Object to Pool",
          description=(
              "**This endpoint allows for users to add an object to a pool of that specified type. The pool must exist.**\n\n"
              "**Parameters:**\n"
              "- **type_name** (str): The object type name of the pool.\n"
              "- **item** (BaseModel): The object to be added to the pool, specified by the pool type.\n\n"
              "**Responses:**\n"
              "- **200:** Object added successfully.\n"
              "- **400:** Object type mismatch or pool size exceeded.\n"
              "- **404:** Pool not found.\n"
              "\n **Example Usage:**\n"
                "```bash\n"
                "curl -X GET \"http://localhost:8000/add-object/?type_name=Shirt\"\n"
                "```\n"
                "**Response:**\n"
                "```json\n"
                "{ Object added successfully } \n"
                "```\n\n"
          ),
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
        example={
            'Book': {
                "title": "1984",
                "author": "George Orwell"
            }
        }
    )
):
    """
    This endpoint allows for users to add an object to a pool of that specified type. The pool type exist.

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

@app.delete("/remove-object/",
            summary="Remove an Object from Pool",
            description=(
                "**This endpoint allows users to remove an object from the specified object pool.**\n\n"
                "**Parameters:**\n"
                "- **type_name** (str): The object type name of the pool.\n"
                "- **item** (BaseModel): The object to be removed from the pool, specified by the pool type.\n\n"
                "**Responses:**\n"
                "- **200:** Object removed successfully.\n"
                "- **404:** Pool not found.\n"
                "- **400:** Object type mismatch.\n"
                "\n **Example Usage:**\n"
                "```bash\n"
                "curl -X GET \"http://localhost:8000/remove-object/?type_name=Shirt\"\n"
                "```\n"
                "**Response:**\n"
                "```json\n"
                "{ Object removed successfully } \n"
                "```\n\n"
            ),
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
                404: {
                    "description": "Pool not found",
                    "content": {
                        "application/json": {
                            "example": {"detail": "Pool not found"}
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
                }
            })
async def remove_object_from_pool(type_name: str = Query(..., description="The object type name of the pool."),
    item: BaseModel = Body(
        ...,
        description="The object to be removed from the pool, specified by the pool type. The pool must exist.",
        example={
            'Shirt': {
                "size": "M",
                "color": "blue"
            },
            'Book': {
                "title": "1984",
                "author": "George Orwell"
            }
        }
    )
):
    """
    This endpoint allows users to remove an object from the specified object pool. The pool must exist.

    Args:
        type_name (str): The object type name of the pool to remove the object from.
        item (BaseModel): The object to be removed from the pool. Must be of the expected type.

    Raises:
        HTTPException: If the pool of the specified type is not found or the object type doesn't match.
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
        raise HTTPException(status_code=400, detail=str(e))

