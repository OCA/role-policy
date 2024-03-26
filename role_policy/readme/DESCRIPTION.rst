This module replaces the standard Odoo Security Groups by Roles.

When installing the module, all security groups are removed from users, actions and menu items.
When the user interface is loaded, the group definition within the XML screen maps are also ignored.

A role is equivalent to a group (every role has an associated 'role group'), but the main difference is the flat nature of a role.
Due to the hierarchical nature of a group, simple actions like installing a new module or adding a group to e.g. a menu item
may lead to automatic and uncontrolled granting of security rights.

With this approach, every right must be granted explicitely to every role.
This implies an extra management cost which can be high and hence we advice to do a risk calculation before
implementing this module.

In order to keep the cost of maintaining the security policies to an acceptable level, the module has an Excel export/import function.

Creating a new role is as simple as exporting an existing one.
In the export file, rights can be added/removed and the result can be reimported in a new role.

From a technical standpoint, this module does not make any changes to the Odoo kernel.
The role groups are used to enforce the security policy.

Default Access Rights on Menus, Actions & Fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The standard Odoo approach is to give users access to all menu items and action bindings without a security group.
This approach is changed by this module. Note: client actions can be added too!
Every menu item and action binding must be added explicitely to a role in order to be available for the user.

All standard groups are removed from the menus and actions except the 'untouchable groups'.
These are defaulted to:

- base.group_no_one
- base.group_erp_manager
- base.group_system
- base.group_portal
- base.group_public

Default Access Rights on Views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the current version of this module, view access is as a consequence secured by a combination of:

- view model ACLs
- action bindings
- menu items

Also the groups inside view architecture are removed at view loading time.

In order to compensate for the capability to add groups on view elements a new
attribute has been added: "roles" with attritue value a list of role codes.

The roles attribute works similar as the groups attribute:
the view element will be removed if a user does not belong to one of the specified roles.

|

Syntax:

.. code-block:: xml

  <button roles="R1, R2" name="button_name" type="object" />

The View Modifier Rules must be used in order to hide view elements.

View Modifier Rules
~~~~~~~~~~~~~~~~~~~

The biggest difference is probably the 'View Modifier Rules' part which replaces the standard view inheritance mechanism when
e.g. some fields need to be hidden for certain roles.
The View Modifier Rules have a *priority* field which determines the winning rule in case you grant multiple roles to a single user.

Combined roles may lead to unexpected results for the end user.
E.g. a user can have access to a button in a certain role but loose that access in a combined role.

A user with multiple roles is recommended to select the enabled role via his *Preferences* (by default, all his roles are combined).

The view/view element approach is different from the other role policy rules in the sense that every view/view element is sent to the user interface since the standard security groups are removed at view rendering time. We do not want to introduce the administrative burden to define every view/view element explicitly in the role.
As a consequence, unwanted view or view elements must be removed via the *remove* option.

The difference between *Invisible* and *Remove* is essential since *Invisible* implies that the user needs ACL access to the field that should not be rendered.

The View Modifier Rules also allow to set the modifiers of a certain element without specifying a view, e.g. to hide a certain field for all views on an object.
This can be further refined by applying a specific view type. The *Remove* option is not allowed without defining a view.

Since complex environments may have a large number of View Modifier Rules, this module allows to load a large ruleset without syntax checking.
Hence loading a new role from Excel may result in screen errors for the concerned users. A syntax check button will be made available in order to check the syntax with autocorrection where feasible.

View Type Attribute Rules
~~~~~~~~~~~~~~~~~~~~~~~~~

With this feature the view type attributes such as create, edit, delete, duplicate, import, export_xlsx become role-based.
Any such attribute can be replaced with these rules (e.g. role based decoration-%).

View Model Operation Rules
~~~~~~~~~~~~~~~~~~~~~~~~~~

With this feature a number of operations for the selected models become role-based.
Defining these operations will have an effect on all views defined on the model.

You can also set defaults for all models by specifying *default* as the model name.

Supported Operations:

- create
- edit
- delete
- duplicate
- export
- import
- archive

Model Methods
~~~~~~~~~~~~~

Via the "Model Methods" tab, you can grant execution rights to a set of predefined methods on ORM models.

The *role_policy* base module provides the framework for this feature.
Application-specific modules are required to extend the predefined set of methods.

Adding extra methods requires only a few lines of code.
It consists of extending a selection list with the Model Method,
adding a role_policy lookup to the method and pass the *role_policy_has_groups_ok* context.

e.g. the module *role_policy_account* adds the account.move,post method to this list

.. code-block::

    class AccountMove(models.Model):
        _inherit = "account.move"

        def post(self):
            self.env["model.method.execution.right"].check_right(
                "account.move,post", raise_exception=True
            )
            ctx = dict(self.env.context, role_policy_has_groups_ok=True)
            self = self.with_context(ctx)
            return super().post()

