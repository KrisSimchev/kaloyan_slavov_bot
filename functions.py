import json
import os
from prompts import assistant_instructions

def create_assistant(client):
    assistant_file_path = 'assistant.json'

    if os.path.exists(assistant_file_path):
        with open(assistant_file_path, 'r') as file:
            assistant_data = json.load(file)
            assistant_id = assistant_data['assistant_id']
            vector_store_id = assistant_data['vector_store_id']
            print("Loaded existing assistant ID.")
    else:
        vector_store = client.beta.vector_stores.create(name="Knowledge about Kaloyan Slavov")
        vector_store_id=vector_store.id
        print("Current working directory:", os.getcwd())

        # If your files are in the same directory as main.py
        file_paths = [
            "Kaloyan Slavov.docx", 
            "Terms & Conditions.docx",
            "results.docx",
            "Blog.docx",
            "Products FAQ and intake.docx",
            "affiliate.docx"
        ]

        # Check if each file exists before proceeding
        for path in file_paths:
            if not os.path.exists(path):
                print(f"File not found: {path}")

        products_folder = "products"  # Remove './' as it's not needed

        if os.path.exists(products_folder):
            product_files = [
                f"products/{file}" for file in os.listdir(products_folder) if file.endswith(".docx")
            ]
            file_paths.extend(product_files)
        else:
            print(f"Folder '{products_folder}' does not exist.")
            print("Available directories:", os.listdir("."))  # List available directories for debugging

        file_streams = [open(path, "rb") for path in file_paths]


        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, 
            files=file_streams
        )

        print("Vector store created!")
        print(file_batch.status)
        print(file_batch.file_counts)

        assistant = client.beta.assistants.create(
            instructions=assistant_instructions,
            model="gpt-4o",
            tools=[{
                "type": "file_search",
                "type": "function",
                "function": {
                    "name": "track_order",
                    "description": "Tracking orders by customer's either: 1. phone number 2. Email 3. order number",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_by": {
                                "type": "string",
                                "description": "The customer's either email, phone number or order number"
                            }
                        },
                        "required": [
                            "order_by"
                        ],
                        "additionalProperties": False
                    },
                    "strict": True
                },
                "type": "function",
                "function": {
                    "name": "unsubscribe",
                    "description": "Unsubscribing for program",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Customer's name"
                            },
                            "phone": {
                                "type": "string",
                                "description": "Customer's phone number"
                            }
                        },
                        "required": [
                            "name", "phone"
                        ],
                        "additionalProperties": False
                    },
                    "strict": True
                },
                "type": "function",
                "function": {
                    "name": "purchase_products",
                    "description": "Making an order",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Customer's name"
                            },
                            "phone": {
                                "type": "string",
                                "description": "Customer's phone number"
                            },
                            "address": {
                                "type": "string",
                                "description": "Customer's address"
                            },
                            "email": {
                                "type": "string",
                                "description": "Customer's phone email"
                            },
                            "products": {
                                "type": "array",
                                "description": "List of products in the order",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                    "quantity": {
                                        "type": "string",
                                        "description": "Quantity of the product"
                                    },
                                    "name": {
                                        "type": "string",
                                        "description": "Name of the product"
                                    },
                                    "price": {
                                        "type": "string",
                                        "description": "Price of the product"
                                    }
                                    },
                                    "required": ["quantity", "name", "price"],
                                    "additionalProperties": False
                                }
                            },
                        },
                        "required": [
                            "name", "phone", "address", "email", "products"
                        ],
                        "additionalProperties": False
                    },
                    "strict": True
                },
            }
            ],
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
        )

        with open(assistant_file_path, 'w') as file:
            IDs = {
                'assistant_id': assistant.id,
                'vector_store_id': vector_store_id
            }
            json.dump(IDs, file)

        assistant_id = assistant.id

    return assistant_id, vector_store_id
