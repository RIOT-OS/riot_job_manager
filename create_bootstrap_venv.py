#!/usr/bin/env python

import os, virtualenv, textwrap

output = virtualenv.create_bootstrap_script(textwrap.dedent("""
#!/usr/bin/env python

import os, subprocess

def after_install(option, home_dir):
    print "YOU NEED libgit2>=0.20.0 AND libxml2."
    subprocess.call([os.path.join(home_dir, 'bin', 'pip'),
                     'install',
                     'django',
                     'django-bootstrap3',
                     'django-model-utils',
                     'lxml',
                     'pygit2',
                     'python-social-auth'])
"""))
f = open('bootstrap_venv.py', 'w').write(output)
os.chmod('bootstrap_venv.py', 0775)
