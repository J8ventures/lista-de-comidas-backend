import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.handlers.ingredients import app as ingredients_app
from src.handlers.recipes import app as recipes_app
from src.handlers.meal_plans import app as meal_plans_app

app = FastAPI(title="Recipe Manager Local Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/", ingredients_app)
app.mount("/", recipes_app)
app.mount("/", meal_plans_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("local_server:app", host="0.0.0.0", port=3001, reload=True)
