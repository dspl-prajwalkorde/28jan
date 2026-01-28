from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

# --- DATABASE CONFIGURATION ---
# We use the same 'testdb' but a different table ('employees')
# Environment variable allows Docker/Local flexibility
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5432/testdb"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLALCHEMY MODEL (Database Table) ---
class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)

# Create tables
Base.metadata.create_all(bind=engine)

# --- PYDANTIC MODELS (Data Validation) ---
class EmployeeBase(BaseModel):
    name: str
    role: str

class EmployeeResponse(EmployeeBase):
    id: int

    class Config:
        orm_mode = True

# --- APP INSTANCE ---
app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ROUTES ---

# 1. CREATE (POST)
@app.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(employee: EmployeeBase, db: Session = Depends(get_db)):
    # Validation: Check if employee with same name AND role exists
    existing_emp = db.query(Employee).filter(
        Employee.name == employee.name, 
        Employee.role == employee.role
    ).first()
    
    if existing_emp:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Employee with this name and role already exists"
        )

    new_emp = Employee(name=employee.name, role=employee.role)
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)
    return new_emp

# 2. READ ALL (GET)
@app.get("/employees", response_model=list[EmployeeResponse])
def get_employees(db: Session = Depends(get_db)):
    return db.query(Employee).all()

# 3. READ ONE (GET)
@app.get("/employees/{emp_id}", response_model=EmployeeResponse)
def get_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp

# 4. UPDATE (PUT)
@app.put("/employees/{emp_id}", response_model=EmployeeResponse)
def update_employee(emp_id: int, employee: EmployeeBase, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    emp.name = employee.name
    emp.role = employee.role
    db.commit()
    db.refresh(emp)
    return emp

# 5. DELETE (DELETE)
@app.delete("/employees/{emp_id}", status_code=status.HTTP_200_OK)
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    db.delete(emp)
    db.commit()
    return {"message": "Employee deleted"}
