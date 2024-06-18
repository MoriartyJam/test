from flask import Flask, render_template, redirect, url_for, jsonify, render_template_string
import requests
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime

# Flask application setup
app = Flask(__name__)

# URL to fetch the products
url = "http://207.180.219.163:65180/floristics/hs/Post/v1/GetAllItemsShopify"

# Basic authentication credentials
username = "web"
password = "Ufpc4405"

# Shopify API credentials
shopify_store_url = "https://quickstart-da63505a.myshopify.com"
access_token = "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"

# Example payload (modify according to the API's requirements)
payload = {}


def fetch_products():
    try:
        response = requests.post(url, auth=HTTPBasicAuth(username, password), json=payload)
        if response.status_code == 200:
            content = response.content.decode('utf-8-sig')
            products = json.loads(content)
            return products
        else:
            print(f"Failed to fetch products. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def transform_to_shopify_format(product):
    shopify_product = {
        "product": {
            "title": product['name_en'],
            "body_html": f"<strong>{product.get('description', '')}</strong>",
            "vendor": product['brand'],
            "product_type": product['group'],
            "created_at": datetime.now().isoformat(),
            "handle": product['name_en'].replace(" ", "-").lower(),
            "updated_at": datetime.now().isoformat(),
            "published_scope": "web",
            "status": "draft",
            "variants": [
                {
                    "title": "Default Title",
                    "price": product['price'],
                    "sku": product['sku'],
                    "position": 1,
                    "inventory_policy": "deny",
                    "compare_at_price": product['price_sale'] if product['price_sale'] else None,
                    "fulfillment_service": "manual",
                    "inventory_management": None,
                    "option1": "Default Title",
                    "taxable": True,
                    "grams": int(product['weight']) if product['weight'].isdigit() else 0,
                    "weight": int(product['weight']) if product['weight'].isdigit() else 0,
                    "weight_unit": "g",
                    "inventory_quantity": int(list(product['warehouses'].values())[0]) if product['warehouses'] else 0,
                    "requires_shipping": True
                }
            ],
            "options": [
                {
                    "name": "Title",
                    "position": 1,
                    "values": [
                        "Default Title"
                    ]
                }
            ],
            "images": [{"src": image_url} for image_url in product.get('images', [])],
            "image": {"src": product['images'][0]} if product.get('images') else None
        }
    }
    return shopify_product


def get_shopify_product_by_sku(sku):
    shopify_url = f"{shopify_store_url}/admin/api/2024-01/products.json?fields=id,variants&limit=250"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }
    try:
        response = requests.get(shopify_url, headers=headers)
        if response.status_code == 200:
            products = response.json().get('products', [])
            for product in products:
                for variant in product['variants']:
                    if variant['sku'] == sku:
                        return product
        else:
            print(f"Failed to fetch products from Shopify. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred while fetching products from Shopify: {e}")
    return None


def update_shopify_product_price(product_id, variant_id, new_price):
    shopify_url = f"{shopify_store_url}/admin/api/2024-01/products/{product_id}/variants/{variant_id}.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }
    data = {
        "variant": {
            "id": variant_id,
            "price": new_price
        }
    }
    try:
        response = requests.put(shopify_url, headers=headers, json=data)
        if response.status_code == 200:
            print(f"Product price updated successfully: {response.json()}")
        else:
            print(f"Failed to update product price. Status code: {response.status_code}, Response: {response.json()}")
    except Exception as e:
        print(f"An error occurred while updating product price on Shopify: {e}")


def send_to_shopify(shopify_product):
    shopify_url = f"{shopify_store_url}/admin/api/2024-01/products.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": access_token
    }
    try:
        response = requests.post(shopify_url, headers=headers, json=shopify_product)
        if response.status_code == 201:
            print("Product added successfully:", response.json())
        else:
            print(f"Failed to add product. Status code: {response.status_code}, Response: {response.json()}")
    except Exception as e:
        print(f"An error occurred while sending product to Shopify: {e}")


def main():
    products = fetch_products()
    if products:
        print("Products fetched successfully:")
        for product in products:
            print(product)
            existing_product = get_shopify_product_by_sku(product['sku'])
            if existing_product:
                variant = existing_product['variants'][0]
                if variant['price'] != product['price']:
                    update_shopify_product_price(existing_product['id'], variant['id'], product['price'])
                else:
                    print(f"Product with SKU {product['sku']} already exists with the same price.")
            else:
                shopify_product = transform_to_shopify_format(product)
                send_to_shopify(shopify_product)
    else:
        print("No products found or an error occurred.")


# Flask route to trigger the product fetch and send process
@app.route('/sync_products')
def sync_products():
    main()
    return jsonify({'status': 'finished'})


# Flask route for the home page with the button
@app.route('/')
def index():
    return render_template_string('''
        <style>
            body, html {
                height: 100%;
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                text-align: center;
                background-color: #f2f2f2;
                font-family: Arial, sans-serif;
            }
            .container {
                max-width: 80%;
                margin: auto;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            h1 {
                margin-bottom: 20px;
                font-size: 3em;
            }
            button {
                padding: 10px;
                font-size: 1.5em;
                cursor: pointer;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 10px;
                transition: background-color 0.3s ease;
            }
            button:hover {
                background-color: #45a049;
            }
            #status img {
                width: 200px;
                height: 250px;
            }
            #status {
                padding-top: 20px;
            }
            @media (max-width: 600px) {
                h1 {
                    font-size: 2em;
                }
                button {
                    padding: 15px 30px;
                    font-size: 1.5em;
                }
                #status img {
                    width: 150px;
                    height: 250px;
                }
            }
        </style>
        <div class="container">
            <h1>Sync 1c to Shopify</h1>
            <button onclick="syncProducts()">Sync Products to Shopify</button>
            <div id="status"></div>
        </div>
        <script> 
            function syncProducts() {
                document.getElementById("status").innerHTML = '<img src="https://i.gifer.com/YCZH.gif" alt="Loading"/>';
                fetch('/sync_products')
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'finished') {
                            document.getElementById("status").innerHTML = 'Sync process finished.';
                        } else {
                            document.getElementById("status").innerHTML = 'An error occurred during sync.';
                        }
                    })
                    .catch(error => {
                        document.getElementById("status").innerHTML = 'An error occurred during sync.';
                    });
            }
        </script>
    ''')


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=80)
