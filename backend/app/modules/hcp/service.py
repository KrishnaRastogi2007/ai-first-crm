"""
Service actual business rules rakhti hai.

Example:

API
 ↓
Service
 ↓
Repository
 ↓
DB

Suppose interaction log karna hai.

Service decide karegi:

HCP exists?
        ↓
Interaction valid?
        ↓
User allowed?
        ↓
Create interaction
        ↓
Create audit log
        ↓
Schedule follow-up?

Memory:

Service = decision maker
"""