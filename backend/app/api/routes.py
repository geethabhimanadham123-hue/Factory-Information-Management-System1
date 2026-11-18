from datetime import datetime
from typing import Optional
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.entities import *
from app.schemas.auth import RegisterIn,LoginIn
from app.core.security import hash_password,verify_password,create_token,current_user,require_admin,allow_roles,ROLES
from app.core.config import settings
router=APIRouter()
ADMIN=('administrator',); MANAGERS=('administrator','production_manager'); OPS=('administrator','production_manager','production_supervisor','machine_operator'); STORES=('administrator','storekeeper'); QUALITY=('administrator','quality_inspector'); MAINT=('administrator','maintenance_technician')
def audit(db,u,action,entity,eid=0,reason=''):
    db.add(AuditLog(user_id=u.id,action=action,entity=entity,entity_id=eid,reason=reason))
def uout(u): return {'id':u.id,'full_name':u.full_name,'email':u.email,'role':u.role,'is_active':u.is_active,'last_login':str(u.last_login or '')}
def authout(u): return {'access_token':create_token(u),'token_type':'bearer','user':uout(u)}
def dump(x,fields): return {k:getattr(x,k) for k in fields}
def stock(db,mid):
    return sum(m.qty if m.movement_type in ('Receipt','Adjustment+') else -m.qty for m in db.query(MaterialMovement).filter_by(material_id=mid).all())
@router.post('/auth/register',status_code=201)
def register(d:RegisterIn,db:Session=Depends(get_db)):
    # DEMO behavior requested by the project owner: Admin and User signup are
    # separate entry points. Admin signup assigns the administrator role; User
    # signup always receives the least-privileged machine_operator role.
    # Do not expose unrestricted admin self-registration on a public deployment.
    role='administrator' if d.role == 'administrator' else 'machine_operator'
    if db.query(User).filter(func.lower(User.email)==d.email.lower()).first():
        raise HTTPException(409,'Email already exists')
    x=User(full_name=d.full_name.strip(),email=d.email.lower(),password_hash=hash_password(d.password),role=role)
    db.add(x);db.flush();audit(db,x,'SELF_REGISTER','User',x.id);db.commit()
    return {'message':'Account created. Sign in with your email and password.','user':uout(x)}
@router.post('/auth/login')
def login(d:LoginIn,db:Session=Depends(get_db)):
    u=db.query(User).filter(func.lower(User.email)==d.email.lower()).first()
    if not u or not verify_password(d.password,u.password_hash):
        raise HTTPException(401,'Incorrect email or password')
    if not u.is_active: raise HTTPException(403,'Account is deactivated')
    u.last_login=datetime.utcnow();audit(db,u,'LOGIN','User',u.id);db.commit()
    return {'message':'Login successful',**authout(u)}
@router.get('/auth/me')
def me(u:User=Depends(current_user)): return uout(u)
@router.get('/dashboard')
def dashboard(db:Session=Depends(get_db),u:User=Depends(current_user)):
    wo=db.query(WorkOrder).all();return {'orders':len(wo),'in_production':sum(x.status=='In Progress' for x in wo),'completed':sum(x.status=='Completed' for x in wo),'delayed':sum(x.status not in ('Completed','Cancelled') and x.due_date and x.due_date<datetime.now().date().isoformat() for x in wo),'planned_units':sum(x.planned_qty for x in wo),'produced_units':sum(x.produced_qty for x in wo),'products':db.query(Product).filter_by(active=True).count(),'suppliers':db.query(Supplier).filter_by(active=True).count(),'quality_open':db.query(QualityInspection).filter_by(status='Pending').count(),'machines':db.query(Machine).count(),'low_stock':sum(stock(db,m.id)<=m.reorder_level for m in db.query(Material).all()),'recent_orders':[{'id':x.id,'order_no':x.order_no,'status':x.status,'planned_qty':x.planned_qty,'produced_qty':x.produced_qty,'product':db.get(Product,x.product_id).name} for x in wo[-6:][::-1]]}
