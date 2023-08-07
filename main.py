from typing import Optional

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import models
from database import engine, SessionLocal
from routers.auth import get_current_user, get_user_exception

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class Todo(BaseModel):
    title: str
    description: Optional[str]
    priority: int = Field(gt=0)
    complete: bool


@app.get("/")
async def read_all_todos(db: Session = Depends(get_db)):
    return db.query(models.Todos).all()


@app.get("/todos/user")
async def read_all_todos_by_user(user: dict = Depends(get_current_user),
                                 db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    return db.query(models.Todos) \
        .filter(models.Todos.owner_id == user.get("id")) \
        .all()


@app.get("/todo/{todo_id}")
async def read_todo_by_user_and_id(todo_id: int,
                                   user: dict = Depends(get_current_user),
                                   db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    todo_model = db.query(models.Todos) \
        .filter(models.Todos.id == todo_id) \
        .filter(models.Todos.owner_id == user.get("id")) \
        .first()

    if todo_model is None:
        raise http_exception()

    return todo_model


@app.post("/create_todo")
async def create_todo_by_user(todo: Todo,
                              user: dict = Depends(get_current_user),
                              db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    todo_model = models.Todos()
    todo_model.title = todo.title
    todo_model.description = todo.description
    todo_model.priority = todo.priority
    todo_model.complete = todo.complete
    todo_model.owner_id = user.get("id")

    db.add(todo_model)
    db.commit()

    return successful_response(201)


@app.put("/update_todo/{todo_id}")
async def update_todo_by_user_and_id(todo_id: int,
                                     todo: Todo,
                                     user: dict = Depends(get_current_user),
                                     db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    todo_model = db.query(models.Todos) \
        .filter(models.Todos.id == todo_id) \
        .filter(models.Todos.owner_id == user.get("id")) \
        .first()

    if todo_model is None:
        raise http_exception()

    todo_model.title = todo.title
    todo_model.description = todo.description
    todo_model.priority = todo.priority
    todo_model.complete = todo.complete

    db.add(todo_model)
    db.commit()

    return successful_response(200)


@app.delete("/delete_todo/{todo_id}")
async def delete_todo_by_user_and_id(todo_id: int,
                                     user: dict = Depends(get_current_user),
                                     db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    todo_model = db.query(models.Todos) \
        .filter(models.Todos.id == todo_id) \
        .filter(models.Todos.owner_id == user.get("id")) \
        .first()

    if todo_model is None:
        raise http_exception()

    db.query(models.Todos) \
        .filter(models.Todos.id == todo_id) \
        .delete()

    db.commit()

    return successful_response(200)


def http_exception():
    return HTTPException(status_code=404, detail="Todo not found")


def successful_response(status_code: int):
    return {
        'status': status_code,
        'transaction': 'Successful'
    }
