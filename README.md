# 17480 HW3 Part 2: Random Object Pool API
## Overview
The Random Object Pool API is a FastAPI-based service for managing a pool of objects of various types and selecting a random object from the pool. This API allows users to create pools for different types of objects, add or remove objects from these pools, and retrieve a random object from a specified pool.

## Features
- Create Object Pools: Define and create pools for different object types.
- Add Objects: Add objects to a specific pool.
- Remove Objects: Remove objects from a pool.
- Select Random Object: Retrieve a random object from a specified pool.

## Usage
### Setup
1. **Install Dependencies**: Ensure that you have uvicorn and any other dependencies required for FastAPI. You can install the required packages using pip:
```
pip install fastapi uvicorn
```
2. **Run the API**: Start the FastAPI server with the following command:
```
uvicorn main:app --reload
```

By default, the server will run on http://127.0.0.1:8000.


### Interact with the API
Test out the functionality of the API by navigating to the endpoints, listed and explained below. To access the auto-generated interactive documentation created through Swagger UI and ReDoc, navigate to /docs and /redoc


## API Endpoints
- /create_object_pool/: Create a new object pool for a specified type.
- /add_object_to_pool/: Add an object to an existing pool.
- /remove/: Remove an object from a pool.
- /random/: Retrieve a random object from a pool.
## Error Handling
- 400 Bad Request: If the object type does not match the pool type or if the pool is full.
- 404 Not Found: If the pool or object is not found.
- 500 Internal Server Error: For any unexpected issues.
