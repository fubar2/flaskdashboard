from app import create_app

server = create_app()
server.run(debug=True,port='5001')

