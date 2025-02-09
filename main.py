from flask import Flask, request, jsonify
from openai import OpenAI
import functions
from prompts import assistant_instructions
import time
import json
import pickle
import base64
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import config
import requests
from datetime import datetime, timedelta, timezone
import pickle

app = Flask(__name__)

# Global variables
client = OpenAI(api_key=config.OPENAI_API_KEY)
assistant_id, vector_store_id = functions.create_assistant(client)
purchase_id = 0

def load_credentials():
    creds = None
    if os.path.exists('token.pkl'):
        with open('token.pkl', 'rb') as token_file:
            creds = pickle.load(token_file)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open('token.pkl', 'wb') as token_file:
            pickle.dump(creds, token_file)
    elif not creds:
        print("Token not found or invalid. Please regenerate it.")
        return None

    return creds

def send_email(recipient_email, subject, body):
    """Send an email using Gmail API and OAuth 2.0."""
    creds = load_credentials()
    service = build("gmail", "v1", credentials=creds)

    # Create email message
    msg = MIMEMultipart()
    msg["From"] = config.GMAIL_SENDER
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Encode and send email
    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    send_message = {"raw": raw_message}
    service.users().messages().send(userId="me", body=send_message).execute()
    print(f"Email sent to {recipient_email}!")

def purchase_products(products, name, address, phone, email):
    """Handles product purchases, assigns an order ID, and sends a confirmation email."""
    global purchase_id
    purchase_id += 1

    subject = f"Заявка за нова поръчка {purchase_id}"
    product_list = "\n".join([f"{p['quantity']} X {p['name']} -   {p['price']}" for p in products])

    body = f"""
    Поръчка номер: {purchase_id}
    Име: {name}
    {product_list}
    Адрес: {address}
    Номер: {phone}
    Имейл: {email}
    """

    send_email("kris.simchev@gmail.com", subject, body)
    return "успешно изпратена заявка. очаквайте потвърждение."

def unsubscribe(name, phone):
    """Sends an email notification when a user unsubscribes."""
    subject = f"Отказ от абонамент - {name}"
    body = f"""
    
    {name} иска да се откаже от абонамент.

    Телефон: {phone}
    """

    send_email("kris.simchev@gmail.com", subject, body)
    return "успешно изпратена заявка. очаквайте потвърждение."

def track_order(order_by):
    all_orders = get_all_orders(order_by)
    if not all_orders:
        phone_number = order_by
        all_orders = get_all_orders("+359" + phone_number[1:])  # Replace first character with +359
    if not all_orders:
        all_orders = get_all_orders("359" + phone_number[1:])  # Replace first character with 359
    if not all_orders:
        all_orders = get_all_orders("0" + phone_number[4:])  # Replace first four characters with 0
    if not all_orders:
        all_orders = get_all_orders("0" + phone_number[3:])  # Replace first three characters with 0
    if not all_orders:
        formatted_phone = f"{phone_number[:3]} {phone_number[3:6]} {phone_number[6:]}"  # Add spaces
        all_orders = get_all_orders(formatted_phone)
    if not all_orders:
        phone_number="0" + phone_number[3:]
        formatted_phone = f"{phone_number[:3]} {phone_number[3:6]} {phone_number[6:]}"  # Add spaces
        all_orders = get_all_orders(formatted_phone)
    if not all_orders:
        phone_number="0" + phone_number[2:]
        formatted_phone = f"{phone_number[:3]} {phone_number[3:6]} {phone_number[6:]}"  # Add spaces
        all_orders = get_all_orders(formatted_phone)



    important_orders = []

    for order in all_orders:
        important_info = {
            "Order Number": order.get("number"),
            "Status": order.get("status"),
            "Total": f"{order.get('total')} {order.get('currency_symbol', 'BGN')}",
            "Payment Method": order.get("payment_method_title"),
            "Shipping Method": order.get("shipping_lines")[0]["method_title"] if order.get("shipping_lines") else "Not specified",
            "Products": [
                {
                    "Product Name": item["name"],
                    "Quantity": item["quantity"],
                    "Price": f"{item['total']} {order.get('currency_symbol', 'BGN')}",
                }
                for item in order.get("line_items", [])
            ],
            "Date Ordered": order.get("date_created"),
            "Address": f"{order.get('billing', {}).get('address_1', '')} {order.get('billing', {}).get('address_1', '')}",
            "Customer Name": f"{order.get('billing', {}).get('first_name', '')} {order.get('billing', {}).get('last_name', '')}",
            "Phone": order.get("billing", {}).get("phone", "No phone provided"),
        }
        important_orders.append(important_info)

    if important_orders: return important_orders
    else: return "no orders found."