class ProductIn(BaseModel): code:str=Field(min_length=2,max_length=40);name:str=Field(min_length=2,max_length=120);category:str='Finished Goods';description:str='';unit:str='pcs';price:float=Field(default=0,ge=0);stock:int=Field(default=0,ge=0)
@router.get('/products')
def products(q:Optional[str]=None,db:Session=Depends(get_db),u:User=Depends(current_user)):
    z=db.query(Product)
    if q:z=z.filter(Product.name.ilike(f'%{q}%'))
    return [dump(x,['id','code','name','category','description','unit','price','stock','active']) for x in z.order_by(Product.id.desc()).all()]
@router.post('/products',status_code=201)
def add_product(d:ProductIn,db:Session=Depends(get_db),u:User=Depends(require_admin)):
    if db.query(Product).filter_by(code=d.code).first():raise HTTPException(409,'Product code already exists')
    x=Product(**d.model_dump());db.add(x);db.flush();audit(db,u,'CREATE','Product',x.id);db.commit();return {'message':'Product created','id':x.id}
class MaterialIn(BaseModel):code:str;name:str;unit:str='pcs';reorder_level:int=Field(default=10,ge=0)
@router.get('/materials')
def materials(db:Session=Depends(get_db),u:User=Depends(current_user)):
    return [{**dump(x,['id','code','name','unit','reorder_level','active']),'stock':stock(db,x.id)} for x in db.query(Material).all()]
@router.post('/materials',status_code=201)
def add_material(d:MaterialIn,db:Session=Depends(get_db),u:User=Depends(require_admin)):
    if db.query(Material).filter_by(code=d.code).first():raise HTTPException(409,'Material code exists')
    x=Material(**d.model_dump());db.add(x);db.flush();audit(db,u,'CREATE','Material',x.id);db.commit();return {'message':'Material created','id':x.id}
class SupplierIn(BaseModel):code:str;name:str;email:str='';phone:str='';contact_name:str='';address:str=''
@router.get('/suppliers')
def suppliers(db:Session=Depends(get_db),u:User=Depends(current_user)):return [dump(x,['id','code','name','email','phone','contact_name','address','active']) for x in db.query(Supplier).all()]
@router.post('/suppliers',status_code=201)
def add_supplier(d:SupplierIn,db:Session=Depends(get_db),u:User=Depends(allow_roles(*STORES))):
    if db.query(Supplier).filter_by(code=d.code).first():raise HTTPException(409,'Supplier code exists')
    x=Supplier(**d.model_dump());db.add(x);db.flush();audit(db,u,'CREATE','Supplier',x.id);db.commit();return {'message':'Supplier created','id':x.id}
class WorkCenterIn(BaseModel):code:str;name:str;location:str='Main Factory';capacity_note:str=''
@router.get('/work-centers')
def work_centers(db:Session=Depends(get_db),u:User=Depends(current_user)):return [dump(x,['id','code','name','location','capacity_note','active']) for x in db.query(WorkCenter).all()]
@router.post('/work-centers',status_code=201)
def add_wc(d:WorkCenterIn,db:Session=Depends(get_db),u:User=Depends(require_admin)):
    x=WorkCenter(**d.model_dump());db.add(x);db.flush();audit(db,u,'CREATE','WorkCenter',x.id);db.commit();return {'id':x.id,'message':'Work center created'}
class MachineIn(BaseModel):code:str;name:str;work_center_id:int|None=None;status:str='Available';maintenance_due:str=''
@router.get('/machines')
def machines(db:Session=Depends(get_db),u:User=Depends(current_user)):return [dump(x,['id','code','name','work_center_id','status','maintenance_due']) for x in db.query(Machine).all()]
@router.post('/machines',status_code=201)
def add_machine(d:MachineIn,db:Session=Depends(get_db),u:User=Depends(require_admin)):
    if d.status not in ('Available','Maintenance Due','Under Maintenance','Down'):raise HTTPException(422,'Invalid machine status')
    x=Machine(**d.model_dump());db.add(x);db.flush();audit(db,u,'CREATE','Machine',x.id);db.commit();return {'id':x.id,'message':'Machine created'}