Methods defined in this set are available only for those roles which have added them in the *Model Methods* notebook page.

Combined Roles - Role Policy Selector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Combined roles may lead to unexpected results for the end user.
E.g. a user can have access to a button in a certain role but loose that access in a combined role.

The following rules have a priority field which determines the winning rule in case you grant multiple roles to a single user:

- View Modifier Rules
- View Type Attribute Rules
- View Model Operation Rules

whereby no rule for one of the user roles is considered highest priority.

This logic makes sense in certain business scenarios but can be completely faulty for other use cases.
In reality it's impossible to come to a maintainable set of roles and configure all possible use cases
for combined roles.

In a large organisation new roles will be added on a regular basis.
Maintaining a consistent set of rules so that this new role can be combined with all existing roles leads to millions of
combinations hence impossible to maintain.


A concrete example to illustrate the winning rule logic:

::

  Let's assume we have three roles: Back Office Sales (BO), Sales Manager (SM), Finance Manager (FM)

  Now we define the following View Modifier Rules on a Sale Order:

  - partner_id readonly=1 for role BO, with priority 2 for this rule.
  - partner_id readonly=0 for role FM, priority 1.
  - no partner_id rule for role SM

  Now the Finance Manager goes on leave and the security officer temporarily adds the FM role to a Back Office Sales employee.
  This person will now be able to change the partner_id on a Sale Order because of the highest priority rule wins.

  The SM will always be able to change the partner_id field since the standard Odoo Sale Order form allows this.
  If the SM temporarily needs to take over BO tasks and hence gets the two roles he will still be able to
  change the Sale Order partner_id field because no rule for one of the user roles is considered highest priority.

  But if we now add the partner_id rule to the SM role with readonly=0 and standard priority 16, than we get
  as result that the SM can update the partner_id in his SM role but looses this capability in the combined SM/BO role.


These types of conflicts should be resolved by either the creation of a new role, hence avoiding the need for combined roles.


In case someone needs to take over the activities of a colleague on temporarily basis, the creation of a new role is not realistic.


For that purpose the **Role Policy Selector** should be used.

Via the 'My Profile' form, the user can select his 'Enabled Roles' as a subset of the roles that he is entitled to.
By doing so he will get access to the capabilities of the Enabled Role(s) and not the combination of all his roles.


Admin User
~~~~~~~~~~

The Role Policy rules are NOT applied to the following users:

- base.user_admin
- base.user_root

This is done to avoid that the admin user can no longer correct mistakes (e.g. when disabling edit on res.users).

From a security standpoint it is recommended to use the admin account (base.user_admin) only in exceptional circumstances
and create other accounts with administration rights to maintain the Odoo configuration.

User Types / Internal User
~~~~~~~~~~~~~~~~~~~~~~~~~~
In the current implementation of this module every user is added to the standard 'base.group_user (User Types / Internal User)' security group.
Most Odoo modules are adding new objects as well as ACLs on those new objects.
In many cases those standard ACLs are set for this base.group_user* group.

This may result in too many rights being granted to users, since from an ACL standpoint new users receive the combined rights
of the *group.group_user* ACLs and the ACLs of their role(s).

A removal of regular users from the 'base.group_user' group is currently under investigation.

ACLs
~~~~

The only objects that are available when creating a new user are the objects with a:

- global ACL (e.g. res_country group_user_all which grants read access on res.country)
- *base.group_user* ACL (e.g. ir_ui_menu group_user which grants read access on ir.ui.menu)

When adding a user to one or more roles, this user will also get all the ACL rights defined within his role(s).

Multi-Company Setup
~~~~~~~~~~~~~~~~~~~

Roles can be shared between companies.
In order to do so, you should adapt the default function on the res.role, company_id field.

Import / Export
~~~~~~~~~~~~~~~

You can change an exported policy file to update a role or create a new role.

In order to remove entries, you should put 'X' in the column with 'Delete Entry' as column header.

Any rows starting with '#' will be ignored during the import.

Standard Groups Removal
~~~~~~~~~~~~~~~~~~~~~~~

The removal of the standard groups may result in unexpected behaviour since there are several modules
that use the standard groups hardcoded in python.

Example= in the Sale module we find the following code block:

.. code-block::

    def _compute_sales_count(self):
        r = {}
        self.sales_count = 0
        if not self.user_has_groups('sales_team.group_sale_salesman'):
            return r

This is not clean from a security administration standpoint, but it is the reality that companies using this module
have to cope with.
Only an experienced Odoo developer is able to find out and fix issues caused by this practice.

It is the intention to create a set of auto-install modules, called *role_policy_X* where *X* is the name of the module
where the methods with such a coding practice have been adapted. This way, the security officer can configure the roles
without depending heavily on Odoo development skills.

Cf. role_policy_sale as an example.

Demo Database
~~~~~~~~~~~~~

You can install the *role_policy_demo* module in order to get a better feeling on how this module works.
