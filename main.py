#main.py

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.v1.app:app", host="0.0.0.0", port=8080)
