from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Date, Time
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.session import Base

class User(Base):
    __tablename__='users'
    id: Mapped[int]=mapped_column(primary_key=True)
    full_name: Mapped[str]=mapped_column(String(120))
    email: Mapped[str]=mapped_column(String(180),unique=True,index=True)
    password_hash: Mapped[str]=mapped_column(String(255))
    role: Mapped[str]=mapped_column(String(40),default='machine_operator',index=True)
    is_active: Mapped[bool]=mapped_column(Boolean,default=True)
    last_login: Mapped[object]=mapped_column(DateTime(timezone=True),nullable=True)
    created_at: Mapped[object]=mapped_column(DateTime(timezone=True),server_default=func.now())

class Product(Base):
    __tablename__='products'
    id: Mapped[int]=mapped_column(primary_key=True); code: Mapped[str]=mapped_column(String(40),unique=True,index=True); name: Mapped[str]=mapped_column(String(120)); category: Mapped[str]=mapped_column(String(60),default='Finished Goods'); description: Mapped[str]=mapped_column(Text,default=''); unit: Mapped[str]=mapped_column(String(20),default='pcs'); price: Mapped[float]=mapped_column(Float,default=0); stock: Mapped[int]=mapped_column(Integer,default=0); active: Mapped[bool]=mapped_column(Boolean,default=True)
class Material(Base):
    __tablename__='materials'
    id: Mapped[int]=mapped_column(primary_key=True); code: Mapped[str]=mapped_column(String(40),unique=True); name: Mapped[str]=mapped_column(String(120)); unit: Mapped[str]=mapped_column(String(20),default='pcs'); reorder_level: Mapped[int]=mapped_column(Integer,default=10); active: Mapped[bool]=mapped_column(Boolean,default=True)
class Supplier(Base):
    __tablename__='suppliers'
    id: Mapped[int]=mapped_column(primary_key=True); code: Mapped[str]=mapped_column(String(40),unique=True); name: Mapped[str]=mapped_column(String(120)); email: Mapped[str]=mapped_column(String(180),default=''); phone: Mapped[str]=mapped_column(String(40),default=''); contact_name: Mapped[str]=mapped_column(String(120),default=''); address: Mapped[str]=mapped_column(Text,default=''); active: Mapped[bool]=mapped_column(Boolean,default=True)
class WorkCenter(Base):
    __tablename__='work_centers'
    id: Mapped[int]=mapped_column(primary_key=True); code: Mapped[str]=mapped_column(String(40),unique=True); name: Mapped[str]=mapped_column(String(120)); location: Mapped[str]=mapped_column(String(120),default='Main Factory'); capacity_note: Mapped[str]=mapped_column(String(200),default=''); active: Mapped[bool]=mapped_column(Boolean,default=True)
class Machine(Base):
    __tablename__='machines'
    id: Mapped[int]=mapped_column(primary_key=True); code: Mapped[str]=mapped_column(String(40),unique=True); name: Mapped[str]=mapped_column(String(120)); work_center_id: Mapped[int|None]=mapped_column(ForeignKey('work_centers.id'),nullable=True); status: Mapped[str]=mapped_column(String(30),default='Available'); maintenance_due: Mapped[str]=mapped_column(String(20),default='')
class Shift(Base):
    __tablename__='shifts'
    id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(80),unique=True); start_time: Mapped[str]=mapped_column(String(10)); end_time: Mapped[str]=mapped_column(String(10)); active: Mapped[bool]=mapped_column(Boolean,default=True)
class BOM(Base):
    __tablename__='boms'
    id: Mapped[int]=mapped_column(primary_key=True); product_id: Mapped[int]=mapped_column(ForeignKey('products.id')); version: Mapped[str]=mapped_column(String(30),default='1'); effective_date: Mapped[str]=mapped_column(String(20),default=''); active: Mapped[bool]=mapped_column(Boolean,default=True)
class BOMLine(Base):
    __tablename__='bom_lines'
    id: Mapped[int]=mapped_column(primary_key=True); bom_id: Mapped[int]=mapped_column(ForeignKey('boms.id')); material_id: Mapped[int]=mapped_column(ForeignKey('materials.id')); qty_per_unit: Mapped[float]=mapped_column(Float)
class ProductionPlan(Base):
    __tablename__='production_plans'
    id: Mapped[int]=mapped_column(primary_key=True); plan_no: Mapped[str]=mapped_column(String(40),unique=True); product_id: Mapped[int]=mapped_column(ForeignKey('products.id')); target_qty: Mapped[int]=mapped_column(Integer); planned_start: Mapped[str]=mapped_column(String(20)); planned_end: Mapped[str]=mapped_column(String(20)); shift_id: Mapped[int|None]=mapped_column(ForeignKey('shifts.id'),nullable=True); work_center_id: Mapped[int|None]=mapped_column(ForeignKey('work_centers.id'),nullable=True); status: Mapped[str]=mapped_column(String(30),default='Draft')
