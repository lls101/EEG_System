import uvicorn

if __name__ == "__main__":
    try:
        uvicorn.run("app:app", host="0.0.0.0", port=8001 ,reload= True)  # , log_config=LOGGING_CONFIG
    except KeyboardInterrupt:
        ...
