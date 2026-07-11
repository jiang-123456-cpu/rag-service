from fastapi import APIRouter,Query,HTTPException
import bcrypt
from db.database import get_db
from schemas.user import RegisterUser, LoginUser, DisabledUser
import datetime
import jwt


router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/register")
async def register(user: RegisterUser):
    if not user.username or not user.email or not user.password:
        return {"error": "用户名、邮箱或密码不能为空"}
    conn = get_db()
    cursor = conn.cursor()
    try:
        sql = "select * from users where username=%s"
        cursor.execute(sql, (user.username,))
        res = cursor.fetchall()
        if len(res) > 0:
            return {"message": "账号已存在"}
        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        sql1 = "insert into users (username,email,password_hash,role,is_active,created_at) values (%s,%s,%s,%s,%s,%s)"
        data = (user.username, user.email, hashed_password, "user", 1, datetime.datetime.now())
        cursor.execute(sql1, data)
        conn.commit()
        return {"message": "注册成功"}
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()


@router.post("/login")
async def login(user: LoginUser):
    conn = get_db()
    cursor = conn.cursor()
    try:
        sql = "select * from users where username=%s"
        cursor.execute(sql, (user.username,))
        res = cursor.fetchall()

        if len(res) == 0:
            return {"error": "账号不存在"}
        result = bcrypt.checkpw(user.password.encode('utf-8'), res[0]['password_hash'].encode('utf-8'))
        if not result:
            return {"error": "密码错误"}
        if not res[0]['is_active']:
            return {"error": "账号已禁用"}
        user1 = {
            "id": res[0]['id'],
            "username": res[0]['username'],
            "email": res[0]['email'],
            "expiresIn": '7h',
            "password": '',
            "created_at": ''
        }
        tokenStr = jwt.encode(user1, "secret_key", algorithm="HS256")
        return {
            "token": 'Bearer ' + tokenStr,
            "message": "登录成功",
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()


@router.post("/disabled")
async def disabled(user: DisabledUser):
    conn = get_db()
    cursor = conn.cursor()
    try:
        sql = "UPDATE users SET is_active = 0 WHERE id = %s"
        cursor.execute(sql, (user.id,))
        conn.commit()
        return {"message": "账号禁用成功"}
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

@router.post("/unban")
async def unban(user: DisabledUser):

    conn = get_db()
    cursor = conn.cursor()
    try:
        sql = "UPDATE users SET is_active = 1 WHERE id = %s"
        cursor.execute(sql, (user.id,))
        conn.commit()
        return {"message": "账号解禁成功"}
    except Exception as e:
        conn.rollback()
        return {"error": str(e)}
    finally:
        cursor.close()
        conn.close()

@router.get("/")
async def get_users(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100)
):
    offset = (page - 1) * page_size
    conn = get_db()
    cursor = conn.cursor()
    try:
        # 总数
        cursor.execute("SELECT COUNT(*) AS total FROM users")
        total = cursor.fetchone()["total"]

        # 分页查询（使用 users 表实际字段名，注意 role 可能是枚举，会自动转为字符串）
        sql = """
                SELECT id, username, email, role, is_active, created_at, last_login_at
                FROM users
                ORDER BY id
                LIMIT %s OFFSET %s
            """
        cursor.execute(sql, (page_size, offset))
        items = cursor.fetchall()

        # 将 is_active 从 1/0 转为布尔值便于前端显示
        for item in items:
            item["is_active"] = bool(item["is_active"])

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
    finally:
        cursor.close()
        conn.close()

