# VMS shell

Shell to interact with KOA VMS API

## Overview


## Install

```
pip install vms-shell
```

## Usage
The overall usage capabilities of this module are extensive, I would
recommend you leverage a good ide that can show all available functions
and arguments. I tried to ensure each function has a basic comment and
I have tested all functionality, but am always looking for ways to break
it in order to improve it.

**Initial Module Import:**
```
import guacamole
```

Defining session arguments and then list users

**syntax:**  
```
guacamole.session("https://{guacamole_base_url}", "{datasource}", "{username}", "{password}")
```

**example:**
```
session = guacamole.session("https://web.app/guacamole", "mysql", "guacadmin", "guacadmin")

session.list_users()
```