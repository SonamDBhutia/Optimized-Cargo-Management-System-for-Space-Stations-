from app import app

if __name__ == "__main__":
    # For frontend application (web UI)
    app.run(host="0.0.0.0", port=8000, debug=True)
