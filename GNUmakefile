##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

PYTHON=$(shell which python)
HERE=$(PWD)
BOTO_DIR=$(HERE)/src/boto-2-8-0-31-JAN-13
ZP_DIR=$(HERE)/ZenPacks/zenoss/AWS
LIB_DIR=$(ZP_DIR)/lib
BIN_DIR=$(ZP_DIR)/bin

default: egg

egg:
	# setup.py will call 'make build' before creating the egg
	python setup.py bdist_egg

build:
	cd $(BOTO_DIR) ; \
		PYTHONPATH="$(PYTHONPATH):$(LIB_DIR)" \
		$(PYTHON) setup.py install \
		--install-lib="$(LIB_DIR)" \
		--install-scripts="$(BIN_DIR)"

clean:
	rm -rf lib build dist *.egg-info
	cd $(BOTO_DIR) ; rm -rf build dist *.egg-info