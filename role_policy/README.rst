.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

===========
Role Policy
===========

This module replaces the standard Odoo security Groups by Roles.


When installing the module all security groups are removed from users, actions and menu items.
When the user interface is loaded the group definition within the XML screen maps are also ignored.


A role is equivalent to a group (every role has an associated 'role group') but a main difference is the flat nature of a role.
The hierarchical nature of a group makes that simple actions like installing a new module or adding a group to e.g. an menu item
causes the risk of automatic and uncontrolled granting of security rights.


With this approach every right must be granted explicitely to every role.
This implies an extra management cost which can be high and hence we advice to do a risk calculation before
choosing for this module.


In order to keep the cost of maintaining the security policies to an acceptable level the module has an Excel export/import function.

Creating a new role is as simple as exporting an existing one.
In the export file rights can be added/removed and the result can be reimported in a new role.


From a technical standpoint, this module doesn't make any changes to the Odoo kernel.
The role groups are used to enforce the security policy.

Default access rights on menus & actions
----------------------------------------

The standard Odoo approach is to give users access to all menu items and action bindings without a security group.
This approach is changed by this module.
Every menu item and action binding must be added explicitely to a role in order to be available for the user.

Default access rights on views
------------------------------

All standard groups are removed from the views.
In the current version of this module view access is as a consequence secured by a combination of

- view model ACL
- action bindings
- menu items

Also the groups inside view architecture are removed at view loading time.
The web modifier rules must be used in order to hide view elements.

Web modifier rules
------------------

The biggest difference is probably the 'web modifier rules' part which replaces the standard view inheritance mechanism when
e.g. some fields must be hidden for certain roles.
The web modifier rules have a 'priority' field which determines the winning rule in case you grant multiple roles to a single user.


Since complex environments may have a large number of web modifier rules this module allows to load a large ruleset without syntax checking.
Hence loading a new role from Excel may result in screen errors for the concerned users. A sanitize button is available in order to
check the syntax with autocorrection where feasible.

User Types / Internal User
--------------------------

In the current implementation of this module every user is added to the standard 'base.group_user (User Types / Internal User)' security group.
Most Odoo modules are adding new objects as well as ACLs on those new objects.
In many cases those standard ACLs are set for this 'base.group_user' group.

This may result in too much rights being granted to users since from an ACL standpoint new users receive the combined rights
of the 'group.group_user' ACL's and the ACLs of their role(s).

A removal of regular users from the 'base.group_user' group is currently under investigation.

Multi-Company setup
-------------------

Roles can be shared between companies.
In order to do so, you should adapt the default function on the res.role, company_id field.

Demo database
-------------

You can install the 'role_policy_demo' module in order to get a better feeling on how this module works.


Roadmap
-------

- fix missing fields when group on ORM field (e.g. res.partner,total_invoiced needs user to be in account_invoicing group)
- Excel import / export.
- Web modifier rules sanitize button
- Role Policy traceability
- Unit tests
- record rules
- role groups on views

