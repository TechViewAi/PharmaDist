-- PharmaDist Database Setup
-- This script creates all tables needed for the pharmaceutical distributor chatbot

-- Create database (uncomment if you need to create the database)
-- CREATE DATABASE pharma;

-- Create vendors table
CREATE TABLE vendors (
    vendor_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    vendor_type VARCHAR(50) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create products table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    generic_name VARCHAR(100) NOT NULL,
    brand_name VARCHAR(100),
    active_ingredients TEXT[] NOT NULL,
    pharmacological_class VARCHAR(100),
    atc_codes VARCHAR[],
    indications TEXT,
    contraindications TEXT,
    mechanism_of_action TEXT,
    dosage_form VARCHAR(50),
    strength VARCHAR(50),
    route_of_administration VARCHAR(50),
    packaging VARCHAR(100),
    synonyms TEXT[],
    description TEXT,
    manufacturer VARCHAR(100),
    storage_conditions VARCHAR(100),
    price_per_unit DECIMAL(10,2) NOT NULL
);

-- Create batches table
CREATE TABLE batches (
    batch_id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    batch_number VARCHAR(50) NOT NULL,
    expiry_date DATE NOT NULL,
    on_hand INT NOT NULL DEFAULT 0,
    reserved INT NOT NULL DEFAULT 0
);

-- Create orders table
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    vendor_id INT REFERENCES vendors(vendor_id),
    order_date TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'Pending'
);

-- Create order_items table
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id),
    product_id INT REFERENCES products(product_id),
    batch_id INT REFERENCES batches(batch_id),
    qty_requested INT NOT NULL,
    qty_reserved INT NOT NULL
);



-- Insert sample data for testing

-- Sample vendors
INSERT INTO vendors (name, vendor_type, contact_person, phone, email, address)
VALUES 
    ('ABC Pharmacy', 'Retail Pharmacy', 'John Doe', '555-1234', 'john.doe@abcpharmacy.com', '123 Health Street, Medical District, NY 10001'),
    ('MediCare Hospital', 'Hospital', 'Jane Smith', '555-5678', 'jane.smith@medicare.org', '456 Care Avenue, Hospital Zone, CA 90210'),
    ('QuickMeds Chain', 'Pharmacy Chain', 'Robert Johnson', '555-9012', 'robert.j@quickmeds.com', '789 Fast Lane, Downtown, TX 75001');

-- Sample products
INSERT INTO products (generic_name, brand_name, active_ingredients, pharmacological_class, atc_codes, indications, contraindications, mechanism_of_action, dosage_form, strength, route_of_administration, packaging, synonyms, description, manufacturer, storage_conditions, price_per_unit)
VALUES
    ('Paracetamol', 'Tylenol', ARRAY['Acetaminophen'], 'Analgesic and antipyretic', ARRAY['N02BE01'], 'Mild to moderate pain, fever', 'Severe liver impairment', 'Inhibits prostaglandin synthesis in the CNS', 'Tablet', '500 mg', 'Oral', 'Blister pack of 20 tablets', ARRAY['Acetaminophen'], 'White, round tablet for pain relief and fever reduction', 'Johnson & Johnson', 'Store below 25°C in a dry place', 0.15),
    
    ('Amoxicillin', 'Amoxil', ARRAY['Amoxicillin trihydrate'], 'Penicillin antibiotic', ARRAY['J01CA04'], 'Bacterial infections', 'Penicillin allergy', 'Inhibits bacterial cell wall synthesis', 'Capsule', '500 mg', 'Oral', 'Bottle of 20 capsules', ARRAY['Amox'], 'Red and yellow capsule for treating bacterial infections', 'GlaxoSmithKline', 'Store below 25°C away from moisture', 0.45),
    
    ('Losartan', 'Cozaar', ARRAY['Losartan potassium'], 'Angiotensin II receptor blocker', ARRAY['C09CA01'], 'Hypertension, diabetic nephropathy', 'Pregnancy', 'Blocks the binding of angiotensin II to AT1 receptors', 'Tablet', '50 mg', 'Oral', 'Blister pack of 30 tablets', ARRAY['Losartan potassium'], 'White, oval tablet for blood pressure control', 'Merck', 'Store at room temperature', 0.80),
    
    ('Ibuprofen', 'Advil', ARRAY['Ibuprofen'], 'NSAID', ARRAY['M01AE01'], 'Pain, inflammation, fever', 'Peptic ulcer, severe heart failure', 'Inhibits cyclooxygenase enzymes COX-1 and COX-2', 'Tablet', '400 mg', 'Oral', 'Bottle of 24 tablets', ARRAY['Ibu'], 'Brown, round, film-coated tablet for pain and inflammation', 'Pfizer', 'Store below 25°C', 0.25),
    
    ('Metformin', 'Glucophage', ARRAY['Metformin hydrochloride'], 'Biguanide antidiabetic', ARRAY['A10BA02'], 'Type 2 diabetes', 'Renal impairment, metabolic acidosis', 'Decreases hepatic glucose production and improves insulin sensitivity', 'Tablet', '850 mg', 'Oral', 'Blister pack of 60 tablets', ARRAY['Metformin HCl'], 'White, round tablet for controlling blood glucose levels', 'Merck', 'Store at room temperature', 0.30);

-- Sample batches
INSERT INTO batches (product_id, batch_number, expiry_date, on_hand, reserved)
VALUES
    (1, 'PARA-A23', '2026-01-31', 1000, 0),
    (1, 'PARA-B23', '2026-03-15', 1500, 0),
    (2, 'AMOX-C22', '2025-06-30', 800, 0),
    (3, 'LOS-D21', '2025-10-15', 600, 0),
    (4, 'IBU-E23', '2026-05-20', 1200, 0),
    (5, 'MET-F22', '2025-08-10', 900, 0);
