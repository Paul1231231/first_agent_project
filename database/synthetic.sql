-- Generate 100 Customers
INSERT INTO customers (name, email, country, created_at)
SELECT 
    (ARRAY['Alice', 'Bob', 'Charlie', 'David', 'Eva', 'Frank', 'Grace', 'Hannah', 'Ian', 'Jack'])[FLOOR(RANDOM() * 10 + 1)] || ' ' ||
    (ARRAY['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez'])[FLOOR(RANDOM() * 10 + 1)] AS name,
    'user' || i || '@example.com' AS email,
    (ARRAY['USA', 'Canada', 'UK', 'Germany', 'Taiwan', 'Japan', 'Australia', 'France'])[FLOOR(RANDOM() * 8 + 1)] AS country,
    NOW() - (RANDOM() * INTERVAL '365 days') AS created_at
FROM generate_series(1, 100) AS i;

-- Generate 20 Products
INSERT INTO products (name, category, price) VALUES
('Wireless Mouse', 'Electronics', 29.99),
('Mechanical Keyboard', 'Electronics', 89.99),
('4K Monitor', 'Electronics', 299.99),
('USB-C Hub', 'Electronics', 45.00),
('Noise Canceling Headphones', 'Electronics', 199.50),
('Ergonomic Chair', 'Furniture', 249.99),
('Standing Desk', 'Furniture', 499.00),
('Desk Lamp', 'Furniture', 35.00),
('Notebook', 'Stationery', 5.99),
('Gel Pens (Pack of 10)', 'Stationery', 12.49),
('Coffee Mug', 'Home', 14.99),
('Stainless Water Bottle', 'Home', 22.00),
('Backpack', 'Accessories', 59.99),
('Laptop Sleeve', 'Accessories', 25.00),
('Smartphone Stand', 'Electronics', 15.99),
('Webcam 1080p', 'Electronics', 69.99),
('Bluetooth Speaker', 'Electronics', 49.99),
('Desk Pad', 'Accessories', 19.99),
('Planner 2026', 'Stationery', 18.00),
('Cable Organizer Clips', 'Electronics', 8.99);

-- Generate 300 Random Orders
INSERT INTO orders (customer_id, order_date, status)
SELECT 
    FLOOR(RANDOM() * 100 + 1)::INT AS customer_id,
    NOW() - (RANDOM() * INTERVAL '180 days') AS order_date,
    (ARRAY['Pending', 'Completed', 'Shipped', 'Cancelled'])[FLOOR(RANDOM() * 4 + 1)] AS status
FROM generate_series(1, 300);

-- Generate 1 to 4 Order Items per Order
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT 
    o.id AS order_id,
    p.id AS product_id,
    FLOOR(RANDOM() * 3 + 1)::INT AS quantity,
    p.price AS unit_price
FROM orders o
CROSS JOIN LATERAL (
    SELECT id, price FROM products ORDER BY RANDOM() LIMIT FLOOR(RANDOM() * 4 + 1)::INT
) p;

-- Recalculate Order Total Amount from Order Items
UPDATE orders o
SET total_amount = sub.calculated_total
FROM (
    SELECT order_id, SUM(quantity * unit_price) AS calculated_total
    FROM order_items
    GROUP BY order_id
) sub
WHERE o.id = sub.order_id;