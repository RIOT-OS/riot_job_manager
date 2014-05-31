PYTHON = /usr/bin/env python
VENV = venv

bootstrap: bootstrap_venv.py
	@$(PYTHON) $< $(VENV)

start_venv: bootstrap
	@. $(VENV)/bin/activate

install: start_venv

bootstrap_venv.py: create_bootstrap_venv.py
	@$(PYTHON) $(VENVFLAGS) $<
