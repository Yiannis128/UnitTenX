# Copyright 2025 Claudionor N. Coelho Jr
#
# if you set DEBUG=1, it tests with DEBUG turned on, which checks
# prints prompts and outputs at each step.
# if you set DEBUG>1, we will print messages from symbolic engine.

PROJECT = djbdns
WORK = test-djbdns
WORK_SERVER = test-djbdns-server

AGENT_REMOTE_VERSION = 10
USER = coelho
REMOTE_PASSWORD = '<YourPasswordHere>'
IP = `python $$UNIT_TEN_X/virtualbox.py ip FreeBSD`
MODEL_NAME =  openai

create_project:
	python $(UNIT_TEN_X)/scan_c_project.py $(PROJECT) -I$(PROJECT) \
		--cflags='-include /usr/include/errno.h' 

build_proj:
	-@rm -rf $(WORK)
	-mkdir $(WORK)
	python $(UNIT_TEN_X)/make_header.py --max-number-of-iterations=4 --work=$(WORK) \
		--model-name=$(MODEL_NAME)
	python $(UNIT_TEN_X)/auto_mockup.py $(PROJECT) -I$(PROJECT) \
		--filename=* --work=$(WORK) \
		--cflags='-include /usr/include/errno.h -ansi' --use-cache # --with-ssh
	python $(UNIT_TEN_X)/make_tail.py $(WORK)

build_server:
	-@rm -rf $(WORK_SERVER)
	-mkdir $(WORK_SERVER)
	python $(UNIT_TEN_X)/make_header.py --max-number-of-iterations=4 --work=$(WORK_SERVER) \
		--model-name=$(MODEL_NAME)
	python $(UNIT_TEN_X)/auto_mockup.py $(PROJECT) -I$(PROJECT) \
		--filename=$(PROJECT)/server.c --work=$(WORK_SERVER) \
		--cflags='-include /usr/include/errno.h -ansi' --use-cache
	python $(UNIT_TEN_X)/make_tail.py $(WORK_SERVER)

build_individual:
	make clean-proj
	-mkdir $(WORK)
	python $(UNIT_TEN_X)/make_header.py --max-number-of-iterations=4 --work=$(WORK) \
		--model-name=$(MODEL_NAME)
	python $(UNIT_TEN_X)/auto_mockup.py $(PROJECT) -I$(PROJECT) \
		--filename=$(PROJECT)/alloc.c --work=$(WORK) \
		--cflags='-include /usr/include/errno.h -ansi' --use-cache
	python $(UNIT_TEN_X)/auto_mockup.py $(PROJECT) -I$(PROJECT) \
		--filename=$(PROJECT)/byte_copy.c --work=$(WORK) \
		--cflags='-include /usr/include/errno.h -ansi' --use-cache
	python $(UNIT_TEN_X)/auto_mockup.py $(PROJECT) -I$(PROJECT) \
		--filename=$(PROJECT)/byte_diff.c --work=$(WORK) \
		--cflags='-include /usr/include/errno.h -ansi' --use-cache
	python $(UNIT_TEN_X)/auto_mockup.py $(PROJECT) -I$(PROJECT) \
		--filename=$(PROJECT)/uint16_unpack.c --work=$(WORK) \
		--cflags='-include /usr/include/errno.h -ansi' --use-cache
	python $(UNIT_TEN_X)/auto_mockup.py $(PROJECT) -I$(PROJECT) \
		--filename=$(PROJECT)/case_diffb.c --work=$(WORK) \
		--cflags='-include /usr/include/errno.h -ansi' --use-cache
	python $(UNIT_TEN_X)/auto_mockup.py $(PROJECT) -I$(PROJECT) \
		--filename=$(PROJECT)/dns_domain.c --work=$(WORK) \
		--cflags='-include /usr/include/errno.h -ansi' --use-cache
	python $(UNIT_TEN_X)/auto_mockup.py $(PROJECT) -I$(PROJECT) \
		--filename=$(PROJECT)/dns_packet.c --work=$(WORK) \
		--cflags='-include /usr/include/errno.h -ansi' --use-cache
	python $(UNIT_TEN_X)/auto_mockup.py $(PROJECT) -I$(PROJECT) \
		--filename=$(PROJECT)/tdlookup.c --work=$(WORK) \
		--cflags='-include /usr/include/errno.h -ansi' --use-cache
	python $(UNIT_TEN_X)/auto_mockup.py $(PROJECT) -I$(PROJECT) \
		--filename=$(PROJECT)/server.c --work=$(WORK) \
		--cflags='-include /usr/include/errno.h -ansi' --use-cache
	python $(UNIT_TEN_X)/make_tail.py $(WORK)

clean-proj:
	rm -rf $(WORK)

clean:
	rm -rf .cache

real-clean:
	rm -rf .cache $(WORK)
