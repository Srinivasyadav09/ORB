"""Create the minimal local browser-E2E dataset through the backend API.

Run inside a running development API container:
  E2E_ADMIN_EMAIL=... E2E_ADMIN_PASSWORD=... python -m scripts.seed_e2e_data

This script is deliberately explicit and refuses production environments. It
uses API registration, verification, address, and farmer-product routes; it
does not write database rows directly.
"""

from __future__ import annotations

import os

import httpx

from app.core.config import settings

API_BASE_URL = os.getenv("E2E_API_BASE_URL", "http://127.0.0.1:8000/api").rstrip("/")
CUSTOMER = {
    "email": "orb.e2e.customer@example.com",
    "password": "OrbE2ECustomer2026!",
    "full_name": "ORB E2E Customer",
    "phone": "+919912300101",
}
FARMER = {
    "email": "orb.e2e.farmer@example.com",
    "password": "OrbE2EFarmer2026!",
    "full_name": "ORB E2E Farmer",
    "phone": "+919912300102",
    "farm_name": "ORB E2E Farm",
    "farm_location": "Bengaluru, Karnataka",
    "farm_description": "Development-only farm account for browser E2E.",
}
PRODUCT = {
    "name": "ORB E2E Tomatoes",
    "description": "Fresh development sample tomatoes for browser E2E.",
    "price": "40.00",
    "unit": "kg",
    "available_quantity": "25.000",
    "image_url": "https://images.unsplash.com/photo-1546094096-0df4bcaaa337?auto=format&fit=crop&w=800&q=85",
    "status": "ACTIVE",
}
ADDRESS = {
    "full_name": CUSTOMER["full_name"],
    "phone": CUSTOMER["phone"],
    "address_line_1": "12 E2E Market Road",
    "address_line_2": "",
    "city": "Bengaluru",
    "state": "Karnataka",
    "postal_code": "560001",
    "country": "India",
    "label": "ORB E2E",
    "is_default": True,
}


def ensure_account(client: httpx.Client, role: str, body: dict) -> tuple[dict, str]:
    path = f"/auth/register/{role}"
    response = client.post(path, json=body)
    if response.status_code not in (201, 409):
        response.raise_for_status()
    login = client.post(
        "/auth/login", json={"email": body["email"], "password": body["password"]}
    )
    login.raise_for_status()
    result = login.json()
    return result["user"], result["access_token"]


def main() -> None:
    if settings.ENVIRONMENT.lower() == "production":
        raise SystemExit("E2E development data is disabled in production.")
    admin_email = os.getenv("E2E_ADMIN_EMAIL", "").strip()
    admin_password = os.getenv("E2E_ADMIN_PASSWORD", "")
    if not admin_email or not admin_password:
        raise SystemExit("Set E2E_ADMIN_EMAIL and E2E_ADMIN_PASSWORD.")

    with httpx.Client(base_url=API_BASE_URL, timeout=20.0) as client:
        customer, customer_token = ensure_account(client, "customer", CUSTOMER)
        farmer, farmer_token = ensure_account(client, "farmer", FARMER)
        admin_login = client.post(
            "/auth/login", json={"email": admin_email, "password": admin_password}
        )
        admin_login.raise_for_status()
        admin_token = admin_login.json()["access_token"]

        verification = client.get(
            "/farmers/me/verification",
            headers={"Authorization": f"Bearer {farmer_token}"},
        )
        verification.raise_for_status()
        # The admin list returns the farmer profile UUID required by its
        # verification endpoint; auth responses intentionally omit that ID.
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        applications = client.get(
            "/admin/farmers", params={"page_size": 100}, headers=admin_headers
        )
        applications.raise_for_status()
        matching = next(
            item
            for item in applications.json()["items"]
            if item["email"] == FARMER["email"]
        )
        farmer_id = matching["id"]
        status_value = verification.json()["status"]
        if status_value == "SUBMITTED":
            update = client.patch(
                f"/admin/farmers/{farmer_id}/verification",
                headers=admin_headers,
                json={"status": "VERIFYING"},
            )
            update.raise_for_status()
            status_value = "VERIFYING"
        if status_value == "VERIFYING":
            update = client.patch(
                f"/admin/farmers/{farmer_id}/verification",
                headers=admin_headers,
                json={"status": "COMPLETED"},
            )
            update.raise_for_status()
        elif status_value != "COMPLETED":
            raise SystemExit(
                f"Farmer is {status_value}; admin workflow cannot publish products."
            )

        categories = client.get("/categories")
        categories.raise_for_status()
        category = next(
            item for item in categories.json() if item["name"].casefold() == "vegetables"
        )
        farmer_headers = {"Authorization": f"Bearer {farmer_token}"}
        farmer_products = client.get(
            "/farmers/me/products",
            params={"search": PRODUCT["name"]},
            headers=farmer_headers,
        )
        farmer_products.raise_for_status()
        existing_product = next(
            (
                item
                for item in farmer_products.json()["items"]
                if item["name"] == PRODUCT["name"]
            ),
            None,
        )
        product_body = {**PRODUCT, "category_id": category["id"]}
        if existing_product:
            product = client.patch(
                f"/farmers/me/products/{existing_product['id']}",
                headers=farmer_headers,
                json=product_body,
            )
        else:
            product = client.post(
                "/farmers/me/products", headers=farmer_headers, json=product_body
            )
        product.raise_for_status()
        product_data = product.json()

        customer_headers = {"Authorization": f"Bearer {customer_token}"}
        addresses = client.get("/addresses", headers=customer_headers)
        addresses.raise_for_status()
        address = next(
            (item for item in addresses.json() if item.get("label") == ADDRESS["label"]),
            None,
        )
        if address is None:
            created = client.post("/addresses", headers=customer_headers, json=ADDRESS)
            created.raise_for_status()
            address = created.json()

        print(f"Customer: {customer['email']} ({customer['id']})")
        print(f"Farmer: {farmer['email']} ({farmer_id}), verification=COMPLETED")
        print(f"Category: {category['name']} ({category['id']})")
        print(
            f"Product: {product_data['name']} ({product_data['id']}), "
            f"status={product_data['status']}, farmer={product_data['farmer']['id']}"
        )
        print(f"Address: {address['label']} ({address['id']})")


if __name__ == "__main__":
    main()
