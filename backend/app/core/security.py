from datetime import datetime,timedelta,timezone
from jose import jwt,JWTError
from passlib.context import CryptContext
from fastapi import Depends,HTTPException
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models.entities import User
pwd=CryptContext(schemes=['bcrypt'],deprecated='auto'); bearer=HTTPBearer(auto_error=False)
ROLES=('administrator','production_manager','production_supervisor','machine_operator','storekeeper','quality_inspector','maintenance_technician')
def hash_password(v): return pwd.hash(v)
def verify_password(v,h): return pwd.verify(v,h)
def create_token(u): return jwt.encode({'sub':str(u.id),'role':u.role,'exp':datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_minutes)},settings.secret_key,algorithm='HS256')
def current_user(creds:HTTPAuthorizationCredentials=Depends(bearer),db:Session=Depends(get_db)):
    if not creds: raise HTTPException(401,'Authentication required')
    try: uid=int(jwt.decode(creds.credentials,settings.secret_key,algorithms=['HS256']).get('sub',0))
    except (JWTError,ValueError): raise HTTPException(401,'Invalid or expired token')
    u=db.get(User,uid)
    if not u or not u.is_active: raise HTTPException(401,'Account is inactive')
    return u
def allow_roles(*roles):
    def guard(u:User=Depends(current_user)):
        if u.role not in roles: raise HTTPException(403,'You do not have permission for this operation')
        return u
    return guard
require_admin=allow_roles('administrator')
