# CorePoint POS

A monolithic, enterprise-grade Point of Sale (POS) system built with Python, Django, and Bootstrap 5. Developed as a comprehensive final-year Computer Science capstone at Kenyatta University, this system completely bypasses the default Django admin panel to deliver a secure, role-protected frontend for inventory, CRM, and sales management.

**Core Features:**

- **Advanced POS Terminal:** Features dynamic category filtering, retail/wholesale pricing toggles, and seamless cart management.
- **Atomic Transactions:** Utilizes Django's `@transaction.atomic` to guarantee database integrity during stock deductions and invoice creation.
- **Quotations & CRM:** Integrated customer management allowing cashiers to generate and export custom quotes without altering inventory levels.
- **Role-Based Access Control:** Custom security decorators enforcing strict permissions across Admin, Manager, and Cashier roles.

**Tech Stack:** Python, Django, HTML5, CSS3, Bootstrap 5, Chart.js.
