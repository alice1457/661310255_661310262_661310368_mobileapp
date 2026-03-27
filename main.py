from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db_connection import get_db_connection
from mysql.connector import Error
from typing import Optional

app = FastAPI()

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================= ROOT =================
@app.get("/")
async def root():
    return {"status": "ok", "message": "Pet Hotel API is running"}


# ================= MODELS =================
class User(BaseModel):
    id: int | None = None
    name: str
    email: str
    password: str
    role: str = "user"  # "admin" | "user"


class Pet(BaseModel):
    id: int | None = None
    user_id: int
    name: str
    type: str
    age: int
    image_url: str | None = None
    vaccine: str | None = None


class PetRecord(BaseModel):
    id: int | None = None
    pet_id: int
    record_type: str
    title: str
    description: str | None = None
    record_date: str | None = None


class PetVaccine(BaseModel):
    id: int | None = None
    pet_id: int
    vaccine_name: str
    dose: str | None = None
    vaccine_date: str | None = None
    next_due: str | None = None
    clinic: str | None = None
    note: str | None = None


class PaymentUpdate(BaseModel):
    payment_slip: str
    payment_status: str = "paid"


class Booking(BaseModel):
    id: int | None = None
    user_id: int
    pet_id: int
    check_in: str
    check_out: str
    note: str | None = None
    # status: pending | approved | rejected | staying | completed
    status: str = "pending"
    total_price: float | None = None
    payment_slip: str | None = None  # URL หรือ base64 ของสลิป
    payment_status: str = "unpaid"  # unpaid | paid


# ================= HELPER =================
def _fetch_one(cursor):
    return cursor.fetchone()


def _fetch_all(cursor):
    return cursor.fetchall()


# ================= USERS =================
@app.post("/users")
async def create_user(user: User):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (user.name, user.email, user.password, user.role),
        )
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
        return {"id": user_id, **user.dict()}
    except Error as err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.get("/users")