class ShiftIn(BaseModel):name:str;start_time:str;end_time:str
@router.get('/shifts')
def shifts(db:Session=Depends(get_db),u:User=Depends(current_user)):return [dump(x,['id','name','start_time','end_time','active']) for x in db.query(Shift).all()]
@router.post('/shifts',status_code=201)
def add_shift(d:ShiftIn,db:Session=Depends(get_db),u:User=Depends(require_admin)):
    x=Shift(**d.model_dump());db.add(x);db.flush();audit(db,u,'CREATE','Shift',x.id);db.commit();return {'id':x.id,'message':'Shift created'}
class BOMIn(BaseModel):product_id:int;material_id:int;qty_per_unit:float=Field(gt=0);version:str='1';effective_date:str=''
@router.get('/boms')
def boms(db:Session=Depends(get_db),u:User=Depends(current_user)):
    return [{'id':l.id,'bom_id':b.id,'product_id':b.product_id,'product':db.get(Product,b.product_id).name,'material_id':l.material_id,'material':db.get(Material,l.material_id).name,'qty_per_unit':l.qty_per_unit,'version':b.version,'effective_date':b.effective_date,'active':b.active} for b in db.query(BOM).all() for l in db.query(BOMLine).filter_by(bom_id=b.id).all()]
@router.post('/boms',status_code=201)
def add_bom(d:BOMIn,db:Session=Depends(get_db),u:User=Depends(require_admin)):
    if not db.get(Product,d.product_id) or not db.get(Material,d.material_id):raise HTTPException(404,'Product or material not found')
    b=BOM(product_id=d.product_id,version=d.version,effective_date=d.effective_date);db.add(b);db.flush();l=BOMLine(bom_id=b.id,material_id=d.material_id,qty_per_unit=d.qty_per_unit);db.add(l);audit(db,u,'CREATE','BOM',b.id);db.commit();return {'id':b.id,'message':'BOM line created'}
class PlanIn(BaseModel):plan_no:str;product_id:int;target_qty:int=Field(gt=0);planned_start:str;planned_end:str;shift_id:int|None=None;work_center_id:int|None=None
@router.get('/production-plans')
def plans(db:Session=Depends(get_db),u:User=Depends(current_user)):return [{**dump(x,['id','plan_no','product_id','target_qty','planned_start','planned_end','shift_id','work_center_id','status']),'product':db.get(Product,x.product_id).name} for x in db.query(ProductionPlan).all()]
@router.post('/production-plans',status_code=201)
def add_plan(d:PlanIn,db:Session=Depends(get_db),u:User=Depends(allow_roles(*MANAGERS))):
    if d.planned_end<d.planned_start:raise HTTPException(422,'End date must be on or after start date')
    x=ProductionPlan(**d.model_dump());db.add(x);db.flush();audit(db,u,'CREATE','ProductionPlan',x.id);db.commit();return {'id':x.id,'message':'Production plan created'}
class WorkOrderIn(BaseModel):order_no:str|None=None;plan_id:int|None=None;product_id:int;planned_qty:int=Field(gt=0);due_date:str='';planned_start:str='';work_center_id:int|None=None;shift_id:int|None=None
@router.get('/work-orders')
def work_orders(db:Session=Depends(get_db),u:User=Depends(current_user)):
    return [{**dump(x,['id','order_no','plan_id','product_id','work_center_id','shift_id','planned_qty','produced_qty','good_qty','rejected_qty','status','planned_start','due_date','created_by']),'product':db.get(Product,x.product_id).name} for x in db.query(WorkOrder).order_by(WorkOrder.id.desc()).all()]
@router.post('/work-orders',status_code=201)
def add_work_order(d:WorkOrderIn,db:Session=Depends(get_db),u:User=Depends(allow_roles(*MANAGERS))):
    if not db.get(Product,d.product_id):raise HTTPException(404,'Product not found')
    no=d.order_no or f'WO-{datetime.now():%Y%m%d%H%M%S}'
    if db.query(WorkOrder).filter_by(order_no=no).first():raise HTTPException(409,'Work order number already exists')
    x=WorkOrder(**d.model_dump(exclude={'order_no'}),order_no=no,created_by=u.id);db.add(x);db.flush();audit(db,u,'CREATE','WorkOrder',x.id);db.commit();return {'id':x.id,'order_no':no,'message':'Work order created'}
