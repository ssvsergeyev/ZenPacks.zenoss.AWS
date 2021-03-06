###########################################################################
#
# This program is part of Zenoss Core, an open source monitoring platform.
# Copyright (C) 2013 Zenoss Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 or (at your
# option) any later version as published by the Free Software Foundation.
#
# For complete information please visit: http://www.zenoss.com/oss/
#
###########################################################################

PYTHON=$(shell which python)
HERE=$(PWD)
BOTO_DIR=$(HERE)/src/boto
ZP_DIR=$(HERE)/ZenPacks/zenoss/AWS
LIB_DIR=$(ZP_DIR)/lib
BIN_DIR=$(ZP_DIR)/bin

default: egg

egg:
	# setup.py will call 'make build' before creating the egg
	python setup.py bdist_egg

build:
	mkdir -p $(LIB_DIR) $(BIN_DIR)
	cd $(BOTO_DIR) ; \
		PYTHONPATH="$(PYTHONPATH):$(LIB_DIR)" \
		$(PYTHON) setup.py install \
		--install-lib="$(LIB_DIR)" \
		--install-scripts="$(BIN_DIR)"

clean:
	rm -rf lib build dist *.egg-info $(BIN_DIR) $(LIB_DIR)
	cd $(BOTO_DIR) ; rm -rf build dist *.egg-info

json:
	cd ZenPacks/zenoss/AWS; \
	wget --quiet https://raw.github.com/garnaat/missingcloud/master/aws.json; \
	if [ -f aws.json.1 ]; then rm aws.json; mv aws.json.1 aws.json; fi

test:
	runtests ZenPacks.zenoss.AWS

pep8:
	./check_pep8.sh
