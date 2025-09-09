"""
Sample Python application for testing the coding assistant pipeline.
This file demonstrates various coding patterns and structures.
"""
import os
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

app = FastAPI(title="Sample API", version="1.0.0")

@dataclass
class User:
    """User data model for the application."""
    id: int
    username: str
    email: str
    is_active: bool = True

class UserService:
    """Service class for managing user operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_user(self, user_data: Dict) -> User:
        """
        Create a new user in the system.
        
        Args:
            user_data: Dictionary containing user information
            
        Returns:
            Created user object
            
        Raises:
            HTTPException: If user creation fails
        """
        try:
            new_user = User(
                id=user_data.get("id"),
                username=user_data.get("username"),
                email=user_data.get("email")
            )
            # Database operations would go here
            return new_user
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"User creation failed: {str(e)}")
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve a user by their ID."""
        # Database query would go here
        return None
    
    def validate_email(self, email: str) -> bool:
        """Validate email format using regex."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

@app.get("/")
async def root():
    """Root endpoint that returns welcome message."""
    return {"message": "Welcome to the Sample API"}

@app.post("/users/")
async def create_user_endpoint(user_data: Dict, user_service: UserService = Depends()):
    """
    Create a new user via REST API.
    
    This endpoint accepts user data and creates a new user in the system.
    It demonstrates API design patterns and error handling.
    """
    try:
        user = await user_service.create_user(user_data)
        return {"user": user, "message": "User created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/users/{user_id}")
async def get_user_endpoint(user_id: int, user_service: UserService = Depends()):
    """Get user by ID endpoint."""
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": user}

def calculate_complexity(code_lines: List[str]) -> int:
    """
    Calculate cyclomatic complexity of code.
    
    This is a simplified complexity calculation for demonstration.
    """
    complexity = 1  # Base complexity
    
    # Count decision points
    for line in code_lines:
        line = line.strip().lower()
        if any(keyword in line for keyword in ['if', 'elif', 'while', 'for', 'except', 'and', 'or']):
            complexity += 1
    
    return complexity

class DatabaseManager:
    """Database connection and transaction manager."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._connection = None
    
    def connect(self):
        """Establish database connection."""
        # Connection logic would go here
        pass
    
    def disconnect(self):
        """Close database connection."""
        # Cleanup logic would go here
        pass
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.disconnect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
