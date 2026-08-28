import random

from django.core.management.base import BaseCommand
from django.db import transaction

from crm.models import Customer, Supplier


CUSTOMERS = [
    ("Amina Wanjiku", "+254 711 204 581"),
    ("Brian Otieno", "+254 722 815 604"),
    ("Cynthia Muthoni", "+254 733 196 472"),
    ("David Kiptoo", "+254 745 320 618"),
    ("Esther Nyambura", "+254 701 445 923"),
    ("Felix Mwangi", "+254 712 756 149"),
    ("Grace Akinyi", "+254 723 867 250"),
    ("Hassan Abdalla", "+254 734 978 361"),
    ("Ivy Wairimu", "+254 746 189 572"),
    ("James Kariuki", "+254 707 290 683"),
    ("Kelvin Ouma", "+254 718 401 794"),
    ("Linet Chebet", "+254 729 512 805"),
    ("Martin Musyoka", "+254 740 623 916"),
    ("Naomi Wambui", "+254 751 734 027"),
    ("Oscar Maina", "+254 702 845 138"),
    ("Peninah Atieno", "+254 713 956 249"),
    ("Quincy Njoroge", "+254 724 167 350"),
    ("Ruth Kendi", "+254 735 278 461"),
    ("Samuel Kamau", "+254 747 389 572"),
    ("Terry Wanjala", "+254 708 490 683"),
]

SUPPLIERS = [
    ("Apex Office Supplies", "Mary Njeri", "+254 720 110 201"),
    ("Bluewave Beverages", "Joseph Otieno", "+254 720 110 202"),
    ("Coastal Catch Foods", "Asha Salim", "+254 720 110 203"),
    ("Dawn Bakery Distributors", "Peter Mwangi", "+254 720 110 204"),
    ("Eastland Electronics", "Kevin Kariuki", "+254 720 110 205"),
    ("Fresh Basket Produce", "Lucy Wambui", "+254 720 110 206"),
    ("Golden Grain Wholesalers", "Daniel Kiptoo", "+254 720 110 207"),
    ("Harbor Home Furnishings", "Faith Akinyi", "+254 720 110 208"),
    ("Icon Apparel Kenya", "Mark Mutua", "+254 720 110 209"),
    ("Jambo Kitchenware", "Anne Wairimu", "+254 720 110 210"),
    ("Kifaru Packaging", "Allan Ouma", "+254 720 110 211"),
    ("Lakeview Dairy", "Brenda Chebet", "+254 720 110 212"),
    ("Metro Mobile Accessories", "Chris Maina", "+254 720 110 213"),
    ("Northstar Hardware", "Diana Kendi", "+254 720 110 214"),
    ("Orbit Cleaning Products", "Eric Njoroge", "+254 720 110 215"),
    ("Peak Sportswear", "Gladys Wanjala", "+254 720 110 216"),
    ("Quality Print and Paper", "Henry Musyoka", "+254 720 110 217"),
    ("Riverbend Meat Suppliers", "Irene Nyambura", "+254 720 110 218"),
    ("Sunrise General Traders", "John Kamau", "+254 720 110 219"),
    ("Tamarind Imports", "Janet Abdalla", "+254 720 110 220"),
]


class Command(BaseCommand):
    help = "Create 20 sample customers and 20 sample suppliers without duplicates."

    @transaction.atomic
    def handle(self, *args, **options):
        customers = CUSTOMERS.copy()
        suppliers = SUPPLIERS.copy()
        random.shuffle(customers)
        random.shuffle(suppliers)

        created_customers = 0
        for name, phone in customers:
            _, created = Customer.objects.get_or_create(
                name=name,
                defaults={"phone": phone, "balance": 0},
            )
            created_customers += created

        created_suppliers = 0
        for name, contact_person, phone in suppliers:
            _, created = Supplier.objects.get_or_create(
                name=name,
                defaults={"contact_person": contact_person, "phone": phone},
            )
            created_suppliers += created

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_customers} customers and {created_suppliers} suppliers."
            )
        )