async def get_users():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        users = _fetch_all(cursor)
        cursor.close()
        return users
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.get("/users/{user_id}")
async def get_user_by_id(user_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        user = _fetch_one(cursor)
        cursor.close()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.put("/users/{user_id}")
async def update_user(user_id: int, user: User):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET name=%s, email=%s, password=%s, role=%s WHERE id=%s",
            (user.name, user.email, user.password, user.role, user_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        cursor.close()
        return {"message": "User updated"}
    except Error as err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        cursor.close()
        return {"message": f"user {user_id} deleted"}
    except Error as err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


# ================= PETS =================
@app.post("/pets")
async def create_pet(pet: Pet):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pets (user_id, name, type, age, image_url, vaccine) VALUES (%s, %s, %s, %s, %s, %s)",
            (pet.user_id, pet.name, pet.type, pet.age, pet.image_url, pet.vaccine),
        )
        conn.commit()
        pet_id = cursor.lastrowid
        cursor.close()
        return {"id": pet_id, **pet.dict()}
    except Error as err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.get("/pets")
async def get_pets():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pets")
        pets = _fetch_all(cursor)
        cursor.close()
        return pets
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.get("/pets/user/{user_id}")
async def get_pets_by_user(user_id: int):
    """คืนสัตว์เลี้ยงทั้งหมดของ user คนนั้น"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pets WHERE user_id=%s", (user_id,))
        pets = _fetch_all(cursor)
        cursor.close()
        return pets
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.get("/pets/{pet_id}")
async def get_pet_by_id(pet_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pets WHERE id=%s", (pet_id,))
        pet = _fetch_one(cursor)
        cursor.close()
        if not pet:
            raise HTTPException(status_code=404, detail="Pet not found")
        return pet
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.put("/pets/{pet_id}")
async def update_pet(pet_id: int, pet: Pet):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE pets SET user_id=%s, name=%s, type=%s, age=%s, image_url=%s, vaccine=%s WHERE id=%s",
            (pet.user_id, pet.name, pet.type, pet.age, pet.image_url, pet.vaccine, pet_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Pet not found")
        cursor.close()
        return {"message": "Pet updated"}
    except Error as err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.delete("/pets/{pet_id}")
async def delete_pet(pet_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pets WHERE id=%s", (pet_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Pet not found")
        cursor.close()
        return {"message": f"pet {pet_id} deleted"}
    except Error as err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


# ================= RECORDS =================
@app.post("/records")
async def create_record(record: PetRecord):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pet_records (pet_id, record_type, title, description, record_date) VALUES (%s, %s, %s, %s, %s)",
            (record.pet_id, record.record_type, record.title, record.description, record.record_date),
        )
        conn.commit()
        record_id = cursor.lastrowid
        cursor.close()
        return {"id": record_id, **record.dict()}
    except Error as err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.get("/records")
async def get_records():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pet_records")
        records = _fetch_all(cursor)
        cursor.close()
        return records
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.get("/records/{record_id}")
async def get_record_by_id(record_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pet_records WHERE id=%s", (record_id,))
        record = _fetch_one(cursor)
        cursor.close()
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        return record
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.put("/records/{record_id}")
async def update_record(record_id: int, record: PetRecord):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE pet_records SET pet_id=%s, record_type=%s, title=%s, description=%s, record_date=%s WHERE id=%s",
            (record.pet_id, record.record_type, record.title, record.description, record.record_date, record_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Record not found")
        cursor.close()
        return {"message": "Record updated"}
    except Error as err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.delete("/records/{record_id}")
async def delete_record(record_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pet_records WHERE id=%s", (record_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Record not found")
        cursor.close()
        return {"message": f"record {record_id} deleted"}
    except Error as err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


# ================= PET VACCINES =================
@app.post("/vaccines")
async def create_vaccine(v: PetVaccine):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pet_vaccines (pet_id, vaccine_name, dose, vaccine_date, next_due, clinic, note) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (v.pet_id, v.vaccine_name, v.dose, v.vaccine_date, v.next_due, v.clinic, v.note),
        )
        conn.commit()
        vid = cursor.lastrowid
        cursor.close()
        return {"id": vid, **v.dict()}
    except Error as err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.get("/vaccines")
async def get_vaccines():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pet_vaccines ORDER BY vaccine_date DESC")
        rows = _fetch_all(cursor)
        cursor.close()
        return rows
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.get("/vaccines/pet/{pet_id}")
async def get_vaccines_by_pet(pet_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pet_vaccines WHERE pet_id=%s ORDER BY vaccine_date DESC", (pet_id,))
        rows = _fetch_all(cursor)
        cursor.close()
        return rows
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.get("/vaccines/{vaccine_id}")
async def get_vaccine_by_id(vaccine_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pet_vaccines WHERE id=%s", (vaccine_id,))
        row = _fetch_one(cursor)
        cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail="Vaccine record not found")
        return row
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.put("/vaccines/{vaccine_id}")
async def update_vaccine(vaccine_id: int, v: PetVaccine):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE pet_vaccines SET pet_id=%s, vaccine_name=%s, dose=%s, vaccine_date=%s, next_due=%s, clinic=%s, note=%s WHERE id=%s",
            (v.pet_id, v.vaccine_name, v.dose, v.vaccine_date, v.next_due, v.clinic, v.note, vaccine_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Vaccine record not found")
        cursor.close()
        return {"message": "Vaccine record updated"}
    except Error as err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.delete("/vaccines/{vaccine_id}")
async def delete_vaccine(vaccine_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pet_vaccines WHERE id=%s", (vaccine_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Vaccine record not found")
        cursor.close()
        return {"message": f"vaccine {vaccine_id} deleted"}
    except Error as err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


# ================= BOOKINGS =================
@app.post("/bookings")
async def create_booking(b: Booking):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO bookings (user_id, pet_id, check_in, check_out, note, status, total_price, payment_slip, payment_status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (b.user_id, b.pet_id, b.check_in, b.check_out, b.note, "pending", b.total_price, b.payment_slip, b.payment_status),
        )
        conn.commit()
        bid = cursor.lastrowid
        cursor.close()
        return {"id": bid, **b.dict(), "status": "pending"}
    except Error as err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.get("/bookings")
async def get_bookings():
    """Admin: ดูการจองทั้งหมด พร้อมข้อมูล user และ pet"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, u.name AS user_name, u.email AS user_email,
                   p.name AS pet_name, p.type AS pet_type
            FROM bookings b
            LEFT JOIN users u ON b.user_id = u.id
            LEFT JOIN pets p ON b.pet_id = p.id
            ORDER BY b.id DESC
        """)
        rows = _fetch_all(cursor)
        cursor.close()
        return rows
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.get("/bookings/user/{user_id}")
async def get_bookings_by_user(user_id: int):
    """User: ดูประวัติการจองของตัวเอง"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT b.*, p.name AS pet_name, p.type AS pet_type
            FROM bookings b
            LEFT JOIN pets p ON b.pet_id = p.id
            WHERE b.user_id = %s
            ORDER BY b.id DESC
        """, (user_id,))
        rows = _fetch_all(cursor)
        cursor.close()
        return rows
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.get("/bookings/{booking_id}")
async def get_booking_by_id(booking_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM bookings WHERE id=%s", (booking_id,))
        row = _fetch_one(cursor)
        cursor.close()
        if not row:
            raise HTTPException(status_code=404, detail="Booking not found")
        return row
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.put("/bookings/{booking_id}/status")
async def update_booking_status(booking_id: int, body: dict):
    """Admin: อนุมัติ / ปฏิเสธ / เปลี่ยนสถานะการจอง
    body: { "status": "approved" | "rejected" | "staying" | "completed" }
    """
    new_status = body.get("status", "")
    valid = {"pending", "approved", "rejected", "staying", "completed"}
    if new_status not in valid:
        raise HTTPException(status_code=400, detail=f"status ต้องเป็นหนึ่งใน {valid}")
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE bookings SET status=%s WHERE id=%s", (new_status, booking_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Booking not found")
        cursor.close()
        return {"message": f"Booking {booking_id} updated to {new_status}"}
    except Error as err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.put("/bookings/{booking_id}/payment")
async def update_booking_payment(booking_id: int, body: PaymentUpdate):
    """User: อัปโหลดสลิปหลังชำระเงิน
    body: { "payment_slip": "...", "payment_status": "paid" }
    """
    slip = body.payment_slip
    pay_status = body.payment_status
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE bookings SET payment_slip=%s, payment_status=%s WHERE id=%s",
            (slip, pay_status, booking_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Booking not found")
        cursor.close()
        return {"message": "Payment updated"}
    except Error as err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()


@app.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bookings WHERE id=%s", (booking_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Booking not found")
        cursor.close()
        return {"message": f"booking {booking_id} deleted"}
    except Error as err:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn and conn.is_connected():
            conn.close()