from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Equipment

router = APIRouter(prefix="/equipment", tags=["equipment"])


class EquipmentCreate(BaseModel):
    manufacturer: str
    model: str
    equipment_type: str


class EquipmentOut(BaseModel):
    id: str
    manufacturer: str
    model: str
    equipment_type: str

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[EquipmentOut])
def list_equipment(db: Session = Depends(get_db)):
    return db.query(Equipment).all()


@router.post("/", response_model=EquipmentOut, status_code=201)
def create_equipment(payload: EquipmentCreate, db: Session = Depends(get_db)):
    eq = Equipment(
        manufacturer=payload.manufacturer,
        model=payload.model,
        equipment_type=payload.equipment_type,
    )
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq


@router.get("/{equipment_id}", response_model=EquipmentOut)
def get_equipment(equipment_id: str, db: Session = Depends(get_db)):
    eq = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return eq


@router.delete("/{equipment_id}", status_code=204)
def delete_equipment(equipment_id: str, db: Session = Depends(get_db)):
    eq = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    db.delete(eq)
    db.commit()