def add_to_email_list(name, email):
    return "success"

def get_all_orders(search_by):
    """Fetches all orders from the WooCommerce store."""
    orders = []
    page = 1
    per_page = 10  # Maximum allowed per request

    date_after = (datetime.now(timezone.utc) - timedelta(days=14)).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


    url = f"{config.WC_API_BASE_URL}/orders"
    params = {
        "consumer_key": config.CONSUMER_KEY,
        "consumer_secret": config.CONSUMER_SECRET,
        "per_page": per_page,
        "page": page,
        "after": date_after,
        "search": search_by
    }

    while True: 
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if not data:  # If no more orders, stop
                break
            orders.extend(data)
            page += 1  # Go to the next page
        else:
            print(f"Error {response.status_code}: {response.text}")
            break
        break

    return orders

@app.route('/start', methods=['GET'])
def start():
    try:
        thread = client.beta.threads.create()
        return jsonify({
            "thread_id": thread.id,
            "status": "success"
        }), 200
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        thread_id = data.get('thread_id')
        user_message = data.get('message')
        
        if not thread_id or not user_message:
            return jsonify({
                "error": "Missing thread_id or message",
                "status": "error"
            }), 400

        # Add the user's message to the thread
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )
        print("Added a message")

        # Create and initialize the run
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            instructions=assistant_instructions
        )
        print("Initialized run")
        
        while True:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            print(run.status)
            time.sleep(0.7)

            if run.status == 'completed':
                messages = client.beta.threads.messages.list(
                    thread_id=thread_id
                )
                assistant_response = [content.text.value 
                                    for message in messages.data 
                                    if message.role == 'assistant' 
                                    for content in message.content 
                                    if content.type == 'text'][0]
                return jsonify({
                    "response": assistant_response,
                    "status": "success"
                }), 200

            if run.status == 'requires_action':
                print("Processing function call")
                # Handle the function call
                for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                    try:
                        print("Arguments: ", tool_call.function.arguments)

                        if tool_call.function.name == "track_order":
                            print("Executing track_order function")
                            arguments = json.loads(tool_call.function.arguments)
                            output = track_order(arguments["order_by"])
                        elif tool_call.function.name == "add_to_email_list":
                            print("Executing add_to_email_list function")
                            arguments = json.loads(tool_call.function.arguments)
                            output = add_to_email_list(
                                arguments["name"],
                                arguments["email"]
                            )
                        elif tool_call.function.name == "unsubscribe":
                            print("Executing unsubscribe function")
                            arguments = json.loads(tool_call.function.arguments)
                            output = unsubscribe(
                                arguments["name"],
                                arguments["phone"]
                            )
                        elif tool_call.function.name == "purchase_products":
                            print("Executing purchase_products function")
                            arguments = json.loads(tool_call.function.arguments)
                            output = purchase_products(
                                name=arguments["name"],
                                phone=arguments["phone"],
                                address=arguments["address"],
                                email=arguments["email"],
                                products=arguments["products"]
                            )
                            
                        run = client.beta.threads.runs.submit_tool_outputs(
                            thread_id=thread_id,
                            run_id=run.id,
                            tool_outputs=[{
                                "tool_call_id": tool_call.id,
                                "output": json.dumps(output)
                            }]
                        )
                        print("Tool outputs submitted successfully.")
                    except Exception as e:
                        print(f"Failed to process tool call: {str(e)}")
                        return jsonify({
                            "error": str(e),
                            "status": "error"
                        }), 500

            if run.status == 'failed':
                print(run.status)
                print(run.last_error)
                return jsonify({
                    "error": run.last_error,
                    "status": "error"
                }), 500

    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)