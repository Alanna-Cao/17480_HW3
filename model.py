from fastapi import HTTPException
from pydantic import BaseModel
import random
from typing import Type, List, Dict, TypeVar, Generic

'''
Type variable for generics
'''
T = TypeVar('T', bound=BaseModel)

'''
Example data models
'''
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

registered_types: Dict[str, Type[BaseModel]] = {
    "shirt": Shirt,
    "pants": Pants,
    "sock": Sock
}

class InputTooLargeError(HTTPException):
    """
    Exception which is raised when an input list is too large for the pool.
    """
    def __init__(self, detail: str = "Input list is too large."):
        super().__init__(status_code=400, detail=detail)

class ObjectPoolManagement(Generic[T]):
    """
    Class that manages a pool of objects.
    """
    def __init__(self, expected_type: Type[T], max_size: int):
        """
        Initialize an object pool for a specified type. 

        Args:
            expected_type (Type[T]): The expected type of objects contained in the pool.
            max_size (int): The maximum number of objects allowed in the pool. Default set to max size of list in Python: 536870912.
        """
        self.pool: List[T] = []
        self.expected_type = expected_type
        self.max_size = max_size

    def add_object_to_pool(self, obj: T) -> None:
        """
        Add an object to the pool.
        
        Args:
            obj (T): Object to be added to the pool.
        
        Raises:
            InputTooLargeError: If the pool has reached its maximum size.
            ValueError: If the object type does not match the expected type.
        """
        if not isinstance(obj, self.expected_type):
            raise ValueError("Object type does not match expected type")
        if len(self.pool) >= self.max_size:
            raise InputTooLargeError()
        self.pool.append(obj)

    def remove_object_from_pool(self, obj: T) -> None:
        """
        Remove an object from the pool.
        
        Args:
            obj (T): Object to be removed from the pool.
        
        Raises:
            ValueError: If the object is not found in the pool.
        """
        if obj not in self.pool:
            raise ValueError("Object not found in pool")
        self.pool.remove(obj)

    def get_random_object_from_pool(self) -> T:
        """
        Retrieve a random object from the pool.
        
        Raises:
            IndexError: If the pool is empty.
        
        Returns:
            T: A randomly selected object from the pool.
        """
        if not self.pool:
            raise IndexError("No objects in the pool")
        return random.choice(self.pool)