class StatusIn(BaseModel):status:str;reason:str=''
@router.patch('/work-orders/{wid}/status')
def status(wid:int,d:StatusIn,db:Session=Depends(get_db),u:User=Depends(allow_roles('administrator','production_manager','production_supervisor'))):
    x=db.get(WorkOrder,wid)
    if not x:raise HTTPException(404,'Work order not found')
    allowed={'Draft':['Planned','Cancelled'],'Planned':['Released','Cancelled'],'Released':['In Progress','Cancelled'],'In Progress':['Paused','Completed'],'Paused':['In Progress','Cancelled']}
    if d.status not in allowed.get(x.status,[]):raise HTTPException(409,f'Cannot change {x.status} to {d.status}')
    if d.status=='Completed' and x.good_qty+x.rejected_qty>x.planned_qty and (u.role!='administrator' or not d.reason.strip()):raise HTTPException(409,'Overproduction requires administrator permission and an audit reason')
    x.status=d.status;audit(db,u,'STATUS_CHANGE','WorkOrder',x.id,d.reason);db.commit();return {'message':'Work order status updated','status':x.status}
class EntryIn(BaseModel):operation:str='Production';shift_id:int|None=None;produced_qty:int=Field(gt=0);good_qty:int=Field(ge=0);rejected_qty:int=Field(ge=0);start_at:str='';end_at:str='';notes:str=''
@router.get('/work-orders/{wid}/production-entries')
def entries(wid:int,db:Session=Depends(get_db),u:User=Depends(current_user)):return [dump(x,['id','work_order_id','user_id','shift_id','operation','produced_qty','good_qty','rejected_qty','start_at','end_at','notes','created_at']) for x in db.query(ProductionEntry).filter_by(work_order_id=wid).all()]
@router.post('/work-orders/{wid}/production-entries',status_code=201)
def add_entry(wid:int,d:EntryIn,db:Session=Depends(get_db),u:User=Depends(allow_roles(*OPS))):
    x=db.get(WorkOrder,wid)
    if not x:raise HTTPException(404,'Work order not found')
    if d.good_qty+d.rejected_qty!=d.produced_qty:raise HTTPException(422,'Good + rejected quantity must equal produced quantity')
    if x.produced_qty+d.produced_qty>x.planned_qty and u.role!='administrator':raise HTTPException(409,'Reported quantity exceeds planned quantity')
    e=ProductionEntry(work_order_id=wid,user_id=u.id,**d.model_dump());db.add(e);x.produced_qty+=d.produced_qty;x.good_qty+=d.good_qty;x.rejected_qty+=d.rejected_qty;audit(db,u,'PRODUCTION_ENTRY','WorkOrder',wid);db.commit();return {'id':e.id,'message':'Production entry saved'}
class MovementIn(BaseModel):material_id:int;qty:int=Field(gt=0);movement_type:str;reference:str='';work_order_id:int|None=None
@router.get('/inventory/movements')
def movements(db:Session=Depends(get_db),u:User=Depends(current_user)):return [{**dump(x,['id','material_id','movement_type','qty','reference','work_order_id','created_at']),'material':db.get(Material,x.material_id).name} for x in db.query(MaterialMovement).order_by(MaterialMovement.id.desc()).all()]
@router.post('/inventory/movements',status_code=201)
@router.post('/inventory/receipts',status_code=201)
@router.post('/inventory/issues',status_code=201)
def add_movement(d:MovementIn,db:Session=Depends(get_db),u:User=Depends(allow_roles(*STORES))):
    if d.movement_type not in ('Receipt','Issue','Adjustment+','Adjustment-'):raise HTTPException(422,'Invalid movement type')
    if not db.get(Material,d.material_id):raise HTTPException(404,'Material not found')
    if d.movement_type in ('Issue','Adjustment-') and d.qty>stock(db,d.material_id):raise HTTPException(409,'Insufficient stock; negative stock is blocked')
    x=MaterialMovement(**d.model_dump(),user_id=u.id);db.add(x);db.flush();audit(db,u,'STOCK_'+d.movement_type.upper(),'Material',d.material_id,d.reference);db.commit();return {'id':x.id,'message':'Stock movement posted','balance':stock(db,d.material_id)}
