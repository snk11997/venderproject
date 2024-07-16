Vendor Management System API
The Vendor Management System API is a Django REST Framework application designed to manage vendors, purchase orders, and track performance metrics.

Setup Instructions
Clone the Repository:

git clone <repository_url>
Install Dependencies:

pip install -r requirements.txt
Run Migrations:

python manage.py migrate
Create a Superuser (Optional):

python manage.py createsuperuser
Start the Development Server:

python manage.py runserver
Access the API:
API Root: http://localhost:8000/api/
Admin Interface: http://localhost:8000/admin/
API Endpoints
Vendors
GET /api/vendors/: Retrieve a list of all vendors.
POST /api/vendors/: Create a new vendor.
GET /api/vendors/{vendor_id}/: Retrieve details of a specific vendor.
PUT /api/vendors/{vendor_id}/: Update details of a specific vendor.
DELETE /api/vendors/{vendor_id}/: Delete a specific vendor.
Purchase Orders
GET /api/purchase_orders/: Retrieve a list of all purchase orders.
POST /api/purchase_orders/: Create a new purchase order.
GET /api/purchase_orders/{po_id}/: Retrieve details of a specific purchase order.
PUT /api/purchase_orders/{po_id}/: Update details of a specific purchase order.
DELETE /api/purchase_orders/{po_id}/: Delete a specific purchase order.
POST /api/purchase_orders/{po_id}/acknowledge: Acknowledge a purchase order.
Vendor Performance Metrics
GET /api/vendors/{vendor_id}/performance/: Retrieve performance metrics for a specific vendor.
Authentication
Authentication is required for certain endpoints, especially those related to creating, updating, or deleting data.
Use token-based authentication or session authentication for accessing authenticated endpoints.
Sample Data
Sample data for vendors and purchase orders can be added using the Django admin interface or through API endpoints.
Refer to the API documentation for sample data payloads and request formats.
Contributing
Contributions are welcome! If you'd like to contribute to this project, please follow these steps:

Fork the repository
Create a new branch (git checkout -b feature)
Make your changes
Commit your changes (git commit -am 'Add new feature')
Push to the branch (git push origin feature)
Create a new Pull Request