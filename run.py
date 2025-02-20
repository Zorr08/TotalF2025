from app_init import create_initialized_flask_app

app = create_initialized_flask_app()

if __name__ == '__main__':
    # Enable debug mode and run on port 8080
    app.run(debug=True, port=8080) 