@router.get('/inventory/stock')
def stock_report(db:Session=Depends(get_db),u:User=Depends(current_user)):return [{'material_id':m.id,'code':m.code,'material':m.name,'balance':stock(db,m.id),'reorder_level':m.reorder_level,'low_stock':stock(db,m.id)<=m.reorder_level} for m in db.query(Material).all()]
class QualityIn(BaseModel):work_order_id:int;inspected_qty:int=Field(gt=0);accepted_qty:int=Field(ge=0);rejected_qty:int=Field(ge=0);defect_category:str='';remarks:str='';inspection_date:str=''
@router.get('/quality/inspections')
def inspections(db:Session=Depends(get_db),u:User=Depends(current_user)):return [{**dump(x,['id','work_order_id','inspected_qty','accepted_qty','rejected_qty','defect_category','status','inspector_id','remarks','inspection_date']),'work_order':db.get(WorkOrder,x.work_order_id).order_no} for x in db.query(QualityInspection).all()]
@router.post('/quality/inspections',status_code=201)
def add_inspection(d:QualityIn,db:Session=Depends(get_db),u:User=Depends(allow_roles(*QUALITY))):
    if d.accepted_qty+d.rejected_qty>d.inspected_qty:raise HTTPException(422,'Accepted + rejected cannot exceed inspected quantity')
    if not db.get(WorkOrder,d.work_order_id):raise HTTPException(404,'Work order not found')
    status='Passed' if d.rejected_qty==0 else 'Failed';x=QualityInspection(**d.model_dump(),status=status,inspector_id=u.id);db.add(x);db.flush();audit(db,u,'CREATE','QualityInspection',x.id);db.commit();return {'id':x.id,'message':'Inspection saved','status':status}
class MaintenanceIn(BaseModel):machine_id:int;task_type:str;planned_date:str;description:str='';assigned_to:int|None=None
@router.get('/maintenance/tasks')
def tasks(db:Session=Depends(get_db),u:User=Depends(current_user)):return [{**dump(x,['id','machine_id','task_type','planned_date','status','description','assigned_to','completed_at','work_performed','parts_note','next_due_date']),'machine':db.get(Machine,x.machine_id).name} for x in db.query(MaintenanceTask).all()]
@router.post('/maintenance/tasks',status_code=201)
def add_task(d:MaintenanceIn,db:Session=Depends(get_db),u:User=Depends(allow_roles(*MAINT))):
    if not db.get(Machine,d.machine_id):raise HTTPException(404,'Machine not found')
    x=MaintenanceTask(**d.model_dump());db.add(x);db.flush();audit(db,u,'CREATE','MaintenanceTask',x.id);db.commit();return {'id':x.id,'message':'Maintenance task scheduled'}
class CompleteTask(BaseModel):completed_at:str;work_performed:str='';parts_note:str='';next_due_date:str=''
@router.patch('/maintenance/tasks/{tid}/complete')
def complete_task(tid:int,d:CompleteTask,db:Session=Depends(get_db),u:User=Depends(allow_roles(*MAINT))):
    x=db.get(MaintenanceTask,tid)
    if not x:raise HTTPException(404,'Task not found')
    for k,v in d.model_dump().items():setattr(x,k,v)
    x.status='Completed';audit(db,u,'COMPLETE','MaintenanceTask',x.id);db.commit();return {'message':'Maintenance completed'}
class DowntimeIn(BaseModel):machine_id:int;work_order_id:int|None=None;start_at:str;end_at:str='';reason:str;notes:str=''
@router.get('/downtime')
def downtimes(db:Session=Depends(get_db),u:User=Depends(current_user)):return [{**dump(x,['id','machine_id','work_order_id','start_at','end_at','reason','user_id','notes']),'machine':db.get(Machine,x.machine_id).name} for x in db.query(Downtime).all()]
@router.post('/downtime',status_code=201)
def add_downtime(d:DowntimeIn,db:Session=Depends(get_db),u:User=Depends(allow_roles(*tuple(dict.fromkeys(OPS+MAINT))))):
    if not db.get(Machine,d.machine_id):raise HTTPException(404,'Machine not found')
    x=Downtime(**d.model_dump(),user_id=u.id);db.add(x);db.flush();audit(db,u,'DOWNTIME','Machine',x.machine_id,d.reason);db.commit();return {'id':x.id,'message':'Downtime logged'}
