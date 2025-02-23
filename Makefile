INTERACTIVE_SHELL := podman exec -it chat-messaging-web /bin/bash

makemigrations:
	 $(INTERACTIVE_SHELL) -c "python manage.py makemigrations"

migrate:
	$(INTERACTIVE_SHELL) -c "python manage.py migrate"

django-shell:
	$(INTERACTIVE_SHELL) -c "python manage.py shell"

shell:
	$(INTERACTIVE_SHELL)
