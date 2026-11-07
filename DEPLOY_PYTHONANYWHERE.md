# Deploy on PythonAnywhere

PythonAnywhere runs this Flask app through WSGI. A free Beginner account is enough for a demo; make sure you choose that account instead of a paid plan. The repository's bundled SQLite database contains a seeded administrator account, so rotate its password before making the site public.

## 1. Create the free account

Use the [direct Beginner account signup](https://www.pythonanywhere.com/registration/register/beginner/). It is the $0 option. If you land on the pricing page, select **Create a Beginner account** under **Explore with a limited account**; do not select Developer or a Custom plan. Current limits include one web app, one worker, 512 MiB storage, and a one-month expiry, so this is suitable for a demo rather than permanent hosting. See [current free account limits](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/).

## 2. Get the code and install dependencies

Create a PythonAnywhere account, open a Bash console, then run:

```bash
git clone https://github.com/rajesh081023/smart-public-transport.git
cd smart-public-transport
mkvirtualenv --python=/usr/local/bin/python3.11 smart-transport
pip install -r requirements.txt
```

Use `/usr/local/bin/python3.11` here. On PythonAnywhere's newer `innit` system image, the `/usr/bin/python3.11` symlink can create a broken virtualenv that fails to import `_posixsubprocess` when running `pip`. See [PythonAnywhere's virtualenv notes](https://help.pythonanywhere.com/pages/VirtualenvsExplained/).

## 3. Change the seeded administrator password

Run this before enabling the public app:

```bash
export DB_TYPE=sqlite
export SQLITE_DB="$PWD/smart_mobility.db"
python reset_admin_password.py
```

The script prompts for a new password and does not echo it. Do not use the seeded `admin@smartmobility.com` / `Admin@123` credentials on a public site.

## 4. Create the web app

In the PythonAnywhere **Web** tab, add a **Manual configuration** app using Python 3.11. Set its virtualenv to `/home/YOUR_USERNAME/.virtualenvs/smart-transport`.

Open the WSGI configuration file linked from that page and replace its Flask section with the following, filling in your PythonAnywhere username and a newly generated random secret. Keep this WSGI file private; it is outside the Git repository.

```python
import os
import sys

project_home = "/home/YOUR_USERNAME/smart-public-transport"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ["SECRET_KEY"] = "PASTE_A_NEW_RANDOM_SECRET_HERE"
os.environ["DB_TYPE"] = "sqlite"
os.environ["SQLITE_DB"] = os.path.join(project_home, "smart_mobility.db")

from app import app as application
```

Generate a secret in a PythonAnywhere Bash console with:

```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

Do not commit the generated secret or put it in `.env.example`.

## 5. Reload and open the site

Click **Reload** in the Web tab. PythonAnywhere will show the public URL for your account, typically `https://YOUR_USERNAME.pythonanywhere.com/`.

For the current free account limits and expiry, see [PythonAnywhere's free account features](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/). Their standard Flask setup uses a WSGI file and a virtualenv; see [the Flask setup guide](https://help.pythonanywhere.com/pages/Flask/).