@router.get('/users')
def users(db:Session=Depends(get_db),u:User=Depends(require_admin)):return [uout(x) for x in db.query(User).order_by(User.id.desc()).all()]
@router.get('/reports/summary')
def report(db:Session=Depends(get_db),u:User=Depends(current_user)):return {'orders':db.query(WorkOrder).count(),'products':db.query(Product).count(),'suppliers':db.query(Supplier).count(),'inspections':db.query(QualityInspection).count(),'produced':db.query(func.sum(WorkOrder.produced_qty)).scalar() or 0,'planned':db.query(func.sum(WorkOrder.planned_qty)).scalar() or 0,'materials':db.query(Material).count(),'downtime_events':db.query(Downtime).count(),'maintenance_tasks':db.query(MaintenanceTask).count()}
@router.get('/reports/production')
def report_production(db:Session=Depends(get_db),u:User=Depends(current_user)):return [{'order_no':x.order_no,'product':db.get(Product,x.product_id).name,'planned':x.planned_qty,'produced':x.produced_qty,'good':x.good_qty,'rejected':x.rejected_qty,'variance':x.planned_qty-x.produced_qty,'status':x.status} for x in db.query(WorkOrder).all()]
@router.get('/reports/quality')
def report_quality(db:Session=Depends(get_db),u:User=Depends(current_user)):return [dump(x,['id','work_order_id','inspected_qty','accepted_qty','rejected_qty','defect_category','status','inspection_date']) for x in db.query(QualityInspection).all()]
@router.get('/reports/inventory')
def report_inventory(db:Session=Depends(get_db),u:User=Depends(current_user)):return stock_report(db,u)

class AdminUserIn(BaseModel):
    full_name:str=Field(min_length=2,max_length=120)
    email:str=Field(min_length=5,max_length=180)
    password:str=Field(min_length=8,max_length=128)
    role:str
@router.post('/users',status_code=201)
def admin_create_user(d:AdminUserIn,db:Session=Depends(get_db),u:User=Depends(require_admin)):
    if d.role not in ROLES: raise HTTPException(422,'Invalid role')
    email=d.email.strip().lower()
    if db.query(User).filter(func.lower(User.email)==email).first(): raise HTTPException(409,'Email already exists')
    x=User(full_name=d.full_name.strip(),email=email,password_hash=hash_password(d.password),role=d.role)
    db.add(x);db.flush();audit(db,u,'CREATE','User',x.id,'Role: '+d.role);db.commit()
    return {'message':'User created','user':uout(x)}
class AdminUserPatch(BaseModel):
    full_name:str|None=None
    role:str|None=None
    is_active:bool|None=None
@router.patch('/users/{uid}')
def admin_update_user(uid:int,d:AdminUserPatch,db:Session=Depends(get_db),u:User=Depends(require_admin)):
    x=db.get(User,uid)
    if not x: raise HTTPException(404,'User not found')
    changes=d.model_dump(exclude_unset=True)
    if 'role' in changes and changes['role'] not in ROLES: raise HTTPException(422,'Invalid role')
    if uid==u.id and changes.get('is_active') is False: raise HTTPException(409,'You cannot deactivate your own account')
    for k,v in changes.items(): setattr(x,k,v)
    audit(db,u,'UPDATE','User',x.id,'; '.join(f'{k}={v}' for k,v in changes.items()));db.commit()
    return {'message':'User updated','user':uout(x)}

@router.get('/audit-logs')
def audit_logs(db:Session=Depends(get_db),u:User=Depends(require_admin)):return [{'id':x.id,'user':db.get(User,x.user_id).email if db.get(User,x.user_id) else '','action':x.action,'entity':x.entity,'entity_id':x.entity_id,'reason':x.reason,'created_at':str(x.created_at)} for x in db.query(AuditLog).order_by(AuditLog.id.desc()).limit(200).all()]
