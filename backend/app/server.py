import uvicorn
import os

# BaseDir
base_dir = os.path.dirname(os.path.realpath(__file__))

if __name__ == '__main__':
    uvicorn.run("main:app",
                host="0.0.0.0",
                port=int(os.environ.get("PORT", 8000)),
                reload=True)