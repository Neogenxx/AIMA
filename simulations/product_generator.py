"""
Product Generator - Generate demo products for testing
"""

import random


def generate_demo_products(count: int = 20) -> list:
    """
    Generate demo products with realistic data
    
    Args:
        count: Number of products to generate
    
    Returns:
        List of product dictionaries
    """
    
    categories = {
        'Electronics': [
            ('Gaming Laptop', 800, 1200),
            ('Wireless Mouse', 12, 25),
            ('Mechanical Keyboard', 50, 120),
            ('USB-C Hub', 20, 45),
            ('Webcam HD', 30, 70),
            ('Bluetooth Speaker', 25, 60),
            ('Noise-Cancelling Headphones', 80, 200),
            ('Graphics Tablet', 60, 150),
            ('Portable SSD', 70, 140),
            ('Monitor Stand', 30, 65)
        ],
        'Office': [
            ('Ergonomic Chair', 150, 350),
            ('Standing Desk', 200, 500),
            ('Desk Lamp', 20, 45),
            ('Whiteboard', 40, 90),
            ('Paper Shredder', 50, 120),
            ('Label Maker', 25, 55),
            ('Stapler Heavy Duty', 15, 30),
            ('File Cabinet', 80, 180),
            ('Cork Board', 12, 28),
            ('Desk Organizer', 18, 35)
        ],
        'Food': [
            ('Premium Coffee Beans', 8, 15),
            ('Organic Green Tea', 6, 12),
            ('Dark Chocolate Bar', 3, 7),
            ('Energy Drink Pack', 10, 22),
            ('Protein Bar Box', 15, 30),
            ('Mixed Nuts', 8, 16),
            ('Granola Cereal', 5, 10),
            ('Instant Noodles Pack', 4, 8),
            ('Olive Oil', 12, 25),
            ('Honey Jar', 8, 18)
        ],
        'Furniture': [
            ('Bookshelf 5-Tier', 60, 140),
            ('Bean Bag Chair', 40, 90),
            ('Coffee Table', 80, 180),
            ('Floor Lamp', 35, 75),
            ('Wall Clock', 15, 35),
            ('Ottoman', 45, 95),
            ('Coat Rack', 25, 55),
            ('Magazine Rack', 18, 40),
            ('TV Stand', 70, 160),
            ('Side Table', 30, 70)
        ]
    }
    
    products = []
    product_num = 1
    
    for category, items in categories.items():
        for item_name, cost, selling in items:
            if product_num > count:
                break
            
            product_id = f"PROD-{product_num:03d}"
            
            # Random stock between 20-150
            stock = random.randint(20, 150)
            
            # Base threshold between 15-50
            base_threshold = random.randint(15, 50)
            
            # Initial popularity metrics
            popularity_ewma = round(random.uniform(0.5, 1.5), 2)
            popularity_index = round(random.uniform(0.8, 1.3), 2)
            
            # Adaptive threshold based on popularity
            adaptive_threshold = round(base_threshold * (1 + 0.2 * (popularity_index - 1)), 1)
            
            products.append({
                'product_id': product_id,
                'name': f"{item_name} {category[0]}{product_num}",
                'stock': stock,
                'base_threshold': base_threshold,
                'adaptive_threshold': adaptive_threshold,
                'popularity_ewma': popularity_ewma,
                'popularity_index': popularity_index,
                'cost_price': cost,
                'selling_price': selling
            })
            
            product_num += 1
        
        if product_num > count:
            break
    
    return products[:count]


if __name__ == '__main__':
    # Test generation
    products = generate_demo_products(10)
    
    print("Generated Demo Products:")
    print("=" * 80)
    for p in products:
        print(f"{p['product_id']}: {p['name']}")
        print(f"  Stock: {p['stock']}, Threshold: {p['adaptive_threshold']}")
        print(f"  Cost: ${p['cost_price']}, Selling: ${p['selling_price']}, Margin: ${p['selling_price'] - p['cost_price']}")
