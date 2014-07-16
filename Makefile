#
# Top-level patch-through Makefile for TAU
# 
# John C. Linford <jlinford@paratools.com>
# June, 2014
#

# Set to 1 to force source code refresh on every build
DEVEL = 1

SRC = src
BUILD = build
RM = rm -rf

.PHONY: all install clean realclean configcheck
ifeq ($(DEVEL),1)
.PHONY: build
endif
.DEFAULT: install

all: install

install: configcheck
	$(MAKE) -C $(BUILD) install

clean: configcheck
	$(MAKE) -C $(BUILD) clean

configcheck: build
	@if [ ! -f build/Makefile ] ; then \
	  echo >&2 "ERROR: Please run configure before make"; \
	  false; \
	fi

build: 
	@echo "Updating source in build directory..."
	@mkdir -p $(BUILD)
	@cd $(SRC) && tar cpf - . | (cd "../$(BUILD)" && tar xf -)

realclean:
	$(RM) $(BUILD)
	$(RM) .active_stub*
	$(RM) .all_configs
	$(RM) .last_config
	$(RM) etc
	$(RM) examples
	$(RM) include
	$(RM) tools
	$(RM) x86_64
	$(RM) bgl
	$(RM) bgp
	$(RM) bgq
	$(RM) craycnl
	$(RM) apple
	$(RM) mic_linux

