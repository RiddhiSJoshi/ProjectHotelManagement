from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["Hotel"]
rooms = db["rooms"]
customers = db["customers"]
bookings = db["bookings"]

@app.route("/addrooms", methods=["POST"])
def create_room():
    data = request.get_json()
    room_data = {
        "room_number": data.get("room_number"),
        "room_type": data.get("room_type"),
        "price": data.get("price"),
        "status": data.get("status")
    }
    rooms.insert_one(room_data)
    return jsonify({"message": "Room created successfully"})

@app.route("/getrooms", methods=["GET"])
def get_rooms():
    data = []
    for room in rooms.find():
        room["_id"] = str(room["_id"])
        data.append(room)
    return jsonify(data)

@app.route("/getrooms/<id>", methods=["GET"])
def get_roomnumber(id):
    room = rooms.find_one({"_id": ObjectId(id)})
    room["_id"] = str(room["_id"])
    return jsonify(room)

@app.route("/rooms/<id>", methods=["PUT"])
def update_room(id):
    data = request.get_json()
    room_data = {
        "room_number": data.get("room_number"),
        "room_type": data.get("room_type"),
        "price": data.get("price"),
        "status": data.get("status")
    }
    result = rooms.update_one(
        {"_id": ObjectId(id)},
        {"$set": room_data}
    )
    print(result)
    return jsonify({"message": "Room updated successfully"})

@app.route("/rooms/<id>", methods=["DELETE"])
def delete_room(id):
    rooms.delete_one(
        {"_id": ObjectId(id)}
    )
    return jsonify({"message": "Room deleted successfully"})

@app.route("/addcustomers", methods=["POST"])
def create_customers():
    data = request.get_json()
    customer_details = {
        "custname": data.get("custname"),
        "phone_number": data.get("phone_number"),
        "email_address": data.get("email_address"),
        "address": data.get("address")
    }
    customers.insert_one(customer_details)
    return jsonify({"message": "customers created successfully"})

@app.route("/getcustomers", methods=["GET"])
def get_customers():
    data = []
    for cust in customers.find():
        cust["_id"] = str(cust["_id"])
        data.append(cust)
    return jsonify(data)

@app.route("/getcustomer/<id>", methods=["GET"])
def get_idcustomers(id):
    customer = customers.find_one({"_id": ObjectId(id)})
    if customer:
        customer["_id"] = str(customer["_id"])
        return jsonify(customer)

    return jsonify({"error": "Customer not found"}), 404

@app.route("/customers/<id>", methods=["PUT"])
def update_customer(id):
    data = request.get_json()
    customer_details = {
        "custname": data.get("custname"),
        "phone_number": data.get("phone_number"),
        "email_address": data.get("email_address"),
        "address": data.get("address")
    }
    customers.update_one(
        {"_id": ObjectId(id)},
        {"$set": customer_details}
    )
    return jsonify({"message": "Customer updated successfully"})

@app.route("/customers/<id>", methods=["DELETE"])
def delete_customer(id):
    customers.delete_one(
        {"_id": ObjectId(id)}
    )
    return jsonify({"message": "customers deleted successfully"})

@app.route("/addbookings", methods=["POST"])
def create_booking():
    data = request.get_json()
    room_id = ObjectId(data["room_id"])
    customer_id = ObjectId(data["customer_id"])
    check_in = datetime.strptime(data["check_in"], "%d/%m/%Y")
    check_out = datetime.strptime(data["check_out"], "%d/%m/%Y")
    # Validate date
    if check_in >= check_out:
        return jsonify({"error": "Invalid date range"}), 400

    # Check room exists
    room = rooms.find_one({"_id": room_id})
    if not room:
        return jsonify({"error": "Room not found"}), 404

    # Check customer exists
    customer = customers.find_one({"_id": customer_id})
    if not customer:
        return jsonify({"error": "Customer not found"}), 404

    # Overlap check
    overlapping = bookings.find_one({
        "room_id": room_id,
        "check_in": {"$lt": check_out},
        "check_out": {"$gt": check_in}
    })

    if overlapping:
        return jsonify({"error": "Room already booked"}), 400
    booking_data = {
        "room_id": room_id,
        "customer_id": customer_id,
        "check_in": check_in,
        "check_out": check_out,
        "status": "Booked",
        "created_at": datetime.utcnow()
    }

    bookings.insert_one(booking_data)
    return jsonify({"message": "Booking created successfully"})