class WorkOrder(Base):
    __tablename__='work_orders'
    id: Mapped[int]=mapped_column(primary_key=True); order_no: Mapped[str]=mapped_column(String(40),unique=True,index=True); plan_id: Mapped[int|None]=mapped_column(ForeignKey('production_plans.id'),nullable=True); product_id: Mapped[int]=mapped_column(ForeignKey('products.id')); work_center_id: Mapped[int|None]=mapped_column(ForeignKey('work_centers.id'),nullable=True); shift_id: Mapped[int|None]=mapped_column(ForeignKey('shifts.id'),nullable=True); planned_qty: Mapped[int]=mapped_column(Integer); produced_qty: Mapped[int]=mapped_column(Integer,default=0); good_qty: Mapped[int]=mapped_column(Integer,default=0); rejected_qty: Mapped[int]=mapped_column(Integer,default=0); status: Mapped[str]=mapped_column(String(30),default='Planned'); planned_start: Mapped[str]=mapped_column(String(20),default=''); due_date: Mapped[str]=mapped_column(String(20),default=''); created_by: Mapped[int]=mapped_column(ForeignKey('users.id'))
class ProductionEntry(Base):
    __tablename__='production_entries'
    id: Mapped[int]=mapped_column(primary_key=True); work_order_id: Mapped[int]=mapped_column(ForeignKey('work_orders.id')); user_id: Mapped[int]=mapped_column(ForeignKey('users.id')); shift_id: Mapped[int|None]=mapped_column(ForeignKey('shifts.id'),nullable=True); operation: Mapped[str]=mapped_column(String(120),default='Production'); produced_qty: Mapped[int]=mapped_column(Integer); good_qty: Mapped[int]=mapped_column(Integer); rejected_qty: Mapped[int]=mapped_column(Integer); start_at: Mapped[str]=mapped_column(String(30),default=''); end_at: Mapped[str]=mapped_column(String(30),default=''); notes: Mapped[str]=mapped_column(Text,default=''); created_at: Mapped[object]=mapped_column(DateTime(timezone=True),server_default=func.now())
class MaterialMovement(Base):
    __tablename__='material_movements'
    id: Mapped[int]=mapped_column(primary_key=True); material_id: Mapped[int]=mapped_column(ForeignKey('materials.id')); movement_type: Mapped[str]=mapped_column(String(20)); qty: Mapped[int]=mapped_column(Integer); reference: Mapped[str]=mapped_column(String(100),default=''); work_order_id: Mapped[int|None]=mapped_column(ForeignKey('work_orders.id'),nullable=True); user_id: Mapped[int|None]=mapped_column(ForeignKey('users.id'),nullable=True); created_at: Mapped[object]=mapped_column(DateTime(timezone=True),server_default=func.now())
class QualityInspection(Base):
    __tablename__='quality_inspections'
    id: Mapped[int]=mapped_column(primary_key=True); work_order_id: Mapped[int]=mapped_column(ForeignKey('work_orders.id')); inspected_qty: Mapped[int]=mapped_column(Integer); accepted_qty: Mapped[int]=mapped_column(Integer); rejected_qty: Mapped[int]=mapped_column(Integer); defect_category: Mapped[str]=mapped_column(String(80),default=''); status: Mapped[str]=mapped_column(String(30),default='Pending'); inspector_id: Mapped[int|None]=mapped_column(ForeignKey('users.id'),nullable=True); remarks: Mapped[str]=mapped_column(Text,default=''); inspection_date: Mapped[str]=mapped_column(String(20),default='')
class Downtime(Base):
    __tablename__='downtime'
    id: Mapped[int]=mapped_column(primary_key=True); machine_id: Mapped[int]=mapped_column(ForeignKey('machines.id')); work_order_id: Mapped[int|None]=mapped_column(ForeignKey('work_orders.id'),nullable=True); start_at: Mapped[str]=mapped_column(String(30)); end_at: Mapped[str]=mapped_column(String(30),default=''); reason: Mapped[str]=mapped_column(String(160)); user_id: Mapped[int]=mapped_column(ForeignKey('users.id')); notes: Mapped[str]=mapped_column(Text,default='')
class MaintenanceTask(Base):
    __tablename__='maintenance_tasks'
    id: Mapped[int]=mapped_column(primary_key=True); machine_id: Mapped[int]=mapped_column(ForeignKey('machines.id')); task_type: Mapped[str]=mapped_column(String(80)); planned_date: Mapped[str]=mapped_column(String(20)); status: Mapped[str]=mapped_column(String(30),default='Scheduled'); description: Mapped[str]=mapped_column(Text,default=''); assigned_to: Mapped[int|None]=mapped_column(ForeignKey('users.id'),nullable=True); completed_at: Mapped[str]=mapped_column(String(30),default=''); work_performed: Mapped[str]=mapped_column(Text,default=''); parts_note: Mapped[str]=mapped_column(Text,default=''); next_due_date: Mapped[str]=mapped_column(String(20),default='')
class AuditLog(Base):
    __tablename__='audit_logs'
    id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey('users.id')); action: Mapped[str]=mapped_column(String(80)); entity: Mapped[str]=mapped_column(String(80)); entity_id: Mapped[int]=mapped_column(Integer,default=0); reason: Mapped[str]=mapped_column(Text,default=''); created_at: Mapped[object]=mapped_column(DateTime(timezone=True),server_default=func.now())
