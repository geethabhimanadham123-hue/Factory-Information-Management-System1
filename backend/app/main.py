from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import Base,engine,SessionLocal
from app.models.entities import *
from app.core.security import hash_password
from app.api.routes import router
app=FastAPI(title='ElectroFIMS API',version='2.0.0',description='Factory Information Management System training/demo API')
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(',')],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
app.include_router(router,prefix='/api')
@app.on_event('startup')
def startup():
    Base.metadata.create_all(bind=engine);db=SessionLocal()
    try:
        demo=[('Factory Administrator','admin@electrofims.demo','administrator'),('Production Manager','manager@electrofims.demo','production_manager'),('Production Supervisor','supervisor@electrofims.demo','production_supervisor'),('Machine Operator','operator@electrofims.demo','machine_operator'),('Storekeeper','storekeeper@electrofims.demo','storekeeper'),('Quality Inspector','quality@electrofims.demo','quality_inspector'),('Maintenance Technician','maintenance@electrofims.demo','maintenance_technician')]
        for name,email,role in demo:
            if not db.query(User).filter_by(email=email).first():db.add(User(full_name=name,email=email,password_hash=hash_password('Demo@12345'),role=role))
        db.flush()
        if db.query(Product).count()==0:db.add_all([Product(code='FG-001',name='Smart Control Unit',category='Finished Goods',description='Factory demo finished product',unit='pcs'),Product(code='FG-002',name='Industrial Sensor Module',category='Finished Goods',description='Factory demo finished product',unit='pcs')])
        if db.query(Material).count()==0:db.add_all([Material(code='MAT-001',name='PCB Assembly',unit='pcs',reorder_level=50),Material(code='MAT-002',name='Sensor Component',unit='pcs',reorder_level=30)])
        if db.query(Supplier).count()==0:db.add(Supplier(code='SUP-001',name='Demo Components Supplier',email='supplier@example.demo',phone='+91 90000 00000',contact_name='Demo Contact',address='Demo Industrial Area'))
        if db.query(WorkCenter).count()==0:db.add(WorkCenter(code='WC-01',name='Electronics Assembly',location='Demo Factory',capacity_note='Demo capacity'))
        db.flush()
        if db.query(Machine).count()==0:db.add(Machine(code='MC-01',name='Assembly Line 01',work_center_id=db.query(WorkCenter).first().id,status='Available'))
        if db.query(Shift).count()==0:db.add_all([Shift(name='Morning',start_time='06:00',end_time='14:00'),Shift(name='Evening',start_time='14:00',end_time='22:00'),Shift(name='Night',start_time='22:00',end_time='06:00')])
        db.commit()
    finally:db.close()
@app.get('/')
def root():return {'name':'ElectroFIMS API','status':'running','docs':'/docs'}
@app.get('/health')
def health():return {'status':'ok'}
