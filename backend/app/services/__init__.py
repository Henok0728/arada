"""
Services package — business logic layer.

Services sit between route handlers (thin) and repositories (data access).
They are NOT aware of HTTP — they receive domain objects, call repositories,
apply business rules, and return domain results.
"""
