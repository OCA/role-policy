import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-role-policy",
    description="Meta package for oca-role-policy Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-role_policy',
        'odoo13-addon-role_policy_account',
        'odoo13-addon-role_policy_demo',
        'odoo13-addon-role_policy_sale',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
