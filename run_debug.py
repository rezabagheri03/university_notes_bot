from flask import Flask
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("Registered URLs:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule}")
    
    print("\nRegistered Blueprints:")
    for blueprint in app.blueprints:
        print(f"Blueprint: {blueprint}")
        
    print("\nStarting Flask application...")
    app.run(debug=True, use_reloader=False) 