@app.route("/getbookings", methods=["GET"])
def get_bookings():
    data = []
    for book in bookings.find():
        book["_id"] = str(book["_id"])
        # Convert additional ObjectIds
        if "room_id" in book:
            book["room_id"] = str(book["room_id"])

        if "customer_id" in book:
            book["customer_id"] = str(book["customer_id"])
        # Convert datetime
        if "check_in" in book:
            book["check_in"] = book["check_in"].strftime("%d/%m/%Y")

        if "check_out" in book:
            book["check_out"] = book["check_out"].strftime("%d/%m/%Y")

        if "created_at" in book:
            book["created_at"] = book["created_at"].strftime("%d/%m/%Y %H:%M:%S")
        data.append(book)
    return jsonify(data)

@app.route("/getbooking/<id>", methods=["GET"])
def get_idbooking(id):
    try:
        obj_id = ObjectId(id)
    except:
        return jsonify({"error": "Invalid ID format"}), 400
    booking = bookings.find_one({"_id": ObjectId(id)})
    if booking:
        booking["_id"] = str(booking["_id"])
        booking["room_id"] = str(booking["room_id"])
        booking["customer_id"] = str(booking["customer_id"])
        return jsonify(booking)

    return jsonify({"error": "Booking not found"}), 404

@app.route("/available-rooms", methods=["GET"])
def available_rooms():
   
   check_in_str = request.args.get("check_in")
   check_out_str = request.args.get("check_out")
   # Validate input
   if not check_in_str or not check_out_str:
        return jsonify({"error": "check_in and check_out are required"}), 400
   try:
        check_in = datetime.strptime(check_in_str, "%d/%m/%Y")
        check_out = datetime.strptime(check_out_str, "%d/%m/%Y")
   except ValueError:
        return jsonify({"error": "Invalid date format. Use DD/MM/YYYY"}), 400

    # Find rooms that are already booked in this date range
   booked_rooms = bookings.find({
        "check_in": {"$lt": check_out},
        "check_out": {"$gt": check_in}
    })

    # Extract booked room IDs
   booked_room_ids = [b["room_id"] for b in booked_rooms]

    # Get rooms NOT in booked list
   available = rooms.find({
        "room_number": {"$nin": booked_room_ids}
    })

   result = []
   for room in available:
        room["_id"] = str(room["_id"])
        result.append(room)

   return jsonify(result)

@app.route("/bookings/<id>", methods=["PUT"])
def update_bookings(id):
    data = request.get_json()
    result = bookings.update_one(
        {"_id": ObjectId(id)},
        {"$set": data}
    )
    return jsonify({"message": "Booking updated successfully"})

@app.route("/bookings/<id>", methods=["DELETE"])
def delete_booking(id):
    booking = bookings.find_one({"_id": ObjectId(id)})
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    bookings.delete_one({"_id": ObjectId(id)})
    return jsonify({"message": "Booking deleted successfully"})

@app.route("/generate-bill/<booking_id>", methods=["GET"])
def generate_bill(booking_id):
    booking = bookings.find_one({"_id": ObjectId(booking_id)})

    days = (booking["check_out"] - booking["check_in"]).days
    room = rooms.find_one({"room_number": booking["room_number"]})

    total = days * room["price"]

    return jsonify({
        "room_number": booking["room_number"],
        "days": days,
        "total_amount": total
    })

if __name__ == '__main__':
    app.run(debug=True)