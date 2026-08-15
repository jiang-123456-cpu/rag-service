from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import bcrypt
import datetime
import jwt

from db.database import get_db
from db.models import Users, UserRole
from schemas.user import RegisterUser, LoginUser, DisabledUser, VerifyUser, ChangePasswordUser
from utils.auth import get_current_user, require_role
from sqlalchemy import select, func

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/register")
async def register(user: RegisterUser, db: AsyncSession = Depends(get_db)):
    if not user.username or not user.email or not user.password:
        raise HTTPException(status_code=400, detail="用户名、邮箱或密码不能为空")
    try:
        result = await db.execute(select(Users).where(Users.username == user.username))
        existing = result.scalar_one_or_none()
        if existing:
            return {"message": "账号已存在"}

        result = await db.execute(select(Users).where(Users.email == user.email))
        existing_email = result.scalar_one_or_none()
        if existing_email:
            return {"message": "邮箱已被注册"}

        hashed_password = await asyncio.to_thread(
            lambda: bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        )
        new_user = Users(
            username=user.username,
            email=user.email,
            password_hash=hashed_password,
            role=UserRole.USER,
            is_active=1,
            created_at=datetime.datetime.now(),
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return {"message": "注册成功", "id": new_user.id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")


@router.post("/login")
async def login(user: LoginUser, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Users).where(Users.username == user.username))
        db_user = result.scalar_one_or_none()
        if not db_user:
            return {"error": "账号不存在"}

        if not await asyncio.to_thread(
            bcrypt.checkpw, user.password.encode('utf-8'), db_user.password_hash.encode('utf-8')
        ):
            return {"error": "密码错误"}

        if not db_user.is_active:
            return {"error": "账号已禁用"}

        db_user.last_login_at = datetime.datetime.now()
        await db.commit()

        payload = {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "role": db_user.role.value,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=7),
        }
        tokenStr = await asyncio.to_thread(jwt.encode, payload, "secret_key", algorithm="HS256")
        return {
            "token": 'Bearer ' + tokenStr,
            "message": "登录成功",
            "username": db_user.username,
            "role": db_user.role.value,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")


@router.post("/disabled")
async def disabled(
    user: DisabledUser,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(require_role(UserRole.ADMIN)),
):
    try:
        result = await db.execute(select(Users).where(Users.id == user.id))
        db_user = result.scalar_one_or_none()
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        db_user.is_active = 0
        await db.commit()
        return {"message": "账号禁用成功"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"禁用失败: {str(e)}")


@router.post("/unban")
async def unban(
    user: DisabledUser,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(require_role(UserRole.ADMIN)),
):
    try:
        result = await db.execute(select(Users).where(Users.id == user.id))
        db_user = result.scalar_one_or_none()
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        db_user.is_active = 1
        await db.commit()
        return {"message": "账号解禁成功"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"解禁失败: {str(e)}")


@router.get("/")
async def get_users(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        db: AsyncSession = Depends(get_db),
        current_user: Users = Depends(require_role(UserRole.ADMIN)),
):
    offset = (page - 1) * page_size
    try:
        count_result = await db.execute(select(func.count(Users.id)))
        total = count_result.scalar()

        users_list = (
            await db.execute(
                select(Users)
                .order_by(Users.id)
                .offset(offset)
                .limit(page_size)
            )
        ).scalars().all()

        items = []
        for u in users_list:
            items.append({
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role.value if u.role else None,
                "is_active": bool(u.is_active),
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            })

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/verify")
async def verifyEmailandAccount(
        user: VerifyUser,
        db: AsyncSession = Depends(get_db),
):
    try:
        result = await db.execute(
            select(Users.id).where(
                Users.email == user.email,
                Users.username == user.username,
            )
        )
        user_id = result.scalar_one_or_none()
        if not user_id:
            raise HTTPException(status_code=404, detail="用户不存在")
        return {"message": "验证成功", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.post("/change-password")
async def changePassword(
        user: ChangePasswordUser,
        db: AsyncSession = Depends(get_db)
):
   try:
       result = await db.execute(select(Users).where(Users.id == user.id))
       db_user = result.scalar_one_or_none()
       if not db_user:
           raise HTTPException(status_code=404, detail="用户不存在")
       hashed_password = await asyncio.to_thread(
           lambda: bcrypt.hashpw(user.newpassword.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
       )
       db_user.password_hash = hashed_password
       await db.commit()
       return {"message": "密码修改成功"}
   except HTTPException:
       raise
   except Exception as e:
       await db.rollback()
       raise HTTPException(status_code=500, detail=f"密码修改失败: {str(e)}")